from app.services.evaluation.ocr_pipeline_optimization import (
    BoxItem,
    clean_component_boxes,
    containment_ratio,
    horizontal_overlap_ratio,
    merge_adjacent_line_boxes,
    reading_order_metrics,
)


def test_containment_and_horizontal_overlap_ratios():
    assert containment_ratio((10, 10, 20, 20), (0, 0, 30, 30)) == 1.0
    assert horizontal_overlap_ratio((0, 0, 100, 20), (50, 5, 150, 25)) == 0.5


def test_clean_component_boxes_removes_noise_duplicates_and_nested_boxes():
    items = [
        BoxItem("noise", (0, 0, 3, 3), confidence=0.9),
        BoxItem("large", (10, 10, 110, 40), confidence=0.95),
        BoxItem("nested", (20, 15, 60, 35), confidence=0.3),
        BoxItem("duplicate", (11, 11, 111, 41), confidence=0.2),
        BoxItem("other", (10, 80, 110, 110), confidence=0.8),
    ]

    kept = clean_component_boxes(items, min_area=25, min_height=4, duplicate_iou_threshold=0.8)

    assert [item.id for item in kept] == ["large", "other"]


def test_merge_adjacent_line_boxes_combines_fragments_rtl_without_gt():
    items = [
        BoxItem("right", (200, 10, 250, 35), "A", 0.9),
        BoxItem("middle", (130, 12, 180, 37), "B", 0.8),
        BoxItem("left", (60, 11, 110, 36), "C", 0.7),
        BoxItem("next", (190, 80, 240, 105), "D", 0.6),
    ]

    merged = merge_adjacent_line_boxes(
        items,
        y_tolerance_ratio=0.6,
        vertical_overlap_threshold=0.35,
        max_horizontal_gap_ratio=0.20,
        page_width=300,
    )

    assert len(merged) == 2
    assert merged[0].text == "A B C"
    assert merged[0].bbox == (60, 10, 250, 37)
    assert merged[1].text == "D"


def test_q5_reading_order_metrics_report_pairwise_and_coverage():
    metrics = reading_order_metrics(["r1", "r2", "l1", "l2"], ["r1", "r2", "l2", "l1"])

    assert metrics["matched_line_coverage"] == 1.0
    assert 0.0 < metrics["pairwise_order_accuracy"] < 1.0
    assert metrics["exact_sequence_match"] is False
