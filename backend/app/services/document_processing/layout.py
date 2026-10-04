from dataclasses import dataclass
from typing import List, Sequence, Tuple

import cv2
import numpy as np


@dataclass(frozen=True)
class LineRegion:
    """Detected text-line region in image coordinates."""

    x: int
    y: int
    width: int
    height: int
    order_index: int
    column_index: int

    @property
    def bbox(self) -> Tuple[int, int, int, int]:
        return self.x, self.y, self.width, self.height


class LayoutAnalyzer:
    """Detect line-like regions and sort them for right-to-left documents."""

    def detect_lines(self, image: np.ndarray, rtl: bool = True) -> List[LineRegion]:
        boxes = self._find_line_boxes(image)
        ordered = self.order_boxes(boxes, rtl=rtl)
        return [
            LineRegion(
                x=x,
                y=y,
                width=w,
                height=h,
                order_index=index,
                column_index=column,
            )
            for index, (column, (x, y, w, h)) in enumerate(ordered)
        ]

    def order_boxes(
        self,
        boxes: Sequence[Tuple[int, int, int, int]],
        rtl: bool = True,
    ) -> List[Tuple[int, Tuple[int, int, int, int]]]:
        columns = self._cluster_columns(boxes)
        if rtl:
            columns.sort(key=lambda column: max(x + w for x, _, w, _ in column), reverse=True)
        else:
            columns.sort(key=lambda column: min(x for x, _, _, _ in column))

        ordered: List[Tuple[int, Tuple[int, int, int, int]]] = []
        for column_index, column in enumerate(columns):
            for box in sorted(column, key=lambda item: (item[1], item[0])):
                ordered.append((column_index, box))
        return ordered

    def _find_line_boxes(self, image: np.ndarray) -> List[Tuple[int, int, int, int]]:
        gray = self._to_gray(image)
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        kernel_width = max(12, gray.shape[1] // 40)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_width, 3))
        merged = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=1)
        contours, _ = cv2.findContours(merged, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        boxes = []
        min_area = max(10, int(gray.shape[0] * gray.shape[1] * 0.0002))
        for contour in contours:
            x, y, width, height = cv2.boundingRect(contour)
            if width * height >= min_area and width >= 8 and height >= 3:
                boxes.append((x, y, width, height))
        return boxes

    def _cluster_columns(
        self,
        boxes: Sequence[Tuple[int, int, int, int]],
    ) -> List[List[Tuple[int, int, int, int]]]:
        columns: List[List[Tuple[int, int, int, int]]] = []
        for box in sorted(boxes, key=lambda item: item[0]):
            x, _, width, _ = box
            center = x + width / 2
            for column in columns:
                left = min(item[0] for item in column)
                right = max(item[0] + item[2] for item in column)
                margin = max(20, (right - left) * 0.25)
                if left - margin <= center <= right + margin:
                    column.append(box)
                    break
            else:
                columns.append([box])
        return columns

    def _to_gray(self, image: np.ndarray) -> np.ndarray:
        if len(image.shape) == 2:
            return image
        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
