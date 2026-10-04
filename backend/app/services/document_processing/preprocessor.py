import os
import json
import time
from typing import Any, Dict, Optional, Tuple, List

import cv2
import numpy as np

from app.services.image_io import ImageIOError, read_image_unicode_safe, write_image_unicode_safe
from app.core.config import settings

class StageRecorder:
    def __init__(self, document_id: int, page_no: int):
        self.document_id = document_id
        self.page_no = page_no
        self.stages = []
        self.base_dir = os.path.join(settings.UPLOAD_DIR, "processed", str(document_id), f"page_{page_no}")
        os.makedirs(self.base_dir, exist_ok=True)
    
    def record_stage(self, stage_id: str, order: int, label: str, image: Optional[np.ndarray], status: str, metadata: dict, warnings: list, ocr_safe: bool = False, is_clean_copy: bool = False):
        stage_data = {
            "id": stage_id,
            "order": order,
            "label": label,
            "status": status,
            "image_url": None, 
            "metadata": metadata or {},
            "warnings": warnings or [],
            "ocr_safe": ocr_safe,
            "is_clean_copy": is_clean_copy
        }
        
        if image is not None and status == "COMPLETED":
            filename = f"{stage_id}.png"
            filepath = os.path.join(self.base_dir, filename)
            write_image_unicode_safe(filepath, image)
            stage_data["file_name"] = filename
            if image is not None:
                stage_data["metadata"]["Çıktı boyutu"] = f"{image.shape[1]} x {image.shape[0]}"
            
        self.stages.append(stage_data)
        
    def save_manifest(self):
        manifest_path = os.path.join(self.base_dir, "processing_manifest.json")
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump({
                "document_id": self.document_id, 
                "page_no": self.page_no, 
                "stages": self.stages
            }, f, ensure_ascii=False, indent=2)
        return manifest_path


class ImagePreprocessor:
    """OpenCV based preprocessing profiles for Ottoman document pages."""

    PROFILES = {
        "temiz_baski": {
            "denoise_h": 12,
            "clahe_clip": 2.5,
            "threshold_method": "otsu",
        },
        "lekeli_sayfa": {
            "denoise_h": 18,
            "clahe_clip": 4.0,
            "threshold_method": "adaptive",
        },
        "el_yazmasi": {
            "denoise_h": 5,
            "clahe_clip": 1.5,
            "threshold_method": None,
        },
    }

    def process_with_profile(
        self,
        image_path: str,
        profile: str,
        document_id: int = 0,
        page_no: int = 0,
        custom_params: Optional[Dict[str, Any]] = None,
    ) -> Tuple[np.ndarray, Dict[str, Any], float]:
        """Process an image file with a named or custom profile and record full pipeline stages."""
        try:
            image = read_image_unicode_safe(image_path)
        except ImageIOError as exc:
            raise ValueError(f"Goruntu okunamadi: {image_path}") from exc
        return self.process_image_array(image, profile, document_id, page_no, custom_params)

    def process(self, image: np.ndarray) -> Tuple[np.ndarray, Dict[str, Any]]:
        """Legacy compatibility wrapper. Auto-selects profile based on blur."""
        blur = cv2.Laplacian(self._to_gray(image), cv2.CV_64F).var()
        profile = "temiz_baski" if blur > 500 else "lekeli_sayfa"
        res, params, score = self.process_image_array(image, profile, 0, 0)
        return res, {"preprocessing_confidence": score, "profile": profile, "parameters": params, "blur_variance": blur}

    def process_image_array(
        self,
        image: np.ndarray,
        profile: str,
        document_id: int = 0,
        page_no: int = 0,
        custom_params: Optional[Dict[str, Any]] = None,
    ) -> Tuple[np.ndarray, Dict[str, Any], float]:
        params = self.PROFILES.get(profile, self.PROFILES["temiz_baski"]).copy()
        if custom_params:
            params.update(custom_params)

        recorder = StageRecorder(document_id, page_no)
        
        
        # 00 ORIGINAL
        recorder.record_stage(
            "00_original", 0, "Orijinal", image, "COMPLETED", 
            {"Aşama": "Orijinal", "Girdi boyutu": f"{image.shape[1]} x {image.shape[0]}"}, []
        )
        
        current_img = image.copy()
        original_gray = self._to_gray(image)
        
        # 01 ORIENTATION CORRECTION
        recorder.record_stage(
            "01_orientation", 1, "Yön Düzeltme", current_img, "SKIPPED",
            {"Aşama": "Yön Düzeltme", "Rotasyon açısı": 0}, 
            warnings=[], ocr_safe=False
        )

        # 02 PERSPECTIVE CORRECTION
        recorder.record_stage(
            "02_perspective", 2, "Perspektif Düzeltme", current_img, "SKIPPED",
            {"Aşama": "Perspektif Düzeltme"}, 
            warnings=["Belge konturu bulunamadı veya düzeltme gerekmedi."], ocr_safe=False
        )

        # 03 DESKEW
        deskewed_img, deskew_angle = self.correct_skew_with_angle(current_img)
        deskew_warnings = []
        if self._is_text_preservation_loss(original_gray, self._to_gray(deskewed_img)):
            deskew_warnings.append("Deskew OCR icin korumali moda alindi; metin korunumu dusuk.")
        
        # Always deskew if angle > 0.1 to maximize layout accuracy
        if abs(deskew_angle) >= 0.1 and not deskew_warnings:
            current_img = deskewed_img
            recorder.record_stage(
                "03_deskew", 3, "Eğrilik Düzeltme", current_img, "COMPLETED",
                {"Aşama": "Eğrilik Düzeltme", "Uygulanan Açı": f"{deskew_angle:.2f}°"}, []
            )
        else:
            recorder.record_stage(
                "03_deskew", 3, "Eğrilik Düzeltme", current_img, "SKIPPED",
                {"Aşama": "Eğrilik Düzeltme", "Tespit Edilen Açı": f"{deskew_angle:.2f}°"}, 
                ["Belge zaten düz veya eşiğin altında."]
            )

        # 04 GRAYSCALE
        if len(current_img.shape) == 3:
            current_img = cv2.cvtColor(current_img, cv2.COLOR_BGR2GRAY)
            recorder.record_stage("04_grayscale", 4, "Gri Tonlama", current_img, "COMPLETED", {}, [])
        else:
            recorder.record_stage("04_grayscale", 4, "Gri Tonlama", current_img, "SKIPPED", {}, ["Görüntü zaten tek kanallı."])

        # 05 DENOISE
        denoised_img = cv2.fastNlMeansDenoising(
            current_img, h=params["denoise_h"], searchWindowSize=21, templateWindowSize=7
        )
        current_img = denoised_img
        recorder.record_stage(
            "05_denoise", 5, "Gürültü Azaltma", current_img, "COMPLETED", 
            {"Denoise h": params["denoise_h"]}, []
        )

        # 06 BACKGROUND NORMALIZATION
        # Simple morphological background estimation
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (35, 35))
        background = cv2.morphologyEx(current_img, cv2.MORPH_DILATE, kernel)
        bg_normalized = cv2.divide(current_img, background, scale=255)
        current_img = bg_normalized
        recorder.record_stage(
            "06_background", 6, "Arka Plan Temizleme", current_img, "COMPLETED", 
            {"Yöntem": "Morphological Division"}, []
        )

        # 07 STAIN DETECTION
        recorder.record_stage("07_stain_detection", 7, "Leke Tespiti", current_img, "SKIPPED", {}, ["Kesin leke maskesi tespiti yapılmadı."])
        
        # 08 SAFE STAIN REMOVAL
        recorder.record_stage("08_stain_removal", 8, "Güvenli Leke Temizleme", current_img, "SKIPPED", {}, ["Maske olmadığı için atlandı."])

        # 09 CONTRAST ENHANCEMENT
        clahe = cv2.createCLAHE(clipLimit=params["clahe_clip"], tileGridSize=(8, 8))
        contrast_img = clahe.apply(current_img)
        current_img = contrast_img
        recorder.record_stage(
            "09_contrast", 9, "Kontrast İyileştirme", current_img, "COMPLETED", 
            {"CLAHE clip": params["clahe_clip"]}, []
        )

        # 10 THRESHOLDING
        thresh_method = params.get("threshold_method")
        thresholded_img = current_img.copy()
        if thresh_method == "otsu":
            _, thresholded_img = cv2.threshold(current_img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        elif thresh_method == "adaptive":
            thresholded_img = cv2.adaptiveThreshold(
                current_img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 15, 5
            )
        
        if thresh_method:
            current_img = thresholded_img
            recorder.record_stage(
                "10_threshold", 10, "Eşikleme", current_img, "COMPLETED", 
                {"Yöntem": thresh_method}, []
            )
        else:
            recorder.record_stage("10_threshold", 10, "Eşikleme", current_img, "SKIPPED", {}, ["Profil gereği atlandı."])

        # 11 SEGMENTATION PREVIEW
        recorder.record_stage("11_segmentation", 11, "Segmentasyon", current_img, "SKIPPED", {}, ["Görsel segmentasyon layout servisine bırakıldı."])

        # 12 OCR SAFE FINAL
        ocr_safe_final, ocr_safe_meta, ocr_safe_warnings = self.select_ocr_optimized_image(
            original=image,
            pipeline_candidate=current_img,
        )
        recorder.record_stage(
            "12_ocr_safe", 12, "OCR Güvenli Sonuç", ocr_safe_final, "COMPLETED", 
            {"Durum": "Kullanıma Hazır"}, [], ocr_safe=True
        )

        # 13 CLEAN DIGITAL COPY (Separate process optimized for human readability, not OCR)
        clean_digital_copy = self.generate_clean_digital_copy(image)
        recorder.record_stage(
            "13_clean_digital_copy", 13, "Temiz Dijital Kopya", clean_digital_copy, "COMPLETED",
            {"Hedef": "İnsan Okunabilirliği"}, [], is_clean_copy=True
        )

        recorder.save_manifest()
        
        score = self._calculate_confidence(image, ocr_safe_final)
        params["ocr_optimized_image"] = ocr_safe_meta
        if ocr_safe_warnings:
            params["warnings"] = ocr_safe_warnings
        return ocr_safe_final, params, score

    def select_ocr_optimized_image(
        self,
        *,
        original: np.ndarray,
        pipeline_candidate: np.ndarray,
    ) -> Tuple[np.ndarray, Dict[str, Any], List[str]]:
        """Select OCR input by text preservation instead of assuming binarization is best."""
        original_gray = self._to_gray(original)
        candidate_gray = self._to_gray(pipeline_candidate)

        _, original_otsu = cv2.threshold(
            original_gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
        )

        candidate_metrics = self._preservation_metrics(original_gray, candidate_gray)
        otsu_metrics = self._preservation_metrics(original_gray, original_otsu)

        selected = candidate_gray
        selected_name = "pipeline_candidate"
        selected_metrics = candidate_metrics
        warnings: List[str] = []

        if self._is_ocr_destructive(candidate_metrics):
            selected = original_otsu
            selected_name = "original_otsu"
            selected_metrics = otsu_metrics
            warnings.append(
                "Pipeline OCR adayi metin yapisini zayiflatti; OCR_OPTIMIZED_IMAGE original_otsu olarak secildi."
            )

        return selected, {
            "ocr_image_role": "OCR_OPTIMIZED_IMAGE",
            "selected_candidate": selected_name,
            "candidate_metrics": candidate_metrics,
            "selected_metrics": selected_metrics,
        }, warnings

    def generate_clean_digital_copy(self, image: np.ndarray) -> np.ndarray:
        """
        Generate a visually pleasing version for human viewing, distinct from OCR.
        Implements robust background estimation, stain reduction, and text protection.
        """
        if image is None:
            raise ValueError("Input image for clean digital copy is None.")

        # Ensure image is BGR
        if len(image.shape) == 2:
            clean = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        else:
            clean = image.copy()

        # 1. Estimate background using downsampled morphological opening
        scale = 0.25
        small = cv2.resize(clean, (0, 0), fx=scale, fy=scale)
        k_size = int(max(small.shape[0], small.shape[1]) * 0.05) | 1
        if k_size < 3: k_size = 3
        
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (k_size, k_size))
        bg_small = cv2.morphologyEx(small, cv2.MORPH_OPEN, kernel)
        bg_small = cv2.GaussianBlur(bg_small, (k_size, k_size), 0)
        
        # Upsample back to original size
        bg = cv2.resize(bg_small, (clean.shape[1], clean.shape[0]))
        
        # 2. Illumination Normalization (Divide by background)
        image_float = clean.astype(np.float32)
        bg_float = bg.astype(np.float32)
        bg_float[bg_float == 0] = 1.0 # avoid div zero
        
        # Target a readable parchment background without washing out the ink.
        normalized = (image_float / bg_float) * 235.0
        normalized = np.clip(normalized, 0, 255).astype(np.uint8)
        
        # 3. Color Cast Neutralization (Reduce saturation for archival look)
        hsv = cv2.cvtColor(normalized, cv2.COLOR_BGR2HSV)
        hsv[:, :, 1] = (hsv[:, :, 1] * 0.75).astype(np.uint8)
        color_corrected = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
        
        # 4. Text Protection Mask
        gray_norm = cv2.cvtColor(normalized, cv2.COLOR_BGR2GRAY)
        thresh = cv2.adaptiveThreshold(
            gray_norm, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 21, 10
        )
        kernel_dilate = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        text_mask = cv2.dilate(thresh, kernel_dilate, iterations=1)
        
        # 5. Background Stain Smoothing
        smoothed = cv2.bilateralFilter(color_corrected, d=9, sigmaColor=75, sigmaSpace=75)
        
        # Blend original dark ink back in for human readability.
        mask_3d = cv2.cvtColor(text_mask, cv2.COLOR_GRAY2BGR).astype(np.float32) / 255.0
        protected_text = np.minimum(clean.astype(np.float32), color_corrected.astype(np.float32))
        final = protected_text * mask_3d + smoothed * (1.0 - mask_3d)
        final = np.clip(final, 0, 255).astype(np.uint8)
        
        # 6. Text Enhancement (Mild CLAHE on L channel)
        lab = cv2.cvtColor(final, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=1.2, tileGridSize=(8, 8))
        l = clahe.apply(l)
        enhanced_lab = cv2.merge((l, a, b))
        final = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)
        
        return final

    def _to_gray(self, image: np.ndarray) -> np.ndarray:
        return image if len(image.shape) == 2 else cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    def _preservation_metrics(self, original_gray: np.ndarray, candidate_gray: np.ndarray) -> Dict[str, float]:
        _, original_binary = cv2.threshold(original_gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        _, candidate_binary = cv2.threshold(candidate_gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        original_foreground = float(np.count_nonzero(original_binary)) / float(original_binary.size)
        candidate_foreground = float(np.count_nonzero(candidate_binary)) / float(candidate_binary.size)
        original_components = self._count_text_components(original_binary)
        candidate_components = self._count_text_components(candidate_binary)

        original_edges = cv2.Canny(original_gray, 80, 160)
        candidate_edges = cv2.Canny(candidate_gray, 80, 160)
        edge_preservation = float(np.count_nonzero(candidate_edges & original_edges)) / max(
            1.0, float(np.count_nonzero(original_edges))
        )

        return {
            "foreground_ratio": round(candidate_foreground, 6),
            "foreground_preservation_ratio": round(candidate_foreground / max(original_foreground, 1e-6), 6),
            "connected_components": float(candidate_components),
            "component_preservation_ratio": round(candidate_components / max(original_components, 1), 6),
            "edge_preservation": round(edge_preservation, 6),
        }

    def _is_ocr_destructive(self, metrics: Dict[str, float]) -> bool:
        return (
            metrics["edge_preservation"] < 0.45
            or metrics["foreground_preservation_ratio"] > 2.2
            or metrics["component_preservation_ratio"] < 0.7
        )

    def _is_text_preservation_loss(self, original_gray: np.ndarray, candidate_gray: np.ndarray) -> bool:
        return self._preservation_metrics(original_gray, candidate_gray)["edge_preservation"] < 0.35

    def _count_text_components(self, binary: np.ndarray) -> int:
        count, _, stats, _ = cv2.connectedComponentsWithStats(binary, 8)
        components = 0
        for index in range(1, count):
            area = int(stats[index, cv2.CC_STAT_AREA])
            width = int(stats[index, cv2.CC_STAT_WIDTH])
            height = int(stats[index, cv2.CC_STAT_HEIGHT])
            if area >= 3 and width >= 1 and height >= 2:
                components += 1
        return components

    def correct_skew_with_angle(self, image: np.ndarray) -> Tuple[np.ndarray, float]:
        """Detect and correct small page skew where possible, returning the applied angle."""
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
            
        if len(np.unique(gray)) > 2:
            _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        elif np.mean(gray) > 127:
            thresh = cv2.bitwise_not(gray)
        else:
            thresh = gray.copy()

        coords = np.column_stack(np.where(thresh > 0))
        if len(coords) == 0:
            return image, 0.0

        rect = cv2.minAreaRect(coords)
        angle = rect[-1]
        if angle < -45:
            angle = -(90 + angle)
        else:
            angle = -angle

        if abs(angle) < 0.5:
            return image, angle

        height, width = image.shape[:2]
        center = (width // 2, height // 2)
        matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
        deskewed = cv2.warpAffine(
            image,
            matrix,
            (width, height),
            flags=cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_CONSTANT,
            borderValue=(255, 255, 255) if len(image.shape) == 3 else 255,
        )
        return deskewed, angle

    def _calculate_confidence(self, original: np.ndarray, processed: np.ndarray) -> float:
        """Estimate sharpness improvement as a bounded quality score."""
        if len(original.shape) == 3:
            gray_orig = cv2.cvtColor(original, cv2.COLOR_BGR2GRAY)
        else:
            gray_orig = original

        orig_blur = cv2.Laplacian(gray_orig, cv2.CV_64F).var()
        proc_blur = cv2.Laplacian(processed, cv2.CV_64F).var()
        if orig_blur == 0:
            return 0.5

        ratio = proc_blur / orig_blur
        score = min(0.99, 0.5 + (ratio - 1) * 0.1)
        return max(0.1, score)
