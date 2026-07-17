"""Phase 9 release-manifest and final-audit regression coverage."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import zipfile
from typing import Any

import pytest


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
RELEASE_SHA = "a" * 40
PACKAGE_COMMIT = "b" * 40
REPOSITORY = "example/alter-score"
WORKFLOW_RUN_ID = 123


def _load_script(filename: str, module_name: str) -> Any:
    source_path = REPOSITORY_ROOT / "scripts" / "ci" / filename
    spec = importlib.util.spec_from_file_location(module_name, source_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _write_archive(
    path: Path, manifest: dict[str, object], *, extra: bool = False
) -> None:
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("release-manifest.json", json.dumps(manifest))
        if extra:
            archive.writestr("unexpected.txt", "not a release manifest")


def test_phase9_release_manifest_round_trip_binds_exact_release_identity(
    tmp_path: Path,
) -> None:
    writer = _load_script("write_release_manifest.py", "phase9_manifest_writer")
    validator = _load_script(
        "validate_release_manifest.py", "phase9_manifest_validator"
    )
    manifest_path = tmp_path / "release-manifest.json"
    writer.write_manifest(
        manifest_path,
        RELEASE_SHA,
        "https://frontend.example",
        "https://frontend-deployment.example",
        "https://backend.example/",
        PACKAGE_COMMIT,
        "key-2026-07",
        "https://github.com/example/alter-score/actions/runs/123",
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    archive_path = tmp_path / "release-manifest.zip"
    _write_archive(archive_path, manifest)

    validator.validate_manifest(
        archive_path,
        RELEASE_SHA,
        "example/alter-score",
        "https://frontend.example/",
        "https://backend.example",
        WORKFLOW_RUN_ID,
    )

    assert manifest["source_sha"] == RELEASE_SHA
    assert manifest["frontend_release_sha"] == RELEASE_SHA
    assert manifest["backend_release_sha"] == RELEASE_SHA
    assert manifest["smoke_status"] == "passed"
    assert manifest["backend_package_commit"] == PACKAGE_COMMIT
    assert manifest["frontend_deployment_url"] == (
        "https://frontend-deployment.example"
    )


def test_phase9_manifest_rejects_extra_files_and_identity_mismatch(
    tmp_path: Path,
) -> None:
    writer = _load_script("write_release_manifest.py", "phase9_manifest_writer_invalid")
    validator = _load_script(
        "validate_release_manifest.py", "phase9_manifest_validator_invalid"
    )
    manifest_path = tmp_path / "release-manifest.json"
    writer.write_manifest(
        manifest_path,
        RELEASE_SHA,
        "https://frontend.example",
        "https://frontend-deployment.example",
        "https://backend.example",
        PACKAGE_COMMIT,
        "key-2026-07",
        "https://github.com/example/alter-score/actions/runs/123",
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    extra_archive = tmp_path / "extra.zip"
    _write_archive(extra_archive, manifest, extra=True)
    with pytest.raises(ValueError, match="only root"):
        validator.validate_manifest(
            extra_archive,
            RELEASE_SHA,
            "example/alter-score",
            "https://frontend.example",
            "https://backend.example",
            WORKFLOW_RUN_ID,
        )

    mismatch = dict(manifest)
    mismatch["backend_release_sha"] = "b" * 40
    mismatch_archive = tmp_path / "mismatch.zip"
    _write_archive(mismatch_archive, mismatch)
    with pytest.raises(ValueError, match="backend_release_sha"):
        validator.validate_manifest(
            mismatch_archive,
            RELEASE_SHA,
            "example/alter-score",
            "https://frontend.example",
            "https://backend.example",
            WORKFLOW_RUN_ID,
        )


def test_phase9_manifest_writer_rejects_unsafe_references(tmp_path: Path) -> None:
    writer = _load_script("write_release_manifest.py", "phase9_manifest_writer_safety")
    output = tmp_path / "release-manifest.json"
    common = (
        output,
        RELEASE_SHA,
        "https://frontend.example",
        "https://frontend-deployment.example",
        "https://backend.example",
        PACKAGE_COMMIT,
    )
    with pytest.raises(ValueError, match="signing key version"):
        writer.write_manifest(
            *common, "key\nsecret", "https://github.com/example/actions/runs/1"
        )
    with pytest.raises(ValueError, match="workflow run URL"):
        writer.write_manifest(
            *common, "key-2026-07", "http://github.com/example/actions/runs/1"
        )


def _workflow_metadata() -> dict[str, object]:
    return {
        "id": 17,
        "name": "Deploy AlterScore backend after CI",
        "path": ".github/workflows/deploy-hf.yml",
        "state": "active",
    }


def _trusted_run() -> dict[str, object]:
    repository = {"id": 71, "full_name": REPOSITORY}
    return {
        "id": WORKFLOW_RUN_ID,
        "workflow_id": 17,
        "name": "Deploy AlterScore backend after CI",
        "path": ".github/workflows/deploy-hf.yml",
        "status": "completed",
        "conclusion": "success",
        "event": "workflow_run",
        "head_branch": "main",
        "head_sha": RELEASE_SHA,
        "html_url": f"https://github.com/{REPOSITORY}/actions/runs/{WORKFLOW_RUN_ID}",
        "repository": repository,
        "head_repository": dict(repository),
    }


def _trusted_artifact() -> dict[str, object]:
    artifact_id = 91
    return {
        "id": artifact_id,
        "name": f"release-manifest-{RELEASE_SHA}",
        "expired": False,
        "size_in_bytes": 2048,
        "archive_download_url": (
            f"https://api.github.com/repos/{REPOSITORY}/actions/artifacts/"
            f"{artifact_id}/zip"
        ),
        "workflow_run": {
            "id": WORKFLOW_RUN_ID,
            "repository_id": 71,
            "head_repository_id": 71,
            "head_branch": "main",
            "head_sha": RELEASE_SHA,
        },
    }


def test_phase9_rollback_provenance_binds_exact_workflow_run_and_artifact() -> None:
    provenance = _load_script(
        "validate_release_provenance.py", "phase9_release_provenance"
    )
    selection = provenance.select_trusted_run(
        _workflow_metadata(),
        {"total_count": 1, "workflow_runs": [_trusted_run()]},
        release_sha=RELEASE_SHA,
        repository=REPOSITORY,
    )
    artifact = provenance.select_trusted_artifact(
        selection,
        {"total_count": 1, "artifacts": [_trusted_artifact()]},
        release_sha=RELEASE_SHA,
        repository=REPOSITORY,
    )

    assert selection["run_id"] == WORKFLOW_RUN_ID
    assert selection["workflow_id"] == 17
    assert artifact["artifact_id"] == 91
    assert artifact["workflow_run_url"].endswith(f"/runs/{WORKFLOW_RUN_ID}")


def test_phase9_rollback_provenance_selects_a_trusted_run_from_page_two() -> None:
    provenance = _load_script(
        "validate_release_provenance.py", "phase9_paginated_release_provenance"
    )
    first_page = {
        "total_count": 101,
        "workflow_runs": [{"id": run_id} for run_id in range(1_000, 1_100)],
    }
    second_page = {"total_count": 101, "workflow_runs": [_trusted_run()]}

    merged = provenance.merge_workflow_run_pages([first_page, second_page])
    selection = provenance.select_trusted_run(
        _workflow_metadata(),
        merged,
        release_sha=RELEASE_SHA,
        repository=REPOSITORY,
    )

    assert len(merged["workflow_runs"]) == 101
    assert selection["run_id"] == WORKFLOW_RUN_ID


def test_phase9_rollback_provenance_rejects_incomplete_or_unstable_pages() -> None:
    provenance = _load_script(
        "validate_release_provenance.py", "phase9_incomplete_release_provenance"
    )
    with pytest.raises(ValueError, match="truncated"):
        provenance.merge_workflow_run_pages(
            [
                {
                    "total_count": 101,
                    "workflow_runs": [{"id": run_id} for run_id in range(1, 101)],
                }
            ]
        )
    with pytest.raises(ValueError, match="changed during pagination"):
        provenance.merge_workflow_run_pages(
            [
                {"total_count": 2, "workflow_runs": [{"id": 1}]},
                {"total_count": 3, "workflow_runs": [{"id": 2}]},
            ]
        )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("workflow_id", 18),
        ("path", ".github/workflows/other.yml"),
        ("status", "queued"),
        ("conclusion", "failure"),
        ("event", "workflow_dispatch"),
        ("head_branch", "feature"),
        ("head_sha", "c" * 40),
    ],
)
def test_phase9_rollback_provenance_rejects_untrusted_runs(
    field: str, value: object
) -> None:
    provenance = _load_script(
        "validate_release_provenance.py", f"phase9_untrusted_run_{field}"
    )
    run = _trusted_run()
    run[field] = value
    with pytest.raises(ValueError, match="no successful trusted deploy run"):
        provenance.select_trusted_run(
            _workflow_metadata(),
            {"total_count": 1, "workflow_runs": [run]},
            release_sha=RELEASE_SHA,
            repository=REPOSITORY,
        )


def test_phase9_rollback_provenance_rejects_cross_run_and_duplicate_artifacts() -> None:
    provenance = _load_script(
        "validate_release_provenance.py", "phase9_untrusted_artifacts"
    )
    selection = provenance.select_trusted_run(
        _workflow_metadata(),
        {"total_count": 1, "workflow_runs": [_trusted_run()]},
        release_sha=RELEASE_SHA,
        repository=REPOSITORY,
    )
    cross_run = _trusted_artifact()
    cross_run["workflow_run"] = {
        **cross_run["workflow_run"],
        "id": WORKFLOW_RUN_ID + 1,
    }
    with pytest.raises(ValueError, match="exactly one"):
        provenance.select_trusted_artifact(
            selection,
            {"total_count": 1, "artifacts": [cross_run]},
            release_sha=RELEASE_SHA,
            repository=REPOSITORY,
        )

    duplicate = {**_trusted_artifact(), "id": 92}
    duplicate["archive_download_url"] = (
        f"https://api.github.com/repos/{REPOSITORY}/actions/artifacts/92/zip"
    )
    with pytest.raises(ValueError, match="exactly one"):
        provenance.select_trusted_artifact(
            selection,
            {"total_count": 2, "artifacts": [_trusted_artifact(), duplicate]},
            release_sha=RELEASE_SHA,
            repository=REPOSITORY,
        )


def test_phase9_manifest_rejects_wrong_run_url_and_unsafe_zip(tmp_path: Path) -> None:
    writer = _load_script("write_release_manifest.py", "phase9_manifest_writer_zip")
    validator = _load_script(
        "validate_release_manifest.py", "phase9_manifest_validator_zip"
    )
    manifest_path = tmp_path / "release-manifest.json"
    writer.write_manifest(
        manifest_path,
        RELEASE_SHA,
        "https://frontend.example",
        "https://frontend-deployment.example",
        "https://backend.example",
        PACKAGE_COMMIT,
        "key-2026-07",
        f"https://github.com/{REPOSITORY}/actions/runs/{WORKFLOW_RUN_ID}",
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    archive_path = tmp_path / "release-manifest.zip"
    _write_archive(archive_path, manifest)
    with pytest.raises(ValueError, match="workflow provenance"):
        validator.validate_manifest(
            archive_path,
            RELEASE_SHA,
            REPOSITORY,
            "https://frontend.example",
            "https://backend.example",
            WORKFLOW_RUN_ID + 1,
        )

    unsafe_path = tmp_path / "unsafe.zip"
    with zipfile.ZipFile(unsafe_path, "w") as package:
        info = zipfile.ZipInfo("release-manifest.json")
        info.create_system = 3
        info.external_attr = 0o120777 << 16
        package.writestr(info, json.dumps(manifest))
    with pytest.raises(ValueError, match="unsafe"):
        validator.validate_manifest(
            unsafe_path,
            RELEASE_SHA,
            REPOSITORY,
            "https://frontend.example",
            "https://backend.example",
            WORKFLOW_RUN_ID,
        )


def test_phase9_production_dependencies_use_one_hash_locked_release_graph() -> None:
    dockerfile = (REPOSITORY_ROOT / "Dockerfile").read_text(encoding="utf-8")
    ci_workflow = (REPOSITORY_ROOT / ".github" / "workflows" / "ci.yml").read_text(
        encoding="utf-8"
    )
    packager = (REPOSITORY_ROOT / "scripts" / "ci" / "prepare_hf_release.py").read_text(
        encoding="utf-8"
    )
    lock = (REPOSITORY_ROOT / "backend" / "requirements.lock").read_text(
        encoding="utf-8"
    )

    assert "COPY backend/requirements.lock ./requirements.lock" in dockerfile
    assert "--require-hashes -r requirements.lock" in dockerfile
    assert (
        ci_workflow.count("pip install --require-hashes -r backend/requirements.lock")
        == 2
    )
    assert '"backend/requirements.lock"' in packager
    assert lock.startswith("# This file was autogenerated by uv")
    assert lock.count("--hash=sha256:") >= 17
    assert "git+" not in lock
    assert "http://" not in lock


def test_phase9_preflight_allows_only_explicit_legacy_bootstrap(monkeypatch) -> None:
    smoke = _load_script("smoke_release.py", "phase9_smoke_runner")
    monkeypatch.setattr(
        smoke,
        "_request",
        lambda *args, **kwargs: smoke.HttpResult(404, {}, {}),
    )
    smoke.require_signing_preflight("https://backend.example", allow_legacy_404=True)
    with pytest.raises(smoke.SmokeFailure, match="expected HTTP 200 or 503"):
        smoke.require_signing_preflight("https://backend.example")
