import json
import asyncio
from typing import Dict, Any, Optional
from openai import AsyncOpenAI
from app.core.config import settings
from .resilience import resilience_manager

# Initialize OpenAI client with NVIDIA base URL
nvidia_client = AsyncOpenAI(
    base_url=settings.NVIDIA_BASE_URL,
    api_key=settings.NVIDIA_API_KEY or "dummy-key-for-local-fallback"
)

SYSTEM_PROMPT = """You are a historical Ottoman Turkish document verification and vision expert.
When analyzing the document image, you must accurately separate and identify:
- OCR/transcription of the main text
- Page layout structure
- Seals (mühür)
- Tughra (tuğra)
- Annotations and derkenar
- Headings
- Marginal notes

CRITICAL INSTRUCTIONS:
- You are not allowed to invent unreadable characters.
- You must distinguish visual evidence from linguistic inference.
- When the image is unclear or text cannot be detected, clearly return "tespit edilemedi" or "tahmin" to distinguish between verified facts and assumptions.
- Do not hallucinate or produce fake information.
- Use the supplied local OCR, transcription and historical retrieval context as evidence, not as unquestionable truth.
- Return only the requested JSON schema.
- Never add explanations outside the JSON."""

def extract_json_safe(text: str) -> Dict[str, Any]:
    """Safely extracts JSON from model response (fenced or unfenced)"""
    text = text.strip()
    if text.startswith("```json"):
        text = text.split("```json")[1].split("```")[0].strip()
    elif text.startswith("```"):
        text = text.split("```")[1].split("```")[0].strip()
        
    # Remove thought blocks if any
    if "<think>" in text:
        text = text.split("</think>")[-1].strip()
        
    try:
        return json.loads(text)
    except Exception as e:
        # Fallback repair attempts can be added here
        raise ValueError(f"Invalid JSON returned: {str(e)}")

async def _call_nvidia_api(
    task: str,
    prompt: str,
    image_url: Optional[str] = None,
    model: str = settings.NVIDIA_PRIMARY_MODEL,
    max_tokens: int = 512
) -> Dict[str, Any]:
    
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    user_content = []
    user_content.append({"type": "text", "text": f"TASK: {task}\n\n{prompt}"})
    
    if image_url:
        user_content.append({
            "type": "image_url",
            "image_url": {"url": image_url}
        })
        
    messages.append({"role": "user", "content": user_content})

    response = await nvidia_client.chat.completions.create(
        model=model,
        messages=messages,
        max_tokens=max_tokens,
        temperature=0.1,
        timeout=settings.NVIDIA_TIMEOUT_SECONDS,
    )
    
    raw_text = response.choices[0].message.content
    if settings.NVIDIA_LOG_RESPONSES:
        print(f"NVIDIA Raw Response ({model}): {raw_text}")
        
    return extract_json_safe(raw_text)

async def verify_task(
    task: str,
    prompt: str,
    image_url: Optional[str] = None,
    model: str = settings.NVIDIA_PRIMARY_MODEL,
    max_tokens: int = 512
) -> Dict[str, Any]:
    if not settings.NVIDIA_ENABLED or not settings.NVIDIA_API_KEY:
        raise Exception("NVIDIA API is not enabled or API key is missing")
        
    # Execute through circuit breaker
    return await resilience_manager.execute(
        _call_nvidia_api,
        task=task,
        prompt=prompt,
        image_url=image_url,
        model=model,
        max_tokens=max_tokens
    )
