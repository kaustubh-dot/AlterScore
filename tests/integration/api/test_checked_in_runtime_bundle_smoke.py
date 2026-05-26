import json
from pathlib import Path
import shutil

from fastapi.testclient import TestClient

from backend.app.core.artifact_loader import load_runtime_artifact_bundle
from backend.app.core.paths import REPO_ROOT, REQUEST_LOG_PATH
from backend.app.core.settings import Settings, load_settings
from backend.app.main import create_app
from backend.app.schemas.analytics import (
    FairnessReport,
    GlobalImportanceResponse,
    HealthResponse,
)
from backend.app.schemas.score import ScoreResponse


def _repo_settings(*, request_log_path: str | None = None) -> Settings:
    env = {"ALTERSCORE_REPO_ROOT": str(REPO_ROOT)}
    if request_log_path is not None:
        env["ALTERSCORE_REQUEST_LOG_PATH"] = request_log_path
    return load_settings(env)


def _load_valid_score_payload() -> dict:
    return json.loads(
        (REPO_ROOT / "tests" / "fixtures" / "score_request_valid.json").read_text(
            encoding="utf-8"
        )
    )


def _copy_checked_in_runtime_bundle(tmp_path) -> Settings:
    model_directories = (
        "artifacts",
        "explainers",
        "preprocessors",
        "registry",
        "reports",
    )
    for directory_name in model_directories:
        source_dir = REPO_ROOT / "models" / directory_name
        target_dir = tmp_path / "models" / directory_name
        target_dir.mkdir(parents=True, exist_ok=True)
        for source_path in source_dir.iterdir():
            if source_path.name == ".gitkeep":
                continue
            shutil.copy2(source_path, target_dir / source_path.name)
    return load_settings({"ALTERSCORE_REPO_ROOT": str(tmp_path)})


def test_checked_in_bundle_loader_validates_real_runtime_artifacts() -> None:
    settings = _repo_settings()
    bundle = load_runtime_artifact_bundle(settings, strict=True)

    assert settings.request_log_path == REQUEST_LOG_PATH
    assert bundle.report.source == "manifest"
    assert bundle.report.runtime_model_name == "stacking_ensemble"
    assert bundle.report.manifest_version is not None
    assert bundle.report.model_version == "0.2.0"
    assert bundle.report.scoring_ready is True
    assert bundle.manifest is not None
    assert bundle.shap_explainer is not None
    assert bundle.dice_explainer is not None
    assert bundle.fairness_report is not None
    assert "calibration_parity" in bundle.fairness_report
    assert "individual_fairness_proxy" in bundle.fairness_report
    assert bundle.global_importance is not None
    assert "production_manifest" in bundle.report.artifacts_loaded
    assert "runtime_model" in bundle.report.artifacts_loaded
    assert "preprocessor" in bundle.report.artifacts_loaded
    assert "text_pca" in bundle.report.artifacts_loaded
    assert "shap_explainer" in bundle.report.artifacts_loaded
    assert "dice_explainer" in bundle.report.artifacts_loaded
    assert "base_models" in bundle.report.artifacts_loaded
    assert bundle.base_models is not None
    assert bundle.stacking_config is not None
    assert bundle.report.missing_artifacts == ()
    assert bundle.report.invalid_artifacts == ()


def test_checked_in_bundle_health_endpoint_reports_validated_optional_status() -> None:
    settings = _repo_settings()
    app = create_app(settings)

    with TestClient(app) as client:
        response = client.get("/api/health")

    assert response.status_code == 200
    payload = HealthResponse.model_validate(response.json())
    assert payload.status == "ok"
    assert payload.artifact_source == "manifest"
    assert payload.manifest_backed is True
    assert payload.manifest_version is not None
    assert payload.model_version == "0.2.0"
    assert "shap_explainer" in payload.artifacts_loaded
    assert "dice_explainer" in payload.artifacts_loaded
    assert payload.missing_artifacts == []
    assert payload.invalid_artifacts == []


def test_copied_checked_in_bundle_marks_invalid_optional_artifacts(tmp_path) -> None:
    settings = _copy_checked_in_runtime_bundle(tmp_path)
    dice_path = settings.repo_root / "models" / "explainers" / "dice_explainer.pkl"
    dice_path.write_text("not-a-valid-dice-artifact", encoding="utf-8")
    app = create_app(settings)

    with TestClient(app) as client:
        response = client.get("/api/health")

    assert response.status_code == 200
    payload = HealthResponse.model_validate(response.json())
    assert payload.status == "degraded"
    assert payload.artifact_source == "manifest"
    assert payload.manifest_backed is True
    assert "shap_explainer" in payload.artifacts_loaded
    assert "dice_explainer" not in payload.artifacts_loaded
    assert "dice_explainer" in payload.invalid_artifacts


def test_checked_in_bundle_global_importance_endpoint_serves_saved_payload() -> None:
    settings = _repo_settings()
    app = create_app(settings)

    with TestClient(app) as client:
        response = client.get("/api/global-importance")

    assert response.status_code == 200
    payload = GlobalImportanceResponse.model_validate(response.json())
    assert payload.model_name is not None
    assert len(payload.items) == 35
    assert payload.items[0].rank == 1


def test_checked_in_bundle_fairness_endpoint_serves_refreshed_governance_payload() -> None:
    settings = _repo_settings()
    app = create_app(settings)

    with TestClient(app) as client:
        response = client.get("/api/fairness-report")

    assert response.status_code == 200
    payload = FairnessReport.model_validate(response.json())
    assert payload.groups["gender"]
    assert payload.calibration_parity is not None
    assert payload.calibration_parity.groups["gender"]
    assert payload.individual_fairness_proxy is not None
    assert payload.individual_fairness_proxy.evaluated_pairs > 0


def test_checked_in_bundle_score_endpoint_appends_to_runtime_log_path() -> None:
    relative_log_path = "runtime/logs/checked_in_bundle_smoke_requests.jsonl"
    settings = _repo_settings(request_log_path=relative_log_path)
    app = create_app(settings)
    log_path = settings.request_log_path

    if log_path.exists():
        log_path.unlink()

    with TestClient(app) as client:
        response = client.post("/api/score", json=_load_valid_score_payload())

    assert response.status_code == 200
    parsed = ScoreResponse.model_validate(response.json())
    assert parsed.credit_score >= 300
    assert parsed.explanation
    if parsed.credit_score < 850:
        assert parsed.counterfactual_actions
    else:
        assert isinstance(parsed.counterfactual_actions, list)
    assert all(item.display_name for item in parsed.explanation)
    assert all(action.estimated_score_gain >= 0 for action in parsed.counterfactual_actions)
    assert log_path.is_file()
    assert log_path.parent == REQUEST_LOG_PATH.parent

    entries = [
        json.loads(line)
        for line in log_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert len(entries) == 1
    assert entries[0]["status_code"] == 200
    assert entries[0]["session_id"] == parsed.session_id
    assert entries[0]["artifact_source"] == "manifest"
    assert entries[0]["manifest_version"] is not None
    assert entries[0]["model_version"] == "0.2.0"

    log_path.unlink()
