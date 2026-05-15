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
from backend.ml.training.neural.train_mlp import (
    DEFAULT_DATASET_PATH,
    DEFAULT_MLP_ARTIFACT_PATH,
    train_mlp,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Train the AlterScore residual MLP neural model on the documented temporal splits.",
    )
    parser.add_argument("--dataset-path", type=Path, default=DEFAULT_DATASET_PATH)
    parser.add_argument("--expected-row-count", type=int, default=None)
    parser.add_argument("--minimum-test-rows", type=int, default=1_000)
    parser.add_argument("--preprocessor-path", type=Path, default=DEFAULT_PREPROCESSOR_ARTIFACT_PATH)
    parser.add_argument("--text-pca-path", type=Path, default=DEFAULT_TEXT_PCA_ARTIFACT_PATH)
    parser.add_argument("--mlp-model-path", type=Path, default=DEFAULT_MLP_ARTIFACT_PATH)
    parser.add_argument("--metrics-path", type=Path, default=DEFAULT_METRICS_PATH)
    parser.add_argument("--population-percentiles-path", type=Path, default=DEFAULT_POPULATION_PERCENTILES_PATH)
    parser.add_argument("--random-state", type=int, default=42)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    artifacts = train_mlp(
        dataset_path=args.dataset_path,
        expected_row_count=args.expected_row_count,
        minimum_test_rows=args.minimum_test_rows,
        preprocessor_artifact_path=args.preprocessor_path,
        text_pca_artifact_path=args.text_pca_path,
        mlp_artifact_path=args.mlp_model_path,
        metrics_path=args.metrics_path,
        population_percentiles_path=args.population_percentiles_path,
        random_state=args.random_state,
    )
    print(
        json.dumps(
            {
                "run_id": artifacts.run_id,
                "mlp_artifact_path": str(artifacts.mlp_artifact_path) if artifacts.mlp_artifact_path else None,
                "metrics_path": str(artifacts.metrics_path) if artifacts.metrics_path else None,
                "population_percentiles_path": str(artifacts.population_percentiles_path) if artifacts.population_percentiles_path else None,
                "test_auc_roc": {
                    m["model_name"]: m["auc_roc"]
                    for m in artifacts.model_stats
                    if m["split"] == "test_months_11_12"
                },
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
