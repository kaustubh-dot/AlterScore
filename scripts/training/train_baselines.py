from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.ml.training.classical.baselines import (
    DEFAULT_BASELINE_METRICS_PATH,
    DEFAULT_DATASET_PATH,
    DEFAULT_LOGISTIC_ARTIFACT_PATH,
    DEFAULT_METRICS_PATH,
    train_baselines,
)
from backend.ml.preprocessing.pipeline import (
    DEFAULT_PREPROCESSOR_ARTIFACT_PATH,
    DEFAULT_TEXT_PCA_ARTIFACT_PATH,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Train the first AlterScore baseline suite on temporal splits.",
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
    parser.add_argument("--random-state", type=int, default=42)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    artifacts = train_baselines(
        dataset_path=args.dataset_path,
        expected_row_count=args.expected_row_count,
        minimum_test_rows=args.minimum_test_rows,
        preprocessor_artifact_path=args.preprocessor_path,
        text_pca_artifact_path=args.text_pca_path,
        logistic_artifact_path=args.logistic_model_path,
        baseline_metrics_path=args.baseline_metrics_path,
        metrics_path=args.metrics_path,
        random_state=args.random_state,
    )
    print(
        json.dumps(
            {
                "run_id": artifacts.run_id,
                "dataset_path": None if artifacts.dataset_path is None else str(artifacts.dataset_path),
                "preprocessor_path": None if artifacts.preprocessor_path is None else str(artifacts.preprocessor_path),
                "text_pca_path": None if artifacts.text_pca_path is None else str(artifacts.text_pca_path),
                "logistic_model_path": None if artifacts.logistic_model_path is None else str(artifacts.logistic_model_path),
                "baseline_metrics_path": None if artifacts.baseline_metrics_path is None else str(artifacts.baseline_metrics_path),
                "logistic_test_auc": next(
                    metric["auc_roc"]
                    for metric in artifacts.model_stats
                    if metric["model_name"] == "logistic_regression"
                    and metric["split"] == "test_months_11_12"
                ),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
