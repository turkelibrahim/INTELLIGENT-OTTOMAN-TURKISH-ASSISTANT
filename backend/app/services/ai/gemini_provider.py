import json
import os
import requests
import logging
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

class GeminiProvider:
    """
    Google Gemini LLM provider using REST API.
    """

    def __init__(
        self,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout_seconds: int = 180,
    ):
        self.model = model or os.getenv("LLM_MODEL") or "gemini-1.5-flash"
        
        # Override qwen model setting if accidentally left over from ollama
        if "qwen" in self.model.lower() or "llama" in self.model.lower() or "gemini-1.5" in self.model.lower():
            self.model = "gemini-2.5-flash"
            
        self.api_key = api_key or os.getenv("LLM_API_KEY")
        if not self.api_key:
            raise RuntimeError("Gemini API key (LLM_API_KEY) is required.")

        self.timeout_seconds = timeout_seconds

    @property
    def base_url(self) -> str:
        return f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"

    def health_check(self) -> Dict[str, Any]:
        """
        Since we don't have a direct health check endpoint without a payload,
        we just assume it's reachable if we have an API key.
        """
        return {
            "provider": "gemini",
            "model": self.model,
            "reachable": True,
            "model_available": True,
        }

    def _convert_messages(self, messages: List[Dict[str, str]]) -> Tuple[Optional[str], List[Dict[str, Any]]]:
        gemini_messages = []
        system_prompt = None
        
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            if role == "system":
                system_prompt = content
                continue
                
            gemini_role = "user" if role == "user" else "model"
            gemini_messages.append({
                "role": gemini_role,
                "parts": [{"text": content}]
            })
            
        return system_prompt, gemini_messages

    def chat(
        self,
        messages: List[Dict[str, str]],
        *,
        schema: Optional[Dict[str, Any]] = None,
        temperature: float = 0.1,
        think: bool = False,
    ) -> str:
        system_prompt, gemini_messages = self._convert_messages(messages)
        
        payload: Dict[str, Any] = {
            "contents": gemini_messages,
            "generationConfig": {
                "temperature": temperature,
            }
        }
        
        if system_prompt:
            payload["system_instruction"] = {
                "parts": [{"text": system_prompt}]
            }
            
        if schema is not None:
            payload["generationConfig"]["responseMimeType"] = "application/json"

        headers = {"Content-Type": "application/json"}
        
        response = requests.post(
            self.base_url,
            headers=headers,
            json=payload,
            timeout=self.timeout_seconds,
        )
        
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            logger.error(f"Gemini API Error: {response.text}")
            raise RuntimeError(f"Gemini API returned an error: {response.text}") from e

        data = response.json()
        
        try:
            content = data["candidates"][0]["content"]["parts"][0]["text"].strip()
        except (KeyError, IndexError) as e:
            raise RuntimeError(f"Unexpected response format from Gemini: {data}") from e

        if not content:
            raise RuntimeError("Gemini returned an empty response.")

        return content

    def chat_json(
        self,
        messages: List[Dict[str, str]],
        schema: Dict[str, Any],
        *,
        temperature: float = 0.1,
    ) -> Dict[str, Any]:
        """
        Requests structured JSON and parses it.
        """
        has_system = any(m.get("role") == "system" for m in messages)
        if has_system:
            for m in messages:
                if m.get("role") == "system":
                    m["content"] += "\nIMPORTANT: Return ONLY valid JSON."
        else:
            messages.insert(0, {"role": "system", "content": "Return ONLY valid JSON."})

        raw = self.chat(
            messages,
            schema=schema,
            temperature=temperature,
        )
        
        # JSON Shield
        if raw.startswith("```json"):
            raw = raw[7:]
        if raw.endswith("```"):
            raw = raw[:-3]
        raw = raw.strip()

        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Gemini returned invalid JSON: {raw}") from exc

        if not isinstance(parsed, dict):
            raise RuntimeError("Gemini structured response must be a JSON object.")

        return parsed
