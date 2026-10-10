import os
import base64
import time
import httpx
import logging
import cv2
import numpy as np
from app.core.config import settings

logger = logging.getLogger(__name__)

class NvidiaVisionOCR:
    def __init__(self):
        self.api_key = settings.NVIDIA_API_KEY
        self.base_url = settings.NVIDIA_BASE_URL
        self.model = getattr(settings, "NVIDIA_VISION_MODEL", "meta/llama-3.2-11b-vision-instruct")
        
    def _encode_image(self, image: np.ndarray) -> str:
        # Convert BGR (OpenCV) or RGB to JPEG base64
        # Assuming safe_image is already a numpy array from preprocessor
        if len(image.shape) == 2:
            # Grayscale to BGR
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        
        success, buffer = cv2.imencode(".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, 85])
        if not success:
            raise ValueError("Failed to encode image to JPEG")
            
        return base64.b64encode(buffer).decode('utf-8')

    async def extract_text(self, image: np.ndarray) -> tuple[str, float, float]:
        """
        Extracts text from an image using NVIDIA's vision model.
        Returns: (text, confidence, duration_ms)
        """
        if not self.api_key or not settings.NVIDIA_ENABLED:
            logger.warning("NVIDIA Vision API is disabled or missing API key.")
            return "", 0.0, 0.0

        base64_img = self._encode_image(image)
        
        prompt = (
            "Sen bir Osmanlı paleografyası uzmanısın. Lütfen bu görüntüdeki Osmanlıca metni tam ve doğru bir şekilde, "
            "Milli Eğitim Bakanlığı veya TDK transkripsiyon kurallarına göre Türkçe Latin alfabesine aktar. "
            "Sadece okunmuş metni ver, açıklama yapma. Eger belge okunamayacak kadar kotu ise bos dondur."
        )

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_img}"}}
                    ]
                }
            ],
            "max_tokens": 1024,
            "temperature": 0.0
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

        start_time = time.perf_counter()
        
        try:
            async with httpx.AsyncClient(timeout=45.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                data = response.json()
                
                duration_ms = (time.perf_counter() - start_time) * 1000
                text = data["choices"][0]["message"]["content"].strip()
                
                # We assign a synthetic confidence based on how much text was found
                # and lack of error messages.
                confidence = 0.85 if len(text) > 5 else 0.4
                
                return text, confidence, duration_ms
                
        except Exception as e:
            logger.error(f"NVIDIA Vision OCR failed: {e}")
            duration_ms = (time.perf_counter() - start_time) * 1000
            return "", 0.0, duration_ms
