import datetime as dt
import json
import os
import statistics
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

import requests

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
EVIDENCE_ROOT = ROOT / "evidence" / "performance_audit"
EVIDENCE = EVIDENCE_ROOT / "1c"
API_BASE = "http://127.0.0.1:8000/api/v1"
OLLAMA_BASE = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", os.getenv("LLM_MODEL", "qwen3.5:4b"))
SAMPLE_FILE = BACKEND / "uploads" / "originals" / "82" / "82_191f0506.jpg"


OTTOMAN_LINES = [
    "كتاب دولت مكتب تاريخ استانبول",
    "حواله ياپدى قرداش اوغلى آق تيمورى",
    "بو فرمان موجب عمل اوله",
    "محكمه دفترنده قيد اولندى",
    "تاريخ سنه ١٣٢٧",
    "صاحب عرض حال محمد امين",
    "باب عالىه takdim kılındı",
    "مهر و امضا محللنده",
    "استانبول vilayeti dahilinde",
    "اشبو ورقه مندرجاتى",
    "نظارت مقامنه ارسال اولندى",
    "جواب تحريرى verilmesi",
    "دفتر خانه ثبتنده",
    "مذكور محلده sakin",
    "اكراد و عربان ذكر اولوندى",
    "مأمورين marifetiyle",
    "تحقيقات icra kılındı",
    "حكم شريف مقتضاسينجه",
    "اوقونامايان كلمه",
    "پاره پاره satir devam eder",
    "مدرسه و مكتب talebesi",
    "رومى تاريخ ١٣٢٥",
    "هجري سنه ١٣٣٠",
    "ماليye nezareti",
    "محل-i mezkur",
    "der saadet tarafindan",
    "ايلان نامه sureti",
    "قيد و tescil",
    "arzuhal sahibi",
    "خاتمه و imza",
]


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def write_json(name: str, payload: Any) -> None:
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    (EVIDENCE / name).write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def percentile(values: List[float], pct: float) -> float:
    if not values:
        return 0.0
    if len(values) == 1:
        return values[0]
    ordered = sorted(values)
    index = (len(ordered) - 1) * pct
    lower = int(index)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = index - lower
    return ordered[lower] + ((ordered[upper] - ordered[lower]) * fraction)


def stats(values: List[float]) -> Dict[str, float]:
    if not values:
        return {}
    return {
        "min": min(values),
        "median": statistics.median(values),
        "mean": statistics.mean(values),
        "max": max(values),
        "p50": percentile(values, 0.50),
        "p95": percentile(values, 0.95),
    }


def load_1b_baseline() -> Dict[str, Any]:
    comparison = json.loads((EVIDENCE_ROOT / "comparison.json").read_text(encoding="utf-8"))
    before = {
        "timestamp": now_iso(),
        "source": "1B staged baseline; live HTTP before-1C was not available before this code change.",
        "status": comparison.get("status"),
        "limitations": comparison.get("limitations", []) + [
            "real_e2e_before is derived from 1B stage evidence, not live POST /api/v1/document/analyze-full."
        ],
        "ocr_real": comparison.get("ocr_real", {}).get("before", {}),
        "llm_real_3_line": {
            "total_ms": comparison.get("llm_real_3_line", {}).get("before_ms"),
            "calls": comparison.get("llm_real_3_line", {}).get("before_calls"),
            "tokens_approx": comparison.get("llm_real_3_line", {}).get("before_tokens_approx"),
        },
        "llm_bulk_call_graph": comparison.get("llm_call_graph_bulk", {}),
    }
    write_json("real_e2e_before.json", before)
    write_json("llm_structured_before.json", before)
    write_json("ocr_deep_profile_before.json", comparison.get("ocr_real", {}).get("before", {}))
    return before


def ollama_stream_json(messages: List[Dict[str, str]], schema: Dict[str, Any]) -> Dict[str, Any]:
    payload = {
        "model": OLLAMA_MODEL,
        "messages": messages,
        "stream": True,
        "think": False,
        "format": schema,
        "keep_alive": os.getenv("OLLAMA_KEEP_ALIVE", "10m"),
        "options": {"temperature": 0.0},
    }
    start = time.perf_counter()
    first_token_ms = None
    content = []
    final: Dict[str, Any] = {}
    with requests.post(f"{OLLAMA_BASE}/api/chat", json=payload, stream=True, timeout=240) as response:
        response.raise_for_status()
        for raw_line in response.iter_lines():
            if not raw_line:
                continue
            item = json.loads(raw_line.decode("utf-8"))
            piece = item.get("message", {}).get("content", "")
            if piece and first_token_ms is None:
                first_token_ms = (time.perf_counter() - start) * 1000
            content.append(piece)
            if item.get("done"):
                final = item
                break
    total_ms = (time.perf_counter() - start) * 1000
    raw = "".join(content).strip()
    parsed = json.loads(raw)
    eval_count = int(final.get("eval_count") or 0)
    eval_duration_s = float(final.get("eval_duration") or 0) / 1_000_000_000
    return {
        "parsed": parsed,
        "raw_chars": len(raw),
        "total_ms": total_ms,
        "ttft_ms": first_token_ms,
        "prompt_tokens": final.get("prompt_eval_count"),
        "output_tokens": final.get("eval_count"),
        "load_ms": (float(final.get("load_duration") or 0) / 1_000_000),
        "prompt_eval_ms": (float(final.get("prompt_eval_duration") or 0) / 1_000_000),
        "generation_ms": (float(final.get("eval_duration") or 0) / 1_000_000),
        "tokens_per_sec": (eval_count / eval_duration_s) if eval_count and eval_duration_s else 0.0,
    }


def structured_schema() -> Dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "lines": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "line_id": {"type": "string"},
                        "transliteration": {"type": "string"},
                        "modern_turkish": {"type": "string"},
                        "uncertain": {"type": "boolean"},
                    },
                    "required": ["line_id", "transliteration", "modern_turkish", "uncertain"],
                },
            }
        },
        "required": ["lines"],
    }


def run_llm_structured_benchmark() -> Dict[str, Any]:
    results: Dict[str, Any] = {"timestamp": now_iso(), "model": OLLAMA_MODEL, "sizes": {}}
    for count in [3, 10, 30]:
        input_lines = [
            {"line_id": f"p1_l{i + 1}", "line_no": i + 1, "ocr_text": OTTOMAN_LINES[i]}
            for i in range(count)
        ]
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a source-faithful Ottoman Turkish line transformation engine. "
                    "Return only JSON and preserve every line_id exactly."
                ),
            },
            {
                "role": "user",
                "content": (
                    "For each input line, produce simple Latin transliteration and faithful Modern Turkish.\n"
                    f"Input lines JSON:\n{json.dumps(input_lines, ensure_ascii=False)}"
                ),
            },
        ]
        measurement = ollama_stream_json(messages, structured_schema())
        output_ids = {line.get("line_id") for line in measurement["parsed"].get("lines", [])}
        measurement["line_id_set_valid"] = output_ids == {item["line_id"] for item in input_lines}
        measurement["request_count"] = 1
        results["sizes"][str(count)] = measurement
    write_json("llm_structured_after.json", results)
    write_json("llm_batch_benchmark.json", results)
    return results


def register_token() -> str:
    stamp = int(time.time() * 1000)
    payload = {
        "email": f"perf1c_{stamp}@example.com",
        "username": f"perf1c_{stamp}",
        "password": "PerfAudit1C123!",
        "full_name": "Performance Audit 1C",
    }
    response = requests.post(f"{API_BASE}/auth/register", json=payload, timeout=30)
    response.raise_for_status()
    return response.json()["access_token"]


def run_http_benchmark() -> Dict[str, Any]:
    token = register_token()
    runs = []
    if not SAMPLE_FILE.exists():
        result = {"status": "blocked", "reason": f"sample file missing: {SAMPLE_FILE}"}
        write_json("http_benchmark.json", result)
        write_json("real_e2e_after.json", result)
        return result
    for index in range(4):
        start = time.perf_counter()
        with SAMPLE_FILE.open("rb") as handle:
            response = requests.post(
                f"{API_BASE}/document/analyze-full",
                headers={"Authorization": f"Bearer {token}"},
                data={"title": f"Performance 1C HTTP Run {index + 1}"},
                files={"file": (SAMPLE_FILE.name, handle, "image/jpeg")},
                timeout=300,
            )
        total_ms = (time.perf_counter() - start) * 1000
        payload_size = len(response.content)
        item: Dict[str, Any] = {
            "run": index + 1,
            "phase": "cold" if index == 0 else "warm",
            "status_code": response.status_code,
            "total_request_ms": total_ms,
            "server_processing_ms": None,
            "payload_size": payload_size,
        }
        try:
            parsed = response.json()
            item["document_id"] = parsed.get("document", {}).get("document_id")
            item["ocr_lines"] = len(parsed.get("ocr", {}).get("lines", []))
            item["transliteration_lines"] = len(parsed.get("transliteration", {}).get("lines", []))
            item["modern_lines"] = len(parsed.get("modern_turkish", {}).get("lines", []))
            item["ocr_engine"] = parsed.get("ocr", {}).get("engine")
            item["fallback_used"] = parsed.get("ocr", {}).get("fallback_used")
            item["line_id_sets_match"] = (
                [line.get("line_id") for line in parsed.get("ocr", {}).get("lines", [])]
                == [line.get("line_id") for line in parsed.get("transliteration", {}).get("lines", [])]
                == [line.get("line_id") for line in parsed.get("modern_turkish", {}).get("lines", [])]
            )
        except Exception as exc:
            item["parse_error"] = str(exc)
            item["body_excerpt"] = response.text[:500]
        runs.append(item)
    warm_ms = [item["total_request_ms"] for item in runs if item["phase"] == "warm" and item["status_code"] == 200]
    result = {
        "timestamp": now_iso(),
        "sample": str(SAMPLE_FILE),
        "runs": runs,
        "warm_stats_ms": stats(warm_ms),
        "limitations": ["Endpoint response does not expose internal server stage timings; total_request_ms is measured client-side."],
    }
    write_json("http_benchmark.json", result)
    write_json("real_e2e_after.json", result)
    return result


def run_qdrant_init_check() -> Dict[str, Any]:
    sys.path.insert(0, str(BACKEND))
    import app.services.historical_rag.qdrant_store as qdrant_store

    qdrant_store._STORE_CACHE = None
    started = time.perf_counter()
    first = qdrant_store.HistoricalQdrantStore()
    first_ms = (time.perf_counter() - started) * 1000
    started = time.perf_counter()
    second = qdrant_store.HistoricalQdrantStore()
    second_ms = (time.perf_counter() - started) * 1000
    result = {
        "timestamp": now_iso(),
        "cached_singleton": first is second,
        "request_per_init": first is not second,
        "first_init_ms": first_ms,
        "second_init_ms": second_ms,
        "collection": first.COLLECTION,
    }
    try:
        first.close()
    finally:
        qdrant_store._STORE_CACHE = None
    write_json("qdrant_init_check.json", result)
    return result


def run_ocr_smoke_with_gpu_sampling() -> Dict[str, Any]:
    before_csv = EVIDENCE / "gpu_sampling_before.csv"
    after_csv = EVIDENCE / "gpu_sampling_after.csv"
    before_csv.write_text("note\n1B before GPU CSV was not captured; see nvidia_smi_before.txt\n", encoding="utf-8")
    sampler = subprocess.Popen(
        [
            "nvidia-smi",
            "--query-gpu=timestamp,utilization.gpu,memory.used,memory.total",
            "--format=csv",
            "-lms",
            "500",
        ],
        stdout=after_csv.open("w", encoding="utf-8"),
        stderr=subprocess.DEVNULL,
    )
    start = time.perf_counter()
    env = os.environ.copy()
    env["PYTHONPATH"] = str(BACKEND) + os.pathsep + env.get("PYTHONPATH", "")
    try:
        proc = subprocess.run(
            [str(BACKEND / "venv" / "Scripts" / "python.exe"), "scripts/real_smoke_test.py"],
            cwd=str(BACKEND),
            capture_output=True,
            text=True,
            timeout=120,
            env=env,
        )
    finally:
        sampler.terminate()
        try:
            sampler.wait(timeout=5)
        except subprocess.TimeoutExpired:
            sampler.kill()
    elapsed_ms = (time.perf_counter() - start) * 1000
    output = (proc.stdout or "") + "\n" + (proc.stderr or "")
    result = {
        "timestamp": now_iso(),
        "elapsed_ms": elapsed_ms,
        "returncode": proc.returncode,
        "stdout_tail": output[-4000:],
        "gpu_sampling_file": str(after_csv),
        "note": "Kraken Python engine is cached, but WSL bridge still starts a subprocess and loads the model for each OCR request.",
    }
    write_json("ocr_deep_profile_after.json", result)
    return result


def write_frontend_duplicate_evidence() -> Dict[str, Any]:
    dashboard = ROOT / "frontend" / "src" / "app" / "(app)" / "dashboard" / "page.tsx"
    source = dashboard.read_text(encoding="utf-8")
    pass_guard = "analyzeInFlightRef.current" in source and "finally" in source
    result = {
        "timestamp": now_iso(),
        "status": "PASS_SOURCE_GUARD" if pass_guard else "FAIL",
        "real_browser_network_test": "not_run_playwright_not_installed",
        "evidence": [
            "analyzeInFlightRef prevents same-tick double click before React state is committed.",
            "Existing isBusy state still disables the visible button during upload/preprocessing.",
        ],
    }
    (EVIDENCE / "frontend_duplicate_request_test.txt").write_text(
        json.dumps(result, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return result


def write_report(payload: Dict[str, Any]) -> None:
    http_runs = payload.get("http", {}).get("runs", [])
    warm_stats = payload.get("http", {}).get("warm_stats_ms", {})
    llm_sizes = payload.get("llm_after", {}).get("sizes", {})
    qdrant = payload.get("qdrant", {})
    duplicate = payload.get("duplicate", {})
    ocr = payload.get("ocr_after", {})
    report = [
        "# Performance Audit 1C Report",
        "",
        "## Final Status",
        "",
        "PARTIAL_REAL_AFTER_PASS_WITH_1B_BASELINE_BEFORE. Real after HTTP/Ollama/OCR/Qdrant evidence was collected where runtime allowed; live HTTP before-1C was unavailable after the optimization patch and is labeled from 1B staged baseline.",
        "",
        "## Real HTTP E2E After",
        "",
        f"- Runs: {len(http_runs)}",
        f"- Warm stats ms: {json.dumps(warm_stats, ensure_ascii=False)}",
        "",
        "## LLM Structured Batch After",
        "",
    ]
    for size, item in llm_sizes.items():
        report.append(
            f"- {size} lines: total_ms={item.get('total_ms'):.2f}, request_count={item.get('request_count')}, "
            f"prompt_tokens={item.get('prompt_tokens')}, output_tokens={item.get('output_tokens')}, "
            f"ttft_ms={item.get('ttft_ms')}, tokens_per_sec={item.get('tokens_per_sec'):.2f}, "
            f"line_id_set_valid={item.get('line_id_set_valid')}"
        )
    report.extend(
        [
            "",
            "## OCR",
            "",
            f"- After smoke returncode: {ocr.get('returncode')}",
            f"- After smoke elapsed_ms: {ocr.get('elapsed_ms')}",
            "- Root cause retained: WSL bridge subprocess/model load per OCR request remains the dominant OCR bottleneck.",
            "",
            "## Qdrant Init",
            "",
            f"- cached_singleton: {qdrant.get('cached_singleton')}",
            f"- request_per_init: {qdrant.get('request_per_init')}",
            f"- first_init_ms: {qdrant.get('first_init_ms')}",
            f"- second_init_ms: {qdrant.get('second_init_ms')}",
            "",
            "## Frontend Duplicate Request",
            "",
            f"- {duplicate.get('status')}",
            f"- real_browser_network_test: {duplicate.get('real_browser_network_test')}",
            "",
            "## Remaining Bottlenecks",
            "",
            "- Kraken WSL bridge still loads the model inside a subprocess per OCR request.",
            "- Endpoint schema does not expose server-side stage timings; client total_request_ms is available.",
            "- Browser-level duplicate network test needs Playwright/browser tooling installed for full PASS.",
        ]
    )
    (EVIDENCE / "PERFORMANCE_1C_REPORT.md").write_text("\n".join(report), encoding="utf-8")


def main() -> int:
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    before = load_1b_baseline()
    llm_after = run_llm_structured_benchmark()
    qdrant = run_qdrant_init_check()
    duplicate = write_frontend_duplicate_evidence()
    http = run_http_benchmark()
    ocr_after = run_ocr_smoke_with_gpu_sampling()
    payload = {
        "before": before,
        "llm_after": llm_after,
        "qdrant": qdrant,
        "duplicate": duplicate,
        "http": http,
        "ocr_after": ocr_after,
    }
    write_report(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
