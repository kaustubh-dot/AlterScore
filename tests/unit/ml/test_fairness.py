import pandas as pd

from backend.ml.evaluation.fairness import build_fairness_report
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
    assert all(not report["groups"][feature_name] for feature_name in PROTECTED_FEATURES)
