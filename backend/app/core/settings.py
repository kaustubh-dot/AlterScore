"""Runtime settings for the public, artifact-free AlterScore API."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from os import environ
from typing import Mapping

DEFAULT_CORS_ORIGINS = (
    "http://localhost:5173",
    "http://127.0.0.1:5173",
)


def _split_csv(value: str | None) -> tuple[str, ...]:
    if not value:
        return ()
    return tuple(item.strip() for item in value.split(",") if item.strip())


def _normalize_environment(value: str | None) -> str:
    """Return the canonical environment spelling used by serving safeguards."""

    return (value or "local").strip().lower() or "local"


@dataclass(frozen=True)
class Settings:
    """Settings consumed by the v2 service and HTTP boundary."""

    environment: str
    api_version: str
    cors_origins: tuple[str, ...]
    cors_origin_regex: str | None
    release_sha: str = "local"
    signing_secret: str | None = None
    signing_key_version: str = "local"


def load_settings(env: Mapping[str, str] | None = None) -> Settings:
    """Load public API settings without reading model or artifact paths."""

    source = environ if env is None else env
    environment = _normalize_environment(source.get("ALTERSCORE_ENV"))
    release_sha = (
        source.get("ALTERSCORE_RELEASE_SHA", "").strip()
        or source.get("GIT_SHA", "").strip()
        or "local"
    )
    return Settings(
        environment=environment,
        api_version=source.get("ALTERSCORE_API_VERSION", "0.2.0"),
        cors_origins=_split_csv(source.get("ALTERSCORE_CORS_ORIGINS"))
        or DEFAULT_CORS_ORIGINS,
        cors_origin_regex=source.get("ALTERSCORE_CORS_ORIGIN_REGEX") or None,
        release_sha=release_sha,
        signing_secret=source.get("ALTERSCORE_SIGNING_SECRET") or None,
        signing_key_version=source.get("ALTERSCORE_SIGNING_KEY_VERSION", "local").strip()
        or "local",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return load_settings()


__all__ = ["DEFAULT_CORS_ORIGINS", "Settings", "get_settings", "load_settings"]
