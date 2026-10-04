import cv2
import numpy as np
import pytest

from app.services.document_processing.preprocessor import ImagePreprocessor
from app.services.image_io import ImageIOError, read_image_unicode_safe, write_image_unicode_safe


UNICODE_NAMES = [
    "Masaüstü",
    "İbrahim",
    "Osmanlı Belgesi.png",
    "şğüöçı",
    "belge_№1.png",
    "ascii_document.png",
]


def _bgr_image() -> np.ndarray:
    image = np.zeros((16, 24, 3), dtype=np.uint8)
    image[:, :, 0] = 17
    image[:, :, 1] = 93
    image[:, :, 2] = 211
    return image


@pytest.mark.parametrize("name", UNICODE_NAMES)
def test_unicode_safe_bgr_roundtrip(tmp_path, name):
    path = tmp_path / name
    if path.suffix.lower() != ".png":
        path = path / "Osmanlı Belgesi.png"

    image = _bgr_image()
    write_image_unicode_safe(path, image)
    loaded = read_image_unicode_safe(path)

    assert loaded.shape == image.shape
    assert loaded.dtype == image.dtype
    assert np.array_equal(loaded, image)


def test_unicode_safe_grayscale_roundtrip(tmp_path):
    path = tmp_path / "Masaüstü" / "şğüöçı" / "belge_№1.png"
    image = np.arange(12 * 18, dtype=np.uint8).reshape(12, 18)

    write_image_unicode_safe(path, image)
    loaded = read_image_unicode_safe(path, flags=cv2.IMREAD_GRAYSCALE)

    assert loaded.shape == image.shape
    assert loaded.dtype == image.dtype
    assert np.array_equal(loaded, image)


def test_unicode_safe_alpha_roundtrip(tmp_path):
    path = tmp_path / "İbrahim" / "Osmanlı Belgesi.png"
    image = np.zeros((10, 14, 4), dtype=np.uint8)
    image[:, :, 0] = 13
    image[:, :, 1] = 71
    image[:, :, 2] = 149
    image[:, :, 3] = 201

    write_image_unicode_safe(path, image)
    loaded = read_image_unicode_safe(path, flags=cv2.IMREAD_UNCHANGED)

    assert loaded.shape == image.shape
    assert loaded.dtype == image.dtype
    assert np.array_equal(loaded, image)


def test_unicode_safe_read_raises_meaningful_error(tmp_path):
    with pytest.raises(ImageIOError, match="could not be read"):
        read_image_unicode_safe(tmp_path / "Masaüstü" / "missing.png")


def test_preprocessor_process_with_profile_reads_unicode_path(tmp_path):
    path = tmp_path / "Masaüstü" / "İbrahim" / "Osmanlı Belgesi.png"
    image = _bgr_image()
    image[5:11, 4:20] = 0
    write_image_unicode_safe(path, image)

    processed, params, score = ImagePreprocessor().process_with_profile(str(path), "temiz_baski")

    assert processed.ndim == 2
    assert processed.shape == image.shape[:2]
    assert processed.dtype == image.dtype
    assert params["threshold_method"] == "otsu"
    assert 0.0 < score <= 1.0
