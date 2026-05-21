"""Production manifest contract helpers for AlterScore serving bundles."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Final

from backend.app.core.paths import resolve_repo_path

MANIFEST_REQUIRED_ARTIFACT_KEYS: Final[tuple[str, ...]] = (
    "runtime_model",
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
)
_REQUIRED_SPLIT_KEYS: Final[tuple[str, ...]] = ("train", "validation", "test")
_REQUIRED_STRING_FIELDS: Final[tuple[str, ...]] = (
    "manifest_schema_version",
    "manifest_version",
    "model_version",
    "run_id",
    "created_at",
    "code_ref",
    "data_version",
    "feature_registry_version",
    "runtime_model_name",
    "runtime_model_type",
    "target",
)
_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class ManifestArtifactEntry:
    """One manifest-declared artifact entry."""

    key: str
    path: str
    sha256: str

    def resolved_path(self, repo_root: Path) -> Path:
        return resolve_repo_path(self.path, repo_root)


@dataclass(frozen=True)
class ProductionManifest:
    """Validated serving-manifest payload."""

    manifest_schema_version: str
    manifest_version: str
    model_version: str
    run_id: str
    created_at: str
    code_ref: str
    data_version: str
    feature_registry_version: str
    runtime_model_name: str
    runtime_model_type: str
    target: str
    split: dict[str, str]
    artifacts: dict[str, ManifestArtifactEntry]
    metrics_summary: dict[str, Any]
    fairness_summary: dict[str, Any]
    drift_summary: dict[str, Any]
    promotion_status: str | None
    promotion_notes: str | None
    raw_payload: dict[str, Any]
    base_models: dict[str, ManifestArtifactEntry] | None = None
    stacking_config: ManifestArtifactEntry | None = None

    def artifact_path(self, artifact_key: str, repo_root: Path) -> Path:
        return self.artifacts[artifact_key].resolved_path(repo_root)

    def artifact_checksum(self, artifact_key: str) -> str:
        return self.artifacts[artifact_key].sha256


def compute_file_sha256(path: str | Path) -> str:
    """Return the lowercase SHA256 checksum for ``path``."""

    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_production_manifest(path: str | Path) -> ProductionManifest:
    """Load and validate a production serving manifest."""

    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("production manifest payload must be a JSON object.")

    for field_name in _REQUIRED_STRING_FIELDS:
        _require_non_empty_string(payload, field_name)

    _validate_iso8601_timestamp(payload["created_at"])

    split = _require_mapping(payload, "split")
    validated_split = {
        key: _require_non_empty_string(split, key, context="production manifest split")
        for key in _REQUIRED_SPLIT_KEYS
    }

    artifacts_payload = _require_mapping(payload, "artifacts")
    artifacts = {
        artifact_key: _parse_artifact_entry(artifacts_payload, artifact_key)
        for artifact_key in MANIFEST_REQUIRED_ARTIFACT_KEYS
    }

    metrics_summary = _require_mapping(payload, "metrics_summary")
    fairness_summary = _require_mapping(payload, "fairness_summary")
    drift_summary = _require_mapping(payload, "drift_summary")

    promotion_status = payload.get("promotion_status")
    if promotion_status is not None and (
        not isinstance(promotion_status, str) or not promotion_status.strip()
    ):
        raise ValueError(
            "production manifest 'promotion_status' must be a non-empty string when present."
        )

    promotion_notes = payload.get("promotion_notes")
    if promotion_notes is not None and not isinstance(promotion_notes, str):
        raise ValueError(
            "production manifest 'promotion_notes' must be a string when present."
        )

    base_models = None
    if "base_models" in payload:
        base_models_payload = _require_mapping(payload, "base_models")
        base_models = {
            k: _parse_artifact_entry(base_models_payload, k)
            for k in base_models_payload
        }

    stacking_config = None
    if "stacking_config" in payload:
        stacking_config = _parse_artifact_entry(payload, "stacking_config")

    if str(payload["runtime_model_type"]) == "ensemble":
        if not base_models:
            raise ValueError(
                "production manifest for an ensemble runtime model must declare "
                "a non-empty 'base_models' artifact map."
            )
        if stacking_config is None:
            raise ValueError(
                "production manifest for an ensemble runtime model must declare "
                "a 'stacking_config' artifact entry."
            )

    return ProductionManifest(
        manifest_schema_version=str(payload["manifest_schema_version"]),
        manifest_version=str(payload["manifest_version"]),
        model_version=str(payload["model_version"]),
        run_id=str(payload["run_id"]),
        created_at=str(payload["created_at"]),
        code_ref=str(payload["code_ref"]),
        data_version=str(payload["data_version"]),
        feature_registry_version=str(payload["feature_registry_version"]),
        runtime_model_name=str(payload["runtime_model_name"]),
        runtime_model_type=str(payload["runtime_model_type"]),
        target=str(payload["target"]),
        split=validated_split,
        artifacts=artifacts,
        metrics_summary=metrics_summary,
        fairness_summary=fairness_summary,
        drift_summary=drift_summary,
        promotion_status=None if promotion_status is None else str(promotion_status),
        promotion_notes=None if promotion_notes is None else str(promotion_notes),
        raw_payload=payload,
        base_models=base_models,
        stacking_config=stacking_config,
    )


def _parse_artifact_entry(
    artifacts_payload: dict[str, Any],
    artifact_key: str,
) -> ManifestArtifactEntry:
    entry_payload = artifacts_payload.get(artifact_key)
    if not isinstance(entry_payload, dict):
        raise ValueError(
            "production manifest artifacts."
            f"{artifact_key} must be a JSON object with 'path' and 'sha256'."
        )

    path_value = _require_non_empty_string(
        entry_payload,
        "path",
        context=f"production manifest artifacts.{artifact_key}",
    )
    sha256_value = _require_non_empty_string(
        entry_payload,
        "sha256",
        context=f"production manifest artifacts.{artifact_key}",
    )
    if not _SHA256_PATTERN.fullmatch(sha256_value):
        raise ValueError(
            "production manifest artifacts."
            f"{artifact_key}.sha256 must be a 64-character lowercase hexadecimal SHA256 digest."
        )

    return ManifestArtifactEntry(
        key=artifact_key,
        path=path_value,
        sha256=sha256_value,
    )


def _require_mapping(
    payload: dict[str, Any],
    field_name: str,
) -> dict[str, Any]:
    value = payload.get(field_name)
    if not isinstance(value, dict):
        raise ValueError(f"production manifest '{field_name}' field must be a JSON object.")
    return value


def _require_non_empty_string(
    payload: dict[str, Any],
    field_name: str,
    *,
    context: str = "production manifest",
) -> str:
    value = payload.get(field_name)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{context} missing required non-empty string field '{field_name}'.")
    return value.strip()


def _validate_iso8601_timestamp(value: str) -> None:
    normalized_value = value.replace("Z", "+00:00")
    try:
        datetime.fromisoformat(normalized_value)
    except ValueError as exc:
        raise ValueError(
            "production manifest 'created_at' must be a valid ISO-8601 timestamp."
        ) from exc


__all__ = [
    "MANIFEST_REQUIRED_ARTIFACT_KEYS",
    "ManifestArtifactEntry",
    "ProductionManifest",
    "compute_file_sha256",
    "load_production_manifest",
]
