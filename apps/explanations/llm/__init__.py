from typing import Any, Dict, Optional

from django.conf import settings

from .base import LLMClient, LLMError, LLMRateLimited
from .gemini import GeminiClient
from .ollama import OllamaClient

LOCAL_NO_LIMIT = 10**9


def provider() -> str:
    return settings.LLM["PROVIDER"]


def active_model() -> str:
    return settings.OLLAMA["MODEL"] if provider() == "ollama" else settings.GEMINI["MODEL"]


def llm_configured() -> bool:
    """True when a client can be built (Gemini needs a key; Ollama needs nothing but a running server)."""
    if not settings.LLM["ENABLED"]:
        return False
    return True if provider() == "ollama" else bool(settings.GEMINI["API_KEY"])


def get_llm_client() -> Optional[LLMClient]:
    """The configured client, or None (then the app serves deterministic explanations only)."""
    if not llm_configured():
        return None
    if provider() == "ollama":
        o = settings.OLLAMA
        return OllamaClient(o["BASE_URL"], o["MODEL"], o["REQUEST_TIMEOUT_SECONDS"], o["NUM_CTX"], o["NUM_PREDICT"], o["TEMPERATURE"])
    g = settings.GEMINI
    return GeminiClient(g["API_KEY"], g["MODEL"], g["BASE_URL"], g["REQUEST_TIMEOUT_SECONDS"], g["MAX_OUTPUT_TOKENS"], g["TEMPERATURE"])


def gate_config() -> Dict[str, Any]:
    """Limits the RateGate enforces. A local model has no quota, but still runs one request at a time."""
    if provider() == "ollama":
        o = settings.OLLAMA
        return {"MIN_INTERVAL_SECONDS": 0.0, "DAILY_LIMIT": LOCAL_NO_LIMIT,
                "QUEUE_WAIT_SECONDS": o["QUEUE_WAIT_SECONDS"], "REQUEST_TIMEOUT_SECONDS": o["REQUEST_TIMEOUT_SECONDS"]}
    return dict(settings.GEMINI)


def narrate_whatif_with_llm() -> bool:
    setting = settings.LLM["WHATIF_NARRATION"]
    if setting in ("true", "1", "yes", "on"):
        return True
    if setting in ("false", "0", "no", "off"):
        return False
    return provider() == "ollama"  # auto: spend a second call only where calls are free


__all__ = ["get_llm_client", "active_model", "provider", "llm_configured", "gate_config",
           "narrate_whatif_with_llm", "GeminiClient", "OllamaClient", "LLMClient", "LLMError", "LLMRateLimited"]
