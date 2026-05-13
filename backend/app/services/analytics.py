"""Report-backed analytics service for AlterScore backend routes."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from backend.app.core.artifact_loader import LoadedArtifactBundle
from backend.app.schemas.analytics import (
    BaselineComparisonResponse,
    CalibrationCurveResponse,
    ModelStatsResponse,
    ConfusionMatrixResponse,
    PrecisionRecallResponse,
    RocCurveResponse,
    ScoreDistributionResponse,
)


class AnalyticsServiceError(RuntimeError):
    """Base error for analytics service failures."""


@dataclass(frozen=True)
class AnalyticsArtifactMissingError(AnalyticsServiceError):
    artifact_key: str
    artifact_path: Path | None

    def __str__(self) -> str:
        if self.artifact_path is None:
            return f"Required analytics artifact '{self.artifact_key}' is missing."
        return (
            f"Required analytics artifact '{self.artifact_key}' is missing at "
            f"{self.artifact_path}."
        )


@dataclass(frozen=True)
class AnalyticsPayloadError(AnalyticsServiceError):
    artifact_key: str
    reason: str

    def __str__(self) -> str:
        return (
            f"Analytics artifact '{self.artifact_key}' is present but invalid: "
            f"{self.reason}"
        )


class AnalyticsService:
    """Serve backend analytics responses from already-generated report artifacts."""

    def __init__(self, artifacts: LoadedArtifactBundle) -> None:
        self.artifacts = artifacts

    def get_model_stats(self) -> ModelStatsResponse:
        metrics_payload = self._require_mapping_payload(
            artifact_key="metrics",
            payload=self.artifacts.metrics_payload,
        )
        model_stats = metrics_payload.get("model_stats")
        if not isinstance(model_stats, list):
            raise AnalyticsPayloadError(
                artifact_key="metrics",
                reason="metrics payload must contain a 'model_stats' JSON list.",
            )
        return self._validate_response(
            ModelStatsResponse,
            model_stats,
            artifact_key="metrics",
        )

    def get_baseline_comparison(self) -> BaselineComparisonResponse:
        baseline_metrics = self.artifacts.baseline_metrics
        if baseline_metrics is None:
            raise AnalyticsArtifactMissingError(
                artifact_key="baseline_metrics",
                artifact_path=self._resolved_path("baseline_metrics"),
            )
        if not isinstance(baseline_metrics, list):
            raise AnalyticsPayloadError(
                artifact_key="baseline_metrics",
                reason="baseline metrics payload must be a JSON list.",
            )
        return self._validate_response(
            BaselineComparisonResponse,
            baseline_metrics,
            artifact_key="baseline_metrics",
        )

    def get_score_distribution(self) -> ScoreDistributionResponse:
        percentile_payload = self._require_mapping_payload(
            artifact_key="population_percentiles",
            payload=self.artifacts.population_percentiles,
        )

        try:
            payload = {
                "model_name": percentile_payload["model_name"],
                "row_count": percentile_payload["row_count"],
                "summary": percentile_payload["summary"],
                "score_histogram": percentile_payload["score_histogram"],
            }
            return self._validate_response(
                ScoreDistributionResponse,
                payload,
                artifact_key="population_percentiles",
            )
        except KeyError as exc:
            raise AnalyticsPayloadError(
                artifact_key="population_percentiles",
                reason=(
                    "population percentiles payload must contain "
                    "'model_name', 'row_count', 'summary', and 'score_histogram'."
                ),
            ) from exc

    def get_roc_data(self) -> RocCurveResponse:
        evaluation_details = self._require_split_evaluation_details()
        return self._validate_response(
            RocCurveResponse,
            self._build_series_payload(evaluation_details, points_key="roc_curve"),
            artifact_key="metrics",
        )

    def get_pr_curve(self) -> PrecisionRecallResponse:
        evaluation_details = self._require_split_evaluation_details()
        return self._validate_response(
            PrecisionRecallResponse,
            self._build_series_payload(evaluation_details, points_key="pr_curve"),
            artifact_key="metrics",
        )

    def get_calibration_curve(self) -> CalibrationCurveResponse:
        evaluation_details = self._require_split_evaluation_details()
        return self._validate_response(
            CalibrationCurveResponse,
            self._build_series_payload(
                evaluation_details,
                points_key="calibration_curve",
            ),
            artifact_key="metrics",
        )

    def get_confusion_matrix(self) -> ConfusionMatrixResponse:
        evaluation_details = self._require_split_evaluation_details()
        return self._validate_response(
            ConfusionMatrixResponse,
            [
                {
                    "model_name": model_name,
                    "model_type": model_payload["model_type"],
                    "split": model_payload["split"],
                    **self._require_nested_mapping(
                        model_payload,
                        nested_key="confusion_matrix",
                        artifact_key="metrics",
                    ),
                }
                for model_name, model_payload in evaluation_details.items()
            ],
            artifact_key="metrics",
        )

    def _require_mapping_payload(
        self,
        *,
        artifact_key: str,
        payload: dict[str, Any] | None,
    ) -> dict[str, Any]:
        if payload is None:
            raise AnalyticsArtifactMissingError(
                artifact_key=artifact_key,
                artifact_path=self._resolved_path(artifact_key),
            )
        if not isinstance(payload, dict):
            raise AnalyticsPayloadError(
                artifact_key=artifact_key,
                reason="artifact payload must be a JSON object.",
            )
        return payload

    def _require_split_evaluation_details(
        self,
        *,
        split: str = "test_months_11_12",
    ) -> dict[str, dict[str, Any]]:
        metrics_payload = self._require_mapping_payload(
            artifact_key="metrics",
            payload=self.artifacts.metrics_payload,
        )
        evaluation_details = metrics_payload.get("evaluation_details")
        if not isinstance(evaluation_details, dict):
            raise AnalyticsPayloadError(
                artifact_key="metrics",
                reason="metrics payload must contain an 'evaluation_details' JSON object.",
            )

        split_payload = evaluation_details.get(split)
        if not isinstance(split_payload, dict):
            raise AnalyticsPayloadError(
                artifact_key="metrics",
                reason=(
                    "metrics payload must contain a split-level evaluation_details "
                    f"object for '{split}'."
                ),
            )

        normalized_payload: dict[str, dict[str, Any]] = {}
        for model_name, model_payload in split_payload.items():
            if not isinstance(model_name, str) or not isinstance(model_payload, dict):
                raise AnalyticsPayloadError(
                    artifact_key="metrics",
                    reason=(
                        "split-level evaluation_details entries must be model-name keys "
                        "mapped to JSON objects."
                    ),
                )
            normalized_payload[model_name] = model_payload

        if not normalized_payload:
            raise AnalyticsPayloadError(
                artifact_key="metrics",
                reason=f"evaluation_details for '{split}' cannot be empty.",
            )

        return normalized_payload

    def _build_series_payload(
        self,
        evaluation_details: dict[str, dict[str, Any]],
        *,
        points_key: str,
    ) -> list[dict[str, Any]]:
        return [
            {
                "model_name": model_name,
                "model_type": model_payload["model_type"],
                "split": model_payload["split"],
                "points": self._require_nested_sequence(
                    model_payload,
                    nested_key=points_key,
                    artifact_key="metrics",
                ),
            }
            for model_name, model_payload in evaluation_details.items()
        ]

    def _require_nested_mapping(
        self,
        payload: dict[str, Any],
        *,
        nested_key: str,
        artifact_key: str,
    ) -> dict[str, Any]:
        nested_payload = payload.get(nested_key)
        if not isinstance(nested_payload, dict):
            raise AnalyticsPayloadError(
                artifact_key=artifact_key,
                reason=f"'{nested_key}' must be a JSON object in evaluation_details.",
            )
        return nested_payload

    def _require_nested_sequence(
        self,
        payload: dict[str, Any],
        *,
        nested_key: str,
        artifact_key: str,
    ) -> list[Any]:
        nested_payload = payload.get(nested_key)
        if not isinstance(nested_payload, list):
            raise AnalyticsPayloadError(
                artifact_key=artifact_key,
                reason=f"'{nested_key}' must be a JSON list in evaluation_details.",
            )
        return nested_payload

    def _validate_response(
        self,
        schema: Any,
        payload: Any,
        *,
        artifact_key: str,
    ) -> Any:
        try:
            return schema.model_validate(payload)
        except ValidationError as exc:
            raise AnalyticsPayloadError(
                artifact_key=artifact_key,
                reason=str(exc),
            ) from exc

    def _resolved_path(self, artifact_key: str) -> Path | None:
        return self.artifacts.report.resolved_paths.get(artifact_key)


__all__ = [
    "AnalyticsArtifactMissingError",
    "AnalyticsPayloadError",
    "AnalyticsService",
    "AnalyticsServiceError",
]
