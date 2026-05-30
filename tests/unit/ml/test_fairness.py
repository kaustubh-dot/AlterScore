import pandas as pd

from backend.ml.evaluation.fairness import (
    FULL_PROFILE_SIMILARITY_FEATURES,
    build_calibration_parity_report,
    build_fairness_report,
    build_individual_fairness_proxy,
    build_post_governance_impact_report,
)
from backend.ml.preprocessing.feature_registry import PROTECTED_FEATURES


def test_build_fairness_report_marks_empty_audit_as_inconclusive() -> None:
    protected_frame = pd.DataFrame(
        {feature_name: ["group_a"] * 4 for feature_name in PROTECTED_FEATURES}
    )

    report = build_fairness_report(
        [1, 1, 1, 1],
        [0.8, 0.7, 0.9, 0.85],
        protected_frame,
        min_group_samples=10,
    )

    assert report["flagged_groups"] == []
    assert "inconclusive" in report["verdict"]
    assert all(
        not report["groups"][feature_name] for feature_name in PROTECTED_FEATURES
    )


def test_calibration_parity_computes_group_curves_and_ece_gaps() -> None:
    protected_frame = _protected_frame(
        row_count=8,
        gender=["female", "female", "female", "female", "male", "male", "male", "male"],
    )

    report = build_calibration_parity_report(
        [0, 0, 1, 1, 0, 1, 0, 1],
        [0.1, 0.2, 0.8, 0.9, 0.3, 0.7, 0.4, 0.6],
        protected_frame,
        min_group_samples=2,
        n_bins=2,
    )

    assert report["n_bins"] == 2
    assert report["evaluated_group_count"] >= 2
    assert report["overall_expected_calibration_error"] >= 0.0
    assert report["max_ece_gap"] >= 0.0
    assert set(report["groups"]) == set(PROTECTED_FEATURES)
    assert report["groups"]["gender"]["female"]["n_samples"] == 4
    assert report["groups"]["gender"]["female"]["points"]


def test_individual_fairness_proxy_flags_large_score_gaps_for_similar_pairs() -> None:
    protected_frame = _protected_frame(
        row_count=4,
        gender=["female", "male", "female", "female"],
        region=["urban", "urban", "rural", "urban"],
    )
    feature_frame = _psychometric_feature_frame(
        [
            [0.90] * len(FULL_PROFILE_SIMILARITY_FEATURES),
            [0.88] * len(FULL_PROFILE_SIMILARITY_FEATURES),
            [0.10] * len(FULL_PROFILE_SIMILARITY_FEATURES),
            [0.89] * len(FULL_PROFILE_SIMILARITY_FEATURES),
        ]
    )

    report = build_individual_fairness_proxy(
        [800, 710, 620, 790],
        protected_frame,
        feature_frame=feature_frame,
        similarity_threshold=0.95,
        score_gap_threshold=50,
    )

    assert report["evaluated_applicants"] == 4
    assert report["evaluated_pairs"] > 0
    assert report["flagged_pair_count"] >= 1
    assert report["max_score_gap"] >= 90
    assert report["worst_pairs"]
    assert report["worst_pairs"][0]["score_gap"] >= 90
    assert any(
        "gender" in pair["differing_attributes"] for pair in report["worst_pairs"]
    )
    assert not set(report["similarity_feature_set"]) & set(PROTECTED_FEATURES)


def test_build_fairness_report_includes_governance_detail_sections() -> None:
    protected_frame = _protected_frame(
        row_count=8,
        gender=["female", "female", "female", "female", "male", "male", "male", "male"],
    )
    feature_frame = _psychometric_feature_frame(
        [
            [0.65] * len(FULL_PROFILE_SIMILARITY_FEATURES),
            [0.66] * len(FULL_PROFILE_SIMILARITY_FEATURES),
            [0.67] * len(FULL_PROFILE_SIMILARITY_FEATURES),
            [0.68] * len(FULL_PROFILE_SIMILARITY_FEATURES),
            [0.65] * len(FULL_PROFILE_SIMILARITY_FEATURES),
            [0.66] * len(FULL_PROFILE_SIMILARITY_FEATURES),
            [0.67] * len(FULL_PROFILE_SIMILARITY_FEATURES),
            [0.68] * len(FULL_PROFILE_SIMILARITY_FEATURES),
        ]
    )

    report = build_fairness_report(
        [0, 0, 1, 1, 0, 1, 0, 1],
        [0.1, 0.2, 0.8, 0.9, 0.3, 0.7, 0.4, 0.6],
        protected_frame,
        feature_frame=feature_frame,
        min_group_samples=2,
    )

    assert report["calibration_parity"]["groups"]["gender"]["female"]["points"]
    assert report["individual_fairness_proxy"]["evaluated_pairs"] > 0
    assert report["post_governance_impact"]["available"] is False


def test_post_governance_impact_report_exposes_subgroup_score_deltas() -> None:
    protected_frame = _protected_frame(
        row_count=8,
        gender=["female", "female", "female", "female", "male", "male", "male", "male"],
    )

    report = build_post_governance_impact_report(
        [0, 0, 1, 1, 0, 1, 0, 1],
        [0.1, 0.2, 0.8, 0.9, 0.3, 0.7, 0.4, 0.6],
        [0.1, 0.2, 0.8, 0.9, 0.2, 0.5, 0.3, 0.4],
        protected_frame,
        min_group_samples=2,
    )

    assert report["available"] is True
    assert report["overall_approval_rate_after_governance"] < (
        report["overall_approval_rate_before_governance"]
    )
    assert report["groups"]["gender"]["male"]["mean_score_delta"] < 0


def _protected_frame(
    *,
    row_count: int,
    gender: list[str] | None = None,
    age_group: list[str] | None = None,
    region: list[str] | None = None,
    education_level: list[str] | None = None,
) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "gender": gender or ["female"] * row_count,
            "age_group": age_group or ["26-35"] * row_count,
            "region": region or ["urban"] * row_count,
            "education_level": education_level or ["secondary"] * row_count,
        }
    )


def _psychometric_feature_frame(rows: list[list[float]]) -> pd.DataFrame:
    return pd.DataFrame(rows, columns=FULL_PROFILE_SIMILARITY_FEATURES)
