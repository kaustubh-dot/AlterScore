import json

from backend.app.core.settings import Settings, load_settings
from backend.ml.data_generation.generator import generate_synthetic_dataset
from backend.ml.training.classical.baselines import train_baselines


def build_runtime_settings(tmp_path) -> Settings:
    model_root = tmp_path / "models"
    train_baselines(
        generate_synthetic_dataset(row_count=2_400, seed=37),
        expected_row_count=2_400,
        minimum_test_rows=300,
        preprocessor_artifact_path=model_root / "preprocessors" / "preprocessor.pkl",
        text_pca_artifact_path=model_root / "preprocessors" / "text_pca.pkl",
        logistic_artifact_path=model_root / "artifacts" / "logistic_best.pkl",
        baseline_metrics_path=model_root / "reports" / "baseline_metrics.json",
        metrics_path=model_root / "reports" / "metrics.json",
    )
    (model_root / "reports" / "population_percentiles.json").write_text(
        json.dumps(
            {
                "score_to_percentile": {
                    "300": 0,
                    "560": 50,
                    "850": 100,
                }
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return load_settings(
        {
            "ALTERSCORE_REPO_ROOT": str(tmp_path),
            "ALTERSCORE_RUNTIME_MODEL_PATH": "models/artifacts/logistic_best.pkl",
        }
    )
