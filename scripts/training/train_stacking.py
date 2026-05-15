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
from backend.ml.training.ensemble.train_stacking import (
    DEFAULT_DATASET_PATH,
    DEFAULT_STACKING_ARTIFACT_PATH,
    DEFAULT_STACKING_CONFIG_PATH,
    train_stacking,
)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description=(
            "Train and calibrate the AlterScore stacking ensemble on the "
            "documented temporal splits. All six base models are re-trained "
            "from scratch; the meta-learner and calibrator are fitted on "
            "validation months 9-10 only."
        )
    )
    p.add_argument("--dataset-path", type=Path, default=DEFAULT_DATASET_PATH)
    p.add_argument("--expected-row-count", type=int, default=None)
    p.add_argument("--minimum-test-rows", type=int, default=1_000)
    p.add_argument("--preprocessor-path", type=Path, default=DEFAULT_PREPROCESSOR_ARTIFACT_PATH)
    p.add_argument("--text-pca-path", type=Path, default=DEFAULT_TEXT_PCA_ARTIFACT_PATH)
    p.add_argument("--stacking-artifact-path", type=Path, default=DEFAULT_STACKING_ARTIFACT_PATH)
    p.add_argument("--stacking-config-path", type=Path, default=DEFAULT_STACKING_CONFIG_PATH)
    p.add_argument("--metrics-path", type=Path, default=DEFAULT_METRICS_PATH)
    p.add_argument("--population-percentiles-path", type=Path, default=DEFAULT_POPULATION_PERCENTILES_PATH)
    p.add_argument("--random-state", type=int, default=42)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    art = train_stacking(
        dataset_path=args.dataset_path,
        expected_row_count=args.expected_row_count,
        minimum_test_rows=args.minimum_test_rows,
        preprocessor_artifact_path=args.preprocessor_path,
        text_pca_artifact_path=args.text_pca_path,
        stacking_artifact_path=args.stacking_artifact_path,
        stacking_config_path=args.stacking_config_path,
        metrics_path=args.metrics_path,
        population_percentiles_path=args.population_percentiles_path,
        random_state=args.random_state,
    )
    print(json.dumps({
        "run_id": art.run_id,
        "stacking_artifact_path": str(art.stacking_artifact_path) if art.stacking_artifact_path else None,
        "base_model_order": list(art.base_model_order),
        "test_auc_roc": {
            m["model_name"]: m["auc_roc"]
            for m in art.model_stats if m["split"] == "test_months_11_12"
        },
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
