from pathlib import Path
from typing import Union

import cv2
import numpy as np


PathLike = Union[str, Path]


class ImageIOError(ValueError):
    """Raised when an image cannot be safely read from or written to disk."""


def read_image_unicode_safe(path: PathLike, flags: int = cv2.IMREAD_COLOR) -> np.ndarray:
    """Read an image through bytes so Windows Unicode paths do not reach cv2.imread."""
    image_path = Path(path)
    try:
        data = image_path.read_bytes()
    except OSError as exc:
        raise ImageIOError(f"Image file could not be read: {image_path}") from exc

    if not data:
        raise ImageIOError(f"Image file is empty: {image_path}")

    buffer = np.frombuffer(data, dtype=np.uint8)
    image = cv2.imdecode(buffer, flags)
    if image is None:
        raise ImageIOError(f"Image bytes could not be decoded by OpenCV: {image_path}")
    return image


def write_image_unicode_safe(path: PathLike, image: np.ndarray) -> None:
    """Write an OpenCV image through encoded bytes so Windows Unicode paths are safe."""
    image_path = Path(path)
    if image is None or not isinstance(image, np.ndarray) or image.size == 0:
        raise ImageIOError(f"Image array is empty or invalid for write: {image_path}")

    extension = image_path.suffix or ".png"
    success, encoded = cv2.imencode(extension, image)
    if not success or encoded is None:
        raise ImageIOError(f"Image array could not be encoded as {extension}: {image_path}")

    try:
        image_path.parent.mkdir(parents=True, exist_ok=True)
        image_path.write_bytes(encoded.tobytes())
    except OSError as exc:
        raise ImageIOError(f"Encoded image could not be written: {image_path}") from exc
