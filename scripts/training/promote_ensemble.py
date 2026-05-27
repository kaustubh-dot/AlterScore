"""CLI entrypoint for the AlterScore ensemble promotion pipeline (Track D).

Usage:
    python scripts/training/promote_ensemble.py [--options]

Runs the full offline pipeline, saves all artifacts, and writes the updated
production_manifest.json.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.ml.training.ensemble.promote_ensemble import (
    DEFAULT_DATASET_PATH,
    DEFAULT_DICE_EXPLAINER_PATH,
    DEFAULT_FAIRNESS_REPORT_PATH,
    DEFAULT_GLOBAL_IMPORTANCE_PATH,
    DEFAULT_MANIFEST_PATH,
    DEFAULT_PREPROCESSOR_PATH,
    DEFAULT_PSI_REPORT_PATH,
    DEFAULT_SHAP_EXPLAINER_PATH,
    DEFAULT_STACKING_ARTIFACT_PATH,
    DEFAULT_STACKING_CONFIG_PATH,
    DEFAULT_TEXT_PCA_PATH,
    promote_ensemble,
)
from backend.ml.training.classical.baselines import (
    DEFAULT_METRICS_PATH,
    DEFAULT_POPULATION_PERCENTILES_PATH,
)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description=(
            "AlterScore ensemble promotion pipeline: trains all six base models, "
            "fits the calibrated stacking ensemble, refreshes SHAP/DICE/fairness "
            "artifacts, and writes production_manifest.json."
        )
    )
    p.add_argument("--dataset-path", type=Path, default=DEFAULT_DATASET_PATH)
    p.add_argument("--expected-row-count", type=int, default=None)
    p.add_argument("--minimum-test-rows", type=int, default=1_000)
    p.add_argument("--random-state", type=int, default=42)
    p.add_argument("--stacking-artifact-path", type=Path, default=DEFAULT_STACKING_ARTIFACT_PATH)
    p.add_argument("--stacking-config-path", type=Path, default=DEFAULT_STACKING_CONFIG_PATH)
    p.add_argument("--preprocessor-path", type=Path, default=DEFAULT_PREPROCESSOR_PATH)
    p.add_argument("--text-pca-path", type=Path, default=DEFAULT_TEXT_PCA_PATH)
    p.add_argument("--shap-explainer-path", type=Path, default=DEFAULT_SHAP_EXPLAINER_PATH)
    p.add_argument("--dice-explainer-path", type=Path, default=DEFAULT_DICE_EXPLAINER_PATH)
    p.add_argument("--global-importance-path", type=Path, default=DEFAULT_GLOBAL_IMPORTANCE_PATH)
    p.add_argument("--fairness-report-path", type=Path, default=DEFAULT_FAIRNESS_REPORT_PATH)
    p.add_argument("--psi-report-path", type=Path, default=DEFAULT_PSI_REPORT_PATH)
    p.add_argument("--metrics-path", type=Path, default=DEFAULT_METRICS_PATH)
    p.add_argument("--population-percentiles-path", type=Path, default=DEFAULT_POPULATION_PERCENTILES_PATH)
    p.add_argument("--manifest-path", type=Path, default=DEFAULT_MANIFEST_PATH)
    p.add_argument("--manifest-version", type=str, default="calibrated_stacking_ensemble_v2")
    p.add_argument("--code-ref", type=str, default="antigravity/dev")
    p.add_argument("--max-epochs", type=int, default=None, help="Max epochs for neural base models")
    p.add_argument("--patience", type=int, default=None, help="Patience for neural base models")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    art = promote_ensemble(
        dataset_path=args.dataset_path,
        expected_row_count=args.expected_row_count,
        minimum_test_rows=args.minimum_test_rows,
        random_state=args.random_state,
        stacking_artifact_path=args.stacking_artifact_path,
        stacking_config_path=args.stacking_config_path,
        preprocessor_path=args.preprocessor_path,
        text_pca_path=args.text_pca_path,
        shap_explainer_path=args.shap_explainer_path,
        dice_explainer_path=args.dice_explainer_path,
        global_importance_path=args.global_importance_path,
        fairness_report_path=args.fairness_report_path,
        psi_report_path=args.psi_report_path,
        metrics_path=args.metrics_path,
        population_percentiles_path=args.population_percentiles_path,
        manifest_path=args.manifest_path,
        manifest_version=args.manifest_version,
        code_ref=args.code_ref,
        max_epochs=args.max_epochs,
        patience=args.patience,
    )
    print(json.dumps({
        "run_id": art.run_id,
        "test_auc_roc": art.test_auc_roc,
        "manifest_path": str(art.manifest_path),
        "stacking_artifact_path": str(art.stacking_artifact_path),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
