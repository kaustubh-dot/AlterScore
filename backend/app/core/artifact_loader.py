"""Runtime artifact loading helpers for AlterScore backend scoring."""

from __future__ import annotations

from dataclasses import dataclass, replace
from functools import lru_cache
import json
from pathlib import Path
from typing import Any, Callable, Final

import joblib

from backend.app.core.paths import MODEL_ARTIFACTS_DIR, resolve_repo_path
from backend.app.core.settings import Settings, get_settings
from backend.ml.explainability.global_importance import (
    normalize_global_importance_payload,
)
from backend.ml.explainability.dice_explainer import (
    PersistedDiceExplainer,
    load_persisted_dice_explainer,
)
from backend.ml.explainability.shap_explainer import (
    PersistedShapExplainer,
    load_persisted_shap_explainer,
)
from backend.ml.preprocessing.feature_registry import ALL_MODEL_FEATURES
from backend.ml.registry.production_manifest import (
    MANIFEST_REQUIRED_ARTIFACT_KEYS,
    ProductionManifest,
    compute_file_sha256,
    load_production_manifest,
)
from backend.ml.training.neural.train_tabnet import load_tabnet_model
from backend.ml.training.neural.train_mlp import load_mlp_model


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
        model_name="xgboost",
        model_type="classical",
        artifact_path=MODEL_ARTIFACTS_DIR / "xgb_best.pkl",
    ),
    RuntimeModelCandidate(
        model_name="lightgbm",
        model_type="classical",
        artifact_path=MODEL_ARTIFACTS_DIR / "lgbm_best.pkl",
    ),
    RuntimeModelCandidate(
        model_name="random_forest",
        model_type="classical",
        artifact_path=MODEL_ARTIFACTS_DIR / "rf_best.pkl",
    ),
    RuntimeModelCandidate(
        model_name="logistic_regression",
        model_type="classical",
        artifact_path=MODEL_ARTIFACTS_DIR / "logistic_best.pkl",
    ),
)
RUNTIME_MODEL_CANDIDATE_FILENAMES: Final[dict[str, str]] = {
    candidate.model_name: candidate.artifact_path.name for candidate in RUNTIME_MODEL_CANDIDATES
}
SCORING_CRITICAL_ARTIFACTS: Final[tuple[str, ...]] = (
    "runtime_model",
    "preprocessor",
    "text_pca",
)
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
    manifest_version: str | None
    model_version: str | None
    runtime_model_path: Path | None
    manifest_path: Path | None
    resolved_paths: dict[str, Path]
    artifacts_present: tuple[str, ...]
    artifacts_loaded: tuple[str, ...]
    missing_artifacts: tuple[str, ...]
    invalid_artifacts: tuple[str, ...]
    artifact_errors: dict[str, str]
    scoring_ready: bool


@dataclass(frozen=True)
class LoadedArtifactBundle:
    report: ArtifactLoadReport
    model: Any | None
    preprocessor: Any | None
    text_pca: Any | None
    shap_explainer: PersistedShapExplainer | None
    dice_explainer: PersistedDiceExplainer | None
    metrics_payload: dict[str, Any] | None
    baseline_metrics: list[dict[str, Any]] | None
    fairness_report: Any | None
    psi_report: Any | None
    global_importance: Any | None
    population_percentiles: dict[str, Any] | None
    manifest: dict[str, Any] | None
    base_models: dict[str, Any] | None = None
    stacking_config: dict[str, Any] | None = None


def inspect_runtime_artifacts(settings: Settings | None = None) -> ArtifactLoadReport:
    """Inspect the current runtime artifact state using the same validation as startup."""

    return load_runtime_artifact_bundle(settings, strict=False).report


def load_runtime_artifact_bundle(
    settings: Settings | None = None,
    *,
    strict: bool = True,
) -> LoadedArtifactBundle:
    """Load the current runtime artifact bundle for backend scoring."""

    resolved_settings = settings or get_settings()
    repo_root = resolved_settings.repo_root
    base_report, manifest = _resolve_artifact_state(resolved_settings)
    loaded_artifacts: set[str] = set()
    invalid_artifacts: set[str] = set()
    artifact_errors: dict[str, str] = {}
    manifest_checksums = (
        {key: entry.sha256 for key, entry in manifest.artifacts.items()}
        if manifest is not None
        else {}
    )

    if manifest is not None and "production_manifest" in base_report.artifacts_present:
        loaded_artifacts.add("production_manifest")

    runtime_model_path = base_report.resolved_paths.get("runtime_model")
    preprocessor_path = base_report.resolved_paths.get("preprocessor")
    text_pca_path = base_report.resolved_paths.get("text_pca")
    shap_explainer_path = base_report.resolved_paths.get("shap_explainer")
    dice_explainer_path = base_report.resolved_paths.get("dice_explainer")
    metrics_path = base_report.resolved_paths.get("metrics")
    baseline_metrics_path = base_report.resolved_paths.get("baseline_metrics")
    fairness_report_path = base_report.resolved_paths.get("fairness_report")
    psi_report_path = base_report.resolved_paths.get("psi_report")
    global_importance_path = base_report.resolved_paths.get("global_importance")
    population_percentiles_path = base_report.resolved_paths.get("population_percentiles")

    model = _load_validated_artifact(
        artifact_key="runtime_model",
        path=runtime_model_path,
        loader=_load_joblib,
        validator=_validate_runtime_model,
        expected_sha256=manifest_checksums.get("runtime_model"),
        loaded_artifacts=loaded_artifacts,
        invalid_artifacts=invalid_artifacts,
        artifact_errors=artifact_errors,
    )
    preprocessor = _load_validated_artifact(
        artifact_key="preprocessor",
        path=preprocessor_path,
        loader=_load_joblib,
        validator=_validate_preprocessor,
        expected_sha256=manifest_checksums.get("preprocessor"),
        loaded_artifacts=loaded_artifacts,
        invalid_artifacts=invalid_artifacts,
        artifact_errors=artifact_errors,
    )
    text_pca = _load_validated_artifact(
        artifact_key="text_pca",
        path=text_pca_path,
        loader=_load_joblib,
        validator=_validate_text_pca,
        expected_sha256=manifest_checksums.get("text_pca"),
        loaded_artifacts=loaded_artifacts,
        invalid_artifacts=invalid_artifacts,
        artifact_errors=artifact_errors,
    )
    shap_explainer = _load_validated_artifact(
        artifact_key="shap_explainer",
        path=shap_explainer_path,
        loader=lambda path: load_persisted_shap_explainer(
            path,
            expected_feature_names=ALL_MODEL_FEATURES,
        ),
        validator=None,
        expected_sha256=manifest_checksums.get("shap_explainer"),
        loaded_artifacts=loaded_artifacts,
        invalid_artifacts=invalid_artifacts,
        artifact_errors=artifact_errors,
    )
    dice_explainer = _load_validated_artifact(
        artifact_key="dice_explainer",
        path=dice_explainer_path,
        loader=lambda path: load_persisted_dice_explainer(
            path,
            expected_feature_names=ALL_MODEL_FEATURES,
        ),
        validator=None,
        expected_sha256=manifest_checksums.get("dice_explainer"),
        loaded_artifacts=loaded_artifacts,
        invalid_artifacts=invalid_artifacts,
        artifact_errors=artifact_errors,
    )
    metrics_payload = _load_validated_artifact(
        artifact_key="metrics",
        path=metrics_path,
        loader=_load_json,
        validator=_validate_json_mapping,
        expected_sha256=manifest_checksums.get("metrics"),
        loaded_artifacts=loaded_artifacts,
        invalid_artifacts=invalid_artifacts,
        artifact_errors=artifact_errors,
    )
    baseline_metrics = _load_validated_artifact(
        artifact_key="baseline_metrics",
        path=baseline_metrics_path,
        loader=_load_json,
        validator=_validate_json_sequence,
        expected_sha256=manifest_checksums.get("baseline_metrics"),
        loaded_artifacts=loaded_artifacts,
        invalid_artifacts=invalid_artifacts,
        artifact_errors=artifact_errors,
    )
    fairness_report = _load_validated_artifact(
        artifact_key="fairness_report",
        path=fairness_report_path,
        loader=_load_json,
        validator=_validate_json_mapping,
        expected_sha256=manifest_checksums.get("fairness_report"),
        loaded_artifacts=loaded_artifacts,
        invalid_artifacts=invalid_artifacts,
        artifact_errors=artifact_errors,
    )
    psi_report = _load_validated_artifact(
        artifact_key="psi_report",
        path=psi_report_path,
        loader=_load_json,
        validator=_validate_json_mapping,
        expected_sha256=manifest_checksums.get("psi_report"),
        loaded_artifacts=loaded_artifacts,
        invalid_artifacts=invalid_artifacts,
        artifact_errors=artifact_errors,
    )
    global_importance = _load_validated_artifact(
        artifact_key="global_importance",
        path=global_importance_path,
        loader=lambda path: normalize_global_importance_payload(
            _load_json(path),
            default_model_name=base_report.runtime_model_name,
            default_model_type=base_report.runtime_model_type,
        ),
        validator=_validate_json_mapping,
        expected_sha256=manifest_checksums.get("global_importance"),
        loaded_artifacts=loaded_artifacts,
        invalid_artifacts=invalid_artifacts,
        artifact_errors=artifact_errors,
    )
    population_percentiles = _load_validated_artifact(
        artifact_key="population_percentiles",
        path=population_percentiles_path,
        loader=lambda path: _resolve_population_percentiles_payload(
            _load_json(path),
            runtime_model_name=base_report.runtime_model_name,
        ),
        validator=_validate_json_mapping,
        expected_sha256=manifest_checksums.get("population_percentiles"),
        loaded_artifacts=loaded_artifacts,
        invalid_artifacts=invalid_artifacts,
        artifact_errors=artifact_errors,
    )

    # Eagerly check scoring-critical artifacts before attempting expensive ensemble loading
    _pre_ensemble_report = _finalize_artifact_report(
        base_report,
        loaded_artifacts=loaded_artifacts,
        invalid_artifacts=invalid_artifacts,
        artifact_errors=artifact_errors,
    )
    if strict and not _pre_ensemble_report.scoring_ready:
        raise ArtifactLoadError(_format_scoring_ready_error(_pre_ensemble_report))

    # Load base models and config if manifest is an ensemble
    base_models: dict[str, Any] | None = None
    stacking_config: dict[str, Any] | None = None

    if manifest is not None and manifest.runtime_model_type == "ensemble":
        if manifest.base_models and manifest.stacking_config:
            try:
                # Load stacking config using the existing _load_json helper
                config_path = manifest.stacking_config.resolved_path(repo_root)
                stacking_config = _load_json(config_path)
                loaded_artifacts.add("stacking_config")

                # Load each base model using the appropriate loader per file type
                base_models = {}
                for model_name, entry in manifest.base_models.items():
                    model_path = entry.resolved_path(repo_root)
                    if model_path.suffix == ".zip":
                        base_models[model_name] = load_tabnet_model(model_path)
                    elif model_path.suffix == ".pt":
                        base_models[model_name] = load_mlp_model(model_path)
                    else:
                        base_models[model_name] = joblib.load(model_path)
                loaded_artifacts.add("base_models")
            except Exception as e:
                invalid_artifacts.add("base_models")
                artifact_errors["base_models"] = f"Failed to load ensemble base models: {e}"
        else:
            invalid_artifacts.add("base_models")
            artifact_errors["base_models"] = "Ensemble manifest is missing base_models or stacking_config."

    # Finalize report after ensemble loading so base_models appear in artifacts_loaded
    report = _finalize_artifact_report(
        base_report,
        loaded_artifacts=loaded_artifacts,
        invalid_artifacts=invalid_artifacts,
        artifact_errors=artifact_errors,
    )

    return LoadedArtifactBundle(
        report=report,
        model=model,
        preprocessor=preprocessor,
        text_pca=text_pca,
        shap_explainer=shap_explainer,
        dice_explainer=dice_explainer,
        metrics_payload=metrics_payload,
        baseline_metrics=baseline_metrics,
        fairness_report=fairness_report,
        psi_report=psi_report,
        global_importance=global_importance,
        population_percentiles=population_percentiles,
        manifest=None if manifest is None else dict(manifest.raw_payload),
        base_models=base_models,
        stacking_config=stacking_config,
    )


@lru_cache(maxsize=1)
def get_runtime_artifact_bundle() -> LoadedArtifactBundle:
    """Cached runtime bundle for future FastAPI startup and request handlers."""

    return load_runtime_artifact_bundle(get_settings(), strict=False)


def _resolve_artifact_state(
    settings: Settings | None,
) -> tuple[ArtifactLoadReport, ProductionManifest | None]:
    resolved_settings = settings or get_settings()

    if resolved_settings.runtime_model_path is not None:
        runtime_model_path = resolved_settings.runtime_model_path
        runtime_model_name, runtime_model_type = _infer_runtime_model_metadata(
            runtime_model_path
        )
        source = "runtime_model_path"
        manifest = None
        manifest_path = None
        manifest_version = None
        model_version = None
        resolved_paths = _build_fallback_paths(
            repo_root=resolved_settings.repo_root,
            runtime_model_path=runtime_model_path,
            manifest_path=resolved_settings.model_manifest_path,
            include_manifest=False,
        )
    elif resolved_settings.model_manifest_path.is_file():
        source = "manifest"
        manifest_path = resolved_settings.model_manifest_path
        manifest = _load_manifest(manifest_path)
        resolved_paths = _build_manifest_paths(
            settings=resolved_settings,
            manifest=manifest,
        )
        runtime_model_path = resolved_paths.get("runtime_model")
        runtime_model_name = manifest.runtime_model_name
        runtime_model_type = manifest.runtime_model_type
        manifest_version = manifest.manifest_version
        model_version = manifest.model_version
        inferred_model_name, inferred_model_type = _infer_runtime_model_metadata(
            runtime_model_path
        )
        if (
            inferred_model_name is not None
            and inferred_model_type != "unknown"
            and (
                inferred_model_name != runtime_model_name
                or inferred_model_type != runtime_model_type
            )
        ):
            raise ArtifactLoadError(
                "production manifest runtime model metadata does not match the "
                f"resolved artifact path: manifest declares {runtime_model_name!r} "
                f"({runtime_model_type!r}) but path resolves to "
                f"{inferred_model_name!r} ({inferred_model_type!r})."
            )
    else:
        source = "candidate"
        manifest = None
        manifest_path = None
        manifest_version = None
        model_version = None
        candidate = _select_runtime_model_candidate(resolved_settings.repo_root)
        runtime_model_path = None if candidate is None else candidate.artifact_path
        runtime_model_name = None if candidate is None else candidate.model_name
        runtime_model_type = None if candidate is None else candidate.model_type
        resolved_paths = _build_fallback_paths(
            repo_root=resolved_settings.repo_root,
            runtime_model_path=runtime_model_path,
            manifest_path=resolved_settings.model_manifest_path,
            include_manifest=False,
        )

    artifacts_present = tuple(
        key for key, path in sorted(resolved_paths.items()) if path.is_file()
    )
    missing_artifacts = tuple(
        key for key, path in sorted(resolved_paths.items()) if not path.is_file()
    )

    return (
        ArtifactLoadReport(
            source=source,
            runtime_model_name=runtime_model_name,
            runtime_model_type=runtime_model_type,
            manifest_version=manifest_version,
            model_version=model_version,
            runtime_model_path=runtime_model_path,
            manifest_path=manifest_path,
            resolved_paths=resolved_paths,
            artifacts_present=artifacts_present,
            artifacts_loaded=(),
            missing_artifacts=missing_artifacts,
            invalid_artifacts=(),
            artifact_errors={},
            scoring_ready=False,
        ),
        manifest,
    )


def _build_manifest_paths(
    *,
    settings: Settings,
    manifest: ProductionManifest,
) -> dict[str, Path]:
    artifact_paths = {
        artifact_key: manifest.artifact_path(artifact_key, settings.repo_root)
        for artifact_key in MANIFEST_REQUIRED_ARTIFACT_KEYS
    }
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


def _load_manifest(path: Path) -> ProductionManifest:
    try:
        return load_production_manifest(path)
    except ValueError as exc:
        raise ArtifactLoadError(str(exc)) from exc


def _select_runtime_model_candidate(repo_root: Path) -> RuntimeModelCandidate | None:
    available_candidates = [
        candidate
        for candidate in _resolve_runtime_model_candidates(repo_root)
        if candidate.artifact_path.is_file()
    ]
    if not available_candidates:
        return None

    metric_scores = _load_candidate_test_auc_by_model(repo_root)
    candidate_priority = {
        candidate.model_name: index for index, candidate in enumerate(RUNTIME_MODEL_CANDIDATES)
    }

    return min(
        available_candidates,
        key=lambda candidate: (
            0 if candidate.model_name in metric_scores else 1,
            -metric_scores.get(candidate.model_name, float("-inf")),
            candidate_priority[candidate.model_name],
        ),
    )


def _infer_runtime_model_metadata(
    runtime_model_path: Path | None,
) -> tuple[str | None, str | None]:
    if runtime_model_path is None:
        return None, None

    for candidate in RUNTIME_MODEL_CANDIDATES:
        if runtime_model_path.name == candidate.artifact_path.name:
            return candidate.model_name, candidate.model_type

    return runtime_model_path.stem, "unknown"


def _resolve_runtime_model_candidates(repo_root: Path) -> tuple[RuntimeModelCandidate, ...]:
    return tuple(
        RuntimeModelCandidate(
            model_name=candidate.model_name,
            model_type=candidate.model_type,
            artifact_path=resolve_repo_path(
                Path("models/artifacts") / RUNTIME_MODEL_CANDIDATE_FILENAMES[candidate.model_name],
                repo_root,
            ),
        )
        for candidate in RUNTIME_MODEL_CANDIDATES
    )


def _load_candidate_test_auc_by_model(repo_root: Path) -> dict[str, float]:
    metrics_path = resolve_repo_path(
        DEFAULT_RUNTIME_ARTIFACT_RELATIVE_PATHS["metrics"],
        repo_root,
    )
    payload = _load_json_if_present(metrics_path)
    if not isinstance(payload, dict):
        return {}

    model_stats = payload.get("model_stats")
    if not isinstance(model_stats, list):
        return {}

    scores: dict[str, float] = {}
    for item in model_stats:
        if not isinstance(item, dict):
            continue
        if item.get("split") != "test_months_11_12":
            continue
        model_name = item.get("model_name")
        auc_roc = item.get("auc_roc")
        if not isinstance(model_name, str):
            continue
        try:
            scores[model_name] = float(auc_roc)
        except (TypeError, ValueError):
            continue
    return scores


def _load_validated_artifact(
    *,
    artifact_key: str,
    path: Path | None,
    loader: Callable[[Path], Any],
    validator: Callable[[Any], None] | None,
    expected_sha256: str | None,
    loaded_artifacts: set[str],
    invalid_artifacts: set[str],
    artifact_errors: dict[str, str],
) -> Any | None:
    if path is None or not path.is_file():
        return None

    try:
        if expected_sha256 is not None:
            actual_sha256 = compute_file_sha256(path)
            if actual_sha256 != expected_sha256:
                raise ValueError(
                    "artifact checksum does not match the production manifest: "
                    f"expected {expected_sha256}, got {actual_sha256}."
                )
        payload = loader(path)
        if validator is not None:
            validator(payload)
    except Exception as exc:
        invalid_artifacts.add(artifact_key)
        artifact_errors[artifact_key] = f"{type(exc).__name__}: {exc}"
        return None

    loaded_artifacts.add(artifact_key)
    return payload


def _finalize_artifact_report(
    base_report: ArtifactLoadReport,
    *,
    loaded_artifacts: set[str],
    invalid_artifacts: set[str],
    artifact_errors: dict[str, str],
) -> ArtifactLoadReport:
    return replace(
        base_report,
        artifacts_loaded=tuple(sorted(loaded_artifacts)),
        invalid_artifacts=tuple(sorted(invalid_artifacts)),
        artifact_errors=dict(sorted(artifact_errors.items())),
        scoring_ready=all(
            artifact_key in loaded_artifacts for artifact_key in SCORING_CRITICAL_ARTIFACTS
        ),
    )


def _format_scoring_ready_error(report: ArtifactLoadReport) -> str:
    critical_missing = [
        artifact_key
        for artifact_key in SCORING_CRITICAL_ARTIFACTS
        if artifact_key in report.missing_artifacts
    ]
    critical_invalid = [
        artifact_key
        for artifact_key in SCORING_CRITICAL_ARTIFACTS
        if artifact_key in report.invalid_artifacts
    ]
    details: list[str] = []
    if critical_missing:
        details.append(f"missing {critical_missing}")
    if critical_invalid:
        details.append(f"invalid {critical_invalid}")
    if not details:
        details.append("unknown scoring-critical artifact failure")
    return "Scoring artifacts are not ready: " + "; ".join(details) + "."


def _load_joblib(path: Path) -> Any:
    return joblib.load(path)


def _load_joblib_if_present(path: Path | None) -> Any | None:
    if path is None or not path.is_file():
        return None
    return _load_joblib(path)


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_json_if_present(path: Path | None) -> Any | None:
    if path is None or not path.is_file():
        return None
    return _load_json(path)


def _validate_runtime_model(model: Any) -> None:
    if not hasattr(model, "predict_proba"):
        raise ValueError("runtime model does not expose predict_proba().")


def _validate_preprocessor(preprocessor: Any) -> None:
    if not callable(getattr(preprocessor, "transform", None)):
        raise ValueError("preprocessor does not expose transform().")


def _validate_text_pca(text_pca: Any) -> None:
    if not callable(getattr(text_pca, "transform", None)):
        raise ValueError("text PCA artifact does not expose transform().")


def _validate_json_mapping(payload: Any) -> None:
    if not isinstance(payload, dict):
        raise ValueError("artifact payload must be a JSON object.")


def _validate_json_sequence(payload: Any) -> None:
    if not isinstance(payload, list):
        raise ValueError("artifact payload must be a JSON list.")


def _resolve_population_percentiles_payload(
    payload: Any | None,
    *,
    runtime_model_name: str | None,
) -> Any | None:
    if not isinstance(payload, dict):
        return payload

    model_payloads = payload.get("models")
    if not isinstance(model_payloads, dict) or not model_payloads:
        return payload

    selected_model_name = (
        runtime_model_name
        if isinstance(runtime_model_name, str) and runtime_model_name in model_payloads
        else payload.get("default_model_name")
    )
    if not isinstance(selected_model_name, str) or selected_model_name not in model_payloads:
        return payload

    selected_payload = model_payloads.get(selected_model_name)
    if not isinstance(selected_payload, dict):
        return payload

    return {
        **selected_payload,
        "selected_model_name": selected_model_name,
        "default_model_name": payload.get("default_model_name"),
        "available_models": payload.get("available_models"),
    }


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
