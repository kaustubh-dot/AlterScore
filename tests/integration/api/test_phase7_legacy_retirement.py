"""Serving-only coverage for Phase 7 public/research separation."""

from __future__ import annotations

import ast
import base64
from pathlib import Path

from fastapi.testclient import TestClient

from backend.app.core.settings import load_settings
from backend.app.main import create_app

REPO_ROOT = Path(__file__).resolve().parents[3]
TEST_SIGNING_SECRET = (
    base64.urlsafe_b64encode(bytes(range(32))).rstrip(b"=").decode("ascii")
)


def _client() -> TestClient:
    settings = load_settings(
        {
            "ALTERSCORE_ENV": "test",
            "ALTERSCORE_API_VERSION": "0.2.0",
            "ALTERSCORE_SIGNING_SECRET": TEST_SIGNING_SECRET,
        }
    )
    return TestClient(create_app(settings), base_url="https://testserver")


def test_legacy_scoring_is_explicitly_retired_without_a_v1_alias() -> None:
    with _client() as client:
        for path in ("/api/score", "/api/debug-score"):
            response = client.post(path, json={"answers": {}})
            assert response.status_code == 410
            assert response.json()["error"]["code"] == "legacy_route_retired"

        assert client.post("/api/v1/score", json={}).status_code == 404


def test_public_readiness_and_health_do_not_require_model_artifacts() -> None:
    with _client() as client:
        live = client.get("/api/live")
        health = client.get("/api/health")
        ready = client.get("/api/ready")

        assert live.status_code == 200
        assert health.status_code == 200
        assert health.json()["service"] == "public-v2"
        assert ready.status_code == 200
        assert ready.json()["status"] == "ready"
        assert {check["name"] for check in ready.json()["checks"]} == {
            "instrument",
            "scorer",
            "signing",
            "attempt_store",
            "verification_store",
            "rate_limits",
        }


def test_former_analytics_routes_are_not_public_research_routes() -> None:
    routes = (
        "model-stats",
        "baseline-comparison",
        "fairness-report",
        "drift-report",
        "global-importance",
        "score-distribution",
        "roc-data",
        "pr-curve",
        "calibration-curve",
        "confusion-matrix",
    )
    with _client() as client:
        assert all(client.get(f"/api/{route}").status_code == 404 for route in routes)


def test_production_python_graph_has_no_archived_research_imports() -> None:
    forbidden = (
        "backend.ml",
        "backend.app.core.artifact_loader",
        "backend.app.core.rate_limit",
        "backend.app.services.scoring",
        "backend.app.services.analytics",
        "backend.app.services.request_logging",
    )
    for source_path in (REPO_ROOT / "backend" / "app").rglob("*.py"):
        tree = ast.parse(source_path.read_text(encoding="utf-8"))
        imported: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.append(node.module)
        assert not any(
            module == prefix or module.startswith(f"{prefix}.")
            for module in imported
            for prefix in forbidden
        ), source_path


def test_production_dependency_and_image_boundaries_are_allow_listed() -> None:
    requirements = (
        (REPO_ROOT / "backend" / "requirements.txt").read_text(encoding="utf-8").lower()
    )
    for package in (
        "numpy",
        "pandas",
        "scikit-learn",
        "xgboost",
        "lightgbm",
        "shap",
        "torch",
        "spacy",
        "sentence-transformers",
        "slowapi",
    ):
        assert package not in requirements

    dockerfile = (REPO_ROOT / "Dockerfile").read_text(encoding="utf-8")
    assert "COPY backend/app ./backend/app" in dockerfile
    assert "COPY . ." not in dockerfile
    assert "COPY models" not in dockerfile
    assert "COPY scripts" not in dockerfile


def test_automation_does_not_execute_archived_research_paths() -> None:
    workflow_sources = (
        REPO_ROOT / ".github" / "workflows" / "ci.yml",
        REPO_ROOT / ".github" / "workflows" / "deploy-hf.yml",
    )
    combined = "\n".join(
        path.read_text(encoding="utf-8").lower() for path in workflow_sources
    )
    for forbidden in (
        "backend.ml",
        "git lfs",
        "lfs: true",
        "models/registry",
        "python -m spacy",
        "scripts/validation",
    ):
        assert forbidden not in combined, forbidden


def test_research_lab_is_static_and_states_the_frozen_boundary() -> None:
    source = (REPO_ROOT / "frontend" / "src" / "pages" / "ResearchLab.jsx").read_text(
        encoding="utf-8"
    )
    lowered = source.lower()
    for required in (
        "synthetic",
        "fairness",
        "auc",
        "generated data",
        "does not score public assessments",
    ):
        assert required in lowered
    for forbidden in ("api.js", "assessmentv2", "questions.js", "sessionstorage"):
        assert forbidden not in lowered

    app_source = (REPO_ROOT / "frontend" / "src" / "App.jsx").read_text(
        encoding="utf-8"
    )
    assert "ResearchLab" in app_source
    assert "/research" in app_source
    assert "/admin" not in app_source
    assert "questions.js" not in "\n".join(
        path.read_text(encoding="utf-8")
        for path in (REPO_ROOT / "frontend" / "src").rglob("*.js")
        if path.name != "questions.js"
    )


def test_active_docs_do_not_describe_the_retired_model_contract() -> None:
    active_docs = (
        REPO_ROOT / "README.md",
        REPO_ROOT / "backend" / "README.md",
        REPO_ROOT / "docs" / "API_CONTRACTS.md",
        REPO_ROOT / "docs" / "BACKEND_RUNTIME_ARCHITECTURE.md",
        REPO_ROOT / "docs" / "DATA_SCHEMA.md",
        REPO_ROOT / "docs" / "DEPLOYMENT.md",
        REPO_ROOT / "docs" / "PROJECT_STRUCTURE.md",
        REPO_ROOT / "docs" / "ROLLBACK_CHECKLIST.md",
        REPO_ROOT / "docs" / "SETUP.md",
        REPO_ROOT / "docs" / "GOVERNANCE_WORKFLOW.md",
    )
    forbidden_phrases = (
        "repayment_probability",
        "calibrated model probability",
        "the active checked-in monotonic bundle",
        "manifest-backed, loaded model",
        "get a credit score without credit history",
    )
    combined = "\n".join(
        path.read_text(encoding="utf-8").lower() for path in active_docs
    )
    for phrase in forbidden_phrases:
        assert phrase not in combined, phrase


def test_retired_payloads_are_absent_from_production_checkout() -> None:
    for retired_path in (
        "research",
        "docs/assets/readme-illustrations",
        "docs/SCORING_V3_CHECKPOINTS.md",
        "docs/SCORING_V3_CODEX_REVIEW_PROMPT.md",
        "docs/SCORING_V3_CURRENT_STATE.md",
        "docs/SCORING_V3_EXHAUSTIVE_CERTIFICATION_2026-07-17.md",
        "docs/SCORING_V3_FINAL_AUDIT.md",
        "docs/SCORING_V3_LUNA_PLAN.md",
        "tests/e2e",
    ):
        assert not (REPO_ROOT / retired_path).exists(), retired_path

    ignore_rules = (REPO_ROOT / ".gitignore").read_text(encoding="utf-8")
    for retired_root in ("/data/", "/experiments/", "/models/", "/research/"):
        assert retired_root in ignore_rules
