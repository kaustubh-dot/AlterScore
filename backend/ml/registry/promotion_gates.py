"""Promotion-gate evaluation for manifest-backed scoring bundles."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Final, Iterable, Literal, Mapping

from backend.app.core.paths import PRODUCTION_MANIFEST_PATH, REPO_ROOT
from backend.ml.registry.production_manifest import load_production_manifest

GateStatus = Literal["pass", "warn", "fail", "skip"]
GateSummaryStatus = Literal["passed", "warning", "failed", "not_evaluated"]

TEST_SPLIT_NAME: Final[str] = "test_months_11_12"
MIN_TEST_AUC_ROC: Final[float] = 0.75
MAX_EXPECTED_CALIBRATION_ERROR: Final[float] = 0.08
MAX_INDIVIDUAL_FAIRNESS_FLAGGED_SHARE: Final[float] = 0.05
MAX_INDIVIDUAL_FAIRNESS_SCORE_GAP: Final[int] = 100
MAX_SUBGROUP_AUC_GAP: Final[float] = 0.075
MAX_POST_GOVERNANCE_AUC_DROP: Final[float] = 0.01
MAX_POST_GOVERNANCE_APPROVAL_RATE_DROP: Final[float] = 0.05
MAX_DRIFT_PSI_ALERT: Final[float] = 0.30
PROMOTED_STATUS: Final[str] = "promoted"
PROMOTION_GATE_POLICY_RELATIVE_PATH: Final[Path] = Path(
    "models/registry/promotion_gate_policy.json"
)
PROMOTION_GATE_POLICY_PATH: Final[Path] = REPO_ROOT / PROMOTION_GATE_POLICY_RELATIVE_PATH
PROMOTION_COMPATIBLE_GATE_STATUSES: Final[frozenset[GateSummaryStatus]] = frozenset(
    {"passed", "warning"}
)


@dataclass(frozen=True)
class PromotionGateCheck:
    name: str
    status: GateStatus
    message: str
    metric_value: float | None = None
    threshold: float | None = None
    blocking: bool = True

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status,
            "message": self.message,
            "metric_value": self.metric_value,
            "threshold": self.threshold,
            "blocking": self.blocking,
        }


@dataclass(frozen=True)
class PromotionGatePolicy:
    policy_schema_version: str
    policy_version: str
    min_test_auc_roc: float
    max_expected_calibration_error: float
    max_individual_fairness_flagged_share: float
    max_individual_fairness_score_gap: float
    max_subgroup_auc_gap: float
    max_post_governance_auc_drop: float
    max_post_governance_approval_rate_drop: float
    max_drift_psi_alert: float

    def as_dict(self) -> dict[str, Any]:
        return {
            "policy_schema_version": self.policy_schema_version,
            "policy_version": self.policy_version,
            "thresholds": {
                "min_test_auc_roc": self.min_test_auc_roc,
                "max_expected_calibration_error": self.max_expected_calibration_error,
                "max_individual_fairness_flagged_share": (
                    self.max_individual_fairness_flagged_share
                ),
                "max_individual_fairness_score_gap": (
                    self.max_individual_fairness_score_gap
                ),
                "max_subgroup_auc_gap": self.max_subgroup_auc_gap,
                "max_post_governance_auc_drop": self.max_post_governance_auc_drop,
                "max_post_governance_approval_rate_drop": (
                    self.max_post_governance_approval_rate_drop
                ),
                "max_drift_psi_alert": self.max_drift_psi_alert,
            },
        }


DEFAULT_PROMOTION_GATE_POLICY: Final[PromotionGatePolicy] = PromotionGatePolicy(
    policy_schema_version="1.0.0",
    policy_version="code_defaults",
    min_test_auc_roc=MIN_TEST_AUC_ROC,
    max_expected_calibration_error=MAX_EXPECTED_CALIBRATION_ERROR,
    max_individual_fairness_flagged_share=MAX_INDIVIDUAL_FAIRNESS_FLAGGED_SHARE,
    max_individual_fairness_score_gap=float(MAX_INDIVIDUAL_FAIRNESS_SCORE_GAP),
    max_subgroup_auc_gap=MAX_SUBGROUP_AUC_GAP,
    max_post_governance_auc_drop=MAX_POST_GOVERNANCE_AUC_DROP,
    max_post_governance_approval_rate_drop=MAX_POST_GOVERNANCE_APPROVAL_RATE_DROP,
    max_drift_psi_alert=MAX_DRIFT_PSI_ALERT,
)


def evaluate_promotion_gates(
    *,
    manifest: Mapping[str, Any] | None,
    metrics_payload: Mapping[str, Any] | None,
    fairness_report: Mapping[str, Any] | None,
    psi_report: Mapping[str, Any] | None,
    policy: PromotionGatePolicy | Mapping[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Evaluate whether a runtime bundle deserves promoted status."""

    if not isinstance(manifest, Mapping):
        return None

    resolved_policy = _resolve_policy(policy)
    runtime_model_name = _as_string(manifest.get("runtime_model_name"))
    promotion_status = _as_string(manifest.get("promotion_status"))
    checks = [
        *_evaluate_metrics_gates(
            runtime_model_name=runtime_model_name,
            metrics_payload=metrics_payload,
            policy=resolved_policy,
        ),
        *_evaluate_fairness_gates(
            fairness_report=fairness_report,
            policy=resolved_policy,
        ),
        *_evaluate_drift_gates(
            psi_report=psi_report,
            policy=resolved_policy,
        ),
    ]

    if not checks:
        return {
            "status": "not_evaluated",
            "promotion_status": promotion_status,
            "policy_version": resolved_policy.policy_version,
            "blocking_failures": [],
            "warnings": [],
            "checks": [],
        }

    blocking_failures = [
        check.name for check in checks if check.blocking and check.status == "fail"
    ]
    warnings = [check.name for check in checks if check.status == "warn"]
    if blocking_failures:
        summary_status: GateSummaryStatus = "failed"
    elif warnings:
        summary_status = "warning"
    else:
        summary_status = "passed"

    return {
        "status": summary_status,
        "promotion_status": promotion_status,
        "policy_version": resolved_policy.policy_version,
        "blocking_failures": blocking_failures,
        "warnings": warnings,
        "checks": [check.as_dict() for check in checks],
    }


def build_promotion_gate_summary_from_manifest(
    manifest_path: str | Path = PRODUCTION_MANIFEST_PATH,
    *,
    repo_root: str | Path = REPO_ROOT,
    policy_path: str | Path | None = PROMOTION_GATE_POLICY_RELATIVE_PATH,
) -> dict[str, Any]:
    """Load manifest-declared reports and evaluate promotion gates."""

    resolved_repo_root = Path(repo_root).resolve()
    resolved_manifest_path = _resolve_manifest_path(
        manifest_path,
        repo_root=resolved_repo_root,
    )
    policy = (
        DEFAULT_PROMOTION_GATE_POLICY
        if policy_path is None
        else load_promotion_gate_policy(policy_path, repo_root=resolved_repo_root)
    )
    production_manifest = load_production_manifest(resolved_manifest_path)
    summary = evaluate_promotion_gates(
        manifest=production_manifest.raw_payload,
        metrics_payload=_load_manifest_report(
            production_manifest.raw_payload,
            "metrics",
            repo_root=resolved_repo_root,
        ),
        fairness_report=_load_manifest_report(
            production_manifest.raw_payload,
            "fairness_report",
            repo_root=resolved_repo_root,
        ),
        psi_report=_load_manifest_report(
            production_manifest.raw_payload,
            "psi_report",
            repo_root=resolved_repo_root,
        ),
        policy=policy,
    )
    if summary is None:
        return {
            "status": "not_evaluated",
            "promotion_status": None,
            "policy_version": policy.policy_version,
            "blocking_failures": ["manifest_unavailable"],
            "warnings": [],
            "checks": [],
        }

    return {
        **summary,
        "manifest_path": str(resolved_manifest_path),
        "runtime_model_name": production_manifest.runtime_model_name,
        "manifest_version": production_manifest.manifest_version,
        "model_version": production_manifest.model_version,
    }


def load_promotion_gate_policy(
    policy_path: str | Path = PROMOTION_GATE_POLICY_RELATIVE_PATH,
    *,
    repo_root: str | Path = REPO_ROOT,
) -> PromotionGatePolicy:
    """Load a versioned promotion-gate threshold policy."""

    resolved_repo_root = Path(repo_root).resolve()
    resolved_policy_path = _resolve_manifest_path(
        policy_path,
        repo_root=resolved_repo_root,
    )
    payload = json.loads(resolved_policy_path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError("promotion gate policy payload must be a JSON object.")
    return _parse_policy(payload)


def promotion_gate_exit_code(
    summary: Mapping[str, Any],
    *,
    fail_on_promoted_incompatibility: bool = True,
    require_clean_pass: bool = False,
) -> int:
    """Return the process exit code for a gate summary."""

    gate_status = _as_string(summary.get("status"))
    promotion_status = _as_string(summary.get("promotion_status"))
    normalized_promotion_status = (
        None if promotion_status is None else promotion_status.lower()
    )

    if require_clean_pass and gate_status != "passed":
        return 1

    if (
        fail_on_promoted_incompatibility
        and normalized_promotion_status == PROMOTED_STATUS
        and gate_status not in PROMOTION_COMPATIBLE_GATE_STATUSES
    ):
        return 1

    return 0


def _evaluate_metrics_gates(
    *,
    runtime_model_name: str | None,
    metrics_payload: Mapping[str, Any] | None,
    policy: PromotionGatePolicy,
) -> list[PromotionGateCheck]:
    if not runtime_model_name or not isinstance(metrics_payload, Mapping):
        return [
            PromotionGateCheck(
                name="metrics_available",
                status="fail",
                message="Runtime model metrics are missing.",
            )
        ]

    test_stats = _find_model_test_stats(
        metrics_payload,
        runtime_model_name=runtime_model_name,
    )
    if test_stats is None:
        return [
            PromotionGateCheck(
                name="metrics_available",
                status="fail",
                message=f"No test metrics found for runtime model {runtime_model_name}.",
            )
        ]

    auc = _as_float(test_stats.get("auc_roc"))
    ece = _as_float(test_stats.get("expected_calibration_error"))
    return [
        _threshold_check(
            name="test_auc_roc",
            metric_value=auc,
            threshold=policy.min_test_auc_roc,
            passing=auc is not None and auc >= policy.min_test_auc_roc,
            message=(
                f"Test AUC-ROC must be at least {policy.min_test_auc_roc:.3f} "
                f"for {runtime_model_name}."
            ),
        ),
        _threshold_check(
            name="expected_calibration_error",
            metric_value=ece,
            threshold=policy.max_expected_calibration_error,
            passing=ece is not None
            and ece <= policy.max_expected_calibration_error,
            message=(
                "Expected calibration error must stay below "
                f"{policy.max_expected_calibration_error:.3f}."
            ),
        ),
    ]


def _evaluate_fairness_gates(
    *,
    fairness_report: Mapping[str, Any] | None,
    policy: PromotionGatePolicy,
) -> list[PromotionGateCheck]:
    if not isinstance(fairness_report, Mapping):
        return [
            PromotionGateCheck(
                name="fairness_report_available",
                status="fail",
                message="Fairness report is missing.",
            )
        ]

    worst_auc_gap = _as_float(fairness_report.get("worst_auc_gap"))
    calibration_parity = fairness_report.get("calibration_parity")
    individual_fairness = fairness_report.get("individual_fairness_proxy")
    post_governance = fairness_report.get("post_governance_impact")

    overall_ece = (
        _as_float(calibration_parity.get("overall_expected_calibration_error"))
        if isinstance(calibration_parity, Mapping)
        else None
    )
    flagged_pair_share = (
        _as_float(individual_fairness.get("flagged_pair_share"))
        if isinstance(individual_fairness, Mapping)
        else None
    )
    max_score_gap = (
        _as_float(individual_fairness.get("max_score_gap"))
        if isinstance(individual_fairness, Mapping)
        else None
    )

    overall_auc = _as_float(fairness_report.get("overall_auc"))
    post_auc = (
        _as_float(post_governance.get("overall_auc_after_governance"))
        if isinstance(post_governance, Mapping)
        else None
    )
    approval_delta = (
        _as_float(post_governance.get("overall_approval_rate_delta"))
        if isinstance(post_governance, Mapping)
        else None
    )
    auc_drop = (
        max(0.0, overall_auc - post_auc)
        if overall_auc is not None and post_auc is not None
        else None
    )

    return [
        _threshold_check(
            name="subgroup_auc_gap",
            metric_value=worst_auc_gap,
            threshold=policy.max_subgroup_auc_gap,
            passing=worst_auc_gap is not None
            and worst_auc_gap <= policy.max_subgroup_auc_gap,
            message=(
                f"Worst subgroup AUC gap must be <= "
                f"{policy.max_subgroup_auc_gap:.3f}."
            ),
        ),
        _threshold_check(
            name="calibration_parity_ece",
            metric_value=overall_ece,
            threshold=policy.max_expected_calibration_error,
            passing=overall_ece is not None
            and overall_ece <= policy.max_expected_calibration_error,
            message=(
                "Fairness calibration parity ECE must stay below "
                f"{policy.max_expected_calibration_error:.3f}."
            ),
        ),
        _threshold_check(
            name="individual_fairness_flagged_share",
            metric_value=flagged_pair_share,
            threshold=policy.max_individual_fairness_flagged_share,
            passing=flagged_pair_share is not None
            and flagged_pair_share <= policy.max_individual_fairness_flagged_share,
            message=(
                "Similar-pair score-gap flagged share must stay below "
                f"{policy.max_individual_fairness_flagged_share:.3f}."
            ),
        ),
        _threshold_check(
            name="individual_fairness_max_score_gap",
            metric_value=max_score_gap,
            threshold=policy.max_individual_fairness_score_gap,
            passing=max_score_gap is not None
            and max_score_gap <= policy.max_individual_fairness_score_gap,
            message=(
                "Maximum similar-pair score gap must stay below "
                f"{policy.max_individual_fairness_score_gap:.0f} points."
            ),
        ),
        _threshold_check(
            name="post_governance_auc_drop",
            metric_value=auc_drop,
            threshold=policy.max_post_governance_auc_drop,
            passing=auc_drop is not None
            and auc_drop <= policy.max_post_governance_auc_drop,
            message=(
                "Post-governance AUC drop must stay below "
                f"{policy.max_post_governance_auc_drop:.3f}."
            ),
        ),
        _threshold_check(
            name="post_governance_approval_rate_delta",
            metric_value=abs(approval_delta) if approval_delta is not None else None,
            threshold=policy.max_post_governance_approval_rate_drop,
            passing=approval_delta is not None
            and abs(approval_delta)
            <= policy.max_post_governance_approval_rate_drop,
            message=(
                "Absolute post-governance approval-rate shift must stay below "
                f"{policy.max_post_governance_approval_rate_drop:.3f}."
            ),
            blocking=False,
        ),
    ]


def _evaluate_drift_gates(
    *,
    psi_report: Mapping[str, Any] | None,
    policy: PromotionGatePolicy,
) -> list[PromotionGateCheck]:
    if not isinstance(psi_report, Mapping):
        return [
            PromotionGateCheck(
                name="psi_report_available",
                status="fail",
                message="PSI drift report is missing.",
            )
        ]

    max_psi = _as_float(psi_report.get("max_psi"))
    verdict = _as_string(psi_report.get("verdict"))
    if max_psi is None:
        return [
            PromotionGateCheck(
                name="drift_max_psi",
                status="fail",
                message="PSI report does not contain max_psi.",
            )
        ]

    if max_psi >= policy.max_drift_psi_alert:
        status: GateStatus = "fail"
    elif verdict == "watch":
        status = "warn"
    else:
        status = "pass"

    return [
        PromotionGateCheck(
            name="drift_max_psi",
            status=status,
            metric_value=max_psi,
            threshold=policy.max_drift_psi_alert,
            blocking=status == "fail",
            message=f"Maximum PSI must stay below {policy.max_drift_psi_alert:.2f}.",
        )
    ]


def _find_model_test_stats(
    metrics_payload: Mapping[str, Any],
    *,
    runtime_model_name: str,
) -> Mapping[str, Any] | None:
    model_stats = metrics_payload.get("model_stats")
    if not isinstance(model_stats, list):
        return None

    for item in model_stats:
        if not isinstance(item, Mapping):
            continue
        if item.get("model_name") != runtime_model_name:
            continue
        if item.get("split") == TEST_SPLIT_NAME:
            return item
    return None


def _threshold_check(
    *,
    name: str,
    metric_value: float | None,
    threshold: float,
    passing: bool,
    message: str,
    blocking: bool = True,
) -> PromotionGateCheck:
    if metric_value is None:
        return PromotionGateCheck(
            name=name,
            status="fail" if blocking else "warn",
            message=f"{message} Metric is missing.",
            threshold=threshold,
            blocking=blocking,
        )

    return PromotionGateCheck(
        name=name,
        status="pass" if passing else ("fail" if blocking else "warn"),
        metric_value=float(metric_value),
        threshold=float(threshold),
        message=message,
        blocking=blocking,
    )


def _as_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _as_string(value: Any) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip()
    return normalized or None


def _resolve_policy(
    policy: PromotionGatePolicy | Mapping[str, Any] | None,
) -> PromotionGatePolicy:
    if policy is None:
        return DEFAULT_PROMOTION_GATE_POLICY
    if isinstance(policy, PromotionGatePolicy):
        return policy
    return _parse_policy(policy)


def _parse_policy(payload: Mapping[str, Any]) -> PromotionGatePolicy:
    thresholds = payload.get("thresholds")
    if not isinstance(thresholds, Mapping):
        raise ValueError("promotion gate policy must contain a thresholds object.")

    return PromotionGatePolicy(
        policy_schema_version=_required_policy_string(
            payload,
            "policy_schema_version",
        ),
        policy_version=_required_policy_string(payload, "policy_version"),
        min_test_auc_roc=_required_threshold(thresholds, "min_test_auc_roc"),
        max_expected_calibration_error=_required_threshold(
            thresholds,
            "max_expected_calibration_error",
        ),
        max_individual_fairness_flagged_share=_required_threshold(
            thresholds,
            "max_individual_fairness_flagged_share",
        ),
        max_individual_fairness_score_gap=_required_threshold(
            thresholds,
            "max_individual_fairness_score_gap",
        ),
        max_subgroup_auc_gap=_required_threshold(thresholds, "max_subgroup_auc_gap"),
        max_post_governance_auc_drop=_required_threshold(
            thresholds,
            "max_post_governance_auc_drop",
        ),
        max_post_governance_approval_rate_drop=_required_threshold(
            thresholds,
            "max_post_governance_approval_rate_drop",
        ),
        max_drift_psi_alert=_required_threshold(thresholds, "max_drift_psi_alert"),
    )


def _required_policy_string(payload: Mapping[str, Any], field_name: str) -> str:
    value = payload.get(field_name)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"promotion gate policy missing string field {field_name}.")
    return value.strip()


def _required_threshold(payload: Mapping[str, Any], field_name: str) -> float:
    value = _as_float(payload.get(field_name))
    if value is None:
        raise ValueError(f"promotion gate policy missing numeric threshold {field_name}.")
    return value


def _resolve_manifest_path(
    manifest_path: str | Path,
    *,
    repo_root: Path,
) -> Path:
    path = Path(manifest_path)
    if path.is_absolute():
        return path.resolve()
    return (repo_root / path).resolve()


def _load_manifest_report(
    manifest_payload: Mapping[str, Any],
    artifact_key: str,
    *,
    repo_root: Path,
) -> Mapping[str, Any] | None:
    artifacts = manifest_payload.get("artifacts")
    if not isinstance(artifacts, Mapping):
        return None

    artifact = artifacts.get(artifact_key)
    if not isinstance(artifact, Mapping):
        return None

    artifact_path = artifact.get("path")
    if not isinstance(artifact_path, str) or not artifact_path.strip():
        return None

    report_path = (repo_root / artifact_path).resolve()
    if not report_path.is_file():
        return None

    payload = json.loads(report_path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, Mapping) else None


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Evaluate AlterScore model promotion gates from a serving manifest.",
    )
    parser.add_argument(
        "--manifest",
        default=str(PRODUCTION_MANIFEST_PATH),
        help="Path to production_manifest.json. Defaults to the checked-in manifest.",
    )
    parser.add_argument(
        "--repo-root",
        default=str(REPO_ROOT),
        help="Repository root used to resolve manifest artifact paths.",
    )
    parser.add_argument(
        "--policy",
        default=str(PROMOTION_GATE_POLICY_RELATIVE_PATH),
        help="Path to the promotion gate policy JSON.",
    )
    parser.add_argument(
        "--require-clean-pass",
        action="store_true",
        help="Exit non-zero unless all gates pass without warnings or failures.",
    )
    parser.add_argument(
        "--allow-promoted-incompatibility",
        action="store_true",
        help=(
            "Do not fail when a manifest marked promoted has failing or "
            "unevaluated gates. Intended only for local inspection."
        ),
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress JSON output and return only the process exit code.",
    )
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    parser = _build_arg_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    summary = build_promotion_gate_summary_from_manifest(
        args.manifest,
        repo_root=args.repo_root,
        policy_path=args.policy,
    )
    if not args.quiet:
        print(json.dumps(summary, indent=2, sort_keys=True))

    return promotion_gate_exit_code(
        summary,
        fail_on_promoted_incompatibility=not args.allow_promoted_incompatibility,
        require_clean_pass=args.require_clean_pass,
    )


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "MAX_EXPECTED_CALIBRATION_ERROR",
    "MAX_INDIVIDUAL_FAIRNESS_FLAGGED_SHARE",
    "MAX_INDIVIDUAL_FAIRNESS_SCORE_GAP",
    "MAX_POST_GOVERNANCE_APPROVAL_RATE_DROP",
    "MAX_POST_GOVERNANCE_AUC_DROP",
    "MAX_SUBGROUP_AUC_GAP",
    "MIN_TEST_AUC_ROC",
    "PromotionGateCheck",
    "PROMOTION_GATE_POLICY_PATH",
    "PROMOTION_GATE_POLICY_RELATIVE_PATH",
    "build_promotion_gate_summary_from_manifest",
    "evaluate_promotion_gates",
    "main",
    "promotion_gate_exit_code",
]
