import argparse
import asyncio
import json
import os
import statistics
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any

import cv2
import numpy as np
import requests
from PIL import Image

BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_ROOT.parent
sys.path.insert(0, str(BACKEND_ROOT))

from app.services.document_processing.ocr_engine import OttomanOCREngine  # noqa: E402


SAMPLE = BACKEND_ROOT / "uploads" / "originals" / "82" / "82_191f0506.jpg"
EVIDENCE_DIR = REPO_ROOT / "evidence" / "performance_audit" / "1d"


class GPUSampler:
    def __init__(self) -> None:
        self.samples: list[dict[str, Any]] = []
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> dict[str, Any]:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2)
        gpu_values = [row["gpu_percent"] for row in self.samples]
        memory_values = [row["memory_used_mib"] for row in self.samples]
        return {
            "samples": len(self.samples),
            "avg_gpu_percent": statistics.fmean(gpu_values) if gpu_values else 0.0,
            "max_gpu_percent": max(gpu_values) if gpu_values else 0,
            "avg_memory_used_mib": statistics.fmean(memory_values) if memory_values else 0.0,
            "peak_memory_used_mib": max(memory_values) if memory_values else 0,
        }

    def _run(self) -> None:
        while not self._stop.is_set():
            try:
                output = subprocess.check_output(
                    [
                        "nvidia-smi",
                        "--query-gpu=timestamp,utilization.gpu,memory.used",
                        "--format=csv,noheader,nounits",
                    ],
                    text=True,
                    stderr=subprocess.DEVNULL,
                    timeout=2,
                ).strip()
                if output:
                    first = output.splitlines()[0]
                    timestamp, gpu, memory = [part.strip() for part in first.split(",")]
                    self.samples.append(
                        {
                            "timestamp": timestamp,
                            "gpu_percent": int(float(gpu)),
                            "memory_used_mib": int(float(memory)),
                        }
                    )
            except Exception:
                pass
            self._stop.wait(0.5)


def service_health() -> dict[str, Any] | None:
    try:
        response = requests.get("http://127.0.0.1:8765/health/ready", timeout=3)
        return response.json()
    except Exception:
        return None


async def run_ocr(mode: str, runs: int) -> dict[str, Any]:
    if mode == "legacy":
        os.environ["OCR_KRAKEN_SERVICE_URL"] = "http://127.0.0.1:1"
    else:
        os.environ["OCR_KRAKEN_SERVICE_URL"] = "http://127.0.0.1:8765"

    if not SAMPLE.exists():
        raise FileNotFoundError(SAMPLE)
    image_rgb = Image.open(SAMPLE).convert("RGB")
    image = cv2.cvtColor(np.array(image_rgb), cv2.COLOR_RGB2BGR)
    engine = OttomanOCREngine(enable_kraken=True, enable_easyocr=True, gpu=True)
    sampler = GPUSampler()
    sampler.start()
    measurements = []
    started = time.perf_counter()
    try:
        for index in range(runs):
            run_started = time.perf_counter()
            page = await engine.extract(image)
            elapsed_ms = (time.perf_counter() - run_started) * 1000
            measurements.append(
                {
                    "run": index + 1,
                    "elapsed_ms": elapsed_ms,
                    "reported_processing_time_ms": page.processing_time_ms,
                    "lines": len(page.lines),
                    "page_confidence": page.page_confidence,
                    "engine_name": page.engine_name,
                    "fallback_used": page.model_metadata.get("fallback_used"),
                    "actual_engine": page.model_metadata.get("actual_engine"),
                    "persistent_service": page.model_metadata.get("persistent_service"),
                    "text": "\n".join(line.text for line in page.lines),
                    "line_confidences": [line.confidence for line in page.lines],
                    "line_boxes": [line.bbox for line in page.lines],
                }
            )
    finally:
        gpu = sampler.stop()

    elapsed_values = [row["elapsed_ms"] for row in measurements]
    return {
        "timestamp": time.time(),
        "mode": mode,
        "sample": str(SAMPLE.relative_to(REPO_ROOT)),
        "runs": runs,
        "total_wall_ms": (time.perf_counter() - started) * 1000,
        "median_ms": statistics.median(elapsed_values) if elapsed_values else None,
        "mean_ms": statistics.fmean(elapsed_values) if elapsed_values else None,
        "min_ms": min(elapsed_values) if elapsed_values else None,
        "max_ms": max(elapsed_values) if elapsed_values else None,
        "measurements": measurements,
        "service_health_after": service_health(),
        "gpu_summary": gpu,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["legacy", "persistent"], required=True)
    parser.add_argument("--runs", type=int, default=1)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    payload = asyncio.run(run_ocr(args.mode, args.runs))
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    sys.stdout.buffer.write(json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8"))
    sys.stdout.buffer.write(b"\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
