"""Phase 8 deterministic generator and branching release gates."""

from __future__ import annotations

import base64
import importlib.util
from itertools import product
from pathlib import Path
import subprocess
import pytest
from typing import Any

from fastapi.testclient import TestClient

from backend.app.branching import (
    build_branching_scenarios,
    enumerate_paths,
    evaluate_all_paths,
    FinancialState,
    InvalidTransition,
    validate_transition,
)
from backend.app.api.v2.service import AnonymousAssessmentService
from backend.app.core.settings import load_settings
from backend.app.instrument import generate_form
from backend.app.main import create_app


FORBIDDEN_PUBLIC_KEYS = {
    "answer",
    "answer_key",
    "correct_answer",
    "generation_rule",
    "key",
    "point",
    "rubric",
    "rubric_points",
    "weight",
}


def _keys(value: Any):
    if isinstance(value, dict):
        yield from value.keys()
        for child in value.values():
            yield from _keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from _keys(child)


def test_phase8_generator_fuzz_has_stable_public_boundary() -> None:
    for seed in range(512):
        first = generate_form(seed)
        second = generate_form(seed)
        assert first.serialize_public() == second.serialize_public()
        payload = first.serialize_public()
        assert len(payload["items"]) == 12
        assert len(payload["behavior_profile_items"]) == 6
        assert not FORBIDDEN_PUBLIC_KEYS.intersection(_keys(payload))


def test_phase8_branching_gate_exhausts_every_reachable_path() -> None:
    scenarios = build_branching_scenarios()
    assert len(scenarios) == 2
    all_paths = set()

    for scenario in scenarios:
        paths = enumerate_paths(scenario)
        results = evaluate_all_paths(scenario)
        expected_paths = set(
            product(
                *(
                    tuple(option.option_id for option in stage.options)
                    for stage in scenario.stages
                )
            )
        )
        assert len(paths) == 27
        assert len(set(paths)) == 27
        assert set(paths) == expected_paths
        assert len(results) == 27
        assert {result.option_ids for result in results} == set(paths)
        all_paths.update((scenario.scenario_presentation_id, path) for path in paths)

    assert len(all_paths) == 54


def test_phase8_unfunded_linked_payment_is_rejected() -> None:
    before = FinancialState(
        cash_available=100,
        required_payments_due=50,
        required_payments_met=0,
        confirmed_inflows=0,
        essential_expenses=0,
        emergency_buffer=0,
        new_borrowing=0,
        borrowing_cost=0,
        avoidable_cost=0,
        late_payments=0,
        unfunded_commitments=0,
    )
    after = before.replace(required_payments_met=10)
    with pytest.raises(InvalidTransition):
        validate_transition(before, after)


TEST_SIGNING_SECRET = (
    base64.urlsafe_b64encode(bytes(range(32))).rstrip(b"=").decode("ascii")
)
REPOSITORY_ROOT = Path(__file__).resolve().parents[3]


def test_phase8_production_readiness_requires_sha_and_key_version() -> None:
    base = {
        "ALTERSCORE_ENV": "production",
        "ALTERSCORE_SIGNING_SECRET": TEST_SIGNING_SECRET,
    }

    missing_sha = AnonymousAssessmentService(load_settings(base)).readiness()
    assert missing_sha.status == "not_ready"
    assert any(
        check.message == "release metadata unavailable" for check in missing_sha.checks
    )

    missing_key_version = dict(base)
    missing_key_version["ALTERSCORE_RELEASE_SHA"] = "a" * 40
    no_key_version = AnonymousAssessmentService(
        load_settings(missing_key_version)
    ).readiness()
    assert no_key_version.status == "not_ready"
    assert any(
        check.name == "signing" and check.status == "fail"
        for check in no_key_version.checks
    )

    ready_config = dict(missing_key_version)
    ready_config["ALTERSCORE_SIGNING_KEY_VERSION"] = "key-2026-07"
    ready = AnonymousAssessmentService(load_settings(ready_config)).readiness()
    assert ready.status == "ready"
    assert all(check.status == "pass" for check in ready.checks)


def test_phase8_production_like_environments_and_operations_fail_closed() -> None:
    base = {
        "ALTERSCORE_ENV": "Production ",
        "ALTERSCORE_SIGNING_SECRET": TEST_SIGNING_SECRET,
    }
    settings = load_settings(base)
    assert settings.environment == "production"
    service = AnonymousAssessmentService(settings)
    assert service.readiness().status == "not_ready"

    with TestClient(create_app(settings), base_url="https://testserver") as client:
        response = client.get("/api/v2/assessment/form")
    assert response.status_code == 503
    error = response.json()["error"]
    assert error["code"] == "form_unavailable"
    assert error["details"] == {"failed_checks": ["scorer"]}
    assert isinstance(error["request_id"], str)
    assert isinstance(error["timestamp"], str)

    staging_service = AnonymousAssessmentService(
        environment="staging",
        signing_secret=TEST_SIGNING_SECRET,
    )
    assert staging_service.readiness().status == "not_ready"

    for local_key_version in ("local ", "LOCAL"):
        direct_production_service = AnonymousAssessmentService(
            environment="production",
            release_sha="a" * 40,
            signing_secret=TEST_SIGNING_SECRET,
            signing_key_version=local_key_version,
        )
        assert direct_production_service.readiness().status == "not_ready"


def test_phase8_linked_payment_rejects_unaccounted_borrowing() -> None:
    before = FinancialState(
        cash_available=100,
        required_payments_due=50,
        required_payments_met=0,
        confirmed_inflows=0,
        essential_expenses=0,
        emergency_buffer=0,
        new_borrowing=0,
        borrowing_cost=0,
        avoidable_cost=0,
        late_payments=0,
        unfunded_commitments=0,
    )
    with pytest.raises(InvalidTransition):
        validate_transition(
            before,
            before.replace(required_payments_met=10, new_borrowing=1_000),
        )

    direct_loan_payment = before.replace(
        cash_available=190,
        required_payments_met=10,
        new_borrowing=100,
    )
    assert validate_transition(before, direct_loan_payment).new_borrowing == 100


def _release_packager_module() -> Any:
    source_path = REPOSITORY_ROOT / "scripts" / "ci" / "prepare_hf_release.py"
    spec = importlib.util.spec_from_file_location(
        "phase8_release_packager", source_path
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _git(source_root: Path, *arguments: str) -> str:
    command = ["git", "-C", str(source_root)]
    if arguments and arguments[0] == "commit":
        command.extend(("-c", "commit.gpgsign=false"))
    command.extend(arguments)
    result = subprocess.run(
        command,
        check=True,
        capture_output=True,
        encoding="utf-8",
        text=True,
    )
    return result.stdout.strip()


def test_phase8_hf_package_uses_a_serving_allowlist(tmp_path: Path) -> None:
    source_root = tmp_path / "source"
    app = source_root / "backend" / "app"
    app.mkdir(parents=True)
    (source_root / "Dockerfile").write_text(
        "\n".join(
            (
                "FROM python:3.12-slim",
                "ARG ALTERSCORE_RELEASE_SHA=local",
                "ARG ALTERSCORE_SIGNING_KEY_VERSION=local",
                "",
            )
        ),
        encoding="utf-8",
    )
    (source_root / "backend" / "requirements.txt").write_text(
        "fastapi==0.115.6\n", encoding="utf-8"
    )
    (source_root / "backend" / "requirements.lock").write_text(
        "fastapi==0.115.6 --hash=sha256:" + "a" * 64 + "\n",
        encoding="utf-8",
    )
    (app / "__init__.py").write_text("", encoding="utf-8")
    (app / "main.py").write_text("app = object()\n", encoding="utf-8")
    (app / ".env").write_text("SENTINEL_APP_SECRET\n", encoding="utf-8")
    (app / "cached.pyc").write_bytes(b"SENTINEL_CACHE")
    (source_root / "backend" / ".env").write_text(
        "SENTINEL_BACKEND_SECRET\n", encoding="utf-8"
    )
    (source_root / "backend" / "ml").mkdir()
    (source_root / "backend" / "ml" / "artifact.pkl").write_bytes(b"SENTINEL_MODEL")
    (app / "untracked_secret.py").write_text(
        "SENTINEL_UNTRACKED_PY\n", encoding="utf-8"
    )

    _git(source_root, "init", "--quiet")
    _git(source_root, "config", "user.email", "phase8@example.test")
    _git(source_root, "config", "user.name", "Phase 8 test")
    _git(
        source_root,
        "add",
        "Dockerfile",
        "backend/requirements.lock",
        "backend/requirements.txt",
        "backend/app/__init__.py",
        "backend/app/main.py",
    )
    _git(source_root, "commit", "--quiet", "-m", "release source")
    release_sha = _git(source_root, "rev-parse", "HEAD")

    output = tmp_path / "package"
    _release_packager_module().prepare_package(
        source_root,
        output,
        release_sha,
        "key-2026-07",
    )

    packaged_paths = {
        path.relative_to(output).as_posix()
        for path in output.rglob("*")
        if path.is_file()
    }
    assert packaged_paths == {
        "Dockerfile",
        "README.md",
        "release-metadata.json",
        "backend/requirements.lock",
        "backend/requirements.txt",
        "backend/app/__init__.py",
        "backend/app/main.py",
    }
    packaged_text = b"".join(
        path.read_bytes() for path in output.rglob("*") if path.is_file()
    )
    assert b"SENTINEL_" not in packaged_text
    packaged_dockerfile = (output / "Dockerfile").read_text(encoding="utf-8")
    assert f"ARG ALTERSCORE_RELEASE_SHA={release_sha}" in packaged_dockerfile
    assert "ARG ALTERSCORE_SIGNING_KEY_VERSION=key-2026-07" in packaged_dockerfile

    (app / "main.py").write_text("app = object()\n# dirty\n", encoding="utf-8")
    with pytest.raises(ValueError, match="uncommitted serving inputs"):
        _release_packager_module().prepare_package(
            source_root,
            tmp_path / "dirty-package",
            release_sha,
            "key-2026-07",
        )


def test_phase8_release_automation_requires_trusted_paired_execution() -> None:
    ci_workflow = (REPOSITORY_ROOT / ".github" / "workflows" / "ci.yml").read_text(
        encoding="utf-8"
    )
    deploy_workflow = (
        REPOSITORY_ROOT / ".github" / "workflows" / "deploy-hf.yml"
    ).read_text(encoding="utf-8")
    rollback_workflow = (
        REPOSITORY_ROOT / ".github" / "workflows" / "rollback-release.yml"
    ).read_text(encoding="utf-8")
    smoke_runner = (REPOSITORY_ROOT / "scripts" / "ci" / "smoke_release.py").read_text(
        encoding="utf-8"
    )

    assert "grep -F -o 'contract_version: 2.0'" in ci_workflow
    assert "if grep -R -n -E" in ci_workflow
    assert "if rg -n" not in ci_workflow
    assert "github.event.workflow_run.event == 'push'" in deploy_workflow
    assert (
        "github.event.workflow_run.head_repository.full_name == github.repository"
        in deploy_workflow
    )
    assert "alterscore-production-release" in deploy_workflow
    assert "alterscore-production-release" in rollback_workflow
    assert (
        "git fetch --no-tags origin +refs/heads/main:refs/remotes/origin/main"
        in deploy_workflow
    )
    assert "VERCEL_TOKEN" in deploy_workflow
    assert (
        "VITE_RELEASE_SHA: ${{ github.event.workflow_run.head_sha }}" in deploy_workflow
    )
    assert "npx --yes vercel@54.21.1 deploy . --prod" in deploy_workflow
    assert (
        "actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02"
        in deploy_workflow
    )
    assert "FRONTEND_URL: https://alterscore.vercel.app" in deploy_workflow
    assert "FRONTEND_URL: https://alterscore.vercel.app" in rollback_workflow
    assert "vars.ALTERSCORE_FRONTEND_URL" not in deploy_workflow
    assert "vars.ALTERSCORE_FRONTEND_URL" not in rollback_workflow
    assert "DEPLOYED_FRONTEND_URL=" in deploy_workflow
    assert "DEPLOYED_FRONTEND_URL=" in rollback_workflow
    assert '--frontend-deployment-url "$DEPLOYED_FRONTEND_URL"' in deploy_workflow
    assert '--frontend-url "$DEPLOYED_FRONTEND_URL"' not in deploy_workflow
    assert '--frontend-url "$DEPLOYED_FRONTEND_URL"' not in rollback_workflow
    assert "--preflight-signing --allow-legacy-404" in deploy_workflow
    assert 'CONTRACT_VERSION.encode("ascii")' in smoke_runner
    assert "actions: read" in rollback_workflow
    assert "release-manifest-$RELEASE_SHA" in rollback_workflow
    assert "validate_release_provenance.py trusted-run" in rollback_workflow
    assert "validate_release_provenance.py trusted-artifact" in rollback_workflow
    assert "actions/workflows/$workflow_id/runs" in rollback_workflow
    assert "for page in $(seq 1 10)" in rollback_workflow
    assert 'runs_args+=(--runs-json "$runs_file")' in rollback_workflow
    assert 'test "$fetched_runs" -eq "$total_runs"' in rollback_workflow
    assert "actions/runs/$run_id/artifacts" in rollback_workflow
    assert '--workflow-run-id "$run_id"' in rollback_workflow
    assert 'test "$CONTROL_REF" = "refs/heads/main"' in rollback_workflow
    assert 'test "$(git rev-parse origin/main)" = "$CONTROL_SHA"' in rollback_workflow
    assert "actions/artifacts?name=" not in rollback_workflow
    assert "needs: validate-release" in rollback_workflow
    assert (
        "VITE_RELEASE_SHA: ${{ needs.validate-release.outputs.release_sha }}"
        in rollback_workflow
    )
    assert "vercel@latest" not in deploy_workflow
    assert "vercel@latest" not in rollback_workflow
    setup_python = "actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065"
    assert deploy_workflow.index(setup_python) < deploy_workflow.index(
        "--preflight-signing"
    )
    assert rollback_workflow.index(setup_python) < rollback_workflow.index(
        "--preflight-signing"
    )
    for workflow in (ci_workflow, deploy_workflow, rollback_workflow):
        assert "uses: actions/checkout@v" not in workflow
        assert "uses: actions/setup-python@v" not in workflow
        assert "uses: actions/setup-node@v" not in workflow


def test_phase8_hf_proxy_trust_is_private_network_scoped() -> None:
    dockerfile = (REPOSITORY_ROOT / "Dockerfile").read_text(encoding="utf-8")

    assert '"--proxy-headers"' in dockerfile
    assert '"--forwarded-allow-ips", "127.0.0.1,10.0.0.0/8"' in dockerfile
    assert '"--forwarded-allow-ips", "*"' not in dockerfile


def test_phase8_public_probes_publish_exact_release_metadata() -> None:
    settings = load_settings(
        {
            "ALTERSCORE_ENV": "production",
            "ALTERSCORE_RELEASE_SHA": "a" * 40,
            "ALTERSCORE_SIGNING_SECRET": TEST_SIGNING_SECRET,
            "ALTERSCORE_SIGNING_KEY_VERSION": "key-2026-07",
        }
    )
    with TestClient(create_app(settings), base_url="https://testserver") as client:
        for path in ("/api/live", "/api/ready"):
            response = client.get(path)
            assert response.status_code == 200
            payload = response.json()
            assert payload["release_sha"] == "a" * 40
            assert payload["contract_version"] == "2.0"
            assert payload["assessment_version"] == "india-en-3.0.0"
            assert payload["scoring_policy_version"] == "readiness-rubric-1.1.0"
