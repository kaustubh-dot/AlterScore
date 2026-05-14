from pathlib import Path

from backend.app.core.paths import (
    PRODUCTION_MANIFEST_PATH,
    REPO_ROOT,
    REQUEST_LOG_PATH,
    REQUIRED_ARTIFACT_PATHS,
    resolve_repo_path,
)
from backend.app.core.settings import DEFAULT_CORS_ORIGINS, load_settings


def test_repo_root_resolves_to_project_root() -> None:
    assert (REPO_ROOT / "docs" / "AI_WORKFLOW_RULES.md").is_file()
    assert (REPO_ROOT / "backend").is_dir()


def test_resolve_repo_path_handles_relative_and_absolute_paths(tmp_path: Path) -> None:
    relative_path = resolve_repo_path("models/registry/production_manifest.json")
    absolute_path = resolve_repo_path(tmp_path / "manifest.json")

    assert relative_path == PRODUCTION_MANIFEST_PATH
    assert absolute_path == (tmp_path / "manifest.json").resolve()


def test_required_artifact_paths_are_centralized_repo_paths() -> None:
    expected_keys = {
        "calibrated_stacking",
        "preprocessor",
        "text_pca",
        "shap_explainer",
        "dice_explainer",
        "metrics",
        "baseline_metrics",
        "fairness_report",
        "psi_report",
        "global_importance",
        "population_percentiles",
        "production_manifest",
    }

    assert set(REQUIRED_ARTIFACT_PATHS) == expected_keys
    assert all(path.is_absolute() for path in REQUIRED_ARTIFACT_PATHS.values())


def test_load_settings_uses_defaults_with_empty_env() -> None:
    settings = load_settings({})

    assert settings.environment == "local"
    assert settings.api_version == "0.1.0"
    assert settings.repo_root == REPO_ROOT
    assert settings.model_manifest_path == PRODUCTION_MANIFEST_PATH
    assert settings.runtime_model_path is None
    assert settings.request_log_path == REQUEST_LOG_PATH
    assert settings.log_level == "INFO"
    assert settings.cors_origins == DEFAULT_CORS_ORIGINS


def test_load_settings_supports_environment_overrides(tmp_path: Path) -> None:
    settings = load_settings(
        {
            "ALTERSCORE_ENV": "test",
            "ALTERSCORE_API_VERSION": "9.9.9",
            "ALTERSCORE_REPO_ROOT": str(tmp_path),
            "ALTERSCORE_MODEL_MANIFEST": "models/registry/test_manifest.json",
            "ALTERSCORE_RUNTIME_MODEL_PATH": "models/artifacts/logistic_best.pkl",
            "ALTERSCORE_REQUEST_LOG_PATH": "runtime/logs/test_requests.jsonl",
            "ALTERSCORE_LOG_LEVEL": "debug",
            "ALTERSCORE_CORS_ORIGINS": "http://localhost:5173, http://localhost:3000",
        }
    )

    assert settings.environment == "test"
    assert settings.api_version == "9.9.9"
    assert settings.repo_root == tmp_path.resolve()
    assert settings.model_manifest_path == (
        tmp_path / "models" / "registry" / "test_manifest.json"
    ).resolve()
    assert settings.runtime_model_path == (
        tmp_path / "models" / "artifacts" / "logistic_best.pkl"
    ).resolve()
    assert settings.request_log_path == (
        tmp_path / "runtime" / "logs" / "test_requests.jsonl"
    ).resolve()
    assert settings.log_level == "DEBUG"
    assert settings.cors_origins == (
        "http://localhost:5173",
        "http://localhost:3000",
    )
