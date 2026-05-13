"""Runtime artifact loading helpers for AlterScore backend scoring."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import json
from pathlib import Path
from typing import Any, Final

import joblib

from backend.app.core.paths import MODEL_ARTIFACTS_DIR, resolve_repo_path
from backend.app.core.settings import Settings, get_settings


@dataclass(frozen=True)
class RuntimeModelCandidate:
    model_name: str
    model_type: str
    artifact_path: Path


RUNTIME_MODEL_CANDIDATES: Final[tuple[RuntimeModelCandidate, ...]] = (
    RuntimeModelCandidate(
        model_name="stacking_ensemble",
        model_type="ensemble",
        artifact_path=MODEL_ARTIFACTS_DIR / "calibrated_stacking.pkl",
    ),
    RuntimeModelCandidate(
        model_name="logistic_regression",
        model_type="classical",
        artifact_path=MODEL_ARTIFACTS_DIR / "logistic_best.pkl",
    ),
    RuntimeModelCandidate(
        model_name="xgboost",
        model_type="classical",
        artifact_path=MODEL_ARTIFACTS_DIR / "xgb_best.pkl",
    ),
    RuntimeModelCandidate(
        model_name="random_forest",
        model_type="classical",
        artifact_path=MODEL_ARTIFACTS_DIR / "rf_best.pkl",
    ),
    RuntimeModelCandidate(
        model_name="lightgbm",
        model_type="classical",
        artifact_path=MODEL_ARTIFACTS_DIR / "lgbm_best.pkl",
    ),
)
ARTIFACT_PATH_KEY_TO_MANIFEST_KEY: Final[dict[str, str]] = {
    "preprocessor": "preprocessor",
    "text_pca": "text_pca",
    "shap_explainer": "shap_explainer",
    "dice_explainer": "dice_explainer",
    "metrics": "metrics",
    "baseline_metrics": "baseline_metrics",
    "fairness_report": "fairness",
    "psi_report": "psi",
    "global_importance": "global_importance",
    "population_percentiles": "percentiles",
}
SCORING_CRITICAL_ARTIFACTS: Final[tuple[str, str]] = ("runtime_model", "preprocessor")
DEFAULT_RUNTIME_ARTIFACT_RELATIVE_PATHS: Final[dict[str, Path]] = {
    "preprocessor": Path("models/preprocessors/preprocessor.pkl"),
    "text_pca": Path("models/preprocessors/text_pca.pkl"),
    "shap_explainer": Path("models/explainers/shap_explainer.pkl"),
    "dice_explainer": Path("models/explainers/dice_explainer.pkl"),
    "metrics": Path("models/reports/metrics.json"),
    "baseline_metrics": Path("models/reports/baseline_metrics.json"),
    "fairness_report": Path("models/reports/fairness_report.json"),
    "psi_report": Path("models/reports/psi_report.json"),
    "global_importance": Path("models/reports/global_importance.json"),
    "population_percentiles": Path("models/reports/population_percentiles.json"),
}


class ArtifactLoadError(RuntimeError):
    """Raised when scoring-critical backend artifacts cannot be loaded."""


@dataclass(frozen=True)
class ArtifactLoadReport:
    source: str
    runtime_model_name: str | None
    runtime_model_type: str | None
    runtime_model_path: Path | None
    manifest_path: Path | None
    resolved_paths: dict[str, Path]
    artifacts_loaded: tuple[str, ...]
    missing_artifacts: tuple[str, ...]
    scoring_ready: bool


@dataclass(frozen=True)
class LoadedArtifactBundle:
    report: ArtifactLoadReport
    model: Any | None
    preprocessor: Any | None
    text_pca: Any | None
    metrics_payload: dict[str, Any] | None
    baseline_metrics: list[dict[str, Any]] | None
    population_percentiles: dict[str, Any] | None
    manifest: dict[str, Any] | None


def inspect_runtime_artifacts(settings: Settings | None = None) -> ArtifactLoadReport:
    """Inspect the current runtime artifact state without loading binaries."""

    report, _ = _resolve_artifact_state(settings)
    return report


def load_runtime_artifact_bundle(
    settings: Settings | None = None,
    *,
    strict: bool = True,
) -> LoadedArtifactBundle:
    """Load the current runtime artifact bundle for backend scoring."""

    report, manifest_payload = _resolve_artifact_state(settings)
    if strict and not report.scoring_ready:
        raise ArtifactLoadError(
            "Missing scoring-critical artifacts: "
            f"{list(_critical_missing_artifacts(report))}"
        )

    runtime_model_path = report.resolved_paths.get("runtime_model")
    preprocessor_path = report.resolved_paths.get("preprocessor")
    text_pca_path = report.resolved_paths.get("text_pca")
    metrics_path = report.resolved_paths.get("metrics")
    baseline_metrics_path = report.resolved_paths.get("baseline_metrics")
    population_percentiles_path = report.resolved_paths.get("population_percentiles")

    model = _load_joblib_if_present(runtime_model_path)
    preprocessor = _load_joblib_if_present(preprocessor_path)
    text_pca = _load_joblib_if_present(text_pca_path)
    metrics_payload = _load_json_if_present(metrics_path)
    baseline_metrics = _load_json_if_present(baseline_metrics_path)
    population_percentiles = _load_json_if_present(population_percentiles_path)

    if strict and model is not None and not hasattr(model, "predict_proba"):
        raise ArtifactLoadError(
            f"Runtime model at {runtime_model_path} does not expose predict_proba()."
        )
    if strict and preprocessor is not None and not hasattr(preprocessor, "transform"):
        raise ArtifactLoadError(
            f"Preprocessor at {preprocessor_path} does not expose transform()."
        )
    if text_pca is not None and not callable(getattr(text_pca, "transform", None)):
        raise ArtifactLoadError(
            f"Text PCA artifact at {text_pca_path} does not expose transform()."
        )

    return LoadedArtifactBundle(
        report=report,
        model=model,
        preprocessor=preprocessor,
        text_pca=text_pca,
        metrics_payload=metrics_payload if isinstance(metrics_payload, dict) else None,
        baseline_metrics=baseline_metrics if isinstance(baseline_metrics, list) else None,
        population_percentiles=(
            population_percentiles
            if isinstance(population_percentiles, dict)
            else None
        ),
        manifest=manifest_payload,
    )


@lru_cache(maxsize=1)
def get_runtime_artifact_bundle() -> LoadedArtifactBundle:
    """Cached runtime bundle for future FastAPI startup and request handlers."""

    return load_runtime_artifact_bundle(get_settings(), strict=False)


def _resolve_artifact_state(
    settings: Settings | None,
) -> tuple[ArtifactLoadReport, dict[str, Any] | None]:
    resolved_settings = settings or get_settings()

    if resolved_settings.runtime_model_path is not None:
        runtime_model_path = resolved_settings.runtime_model_path
        runtime_model_name, runtime_model_type = _infer_runtime_model_metadata(
            runtime_model_path
        )
        source = "runtime_model_path"
        manifest_payload = None
        manifest_path = None
        resolved_paths = _build_fallback_paths(
            repo_root=resolved_settings.repo_root,
            runtime_model_path=runtime_model_path,
            manifest_path=resolved_settings.model_manifest_path,
            include_manifest=False,
        )
    elif resolved_settings.model_manifest_path.is_file():
        source = "manifest"
        manifest_path = resolved_settings.model_manifest_path
        manifest_payload = _load_manifest(manifest_path)
        resolved_paths = _build_manifest_paths(
            settings=resolved_settings,
            manifest_payload=manifest_payload,
        )
        runtime_model_path = resolved_paths.get("runtime_model")
        runtime_model_name, runtime_model_type = _infer_runtime_model_metadata(
            runtime_model_path
        )
    else:
        source = "candidate"
        manifest_payload = None
        manifest_path = None
        candidate = _select_runtime_model_candidate()
        runtime_model_path = None if candidate is None else candidate.artifact_path
        runtime_model_name = None if candidate is None else candidate.model_name
        runtime_model_type = None if candidate is None else candidate.model_type
        resolved_paths = _build_fallback_paths(
            repo_root=resolved_settings.repo_root,
            runtime_model_path=runtime_model_path,
            manifest_path=resolved_settings.model_manifest_path,
            include_manifest=False,
        )

    artifacts_loaded = tuple(
        key
        for key, path in sorted(resolved_paths.items())
        if path.is_file()
    )
    missing_artifacts = tuple(
        key
        for key, path in sorted(resolved_paths.items())
        if not path.is_file()
    )
    scoring_ready = all(
        artifact_key in artifacts_loaded for artifact_key in SCORING_CRITICAL_ARTIFACTS
    )

    return (
        ArtifactLoadReport(
            source=source,
            runtime_model_name=runtime_model_name,
            runtime_model_type=runtime_model_type,
            runtime_model_path=runtime_model_path,
            manifest_path=manifest_path,
            resolved_paths=resolved_paths,
            artifacts_loaded=artifacts_loaded,
            missing_artifacts=missing_artifacts,
            scoring_ready=scoring_ready,
        ),
        manifest_payload,
    )


def _build_manifest_paths(
    *,
    settings: Settings,
    manifest_payload: dict[str, Any],
) -> dict[str, Path]:
    artifact_paths = _base_runtime_paths(settings.repo_root)
    manifest_artifacts = manifest_payload.get("artifacts", {})
    if not isinstance(manifest_artifacts, dict):
        raise ArtifactLoadError("production manifest 'artifacts' field must be a JSON object.")

    model_value = manifest_artifacts.get("model")
    if model_value:
        artifact_paths["runtime_model"] = resolve_repo_path(model_value, settings.repo_root)

    for artifact_key, manifest_key in ARTIFACT_PATH_KEY_TO_MANIFEST_KEY.items():
        manifest_value = manifest_artifacts.get(manifest_key)
        if manifest_value:
            artifact_paths[artifact_key] = resolve_repo_path(
                manifest_value,
                settings.repo_root,
            )

    artifact_paths["production_manifest"] = settings.model_manifest_path
    return artifact_paths


def _build_fallback_paths(
    *,
    repo_root: Path,
    runtime_model_path: Path | None,
    manifest_path: Path,
    include_manifest: bool,
) -> dict[str, Path]:
    artifact_paths = _base_runtime_paths(repo_root)
    if runtime_model_path is not None:
        artifact_paths["runtime_model"] = runtime_model_path
    if include_manifest:
        artifact_paths["production_manifest"] = manifest_path
    return artifact_paths


def _base_runtime_paths(repo_root: Path) -> dict[str, Path]:
    return {
        artifact_key: resolve_repo_path(relative_path, repo_root)
        for artifact_key, relative_path in DEFAULT_RUNTIME_ARTIFACT_RELATIVE_PATHS.items()
    }


def _load_manifest(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ArtifactLoadError("production manifest payload must be a JSON object.")
    return payload


def _select_runtime_model_candidate() -> RuntimeModelCandidate | None:
    for candidate in RUNTIME_MODEL_CANDIDATES:
        if candidate.artifact_path.is_file():
            return candidate
    return None


def _infer_runtime_model_metadata(
    runtime_model_path: Path | None,
) -> tuple[str | None, str | None]:
    if runtime_model_path is None:
        return None, None

    for candidate in RUNTIME_MODEL_CANDIDATES:
        if runtime_model_path.name == candidate.artifact_path.name:
            return candidate.model_name, candidate.model_type

    return runtime_model_path.stem, "unknown"


def _critical_missing_artifacts(report: ArtifactLoadReport) -> tuple[str, ...]:
    return tuple(
        artifact_key
        for artifact_key in SCORING_CRITICAL_ARTIFACTS
        if artifact_key in report.missing_artifacts
    )


def _load_joblib_if_present(path: Path | None) -> Any | None:
    if path is None or not path.is_file():
        return None
    return joblib.load(path)


def _load_json_if_present(path: Path | None) -> Any | None:
    if path is None or not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


__all__ = [
    "ArtifactLoadError",
    "ArtifactLoadReport",
    "LoadedArtifactBundle",
    "RUNTIME_MODEL_CANDIDATES",
    "RuntimeModelCandidate",
    "get_runtime_artifact_bundle",
    "inspect_runtime_artifacts",
    "load_runtime_artifact_bundle",
]
