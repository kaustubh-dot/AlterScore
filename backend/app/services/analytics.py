"""Report-backed analytics service for AlterScore backend routes."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from backend.app.core.artifact_loader import LoadedArtifactBundle
from backend.app.schemas.analytics import (
    BaselineComparisonResponse,
    ModelStatsResponse,
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
        return ModelStatsResponse.model_validate(model_stats)

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
        return BaselineComparisonResponse.model_validate(baseline_metrics)

    def get_score_distribution(self) -> ScoreDistributionResponse:
        percentile_payload = self._require_mapping_payload(
            artifact_key="population_percentiles",
            payload=self.artifacts.population_percentiles,
        )

        try:
            return ScoreDistributionResponse.model_validate(
                {
                    "model_name": percentile_payload["model_name"],
                    "row_count": percentile_payload["row_count"],
                    "summary": percentile_payload["summary"],
                    "score_histogram": percentile_payload["score_histogram"],
                }
            )
        except KeyError as exc:
            raise AnalyticsPayloadError(
                artifact_key="population_percentiles",
                reason=(
                    "population percentiles payload must contain "
                    "'model_name', 'row_count', 'summary', and 'score_histogram'."
                ),
            ) from exc

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

    def _resolved_path(self, artifact_key: str) -> Path | None:
        return self.artifacts.report.resolved_paths.get(artifact_key)


__all__ = [
    "AnalyticsArtifactMissingError",
    "AnalyticsPayloadError",
    "AnalyticsService",
    "AnalyticsServiceError",
]
