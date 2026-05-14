from fastapi.testclient import TestClient

from backend.app.main import create_app
from backend.app.schemas.analytics import HealthResponse
from tests.integration.api._support import build_runtime_settings


def test_health_endpoint_reports_degraded_when_optional_artifacts_are_missing(
    tmp_path,
) -> None:
    settings = build_runtime_settings(tmp_path)
    app = create_app(settings)

    with TestClient(app) as client:
        response = client.get("/api/health")

    assert response.status_code == 200
    payload = HealthResponse.model_validate(response.json())
    assert payload.status == "degraded"
    assert payload.version == settings.api_version
    assert payload.model_loaded is True
    assert "runtime_model" in payload.artifacts_loaded
    assert "preprocessor" in payload.artifacts_loaded
    assert "text_pca" in payload.artifacts_loaded
    assert "dice_explainer" in payload.artifacts_loaded
    assert "shap_explainer" in payload.missing_artifacts
    assert payload.invalid_artifacts == []


def test_health_endpoint_reports_invalid_optional_artifacts_separately(
    tmp_path,
) -> None:
    settings = build_runtime_settings(tmp_path)
    shap_path = tmp_path / "models" / "explainers" / "shap_explainer.pkl"
    shap_path.parent.mkdir(parents=True, exist_ok=True)
    shap_path.write_text("not-a-joblib-artifact", encoding="utf-8")
    app = create_app(settings)

    with TestClient(app) as client:
        response = client.get("/api/health")

    assert response.status_code == 200
    payload = HealthResponse.model_validate(response.json())
    assert payload.status == "degraded"
    assert "dice_explainer" in payload.artifacts_loaded
    assert "shap_explainer" not in payload.artifacts_loaded
    assert "shap_explainer" in payload.invalid_artifacts
    assert "dice_explainer" not in payload.missing_artifacts
