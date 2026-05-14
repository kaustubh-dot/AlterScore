"""Analytics and health response schemas for AlterScore."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import Field, RootModel

from backend.app.schemas.common import SchemaModel

HealthStatus = Literal["ok", "degraded", "error"]
DriftStatus = Literal["stable", "watch", "alert"]
FairnessFlag = Literal["green", "yellow", "red"]


class HealthResponse(SchemaModel):
    status: HealthStatus
    version: str = Field(..., min_length=1)
    model_loaded: bool
    artifacts_loaded: list[str]
    missing_artifacts: list[str]
    invalid_artifacts: list[str]
    timestamp: datetime


class ModelStatsItem(SchemaModel):
    model_name: str = Field(..., min_length=1)
    model_type: str = Field(..., min_length=1)
    auc_roc: float = Field(..., ge=0, le=1)
    auc_pr: float = Field(..., ge=0, le=1)
    ks_statistic: float = Field(..., ge=0, le=1)
    brier_score: float = Field(..., ge=0, le=1)
    expected_calibration_error: float = Field(..., ge=0, le=1)
    accuracy: float = Field(..., ge=0, le=1)
    precision: float = Field(..., ge=0, le=1)
    recall: float = Field(..., ge=0, le=1)
    f1: float = Field(..., ge=0, le=1)
    threshold: float = Field(..., ge=0, le=1)
    split: str = Field(..., min_length=1)


class ModelStatsResponse(RootModel[list[ModelStatsItem]]):
    pass


class BaselineComparisonItem(SchemaModel):
    model_name: str = Field(..., min_length=1)
    model_type: str = Field(..., min_length=1)
    auc_roc: float = Field(..., ge=0, le=1)
    ks_statistic: float = Field(..., ge=0, le=1)
    brier_score: float = Field(..., ge=0, le=1)
    expected_calibration_error: float = Field(..., ge=0, le=1)
    lift_vs_loan_officer: float


class BaselineComparisonResponse(RootModel[list[BaselineComparisonItem]]):
    pass


class ScoreDistributionBucket(SchemaModel):
    label: str = Field(..., min_length=1)
    score_min: int = Field(..., ge=300, le=850)
    score_max: int = Field(..., ge=300, le=850)
    count: int = Field(..., ge=0)
    share: float = Field(..., ge=0, le=1)


class ScoreDistributionSummary(SchemaModel):
    min_score: int = Field(..., ge=300, le=850)
    max_score: int = Field(..., ge=300, le=850)
    mean_score: float = Field(..., ge=300, le=850)
    median_score: float = Field(..., ge=300, le=850)


class ScoreDistributionResponse(SchemaModel):
    model_name: str = Field(..., min_length=1)
    row_count: int = Field(..., ge=1)
    summary: ScoreDistributionSummary
    score_histogram: list[ScoreDistributionBucket]


class RocPoint(SchemaModel):
    fpr: float = Field(..., ge=0, le=1)
    tpr: float = Field(..., ge=0, le=1)


class RocCurveSeries(SchemaModel):
    model_name: str = Field(..., min_length=1)
    model_type: str = Field(..., min_length=1)
    split: str = Field(..., min_length=1)
    points: list[RocPoint]


class RocCurveResponse(RootModel[list[RocCurveSeries]]):
    pass


class PrecisionRecallPoint(SchemaModel):
    recall: float = Field(..., ge=0, le=1)
    precision: float = Field(..., ge=0, le=1)


class PrecisionRecallSeries(SchemaModel):
    model_name: str = Field(..., min_length=1)
    model_type: str = Field(..., min_length=1)
    split: str = Field(..., min_length=1)
    points: list[PrecisionRecallPoint]


class PrecisionRecallResponse(RootModel[list[PrecisionRecallSeries]]):
    pass


class CalibrationPoint(SchemaModel):
    mean_predicted: float = Field(..., ge=0, le=1)
    fraction_positive: float = Field(..., ge=0, le=1)
    count: int = Field(..., ge=0)


class CalibrationCurveSeries(SchemaModel):
    model_name: str = Field(..., min_length=1)
    model_type: str = Field(..., min_length=1)
    split: str = Field(..., min_length=1)
    points: list[CalibrationPoint]


class CalibrationCurveResponse(RootModel[list[CalibrationCurveSeries]]):
    pass


class ConfusionMatrixItem(SchemaModel):
    model_name: str = Field(..., min_length=1)
    model_type: str = Field(..., min_length=1)
    split: str = Field(..., min_length=1)
    threshold: float = Field(..., ge=0, le=1)
    tp: int = Field(..., ge=0)
    fp: int = Field(..., ge=0)
    fn: int = Field(..., ge=0)
    tn: int = Field(..., ge=0)
    tpr: float = Field(..., ge=0, le=1)
    fpr: float = Field(..., ge=0, le=1)
    fnr: float = Field(..., ge=0, le=1)


class ConfusionMatrixResponse(RootModel[list[ConfusionMatrixItem]]):
    pass


class GlobalImportanceItem(SchemaModel):
    feature: str = Field(..., min_length=1)
    display_name: str = Field(..., min_length=1)
    mean_abs_shap: float = Field(..., ge=0)
    category: str = Field(..., min_length=1)
    rank: int = Field(..., ge=1)


class GlobalImportanceResponse(SchemaModel):
    model_name: str = Field(..., min_length=1)
    model_type: str = Field(..., min_length=1)
    items: list[GlobalImportanceItem]


class DriftThresholds(SchemaModel):
    stable_below: float = Field(..., ge=0)
    watch_below: float = Field(..., ge=0)
    alert_at_or_above: float = Field(..., ge=0)


class DriftFeatureItem(SchemaModel):
    feature: str = Field(..., min_length=1)
    psi: float = Field(..., ge=0)
    status: DriftStatus


class DriftReport(SchemaModel):
    max_psi: float = Field(..., ge=0)
    verdict: str = Field(..., min_length=1)
    thresholds: DriftThresholds
    top_drifted_features: list[DriftFeatureItem]
    all_features: list[DriftFeatureItem]


class FairnessGroupMetrics(SchemaModel):
    n_samples: int = Field(..., ge=0)
    auc: float = Field(..., ge=0, le=1)
    auc_gap_from_overall: float = Field(..., ge=0, le=1)
    approval_rate: float = Field(..., ge=0, le=1)
    fpr: float = Field(..., ge=0, le=1)
    fnr: float = Field(..., ge=0, le=1)
    mean_score: float = Field(..., ge=300, le=850)
    flag: FairnessFlag


class FairnessReport(SchemaModel):
    overall_auc: float = Field(..., ge=0, le=1)
    overall_approval_rate: float = Field(..., ge=0, le=1)
    overall_default_rate: float = Field(..., ge=0, le=1)
    worst_auc_gap: float = Field(..., ge=0, le=1)
    flagged_groups: list[str]
    verdict: str = Field(..., min_length=1)
    groups: dict[str, dict[str, FairnessGroupMetrics]]


__all__ = [
    "BaselineComparisonItem",
    "BaselineComparisonResponse",
    "CalibrationCurveResponse",
    "CalibrationCurveSeries",
    "CalibrationPoint",
    "ConfusionMatrixItem",
    "ConfusionMatrixResponse",
    "DriftFeatureItem",
    "DriftReport",
    "DriftThresholds",
    "FairnessGroupMetrics",
    "FairnessReport",
    "GlobalImportanceItem",
    "GlobalImportanceResponse",
    "HealthResponse",
    "ModelStatsItem",
    "ModelStatsResponse",
    "PrecisionRecallPoint",
    "PrecisionRecallResponse",
    "PrecisionRecallSeries",
    "RocCurveResponse",
    "RocCurveSeries",
    "RocPoint",
    "ScoreDistributionBucket",
    "ScoreDistributionResponse",
    "ScoreDistributionSummary",
]
