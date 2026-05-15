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
    DEFAULT_METRICS_PATH,
    DEFAULT_POPULATION_PERCENTILES_PATH,
)
from backend.ml.training.neural.train_tabnet import (
    DEFAULT_DATASET_PATH,
    DEFAULT_TABNET_ARTIFACT_PATH,
    train_tabnet,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Train the AlterScore TabNet neural model on the documented temporal splits.",
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
        "--tabnet-model-path",
        type=Path,
        default=DEFAULT_TABNET_ARTIFACT_PATH,
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
    parser.add_argument("--random-state", type=int, default=42)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    artifacts = train_tabnet(
        dataset_path=args.dataset_path,
        expected_row_count=args.expected_row_count,
        minimum_test_rows=args.minimum_test_rows,
        preprocessor_artifact_path=args.preprocessor_path,
        text_pca_artifact_path=args.text_pca_path,
        tabnet_artifact_path=args.tabnet_model_path,
        metrics_path=args.metrics_path,
        population_percentiles_path=args.population_percentiles_path,
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
                "tabnet_artifact_path": (
                    None
                    if artifacts.tabnet_artifact_path is None
                    else str(artifacts.tabnet_artifact_path)
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
