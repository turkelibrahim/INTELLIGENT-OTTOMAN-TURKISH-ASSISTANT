import inspect
import json
from pathlib import Path

from app.services.evaluation import ocr_pipeline_optimization as opt
from app.services.evaluation.ocr_pipeline_optimization import (
    BoxItem,
    arabic_script_ratio,
    assign_components_to_lines,
    freeze_config,
    reconstruct_rtl_line_text,
    score_recognition_candidate,
    suppress_duplicate_boxes,
)


def test_component_to_line_assignment_is_one_to_one():
    lines = [BoxItem("l1", (0, 0, 200, 40)), BoxItem("l2", (0, 60, 200, 100))]
    components = [
        BoxItem("c1", (120, 8, 180, 32), "حق", 0.9),
        BoxItem("c2", (20, 70, 90, 92), "سطر", 0.8),
    ]
    result = assign_components_to_lines(lines, components)
    assert result["assigned_component_count"] == 2
    assert [item["component_id"] for item in result["assignments"]["l1"]] == ["c1"]
    assert [item["component_id"] for item in result["assignments"]["l2"]] == ["c2"]


def test_ambiguous_assignment_is_deterministic():
    lines = [BoxItem("a", (0, 0, 100, 40)), BoxItem("b", (0, 30, 100, 70))]
    components = [BoxItem("mid", (10, 28, 80, 42), "x", 0.5)]
    first = assign_components_to_lines(lines, components)
    second = assign_components_to_lines(list(reversed(lines)), components)
    assert first["assigned_component_count"] == 1
    assert first["assignments"] == second["assignments"]
    assert first["ambiguous_component_count"] >= 1


def test_duplicate_component_suppression_keeps_confident_box():
    items = [BoxItem("low", (0, 0, 100, 40), "a", 0.1), BoxItem("high", (1, 1, 101, 41), "a", 0.9)]
    assert [item.id for item in suppress_duplicate_boxes(items, threshold=0.8)] == ["high"]


def test_rtl_component_ordering_and_word_gap_joining():
    comps = [
        BoxItem("left", (0, 0, 40, 20), "لر", 0.9),
        BoxItem("right", (110, 0, 160, 20), "غازى", 0.9),
        BoxItem("middle", (55, 0, 100, 20), "لر", 0.9),
    ]
    assert reconstruct_rtl_line_text(comps, join_gap_ratio=0.1) == "غازى لر لر"
    assert reconstruct_rtl_line_text(comps, join_gap_ratio=1.0) == "غازىلرلر"


def test_punctuation_and_number_reconstruction():
    comps = [
        BoxItem("num", (120, 0, 150, 20), "١٢", 0.9),
        BoxItem("comma", (100, 0, 112, 20), "،", 0.9),
        BoxItem("word", (20, 0, 90, 20), "سنه", 0.9),
    ]
    assert reconstruct_rtl_line_text(comps, join_gap_ratio=0.2) == "١٢،سنه"


def test_low_confidence_and_empty_lines():
    assert reconstruct_rtl_line_text([]) == ""
    comps = [BoxItem("weak", (0, 0, 50, 20), "ضعيف", 0.1), BoxItem("ok", (70, 0, 120, 20), "قوى", 0.8)]
    assert reconstruct_rtl_line_text(comps, low_confidence_threshold=0.5) == "قوى"


def test_candidate_scoring_prefers_usable_ottoman_text():
    good = {"text": "عثمان غازى", "confidence": 0.8, "component_coverage": 1.0, "expected_length_proxy": 12}
    bad = {"text": "!!! 123 ___", "confidence": 0.95, "component_coverage": 1.0, "expected_length_proxy": 12}
    assert arabic_script_ratio(good["text"]) > 0.9
    assert score_recognition_candidate(good) > score_recognition_candidate(bad)


def test_hybrid_selection_without_ground_truth_leakage():
    source = (
        inspect.getsource(opt.assign_components_to_lines)
        + inspect.getsource(opt.reconstruct_rtl_line_text)
        + inspect.getsource(opt.score_recognition_candidate)
    ).lower()
    assert "ground_truth" not in source
    assert "gt_" not in source


def test_q5_frozen_config_hash_matches():
    path = Path("..") / "evidence" / "line_segmentation_q5" / "selected_line_strategy.json"
    digest = opt.hashlib.sha256(json.dumps(json.loads(path.read_text(encoding="utf-8")), ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8")).hexdigest()
    assert digest == "310d5a33874e38194d31101a26a83b0bb2c415af6a3209fb4c15d61fa9316373"


def test_q6_config_freeze_hash(tmp_path):
    digest = freeze_config({"candidate": "hybrid", "split": "development_only"}, tmp_path / "selected_hybrid_config.json")
    assert len(digest) == 64
    assert (tmp_path / "selected_hybrid_config.json.sha256").read_text().strip() == digest
