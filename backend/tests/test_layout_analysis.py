import numpy as np

from app.services.document_processing.layout import LayoutAnalyzer


def _two_column_fixture():
    image = np.full((180, 260), 255, dtype=np.uint8)
    # Right column, two lines.
    image[30:42, 160:240] = 0
    image[70:82, 150:230] = 0
    # Left column, two lines.
    image[35:47, 25:105] = 0
    image[75:87, 35:115] = 0
    return image


def test_layout_detects_line_regions_with_coordinates():
    lines = LayoutAnalyzer().detect_lines(_two_column_fixture())

    assert len(lines) == 4
    assert all(line.width > 40 for line in lines)
    assert all(line.height >= 10 for line in lines)
    assert [line.order_index for line in lines] == [0, 1, 2, 3]


def test_rtl_reading_order_is_right_column_then_left_column_top_down():
    lines = LayoutAnalyzer().detect_lines(_two_column_fixture(), rtl=True)

    assert [line.column_index for line in lines] == [0, 0, 1, 1]
    assert lines[0].x > lines[2].x
    assert lines[0].y < lines[1].y
    assert lines[2].y < lines[3].y


def test_ltr_reading_order_is_left_column_then_right_column_top_down():
    lines = LayoutAnalyzer().detect_lines(_two_column_fixture(), rtl=False)

    assert [line.column_index for line in lines] == [0, 0, 1, 1]
    assert lines[0].x < lines[2].x
    assert lines[0].y < lines[1].y
    assert lines[2].y < lines[3].y
