"""Phase 9 release-manifest and final-audit regression coverage."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import zipfile
from typing import Any

import pytest


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
RELEASE_SHA = "a" * 40


def _load_script(filename: str, module_name: str) -> Any:
    source_path = REPOSITORY_ROOT / "scripts" / "ci" / filename
    spec = importlib.util.spec_from_file_location(module_name, source_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
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
        "hf-package-commit",
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
    )

    assert manifest["source_sha"] == RELEASE_SHA
    assert manifest["frontend_release_sha"] == RELEASE_SHA
    assert manifest["backend_release_sha"] == RELEASE_SHA
    assert manifest["smoke_status"] == "passed"
    assert manifest["backend_package_commit"] == "hf-package-commit"
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
        "hf-package-commit",
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
        "hf-package-commit",
    )
    with pytest.raises(ValueError, match="signing key version"):
        writer.write_manifest(
            *common, "key\nsecret", "https://github.com/example/actions/runs/1"
        )
    with pytest.raises(ValueError, match="workflow run URL"):
        writer.write_manifest(
            *common, "key-2026-07", "http://github.com/example/actions/runs/1"
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
