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
    assert "shap_explainer" in payload.missing_artifacts
