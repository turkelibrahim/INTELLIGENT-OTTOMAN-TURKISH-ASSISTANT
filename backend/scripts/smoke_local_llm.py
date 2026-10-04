import json
import sys

from app.services.ai.ollama_provider import OllamaProvider


def main():
    provider = OllamaProvider()

    print("=== OLLAMA HEALTH ===")

    health = provider.health_check()

    print(
        json.dumps(
            health,
            ensure_ascii=False,
            indent=2,
        )
    )

    if not health["reachable"]:
        raise RuntimeError("Ollama is not reachable.")

    if not health["model_available"]:
        raise RuntimeError(
            f"Configured model is not installed: {provider.model}"
        )

    schema = {
        "type": "object",
        "properties": {
            "status": {
                "type": "string"
            },
            "provider": {
                "type": "string"
            },
            "model": {
                "type": "string"
            }
        },
        "required": [
            "status",
            "provider",
            "model"
        ]
    }

    result = provider.chat_json(
        messages=[
            {
                "role": "system",
                "content": (
                    "Sen Intelligent Ottoman Turkish Assistant "
                    "uygulamasının yerel yapay zekâ servis testisin. "
                    "Yalnız istenen JSON yapısında cevap ver."
                ),
            },
            {
                "role": "user",
                "content": (
                    "status alanını LOCAL_BACKEND_LLM_OK, "
                    "provider alanını ollama ve "
                    "model alanını qwen3.5:4b olarak döndür."
                ),
            },
        ],
        schema=schema,
        temperature=0.0,
    )

    print()
    print("=== STRUCTURED RESPONSE ===")

    print(
        json.dumps(
            result,
            ensure_ascii=False,
            indent=2,
        )
    )

    if result.get("status") != "LOCAL_BACKEND_LLM_OK":
        raise RuntimeError(
            f"Unexpected status: {result}"
        )

    print()
    print("LOCAL_BACKEND_LLM_GATE: PASS")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print()
        print("LOCAL_BACKEND_LLM_GATE: FAIL")
        print(type(exc).__name__ + ":", exc)
        sys.exit(1)
