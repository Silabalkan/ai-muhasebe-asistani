from dataclasses import dataclass
from functools import lru_cache
import os

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    ai_provider: str
    ai_timeout_seconds: int
    openai_api_key: str | None
    openai_base_url: str
    openai_model: str
    ollama_base_url: str
    ollama_model: str


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    provider = (os.getenv("AI_PROVIDER", "ollama") or "ollama").strip().lower()
    if provider not in {"ollama", "openai"}:
        provider = "ollama"

    timeout_raw = os.getenv("AI_TIMEOUT_SECONDS", "20")
    try:
        timeout_seconds = max(5, int(timeout_raw))
    except ValueError:
        timeout_seconds = 20

    return Settings(
        ai_provider=provider,
        ai_timeout_seconds=timeout_seconds,
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        openai_base_url=(os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1") or "https://api.openai.com/v1").rstrip("/"),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        ollama_base_url=(os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434") or "http://127.0.0.1:11434").rstrip("/"),
        ollama_model=os.getenv("OLLAMA_MODEL", "llama3.1:8b"),
    )
