"""OCR pipeline diagnostics for locked Ottoman ground-truth pilots.

This module intentionally keeps pure geometry/order helpers separate from the
heavy EasyOCR runner so unit tests can exercise the risky logic quickly.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import statistics
from pathlib import Path
from typing import Iterable, Sequence


BBox = tuple[float, float, float, float]


@dataclass(frozen=True)
class BoxItem:
    id: str
    bbox: BBox
    text: str = ""
    confidence: float = 0.0


def as_bbox(value: Sequence[float]) -> BBox:
    if len(value) != 4:
        raise ValueError("bbox must contain four coordinates")
    x1, y1, x2, y2 = [float(item) for item in value]
    if x2 < x1:
        x1, x2 = x2, x1
    if y2 < y1:
        y1, y2 = y2, y1
    return (x1, y1, x2, y2)


def bbox_area(box: BBox) -> float:
    x1, y1, x2, y2 = box
    return max(0.0, x2 - x1) * max(0.0, y2 - y1)


def iou(box_a: BBox, box_b: BBox) -> float:
    ax1, ay1, ax2, ay2 = box_a
    bx1, by1, bx2, by2 = box_b
    ix1, iy1 = max(ax1, bx1), max(ay1, by1)
    ix2, iy2 = min(ax2, bx2), min(ay2, by2)
    intersection = bbox_area((ix1, iy1, ix2, iy2))
    union = bbox_area(box_a) + bbox_area(box_b) - intersection
    return intersection / union if union > 0 else 0.0


def vertical_overlap_ratio(box_a: BBox, box_b: BBox) -> float:
    """Return overlap divided by the shorter box height."""
    top = max(box_a[1], box_b[1])
    bottom = min(box_a[3], box_b[3])
    overlap = max(0.0, bottom - top)
    shorter = min(max(0.0, box_a[3] - box_a[1]), max(0.0, box_b[3] - box_b[1]))
    return overlap / shorter if shorter else 0.0


def merge_bboxes(boxes: Sequence[BBox]) -> BBox:
    if not boxes:
        raise ValueError("cannot merge empty bbox sequence")
    return (
        min(box[0] for box in boxes),
        min(box[1] for box in boxes),
        max(box[2] for box in boxes),
        max(box[3] for box in boxes),
    )


def suppress_duplicate_boxes(items: Sequence[BoxItem], threshold: float = 0.85) -> list[BoxItem]:
    kept: list[BoxItem] = []
    for item in sorted(items, key=lambda entry: (-entry.confidence, entry.id)):
        if all(iou(item.bbox, existing.bbox) < threshold for existing in kept):
            kept.append(item)
    return sorted(kept, key=lambda entry: entry.id)


def filter_noise_components(
    items: Sequence[BoxItem],
    *,
    page_size: tuple[int, int] | None = None,
    min_area: float = 25.0,
    min_height: float = 4.0,
    margin_ratio: float = 0.02,
) -> list[BoxItem]:
    width, height = page_size or (0, 0)
    kept: list[BoxItem] = []
    for item in items:
        x1, y1, x2, y2 = item.bbox
        if bbox_area(item.bbox) < min_area or (y2 - y1) < min_height:
            continue
        if page_size:
            margin_x = width * margin_ratio
            margin_y = height * margin_ratio
            if x2 < -margin_x or y2 < -margin_y or x1 > width + margin_x or y1 > height + margin_y:
                continue
        kept.append(item)
    return kept


def match_boxes(
    ground_truth: Sequence[BoxItem],
    detected: Sequence[BoxItem],
    iou_threshold: float = 0.5,
) -> dict:
    candidates: list[tuple[float, str, str]] = []
    for gt in ground_truth:
        for det in detected:
            score = iou(gt.bbox, det.bbox)
            if score >= iou_threshold:
                candidates.append((score, gt.id, det.id))
    matches: list[dict] = []
    used_gt: set[str] = set()
    used_det: set[str] = set()
    for score, gt_id, det_id in sorted(candidates, key=lambda item: (-item[0], item[1], item[2])):
        if gt_id in used_gt or det_id in used_det:
            continue
        used_gt.add(gt_id)
        used_det.add(det_id)
        matches.append({"gt_id": gt_id, "detected_id": det_id, "iou": score})
    precision = len(matches) / len(detected) if detected else 0.0
    recall = len(matches) / len(ground_truth) if ground_truth else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "iou_threshold": iou_threshold,
        "matches": matches,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "missed": [item.id for item in ground_truth if item.id not in used_gt],
        "extra": [item.id for item in detected if item.id not in used_det],
        "duplicate_boxes": max(0, len(detected) - len({item.bbox for item in detected})),
    }


def logical_line_items(
    components: Sequence[BoxItem],
    *,
    page_size: tuple[int, int] | None = None,
    y_tolerance_ratio: float = 0.48,
    vertical_overlap_threshold: float = 0.35,
    duplicate_iou_threshold: float = 0.9,
    min_area: float = 25.0,
    min_height: float = 4.0,
    id_prefix: str = "line",
) -> list[BoxItem]:
    """Build GT-independent logical line predictions from OCR components.

    The function uses only component geometry and text. It intentionally has no
    dependency on ground-truth models or tables; GT belongs in evaluation code.
    """
    clean = suppress_duplicate_boxes(
        filter_noise_components(components, page_size=page_size, min_area=min_area, min_height=min_height),
        threshold=duplicate_iou_threshold,
    )
    if not clean:
        return []
    heights = [item.bbox[3] - item.bbox[1] for item in clean if item.bbox[3] > item.bbox[1]]
    median_height = statistics.median(heights) if heights else min_height
    ordered = sorted(clean, key=lambda item: ((item.bbox[1] + item.bbox[3]) / 2, -item.bbox[2], item.id))
    lines: list[list[BoxItem]] = []
    for item in ordered:
        center_y = (item.bbox[1] + item.bbox[3]) / 2
        placed_at: int | None = None
        best_distance = float("inf")
        for index, line in enumerate(lines):
            line_box = merge_bboxes([entry.bbox for entry in line])
            line_center = (line_box[1] + line_box[3]) / 2
            line_height = max(median_height, line_box[3] - line_box[1])
            distance = abs(center_y - line_center)
            has_overlap = vertical_overlap_ratio(item.bbox, line_box) >= vertical_overlap_threshold
            if distance <= line_height * y_tolerance_ratio or has_overlap:
                if distance < best_distance:
                    placed_at = index
                    best_distance = distance
        if placed_at is None:
            lines.append([item])
        else:
            lines[placed_at].append(item)

    logical: list[BoxItem] = []
    for index, line in enumerate(lines):
        line.sort(key=lambda item: (-item.bbox[2], -item.bbox[0], item.id))
        merged = merge_bboxes([item.bbox for item in line])
        text_parts: list[str] = []
        seen: set[tuple[str, BBox]] = set()
        confidences: list[float] = []
        for item in line:
            key = (item.text, item.bbox)
            if key in seen:
                continue
            seen.add(key)
            if item.text:
                text_parts.append(item.text.strip())
            confidences.append(item.confidence)
        logical.append(
            BoxItem(
                f"{id_prefix}_{index:04d}",
                merged,
                " ".join(part for part in text_parts if part).strip(),
                statistics.mean(confidences) if confidences else 0.0,
            )
        )
    return sorted(logical, key=lambda item: (item.bbox[1], item.bbox[0], item.id))


def projection_profile_line_boxes(
    image,
    *,
    min_band_height: int = 8,
    gap_tolerance: int = 3,
    min_ink_pixels: int = 8,
    threshold: int = 210,
    horizontal_margin: int = 4,
) -> list[BoxItem]:
    """Detect line bands from ink-density without reading GT.

    `image` is kept untyped to avoid forcing Pillow as an import dependency for
    lightweight geometry tests that do not need image processing.
    """
    import numpy as np
    from PIL import ImageOps

    gray = ImageOps.grayscale(image)
    arr = np.array(gray)
    ink = arr < threshold
    row_counts = ink.sum(axis=1)
    active = row_counts >= min_ink_pixels
    bands: list[tuple[int, int]] = []
    start: int | None = None
    last = 0
    gap = 0
    for idx, value in enumerate(active):
        if value:
            if start is None:
                start = idx
            last = idx
            gap = 0
        elif start is not None:
            gap += 1
            if gap > gap_tolerance:
                if last - start + 1 >= min_band_height:
                    bands.append((start, last))
                start = None
                gap = 0
    if start is not None and last - start + 1 >= min_band_height:
        bands.append((start, last))

    items: list[BoxItem] = []
    for index, (top, bottom) in enumerate(bands):
        rows = ink[top : bottom + 1, :]
        cols = np.where(rows.any(axis=0))[0]
        if cols.size == 0:
            continue
        x1 = max(0, int(cols.min()) - horizontal_margin)
        x2 = min(image.width, int(cols.max()) + horizontal_margin + 1)
        items.append(BoxItem(f"projection_{index:04d}", (x1, float(top), x2, float(bottom + 1)), "", 1.0))
    return items


def hybrid_line_items(
    components: Sequence[BoxItem],
    bands: Sequence[BoxItem],
    *,
    id_prefix: str = "hybrid",
) -> list[BoxItem]:
    if not bands:
        return logical_line_items(components, id_prefix=id_prefix)
    lines: list[BoxItem] = []
    assigned: set[str] = set()
    for band_index, band in enumerate(sorted(bands, key=lambda item: item.bbox[1])):
        members = [
            item
            for item in components
            if vertical_overlap_ratio(item.bbox, band.bbox) >= 0.2
            or ((item.bbox[1] + item.bbox[3]) / 2 >= band.bbox[1] and (item.bbox[1] + item.bbox[3]) / 2 <= band.bbox[3])
        ]
        if not members:
            lines.append(BoxItem(f"{id_prefix}_{band_index:04d}", band.bbox, "", 0.0))
            continue
        for item in members:
            assigned.add(item.id)
        merged = merge_bboxes([band.bbox, *[item.bbox for item in members]])
        ordered = sorted(members, key=lambda item: (-item.bbox[2], -item.bbox[0], item.id))
        lines.append(
            BoxItem(
                f"{id_prefix}_{band_index:04d}",
                merged,
                " ".join(item.text.strip() for item in ordered if item.text).strip(),
                statistics.mean([item.confidence for item in ordered]) if ordered else 0.0,
            )
        )
    leftovers = [item for item in components if item.id not in assigned]
    if leftovers:
        lines.extend(logical_line_items(leftovers, id_prefix=f"{id_prefix}_extra"))
    return sorted(lines, key=lambda item: (item.bbox[1], item.bbox[0], item.id))


def component_coverage_metrics(
    ground_truth: Sequence[BoxItem],
    components: Sequence[BoxItem],
    *,
    coverage_iou_threshold: float = 0.05,
) -> dict:
    duplicate_count = max(0, len(components) - len(suppress_duplicate_boxes(components, threshold=0.9)))
    covered_counts: dict[str, int] = {}
    noise = 0
    for comp in components:
        covered = [gt for gt in ground_truth if iou(gt.bbox, comp.bbox) >= coverage_iou_threshold]
        if covered:
            for gt in covered:
                covered_counts[gt.id] = covered_counts.get(gt.id, 0) + 1
        else:
            noise += 1
    covered_lines = len(covered_counts)
    return {
        "prediction_representation": "raw_component",
        "component_count": len(components),
        "duplicate_count": duplicate_count,
        "covered_gt_lines": covered_lines,
        "component_coverage": covered_lines / len(ground_truth) if ground_truth else 0.0,
        "components_per_covered_gt_line": covered_counts,
        "noise_component_count": noise,
    }


def reading_order_metrics(expected_ids: Sequence[str], actual_ids: Sequence[str]) -> dict:
    expected = list(expected_ids)
    actual = [item for item in actual_ids if item in set(expected)]
    matched = [item for item in expected if item in set(actual)]
    coverage = len(matched) / len(expected) if expected else (1.0 if not actual else 0.0)
    if len(actual) < 2:
        pairwise = 1.0 if len(actual) == len(matched) and len(actual) <= 1 else 0.0
    else:
        expected_pos = {item: idx for idx, item in enumerate(expected)}
        correct = total = 0
        for i in range(len(actual)):
            for j in range(i + 1, len(actual)):
                total += 1
                if expected_pos[actual[i]] < expected_pos[actual[j]]:
                    correct += 1
        pairwise = correct / total if total else 0.0
    adjacent_total = max(0, len(expected) - 1)
    adjacent_correct = 0
    actual_pairs = {(actual[i], actual[i + 1]) for i in range(max(0, len(actual) - 1))}
    for idx in range(adjacent_total):
        if (expected[idx], expected[idx + 1]) in actual_pairs:
            adjacent_correct += 1
    adjacent = adjacent_correct / adjacent_total if adjacent_total else 1.0
    exact = expected == actual
    return {
        "matched_line_coverage": coverage,
        "pairwise_order_accuracy": pairwise,
        "adjacent_pair_accuracy": adjacent,
        "exact_sequence_match": exact,
        "unmatched_line_count": len([item for item in expected if item not in set(actual)]),
        "overall_reading_order": coverage * pairwise,
        "legacy_exact_position_accuracy": reading_order_accuracy(expected, actual),
    }


def group_rtl_lines(
    items: Sequence[BoxItem],
    y_tolerance_ratio: float = 0.55,
    min_height: float = 8.0,
) -> list[list[BoxItem]]:
    """Group visual line fragments top-to-bottom; order fragments right-to-left."""
    ordered = sorted(items, key=lambda item: ((item.bbox[1] + item.bbox[3]) / 2, -item.bbox[2], item.id))
    lines: list[list[BoxItem]] = []
    for item in ordered:
        height = max(min_height, item.bbox[3] - item.bbox[1])
        center_y = (item.bbox[1] + item.bbox[3]) / 2
        placed = False
        for line in lines:
            line_center = sum((entry.bbox[1] + entry.bbox[3]) / 2 for entry in line) / len(line)
            line_height = max(min_height, sum(entry.bbox[3] - entry.bbox[1] for entry in line) / len(line))
            if abs(center_y - line_center) <= max(height, line_height) * y_tolerance_ratio:
                line.append(item)
                placed = True
                break
        if not placed:
            lines.append([item])
    for line in lines:
        line.sort(key=lambda item: (-item.bbox[2], -item.bbox[0], item.id))
    lines.sort(key=lambda line: (min(item.bbox[1] for item in line), min(item.id for item in line)))
    return lines


def flatten_grouped_text(lines: Sequence[Sequence[BoxItem]]) -> list[str]:
    return [" ".join(item.text for item in line if item.text).strip() for line in lines]


def reading_order_accuracy(expected_ids: Sequence[str], actual_ids: Sequence[str]) -> float:
    if not expected_ids:
        return 1.0 if not actual_ids else 0.0
    hits = sum(1 for index, expected in enumerate(expected_ids) if index < len(actual_ids) and actual_ids[index] == expected)
    return hits / len(expected_ids)


def freeze_config(config: dict, output_path: Path) -> str:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(config, ensure_ascii=False, indent=2, sort_keys=True)
    output_path.write_text(data, encoding="utf-8")
    digest = hashlib.sha256(data.encode("utf-8")).hexdigest()
    output_path.with_suffix(output_path.suffix + ".sha256").write_text(digest + "\n", encoding="utf-8")
    return digest


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def combined_sha256(parts: Iterable[str]) -> str:
    digest = hashlib.sha256()
    for part in parts:
        digest.update(part.encode("utf-8"))
        digest.update(b"\n")
    return digest.hexdigest()


def horizontal_overlap_ratio(box_a: BBox, box_b: BBox) -> float:
    """Return horizontal overlap divided by the shorter box width."""
    left = max(box_a[0], box_b[0])
    right = min(box_a[2], box_b[2])
    overlap = max(0.0, right - left)
    shorter = min(max(0.0, box_a[2] - box_a[0]), max(0.0, box_b[2] - box_b[0]))
    return overlap / shorter if shorter else 0.0


def containment_ratio(inner: BBox, outer: BBox) -> float:
    """Return how much of inner is covered by outer."""
    ix1, iy1 = max(inner[0], outer[0]), max(inner[1], outer[1])
    ix2, iy2 = min(inner[2], outer[2]), min(inner[3], outer[3])
    intersection = bbox_area((ix1, iy1, ix2, iy2))
    area = bbox_area(inner)
    return intersection / area if area else 0.0


def remove_nested_boxes(items: Sequence[BoxItem], threshold: float = 0.92) -> list[BoxItem]:
    """Drop low-confidence boxes almost fully contained by another prediction."""
    ordered = sorted(items, key=lambda item: (-bbox_area(item.bbox), -item.confidence, item.id))
    kept: list[BoxItem] = []
    for item in ordered:
        if any(
            containment_ratio(item.bbox, existing.bbox) >= threshold
            and bbox_area(existing.bbox) >= bbox_area(item.bbox)
            and existing.confidence >= item.confidence
            for existing in kept
        ):
            continue
        kept.append(item)
    return sorted(kept, key=lambda item: item.id)


def clean_component_boxes(
    items: Sequence[BoxItem],
    *,
    page_size: tuple[int, int] | None = None,
    min_area: float = 25.0,
    min_height: float = 4.0,
    duplicate_iou_threshold: float = 0.9,
    nested_threshold: float = 0.92,
) -> list[BoxItem]:
    """Apply the Q5 component cleanup chain without consulting ground truth."""
    return remove_nested_boxes(
        suppress_duplicate_boxes(
            filter_noise_components(items, page_size=page_size, min_area=min_area, min_height=min_height),
            threshold=duplicate_iou_threshold,
        ),
        threshold=nested_threshold,
    )


def merge_adjacent_line_boxes(
    items: Sequence[BoxItem],
    *,
    y_tolerance_ratio: float = 0.55,
    vertical_overlap_threshold: float = 0.35,
    max_horizontal_gap_ratio: float = 0.08,
    page_width: float | None = None,
    id_prefix: str = "merged",
) -> list[BoxItem]:
    """Merge fragmented word or phrase boxes into logical RTL line boxes.

    This uses only detected geometry/text. It is suitable for validation/test
    evaluation because no ground-truth box or text value influences grouping.
    """
    if not items:
        return []
    width = page_width or max(item.bbox[2] for item in items)
    seed_lines = logical_line_items(
        items,
        y_tolerance_ratio=y_tolerance_ratio,
        vertical_overlap_threshold=vertical_overlap_threshold,
        id_prefix=f"{id_prefix}_seed",
    )
    merged: list[list[BoxItem]] = []
    for item in sorted(seed_lines, key=lambda entry: ((entry.bbox[1] + entry.bbox[3]) / 2, -entry.bbox[2], entry.id)):
        placed = False
        for group in merged:
            box = merge_bboxes([entry.bbox for entry in group])
            y_close = vertical_overlap_ratio(item.bbox, box) >= vertical_overlap_threshold
            center_delta = abs(((item.bbox[1] + item.bbox[3]) / 2) - ((box[1] + box[3]) / 2))
            height = max(item.bbox[3] - item.bbox[1], box[3] - box[1], 1.0)
            horizontal_gap = max(0.0, max(item.bbox[0], box[0]) - min(item.bbox[2], box[2]))
            if (y_close or center_delta <= height * y_tolerance_ratio) and horizontal_gap <= width * max_horizontal_gap_ratio:
                group.append(item)
                placed = True
                break
        if not placed:
            merged.append([item])
    output: list[BoxItem] = []
    for index, group in enumerate(merged):
        group.sort(key=lambda entry: (-entry.bbox[2], -entry.bbox[0], entry.id))
        output.append(
            BoxItem(
                f"{id_prefix}_{index:04d}",
                merge_bboxes([entry.bbox for entry in group]),
                " ".join(entry.text.strip() for entry in group if entry.text).strip(),
                statistics.mean([entry.confidence for entry in group]) if group else 0.0,
            )
        )
    return sorted(output, key=lambda item: (item.bbox[1], -item.bbox[2], item.id))


def arabic_script_ratio(text: str) -> float:
    letters = [char for char in text if not char.isspace()]
    if not letters:
        return 0.0
    arabic = [char for char in letters if "\u0600" <= char <= "\u06ff" or "\u0750" <= char <= "\u077f" or "\u08a0" <= char <= "\u08ff"]
    return len(arabic) / len(letters)


def assign_components_to_lines(
    lines: Sequence[BoxItem],
    components: Sequence[BoxItem],
    *,
    min_score: float = 0.15,
) -> dict:
    """Assign each OCR component to at most one predicted layout line.

    This is a production-side geometry routine: it consumes only predicted line
    boxes and OCR components, never ground-truth annotations.
    """
    assignments: dict[str, list[dict]] = {line.id: [] for line in lines}
    ambiguous = 0
    unassigned: list[str] = []
    for component in sorted(components, key=lambda item: (item.bbox[1], -item.bbox[2], item.id)):
        c_y = (component.bbox[1] + component.bbox[3]) / 2
        c_h = max(1.0, component.bbox[3] - component.bbox[1])
        scored: list[tuple[float, str, dict]] = []
        for line in lines:
            l_y = (line.bbox[1] + line.bbox[3]) / 2
            l_h = max(1.0, line.bbox[3] - line.bbox[1])
            overlap = vertical_overlap_ratio(component.bbox, line.bbox)
            center_distance = abs(c_y - l_y) / max(c_h, l_h, 1.0)
            center_inside = 1.0 if line.bbox[1] <= c_y <= line.bbox[3] else 0.0
            horizontal_relation = 1.0 if component.bbox[2] >= line.bbox[0] and component.bbox[0] <= line.bbox[2] else 0.0
            score = (0.42 * overlap) + (0.24 * center_inside) + (0.16 * max(0.0, 1.0 - center_distance)) + (0.10 * horizontal_relation) + (0.08 * max(0.0, min(1.0, component.confidence)))
            scored.append(
                (
                    score,
                    line.id,
                    {
                        "component_id": component.id,
                        "line_id": line.id,
                        "score": score,
                        "vertical_overlap": overlap,
                        "center_inside": bool(center_inside),
                        "normalized_center_distance": center_distance,
                        "confidence": component.confidence,
                        "reason": "best_geometric_score",
                    },
                )
            )
        scored.sort(key=lambda item: (-item[0], item[1]))
        if len(scored) > 1 and scored[0][0] - scored[1][0] < 0.03:
            ambiguous += 1
        if not scored or scored[0][0] < min_score:
            unassigned.append(component.id)
            continue
        assignments[scored[0][1]].append(scored[0][2])
    return {
        "assignments": assignments,
        "assigned_component_count": sum(len(value) for value in assignments.values()),
        "unassigned_component_ids": unassigned,
        "unassigned_component_count": len(unassigned),
        "ambiguous_component_count": ambiguous,
    }


def reconstruct_rtl_line_text(
    components: Sequence[BoxItem],
    *,
    join_gap_ratio: float = 0.18,
    low_confidence_threshold: float = 0.0,
) -> str:
    usable = [item for item in components if item.text and item.confidence >= low_confidence_threshold]
    if not usable:
        return ""
    heights = [max(1.0, item.bbox[3] - item.bbox[1]) for item in usable]
    median_height = statistics.median(heights) if heights else 1.0
    ordered = sorted(usable, key=lambda item: (-item.bbox[2], -item.bbox[0], item.id))
    parts: list[str] = []
    previous: BoxItem | None = None
    punctuation = set(".,;:!?،؛؟)")
    for item in ordered:
        text = item.text.strip()
        if not text:
            continue
        if previous is None:
            parts.append(text)
        else:
            gap = max(0.0, previous.bbox[0] - item.bbox[2])
            attach = gap / median_height <= join_gap_ratio or text[0] in punctuation or (parts and parts[-1][-1:] in punctuation or parts[-1][-1:] in "(/-")
            if attach and parts:
                parts[-1] = parts[-1] + text
            else:
                parts.append(text)
        previous = item
    return " ".join(part for part in parts if part).strip()


def score_recognition_candidate(candidate: dict) -> float:
    text = candidate.get("text", "") or ""
    if not text.strip():
        return -10.0
    length = len(text.replace(" ", ""))
    unique = len(set(text.replace(" ", "")))
    repeat_penalty = 0.0 if length == 0 else max(0.0, 1.0 - unique / max(1, length)) * 1.2
    noise = sum(1 for char in text if not char.isspace() and not ("\u0600" <= char <= "\u06ff") and not char.isdigit() and char not in ".,;:!?،؛؟-()[]") / max(1, length)
    return (
        2.0 * arabic_script_ratio(text)
        + 0.9 * float(candidate.get("confidence", 0.0) or 0.0)
        + 0.7 * float(candidate.get("component_coverage", 0.0) or 0.0)
        + 0.25 * min(1.0, length / max(1.0, float(candidate.get("expected_length_proxy", length) or length)))
        - repeat_penalty
        - noise
    )
