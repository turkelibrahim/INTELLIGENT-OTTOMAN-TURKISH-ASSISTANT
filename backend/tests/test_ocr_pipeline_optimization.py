import json
from pathlib import Path

from app.services.evaluation.ocr_pipeline_optimization import (
    BoxItem,
    freeze_config,
    group_rtl_lines,
    iou,
    match_boxes,
    reading_order_accuracy,
    suppress_duplicate_boxes,
)


def test_iou_and_box_matching():
    gt = [BoxItem("g1", (0, 0, 100, 50)), BoxItem("g2", (0, 60, 100, 110))]
    det = [BoxItem("d1", (5, 5, 95, 45)), BoxItem("d2", (200, 200, 260, 260))]
    assert iou(gt[0].bbox, det[0].bbox) > 0.7
    result = match_boxes(gt, det, iou_threshold=0.5)
    assert result["precision"] == 0.5
    assert result["recall"] == 0.5
    assert result["missed"] == ["g2"]
    assert result["extra"] == ["d2"]


def test_duplicate_suppression_keeps_highest_confidence():
    items = [
        BoxItem("a", (0, 0, 100, 50), confidence=0.2),
        BoxItem("b", (1, 1, 101, 51), confidence=0.9),
        BoxItem("c", (0, 80, 100, 130), confidence=0.1),
    ]
    kept = suppress_duplicate_boxes(items, threshold=0.8)
    assert [item.id for item in kept] == ["b", "c"]


def test_group_rtl_single_box_lines_and_mixed_input():
    items = [
        BoxItem("line2", (100, 100, 200, 130), "second"),
        BoxItem("line1", (100, 10, 200, 40), "first"),
    ]
    grouped = group_rtl_lines(items)
    assert [[item.id for item in line] for line in grouped] == [["line1"], ["line2"]]


def test_group_rtl_three_segments_same_line():
    items = [
        BoxItem("left", (10, 10, 60, 40), "C"),
        BoxItem("right", (180, 12, 240, 42), "A"),
        BoxItem("middle", (90, 11, 150, 41), "B"),
    ]
    grouped = group_rtl_lines(items)
    assert [[item.id for item in line] for line in grouped] == [["right", "middle", "left"]]


def test_group_rtl_near_but_separate_lines():
    items = [
        BoxItem("top", (10, 10, 100, 25)),
        BoxItem("bottom", (10, 40, 100, 55)),
    ]
    grouped = group_rtl_lines(items, y_tolerance_ratio=0.25)
    assert [[item.id for item in line] for line in grouped] == [["top"], ["bottom"]]


def test_header_body_noise_and_deterministic_order():
    items = [
        BoxItem("noise", (-200, -200, -100, -100)),
        BoxItem("body_b", (50, 100, 120, 130)),
        BoxItem("body_a", (150, 100, 220, 130)),
        BoxItem("header", (80, 10, 180, 40)),
    ]
    grouped = group_rtl_lines(items)
    assert [[item.id for item in line] for line in grouped] == [["noise"], ["header"], ["body_a", "body_b"]]


def test_reading_order_accuracy_and_config_freeze(tmp_path: Path):
    assert reading_order_accuracy(["a", "b", "c"], ["a", "x", "c"]) == 2 / 3
    config = {"padding": 8, "decoder": {"beamWidth": 5}, "split_policy": "dev_only"}
    digest = freeze_config(config, tmp_path / "selected_config.json")
    assert len(digest) == 64
    assert (tmp_path / "selected_config.json.sha256").read_text().strip() == digest
    assert json.loads((tmp_path / "selected_config.json").read_text())["split_policy"] == "dev_only"
