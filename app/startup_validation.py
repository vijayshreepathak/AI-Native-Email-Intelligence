"""Production startup validation — fails loudly on Render when config is missing."""

from __future__ import annotations

import os

from app.config import Settings, get_settings


def _is_render() -> bool:
    return os.getenv("RENDER", "").lower() in {"true", "1", "yes"}


def validate_production_env(settings: Settings | None = None) -> None:
    """Raise RuntimeError if required production environment variables are missing."""
    if not _is_render():
        return

    settings = settings or get_settings()
    missing: list[str] = []

    if not settings.database_url.strip():
        missing.append("DATABASE_URL")
    if not settings.clerk_secret_key.strip():
        missing.append("CLERK_SECRET_KEY")
    if not settings.anthropic_api_key.strip():
        missing.append("ANTHROPIC_API_KEY")
    if not settings.cors_origin_list():
        missing.append("CORS_ORIGINS")

    if missing:
        raise RuntimeError(
            "Missing required environment variables on Render: "
            + ", ".join(missing)
            + ". Set them in Render Dashboard → Environment."
        )


def env_summary(settings: Settings | None = None) -> dict[str, str]:
    """Return a safe summary of env var presence (never prints secrets)."""
    settings = settings or get_settings()
    return {
        "DATABASE_URL": "set" if settings.database_url.strip() else "MISSING",
        "CLERK_SECRET_KEY": "set" if settings.clerk_secret_key.strip() else "MISSING",
        "ANTHROPIC_API_KEY": "set" if settings.anthropic_api_key.strip() else "MISSING",
        "GEMINI_API_KEY": "set" if settings.effective_gemini_key.strip() else "MISSING",
        "CORS_ORIGINS": "set" if settings.cors_origin_list() else "MISSING",
        "CLERK_JWKS_URL": "set" if settings.clerk_jwks_url.strip() else "MISSING",
        "CLERK_ISSUER": "set" if settings.clerk_issuer.strip() else "MISSING",
    }
