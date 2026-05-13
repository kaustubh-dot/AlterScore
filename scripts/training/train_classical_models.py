from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.ml.preprocessing.pipeline import DEFAULT_PREPROCESSOR_ARTIFACT_PATH
from backend.ml.training.classical.baselines import (
    DEFAULT_BASELINE_METRICS_PATH,
    DEFAULT_METRICS_PATH,
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
    artifacts = train_classical_models(
        dataset_path=args.dataset_path,
        expected_row_count=args.expected_row_count,
        minimum_test_rows=args.minimum_test_rows,
        preprocessor_artifact_path=args.preprocessor_path,
        random_forest_artifact_path=args.random_forest_model_path,
        xgboost_artifact_path=args.xgboost_model_path,
        lightgbm_artifact_path=args.lightgbm_model_path,
        baseline_metrics_path=args.baseline_metrics_path,
        metrics_path=args.metrics_path,
        random_state=args.random_state,
    )
    print(
        json.dumps(
            {
                "run_id": artifacts.run_id,
                "dataset_path": None
                if artifacts.dataset_path is None
                else str(artifacts.dataset_path),
                "metrics_path": None
                if artifacts.metrics_path is None
                else str(artifacts.metrics_path),
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
