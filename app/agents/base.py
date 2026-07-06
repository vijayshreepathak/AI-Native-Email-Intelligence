"""Shared LLM client for all agents."""

import time
from typing import Any

import httpx
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage

from app.config import get_settings
from app.prompts import SYSTEM_PROMPT
from app.utils.helpers import extract_json_from_text, retry_async
from app.utils.logger import get_logger

logger = get_logger(__name__)

GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


def _is_claude_error(exc: Exception) -> bool:
    """Return True if error suggests Claude auth/quota/unavailability."""
    msg = str(exc).lower()
    markers = (
        "401",
        "403",
        "authentication",
        "invalid x-api-key",
        "invalid api key",
        "credit balance",
        "rate limit",
        "overloaded",
        "not_found",
        "model_not_found",
        "api_key",
        "unauthorized",
        "permission",
        "expired",
    )
    return any(m in msg for m in markers)


class LLMClient:
    """Claude-first LLM client with automatic Gemini fallback."""

    def __init__(self) -> None:
        settings = get_settings()
        self._anthropic_model = settings.anthropic_model
        self._gemini_model = settings.gemini_model
        self._max_retries = settings.max_retries
        self._anthropic_key = settings.anthropic_api_key.strip()
        self._gemini_key = settings.gemini_api_key.strip()
        self._provider = "claude" if self._anthropic_key else "gemini"
        self._model = self._anthropic_model if self._anthropic_key else self._gemini_model
        self._llm: ChatAnthropic | None = None

        if self._anthropic_key:
            self._llm = ChatAnthropic(
                model=self._anthropic_model,
                api_key=self._anthropic_key,
                max_tokens=4096,
                temperature=0.1,
            )

    @property
    def model_name(self) -> str:
        return self._model

    @property
    def provider(self) -> str:
        return self._provider

    @property
    def fallback_available(self) -> bool:
        return bool(self._gemini_key)

    async def invoke(
        self,
        prompt: str,
        system: str = SYSTEM_PROMPT,
        parse_json: bool = True,
    ) -> tuple[Any, dict[str, Any]]:
        """Invoke LLM (Claude primary, Gemini fallback) and optionally parse JSON."""
        if self._anthropic_key and self._llm:
            try:
                return await self._invoke_claude(prompt, system, parse_json)
            except Exception as exc:
                if self._gemini_key and _is_claude_error(exc):
                    logger.warning(
                        "Claude unavailable (%s), falling back to Gemini %s",
                        exc,
                        self._gemini_model,
                    )
                elif self._gemini_key:
                    logger.warning(
                        "Claude call failed (%s), falling back to Gemini %s",
                        exc,
                        self._gemini_model,
                    )
                else:
                    raise

        if self._gemini_key:
            return await self._invoke_gemini(prompt, system, parse_json)

        raise RuntimeError(
            "No LLM API key configured. Set ANTHROPIC_API_KEY and/or GEMINI_API_KEY in .env"
        )

    async def _invoke_claude(
        self,
        prompt: str,
        system: str,
        parse_json: bool,
    ) -> tuple[Any, dict[str, Any]]:
        start = time.perf_counter()
        metrics: dict[str, Any] = {
            "tokens": 0,
            "latency_ms": 0.0,
            "model": self._anthropic_model,
            "provider": "claude",
        }

        async def _call() -> Any:
            messages = [
                SystemMessage(content=system),
                HumanMessage(content=prompt),
            ]
            return await self._llm.ainvoke(messages)  # type: ignore[union-attr]

        response = await retry_async(_call, max_retries=self._max_retries)
        metrics["latency_ms"] = round((time.perf_counter() - start) * 1000, 2)

        content = _extract_message_content(response.content)
        usage = getattr(response, "usage_metadata", None) or {}
        metrics["tokens"] = (
            usage.get("total_tokens", 0)
            if isinstance(usage, dict)
            else getattr(usage, "total_tokens", 0)
        )

        self._provider = "claude"
        self._model = self._anthropic_model

        result = extract_json_from_text(str(content)) if parse_json else str(content)
        logger.debug(
            "Claude call completed: model=%s tokens=%d latency=%.2fms",
            self._anthropic_model,
            metrics["tokens"],
            metrics["latency_ms"],
        )
        return result, metrics

    async def _invoke_gemini(
        self,
        prompt: str,
        system: str,
        parse_json: bool,
    ) -> tuple[Any, dict[str, Any]]:
        start = time.perf_counter()
        metrics: dict[str, Any] = {
            "tokens": 0,
            "latency_ms": 0.0,
            "model": self._gemini_model,
            "provider": "gemini",
        }

        url = GEMINI_API_URL.format(model=self._gemini_model)
        payload = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "systemInstruction": {"parts": [{"text": system}]},
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": 4096,
                "responseMimeType": "application/json" if parse_json else "text/plain",
            },
        }

        async def _call() -> dict[str, Any]:
            async with httpx.AsyncClient(timeout=120.0) as client:
                resp = await client.post(
                    url,
                    params={"key": self._gemini_key},
                    json=payload,
                )
                resp.raise_for_status()
                return resp.json()

        data = await retry_async(_call, max_retries=self._max_retries)
        metrics["latency_ms"] = round((time.perf_counter() - start) * 1000, 2)

        candidates = data.get("candidates") or []
        if not candidates:
            raise ValueError(f"Gemini returned no candidates: {data}")

        parts = candidates[0].get("content", {}).get("parts") or []
        content = "".join(p.get("text", "") for p in parts if isinstance(p, dict))

        usage = data.get("usageMetadata") or {}
        metrics["tokens"] = usage.get("totalTokenCount", 0)

        self._provider = "gemini"
        self._model = self._gemini_model

        if parse_json:
            result = extract_json_from_text(content)
        else:
            result = content

        logger.info(
            "Gemini call completed: model=%s tokens=%d latency=%.2fms",
            self._gemini_model,
            metrics["tokens"],
            metrics["latency_ms"],
        )
        return result, metrics


def _extract_message_content(content: Any) -> str:
    if isinstance(content, list):
        return " ".join(
            block.get("text", "") if isinstance(block, dict) else str(block)
            for block in content
        )
    return str(content)


_llm_client: LLMClient | None = None


def get_llm_client() -> LLMClient:
    """Singleton LLM client for dependency injection."""
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client
