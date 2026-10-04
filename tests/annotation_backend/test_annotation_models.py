import pytest
from pydantic import ValidationError
from backend.app.schemas.annotation import AnnotationLineCreate, BBox

def test_bbox_validation():
    with pytest.raises(ValidationError):
        BBox(x=-1, y=0, width=10, height=10)
    with pytest.raises(ValidationError):
        BBox(x=0, y=0, width=-1, height=10)

def test_transcription_validation():
    # Valid
    AnnotationLineCreate(line_order=1, bbox_json=BBox(x=0, y=0, width=10, height=10), transcription="test")
    # Empty
    with pytest.raises(ValidationError):
        AnnotationLineCreate(line_order=1, bbox_json=BBox(x=0, y=0, width=10, height=10), transcription="")
    # Whitespace
    with pytest.raises(ValidationError):
        AnnotationLineCreate(line_order=1, bbox_json=BBox(x=0, y=0, width=10, height=10), transcription="   ")
    # Control chars
    with pytest.raises(ValidationError):
        AnnotationLineCreate(line_order=1, bbox_json=BBox(x=0, y=0, width=10, height=10), transcription="test\x00")
