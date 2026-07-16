from fastapi.testclient import TestClient

from backend.app.main import create_app
from backend.app.schemas.analytics import HealthResponse
from tests.integration.api._support import build_runtime_settings


def test_health_endpoint_reports_degraded_when_optional_artifacts_are_missing(
    trained_model_dir,
) -> None:
    settings = build_runtime_settings(trained_model_dir)
    app = create_app(settings)

    with TestClient(app) as client:
        response = client.get("/api/health")

    assert response.status_code == 200
    payload = HealthResponse.model_validate(response.json())
    assert payload.status == "degraded"
    assert payload.version == settings.api_version
    assert payload.model_loaded is True
    assert payload.artifact_source == "runtime_model_path"
    assert payload.manifest_backed is False
    assert payload.manifest_version is None
    assert payload.model_version is None
    assert "runtime_model" in payload.artifacts_loaded
    assert "preprocessor" in payload.artifacts_loaded
    assert "dice_explainer" in payload.artifacts_loaded
    assert "shap_explainer" in payload.missing_artifacts
    assert payload.invalid_artifacts == []


def test_health_endpoint_reports_invalid_optional_artifacts_separately(
    trained_model_dir,
) -> None:
    settings = build_runtime_settings(trained_model_dir)
    shap_path = trained_model_dir / "models" / "explainers" / "shap_explainer.pkl"
    shap_path.parent.mkdir(parents=True, exist_ok=True)
    shap_path.write_text("not-a-joblib-artifact", encoding="utf-8")
    app = create_app(settings)

    with TestClient(app) as client:
        response = client.get("/api/health")

    assert response.status_code == 200
    payload = HealthResponse.model_validate(response.json())
    assert payload.status == "degraded"
    assert payload.artifact_source == "runtime_model_path"
    assert payload.manifest_backed is False
    assert "dice_explainer" in payload.artifacts_loaded
    assert "shap_explainer" not in payload.artifacts_loaded
    assert "shap_explainer" in payload.invalid_artifacts
    assert "dice_explainer" not in payload.missing_artifacts
