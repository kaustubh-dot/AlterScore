from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.ml.preprocessing.pipeline import (
    DEFAULT_PREPROCESSOR_ARTIFACT_PATH,
    DEFAULT_TEXT_PCA_ARTIFACT_PATH,
)
from backend.ml.training.classical.baselines import (
    DEFAULT_BASELINE_METRICS_PATH,
    DEFAULT_DICE_EXPLAINER_PATH,
    DEFAULT_FAIRNESS_REPORT_PATH,
    DEFAULT_GLOBAL_IMPORTANCE_PATH,
    DEFAULT_METRICS_PATH,
    DEFAULT_LOGISTIC_ARTIFACT_PATH,
    DEFAULT_POPULATION_PERCENTILES_PATH,
    DEFAULT_PSI_REPORT_PATH,
)
from backend.ml.training.classical.train_classical import (
    DEFAULT_DATASET_PATH,
    DEFAULT_LGBM_ARTIFACT_PATH,
    DEFAULT_RF_ARTIFACT_PATH,
    DEFAULT_XGB_ARTIFACT_PATH,
    train_classical_models,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Train the AlterScore bounded classical model suite on temporal splits.",
    )
    parser.add_argument("--dataset-path", type=Path, default=DEFAULT_DATASET_PATH)
    parser.add_argument("--expected-row-count", type=int, default=None)
    parser.add_argument("--minimum-test-rows", type=int, default=1_000)
    parser.add_argument(
        "--preprocessor-path",
        type=Path,
        default=DEFAULT_PREPROCESSOR_ARTIFACT_PATH,
    )
    parser.add_argument(
        "--text-pca-path",
        type=Path,
        default=DEFAULT_TEXT_PCA_ARTIFACT_PATH,
    )
    parser.add_argument(
        "--random-forest-model-path",
        type=Path,
        default=DEFAULT_RF_ARTIFACT_PATH,
    )
    parser.add_argument(
        "--xgboost-model-path",
        type=Path,
        default=DEFAULT_XGB_ARTIFACT_PATH,
    )
    parser.add_argument(
        "--lightgbm-model-path",
        type=Path,
        default=DEFAULT_LGBM_ARTIFACT_PATH,
    )
    parser.add_argument(
        "--logistic-model-path",
        type=Path,
        default=DEFAULT_LOGISTIC_ARTIFACT_PATH,
    )
    parser.add_argument(
        "--baseline-metrics-path",
        type=Path,
        default=DEFAULT_BASELINE_METRICS_PATH,
    )
    parser.add_argument(
        "--metrics-path",
        type=Path,
        default=DEFAULT_METRICS_PATH,
    )
    parser.add_argument(
        "--population-percentiles-path",
        type=Path,
        default=DEFAULT_POPULATION_PERCENTILES_PATH,
    )
    parser.add_argument(
        "--psi-report-path",
        type=Path,
        default=DEFAULT_PSI_REPORT_PATH,
    )
    parser.add_argument(
        "--fairness-report-path",
        type=Path,
        default=DEFAULT_FAIRNESS_REPORT_PATH,
    )
    parser.add_argument(
        "--global-importance-path",
        type=Path,
        default=DEFAULT_GLOBAL_IMPORTANCE_PATH,
    )
    parser.add_argument(
        "--dice-explainer-path",
        type=Path,
        default=DEFAULT_DICE_EXPLAINER_PATH,
    )
    parser.add_argument("--random-state", type=int, default=42)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    artifacts = train_classical_models(
        dataset_path=args.dataset_path,
        expected_row_count=args.expected_row_count,
        minimum_test_rows=args.minimum_test_rows,
        preprocessor_artifact_path=args.preprocessor_path,
        text_pca_artifact_path=args.text_pca_path,
        random_forest_artifact_path=args.random_forest_model_path,
        xgboost_artifact_path=args.xgboost_model_path,
        lightgbm_artifact_path=args.lightgbm_model_path,
        logistic_artifact_path=args.logistic_model_path,
        baseline_metrics_path=args.baseline_metrics_path,
        metrics_path=args.metrics_path,
        population_percentiles_path=args.population_percentiles_path,
        psi_report_path=args.psi_report_path,
        fairness_report_path=args.fairness_report_path,
        global_importance_path=args.global_importance_path,
        dice_explainer_path=args.dice_explainer_path,
        random_state=args.random_state,
    )
    print(
        json.dumps(
            {
                "run_id": artifacts.run_id,
                "dataset_path": (
                    None
                    if artifacts.dataset_path is None
                    else str(artifacts.dataset_path)
                ),
                "text_pca_path": (
                    None
                    if artifacts.text_pca_path is None
                    else str(artifacts.text_pca_path)
                ),
                "metrics_path": (
                    None
                    if artifacts.metrics_path is None
                    else str(artifacts.metrics_path)
                ),
                "population_percentiles_path": (
                    None
                    if artifacts.population_percentiles_path is None
                    else str(artifacts.population_percentiles_path)
                ),
                "psi_report_path": (
                    None
                    if artifacts.psi_report_path is None
                    else str(artifacts.psi_report_path)
                ),
                "fairness_report_path": (
                    None
                    if artifacts.fairness_report_path is None
                    else str(artifacts.fairness_report_path)
                ),
                "global_importance_path": (
                    None
                    if artifacts.global_importance_path is None
                    else str(artifacts.global_importance_path)
                ),
                "dice_explainer_path": (
                    None
                    if artifacts.dice_explainer_path is None
                    else str(artifacts.dice_explainer_path)
                ),
                "artifacts": {
                    model_name: None if path is None else str(path)
                    for model_name, path in artifacts.model_artifact_paths.items()
                },
                "test_auc_roc": {
                    metric["model_name"]: metric["auc_roc"]
                    for metric in artifacts.model_stats
                    if metric["split"] == "test_months_11_12"
                },
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
