"""Central filesystem paths for AlterScore.

Paths are intentionally resolved from the repository root so training jobs,
offline report builders, and the backend service can share one convention.
"""

from pathlib import Path
from typing import Final


def discover_repo_root(start: Path | None = None) -> Path:
    """Find the AlterScore repository root by walking upward from ``start``."""
    current = (start or Path(__file__)).resolve()
    if current.is_file():
        current = current.parent

    for candidate in (current, *current.parents):
        if (candidate / "docs" / "AI_WORKFLOW_RULES.md").is_file() and (
            candidate / "backend"
        ).is_dir():
            return candidate

    raise RuntimeError("Could not locate the AlterScore repository root.")


def resolve_repo_path(path: str | Path, repo_root: Path | None = None) -> Path:
    """Resolve an absolute path or a path relative to the repository root."""
    path_obj = Path(path)
    if path_obj.is_absolute():
        return path_obj.resolve()

    return ((repo_root or REPO_ROOT) / path_obj).resolve()


REPO_ROOT: Final[Path] = discover_repo_root()
BACKEND_DIR: Final[Path] = REPO_ROOT / "backend"
FRONTEND_DIR: Final[Path] = REPO_ROOT / "frontend"
DATA_DIR: Final[Path] = REPO_ROOT / "data"
MODELS_DIR: Final[Path] = REPO_ROOT / "models"
EXPERIMENTS_DIR: Final[Path] = REPO_ROOT / "experiments"

RAW_DATA_DIR: Final[Path] = DATA_DIR / "raw"
INTERIM_DATA_DIR: Final[Path] = DATA_DIR / "interim"
PROCESSED_DATA_DIR: Final[Path] = DATA_DIR / "processed"
DATA_REPORTS_DIR: Final[Path] = DATA_DIR / "reports"
DATA_VALIDATION_DIR: Final[Path] = DATA_DIR / "validation"

MODEL_ARTIFACTS_DIR: Final[Path] = MODELS_DIR / "artifacts"
MODEL_PREPROCESSORS_DIR: Final[Path] = MODELS_DIR / "preprocessors"
MODEL_EXPLAINERS_DIR: Final[Path] = MODELS_DIR / "explainers"
MODEL_REPORTS_DIR: Final[Path] = MODELS_DIR / "reports"
MODEL_REGISTRY_DIR: Final[Path] = MODELS_DIR / "registry"

RUNTIME_DIR: Final[Path] = BACKEND_DIR / "runtime"
RUNTIME_LOG_DIR: Final[Path] = RUNTIME_DIR / "logs"

PRODUCTION_MANIFEST_PATH: Final[Path] = (
    MODEL_REGISTRY_DIR / "production_manifest.json"
)

REQUIRED_ARTIFACT_PATHS: Final[dict[str, Path]] = {
    "calibrated_stacking": MODEL_ARTIFACTS_DIR / "calibrated_stacking.pkl",
    "preprocessor": MODEL_PREPROCESSORS_DIR / "preprocessor.pkl",
    "text_pca": MODEL_PREPROCESSORS_DIR / "text_pca.pkl",
    "shap_explainer": MODEL_EXPLAINERS_DIR / "shap_explainer.pkl",
    "dice_explainer": MODEL_EXPLAINERS_DIR / "dice_explainer.pkl",
    "metrics": MODEL_REPORTS_DIR / "metrics.json",
    "baseline_metrics": MODEL_REPORTS_DIR / "baseline_metrics.json",
    "fairness_report": MODEL_REPORTS_DIR / "fairness_report.json",
    "psi_report": MODEL_REPORTS_DIR / "psi_report.json",
    "global_importance": MODEL_REPORTS_DIR / "global_importance.json",
    "population_percentiles": MODEL_REPORTS_DIR / "population_percentiles.json",
    "production_manifest": PRODUCTION_MANIFEST_PATH,
}

__all__ = [
    "BACKEND_DIR",
    "DATA_DIR",
    "DATA_REPORTS_DIR",
    "DATA_VALIDATION_DIR",
    "EXPERIMENTS_DIR",
    "FRONTEND_DIR",
    "INTERIM_DATA_DIR",
    "MODELS_DIR",
    "MODEL_ARTIFACTS_DIR",
    "MODEL_EXPLAINERS_DIR",
    "MODEL_PREPROCESSORS_DIR",
    "MODEL_REGISTRY_DIR",
    "MODEL_REPORTS_DIR",
    "PROCESSED_DATA_DIR",
    "PRODUCTION_MANIFEST_PATH",
    "RAW_DATA_DIR",
    "REPO_ROOT",
    "REQUIRED_ARTIFACT_PATHS",
    "RUNTIME_DIR",
    "RUNTIME_LOG_DIR",
    "discover_repo_root",
    "resolve_repo_path",
]
