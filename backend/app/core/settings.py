"""Runtime settings for the AlterScore backend."""

from dataclasses import dataclass
from functools import lru_cache
from os import environ
from pathlib import Path
from typing import Mapping

from backend.app.core.paths import PRODUCTION_MANIFEST_PATH, REPO_ROOT, resolve_repo_path


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
    log_level: str
    cors_origins: tuple[str, ...]


def _split_csv(value: str | None) -> tuple[str, ...]:
    if not value:
        return ()

    return tuple(item.strip() for item in value.split(",") if item.strip())


def load_settings(env: Mapping[str, str] | None = None) -> Settings:
    """Load settings from environment variables without side effects."""
    source = environ if env is None else env
    repo_root = Path(source["ALTERSCORE_REPO_ROOT"]).resolve() if source.get(
        "ALTERSCORE_REPO_ROOT"
    ) else REPO_ROOT
    manifest_value = source.get("ALTERSCORE_MODEL_MANIFEST")
    model_manifest_path = (
        resolve_repo_path(manifest_value, repo_root)
        if manifest_value
        else PRODUCTION_MANIFEST_PATH
    )
    cors_origins = _split_csv(source.get("ALTERSCORE_CORS_ORIGINS"))

    return Settings(
        environment=source.get("ALTERSCORE_ENV", "local"),
        api_version=source.get("ALTERSCORE_API_VERSION", "0.1.0"),
        repo_root=repo_root,
        model_manifest_path=model_manifest_path,
        log_level=source.get("ALTERSCORE_LOG_LEVEL", "INFO").upper(),
        cors_origins=cors_origins or DEFAULT_CORS_ORIGINS,
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
