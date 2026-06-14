"""Runtime settings for the AlterScore backend."""

from dataclasses import dataclass
from functools import lru_cache
from os import environ
from pathlib import Path
from typing import Mapping

from backend.app.core.paths import (
    PRODUCTION_MANIFEST_RELATIVE_PATH,
    REPO_ROOT,
    REQUEST_LOG_RELATIVE_PATH,
    resolve_repo_path,
)

DEFAULT_CORS_ORIGINS = (
    "http://localhost:5173",
    "http://127.0.0.1:5173",
)


@dataclass(frozen=True)
class Settings:
    environment: str
    api_version: str
    repo_root: Path
    model_manifest_path: Path
    runtime_model_path: Path | None
    request_log_path: Path
    log_level: str
    cors_origins: tuple[str, ...]
    cors_origin_regex: str | None
    enable_debug_score: bool
    rate_limit_enabled: bool
    score_rate_limit: str


def _split_csv(value: str | None) -> tuple[str, ...]:
    if not value:
        return ()

    return tuple(item.strip() for item in value.split(",") if item.strip())


def _env_flag(value: str | None, *, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def load_settings(env: Mapping[str, str] | None = None) -> Settings:
    """Load settings from environment variables without side effects."""
    source = environ if env is None else env
    repo_root = (
        Path(source["ALTERSCORE_REPO_ROOT"]).resolve()
        if source.get("ALTERSCORE_REPO_ROOT")
        else REPO_ROOT
    )
    manifest_value = source.get("ALTERSCORE_MODEL_MANIFEST")
    model_manifest_path = (
        resolve_repo_path(manifest_value, repo_root)
        if manifest_value
        else resolve_repo_path(PRODUCTION_MANIFEST_RELATIVE_PATH, repo_root)
    )
    runtime_model_value = source.get("ALTERSCORE_RUNTIME_MODEL_PATH")
    runtime_model_path = (
        resolve_repo_path(runtime_model_value, repo_root)
        if runtime_model_value
        else None
    )
    request_log_value = source.get("ALTERSCORE_REQUEST_LOG_PATH")
    request_log_path = (
        resolve_repo_path(request_log_value, repo_root)
        if request_log_value
        else resolve_repo_path(REQUEST_LOG_RELATIVE_PATH, repo_root)
    )
    cors_origins = _split_csv(source.get("ALTERSCORE_CORS_ORIGINS"))
    cors_origin_regex = source.get("ALTERSCORE_CORS_ORIGIN_REGEX") or None
    environment = source.get("ALTERSCORE_ENV", "local")

    # Rate limiting protects the expensive scoring pipeline. It defaults on only
    # in production so tests and local development stay unthrottled; an explicit
    # ALTERSCORE_RATE_LIMIT_ENABLED flag overrides the default either way.
    rate_limit_enabled = _env_flag(
        source.get("ALTERSCORE_RATE_LIMIT_ENABLED"),
        default=environment == "production",
    )
    score_rate_limit = (
        source.get("ALTERSCORE_SCORE_RATE_LIMIT", "").strip() or "30/minute"
    )

    return Settings(
        environment=environment,
        api_version=source.get("ALTERSCORE_API_VERSION", "0.1.0"),
        repo_root=repo_root,
        model_manifest_path=model_manifest_path,
        runtime_model_path=runtime_model_path,
        request_log_path=request_log_path,
        log_level=source.get("ALTERSCORE_LOG_LEVEL", "INFO").upper(),
        cors_origins=cors_origins or DEFAULT_CORS_ORIGINS,
        cors_origin_regex=cors_origin_regex,
        enable_debug_score=_env_flag(source.get("ALTERSCORE_ENABLE_DEBUG_SCORE")),
        rate_limit_enabled=rate_limit_enabled,
        score_rate_limit=score_rate_limit,
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return load_settings()


__all__ = [
    "DEFAULT_CORS_ORIGINS",
    "Settings",
    "get_settings",
    "load_settings",
]
