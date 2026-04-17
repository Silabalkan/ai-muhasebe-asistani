from __future__ import annotations

from abc import ABC, abstractmethod
from functools import lru_cache
import json
import logging
from urllib import error, request

from config import get_settings


logger = logging.getLogger(__name__)


class AIServiceError(RuntimeError):
    pass


class BaseAIProvider(ABC):
    @abstractmethod
    def generate(self, summary: str) -> str:
        raise NotImplementedError


class OllamaProvider(BaseAIProvider):
    def __init__(self, *, base_url: str, model: str, timeout_seconds: int):
        self.base_url = base_url
        self.model = model
        self.timeout_seconds = timeout_seconds

    def generate(self, summary: str) -> str:
        payload = {
            "model": self.model,
            "prompt": _build_prompt(summary),
            "stream": False,
        }
        req = request.Request(
            url=f"{self.base_url}/api/generate",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with request.urlopen(req, timeout=self.timeout_seconds) as resp:
                raw = resp.read().decode("utf-8")
            data = json.loads(raw)
            text = (data.get("response") or "").strip()
            if not text:
                raise AIServiceError("Ollama bos yanit dondurdu")
            return text
        except (error.URLError, error.HTTPError, TimeoutError, json.JSONDecodeError) as exc:
            raise AIServiceError(f"Ollama cagri hatasi: {exc}") from exc


class OpenAIProvider(BaseAIProvider):
    def __init__(
        self,
        *,
        api_key: str | None,
        base_url: str,
        model: str,
        timeout_seconds: int,
    ):
        if not api_key:
            raise AIServiceError("OPENAI_API_KEY tanimli degil")
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.timeout_seconds = timeout_seconds

    def generate(self, summary: str) -> str:
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "KOBI odakli finansal yorum asistanisin. Kisa, net, eyleme donuk konus.",
                },
                {"role": "user", "content": _build_prompt(summary)},
            ],
            "temperature": 0.3,
            "max_tokens": 220,
        }

        req = request.Request(
            url=f"{self.base_url}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )
        try:
            with request.urlopen(req, timeout=self.timeout_seconds) as resp:
                raw = resp.read().decode("utf-8")
            data = json.loads(raw)
            text = (
                data.get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
                .strip()
            )
            if not text:
                raise AIServiceError("OpenAI bos yanit dondurdu")
            return text
        except (error.URLError, error.HTTPError, TimeoutError, json.JSONDecodeError, KeyError, IndexError) as exc:
            raise AIServiceError(f"OpenAI cagri hatasi: {exc}") from exc


class AICommentService:
    def __init__(self, *, primary: BaseAIProvider, fallback: BaseAIProvider | None = None):
        self.primary = primary
        self.fallback = fallback

    def generate_financial_comment(self, summary: str) -> str:
        cleaned = (summary or "").strip()
        if not cleaned:
            raise AIServiceError("Summary bos olamaz")

        try:
            return self.primary.generate(cleaned)
        except AIServiceError as primary_exc:
            logger.warning("Primary provider failed: %s", primary_exc)
            if self.fallback is not None:
                try:
                    return self.fallback.generate(cleaned)
                except AIServiceError as fallback_exc:
                    logger.warning("Fallback provider failed: %s", fallback_exc)
            return _rule_based_fallback(cleaned)


def _build_prompt(summary: str) -> str:
    return (
        "Asagidaki finansal ozeti analiz et. Turkce, sade ve is odakli 3-5 cumle ile yorumla. "
        "1) Durum ozeti 2) Risk/Uyari 3) Tek aksiyon onerisi ver.\n\n"
        f"Finansal ozet:\n{summary}"
    )


def _rule_based_fallback(summary: str) -> str:
    return (
        "Finansal veriler analiz edildi. Gelir-gider dengesini aylik olarak takip edin ve "
        "sapma gosteren gider kalemlerine oncelik verin. Ozet veriye gore butce disiplini korunursa "
        "nakit akisi daha saglikli ilerleyecektir."
    )


@lru_cache(maxsize=1)
def _build_service() -> AICommentService:
    settings = get_settings()

    if settings.ai_provider == "openai":
        primary = OpenAIProvider(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            model=settings.openai_model,
            timeout_seconds=settings.ai_timeout_seconds,
        )
        fallback = OllamaProvider(
            base_url=settings.ollama_base_url,
            model=settings.ollama_model,
            timeout_seconds=settings.ai_timeout_seconds,
        )
        return AICommentService(primary=primary, fallback=fallback)

    primary = OllamaProvider(
        base_url=settings.ollama_base_url,
        model=settings.ollama_model,
        timeout_seconds=settings.ai_timeout_seconds,
    )
    return AICommentService(primary=primary)


def generate_financial_comment(summary: str) -> str:
    return _build_service().generate_financial_comment(summary)


def get_ai_runtime_status() -> dict:
    settings = get_settings()

    if settings.ai_provider == "openai":
        if not settings.openai_api_key:
            return {
                "provider": "openai",
                "configured_model": settings.openai_model,
                "healthy": False,
                "detail": "OPENAI_API_KEY tanimli degil",
            }
        return {
            "provider": "openai",
            "configured_model": settings.openai_model,
            "healthy": True,
            "detail": "OpenAI ayarlari mevcut",
        }

    req = request.Request(
        url=f"{settings.ollama_base_url}/api/tags",
        headers={"Content-Type": "application/json"},
        method="GET",
    )
    try:
        with request.urlopen(req, timeout=settings.ai_timeout_seconds) as resp:
            raw = resp.read().decode("utf-8")
        data = json.loads(raw)
        models = [m.get("name") for m in data.get("models", []) if isinstance(m, dict)]
        if settings.ollama_model in models:
            return {
                "provider": "ollama",
                "configured_model": settings.ollama_model,
                "healthy": True,
                "detail": "Ollama erisilebilir ve model yuklu",
            }
        return {
            "provider": "ollama",
            "configured_model": settings.ollama_model,
            "healthy": False,
            "detail": "Ollama erisilebilir ama model yuklu degil",
        }
    except (error.URLError, error.HTTPError, TimeoutError, json.JSONDecodeError):
        return {
            "provider": "ollama",
            "configured_model": settings.ollama_model,
            "healthy": False,
            "detail": "Ollama servisine erisilemiyor",
        }
