import numpy as np
from app.services.document_processing.layout import LayoutAnalyzer

def test_layout_analyzer_detects_lines():
    analyzer = LayoutAnalyzer()
    
    # Create synthetic image with two black lines
    image = np.full((100, 100), 255, dtype=np.uint8)
    image[20:30, 10:90] = 0  # top line
    image[60:70, 10:90] = 0  # bottom line
    
    lines = analyzer.detect_lines(image, rtl=True)
    
    assert len(lines) == 2
    
    # RTL order check - for single column, top to bottom or bottom to top?
    # Actually rtl just orders right to left columns. For 1 column, it's just top to bottom
    assert lines[0].order_index == 0
    assert lines[1].order_index == 1
