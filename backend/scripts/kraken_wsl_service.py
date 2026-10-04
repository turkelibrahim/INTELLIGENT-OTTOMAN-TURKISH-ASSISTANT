import argparse
import hashlib
import json
import logging
import signal
import threading
import time
from datetime import datetime, timezone
from email import policy
from email.parser import BytesParser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from io import BytesIO
from typing import Any, Dict


LOGGER = logging.getLogger("kraken_wsl_service")


class KrakenServiceState:
    def __init__(self, model_path: str, concurrency: int):
        self.model_path = model_path
        self.concurrency = max(1, int(concurrency))
        self.service_started_at = datetime.now(timezone.utc).isoformat()
        self.service_start_count = 1
        self.model_loaded = False
        self.model_loaded_at = None
        self.model_load_count = 0
        self.model_sha256 = None
        self.device = "unknown"
        self.cuda_available = False
        self.cuda_device_name = None
        self.request_count = 0
        self.error_message = None
        self.torch = None
        self.model = None
        self.rpred = None
        self.Image = None
        self.BBoxLine = None
        self.Segmentation = None
        self.lock = threading.Semaphore(self.concurrency)
        self.shutdown_requested = False

    def load_model(self) -> None:
        started = time.perf_counter()
        try:
            import torch
            from kraken.containers import BBoxLine, Segmentation
            from kraken.lib.models import load_any
            from kraken.rpred import rpred
            from PIL import Image

            self.torch = torch
            self.rpred = rpred
            self.Image = Image
            self.BBoxLine = BBoxLine
            self.Segmentation = Segmentation

            self.cuda_available = bool(torch.cuda.is_available())
            self.device = "cuda" if self.cuda_available else "cpu"
            self.cuda_device_name = torch.cuda.get_device_name(0) if self.cuda_available else None
            if hasattr(torch, "set_float32_matmul_precision"):
                torch.set_float32_matmul_precision("high")
            if hasattr(torch.backends, "cudnn"):
                torch.backends.cudnn.benchmark = True

            sha256_hash = hashlib.sha256()
            with open(self.model_path, "rb") as handle:
                for block in iter(lambda: handle.read(8192), b""):
                    sha256_hash.update(block)
            self.model_sha256 = sha256_hash.hexdigest()

            model = load_any(self.model_path)
            if self.device == "cuda" and hasattr(model, "to"):
                moved = model.to("cuda")
                if moved is not None:
                    model = moved
            if hasattr(model, "eval"):
                model.eval()
            self.model = model
            self.model_loaded = True
            self.model_loaded_at = datetime.now(timezone.utc).isoformat()
            self.model_load_count += 1
            self.error_message = None
            LOGGER.info(
                "Kraken model loaded once in %.2f ms on %s",
                (time.perf_counter() - started) * 1000,
                self.device,
            )
        except Exception as exc:
            self.error_message = repr(exc)
            LOGGER.exception("Kraken service startup failed")
            raise

    def health(self) -> Dict[str, Any]:
        return {
            "status": "ready" if self.model_loaded else "starting",
            "model_loaded": self.model_loaded,
            "service_start_count": self.service_start_count,
            "model_load_count": self.model_load_count,
            "model_loaded_at": self.model_loaded_at,
            "service_started_at": self.service_started_at,
            "device": self.device,
            "cuda_available": self.cuda_available,
            "cuda_device_name": self.cuda_device_name,
            "model_path": self.model_path,
            "model_sha256": self.model_sha256,
            "request_count": self.request_count,
            "concurrency": self.concurrency,
            "error_message": self.error_message,
        }

    def ocr(self, image_bytes: bytes, boxes: Dict[str, Any]) -> Dict[str, Any]:
        if not self.model_loaded or self.model is None:
            raise RuntimeError("Kraken model is not ready")
        started = time.perf_counter()
        acquired = time.perf_counter()
        with self.lock:
            queue_ms = (time.perf_counter() - acquired) * 1000
            inference_started = time.perf_counter()
            img = self.Image.open(BytesIO(image_bytes)).convert("RGB")
            lines = []
            for box_id, coords in boxes.items():
                lines.append(self.BBoxLine(id=str(box_id), bbox=[int(v) for v in coords]))
            seg = self.Segmentation(
                type="bbox",
                lines=lines,
                text_direction="horizontal-rl",
                imagename="memory-upload.png",
                script_detection=False,
            )
            if self.torch is not None and hasattr(self.torch, "inference_mode"):
                with self.torch.inference_mode():
                    records = list(self.rpred(network=self.model, im=img, bounds=seg))
            else:
                records = list(self.rpred(network=self.model, im=img, bounds=seg))
            inference_ms = (time.perf_counter() - inference_started) * 1000

        output_lines = []
        for index, record in enumerate(records):
            confidences = getattr(record, "confidences", None)
            confidence = float(sum(confidences) / len(confidences)) if confidences else 0.0
            output_lines.append(
                {
                    "id": str(index),
                    "text": getattr(record, "prediction", "") or "",
                    "confidence": confidence,
                }
            )
        self.request_count += 1
        return {
            "status": "success",
            "lines": output_lines,
            "timings": {
                "queue_ms": queue_ms,
                "inference_ms": inference_ms,
                "total_ms": (time.perf_counter() - started) * 1000,
            },
            "service_state": self.health(),
        }


STATE: KrakenServiceState | None = None


class Handler(BaseHTTPRequestHandler):
    server_version = "KrakenWSLService/1.0"

    def _send_json(self, status_code: int, payload: Dict[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_multipart(self) -> Dict[str, bytes]:
        content_type = self.headers.get("Content-Type", "")
        content_length = int(self.headers.get("Content-Length", "0") or "0")
        body = self.rfile.read(content_length)
        message = BytesParser(policy=policy.default).parsebytes(
            (
                f"Content-Type: {content_type}\r\n"
                "MIME-Version: 1.0\r\n\r\n"
            ).encode("utf-8")
            + body
        )
        fields: Dict[str, bytes] = {}
        if not message.is_multipart():
            return fields
        for part in message.iter_parts():
            name = part.get_param("name", header="content-disposition")
            if name:
                fields[name] = part.get_payload(decode=True) or b""
        return fields

    def do_GET(self) -> None:
        if self.path == "/health/live":
            self._send_json(200, {"status": "live", "service_start_count": STATE.service_start_count})
            return
        if self.path == "/health/ready":
            payload = STATE.health()
            self._send_json(200 if payload["model_loaded"] else 503, payload)
            return
        self._send_json(404, {"error": "not_found"})

    def do_POST(self) -> None:
        if self.path == "/shutdown":
            self._send_json(200, {"status": "shutting_down"})
            threading.Thread(target=self.server.shutdown, daemon=True).start()
            return
        if self.path != "/ocr":
            self._send_json(404, {"error": "not_found"})
            return
        try:
            content_type = self.headers.get("Content-Type", "")
            if "multipart/form-data" not in content_type:
                self._send_json(415, {"status": "error", "error_message": "multipart/form-data required"})
                return
            fields = self._read_multipart()
            image_bytes = fields.get("image")
            boxes_bytes = fields.get("boxes")
            if image_bytes is None or boxes_bytes is None:
                self._send_json(400, {"status": "error", "error_message": "image and boxes fields are required"})
                return
            boxes = json.loads(boxes_bytes.decode("utf-8"))
            self._send_json(200, STATE.ocr(image_bytes, boxes))
        except Exception as exc:
            LOGGER.exception("OCR request failed")
            self._send_json(500, {"status": "error", "error_message": str(exc)})

    def log_message(self, format: str, *args: Any) -> None:
        LOGGER.info("%s - %s", self.address_string(), format % args)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--model-path", required=True)
    parser.add_argument("--concurrency", type=int, default=1)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    global STATE
    STATE = KrakenServiceState(args.model_path, args.concurrency)
    STATE.load_model()

    httpd = ThreadingHTTPServer((args.host, args.port), Handler)
    signal.signal(signal.SIGTERM, lambda *_: httpd.shutdown())
    LOGGER.info("Kraken WSL service listening on %s:%s", args.host, args.port)
    httpd.serve_forever()
    LOGGER.info("Kraken WSL service stopped")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
