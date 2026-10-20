"""Client for a local Ollama server (e.g. Llama 3.2 3B). No quota, but one request at a time on CPU."""
import requests
from .base import LLMError

class OllamaClient:
    def __init__(self, base_url: str, model: str, timeout: float, num_ctx: int, num_predict: int, temperature: float):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self.num_ctx = num_ctx
        self.num_predict = num_predict
        self.temperature = temperature

    def generate_json(self, system: str, prompt: str) -> str:
        body = {
            "model": self.model,
            "stream": False,
            "format": "json",  # constrains the output to valid JSON
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}],
            "options": {"temperature": self.temperature, "num_ctx": self.num_ctx, "num_predict": self.num_predict},
        }
        try:
            response = requests.post(f"{self.base_url}/api/chat", json=body, timeout=self.timeout)
        except requests.ConnectionError as exc:
            raise LLMError(f"cannot reach Ollama at {self.base_url}; is it running?") from exc
        except requests.RequestException as exc:
            raise LLMError(f"network error: {exc.__class__.__name__}") from exc

        if response.status_code == 404:
            raise LLMError(f"Ollama has no model '{self.model}'; run: ollama pull {self.model}")
        if response.status_code >= 400:
            raise LLMError(f"Ollama returned HTTP {response.status_code}")
        try:
            data = response.json()
            text = data["message"]["content"]
        except (ValueError, KeyError, TypeError) as exc:
            raise LLMError("unexpected response from Ollama") from exc
        if data.get("done_reason") == "length":
            raise LLMError("generation was cut off (raise OLLAMA_NUM_PREDICT)")
        if not text.strip():
            raise LLMError("empty response")
        return text
