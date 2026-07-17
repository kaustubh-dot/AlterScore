"""Validate a downloaded verified release-manifest artifact."""

from __future__ import annotations

import argparse
import json
import re
import stat
import zipfile
from pathlib import Path


SHA_PATTERN = re.compile(r"[0-9a-f]{40}")
SIGNING_KEY_VERSION_PATTERN = re.compile(r"[A-Za-z0-9._:-]{1,100}")
TIMESTAMP_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z")
CONTRACT_VERSION = "2.0"
ASSESSMENT_VERSION = "india-en-3.0.0"
SCORING_POLICY_VERSION = "readiness-rubric-1.1.0"
MAX_MANIFEST_BYTES = 65_536
MAX_COMPRESSION_RATIO = 100
MANIFEST_KEYS = {
    "source_sha",
    "frontend_release_sha",
    "backend_release_sha",
    "contract_version",
    "assessment_version",
    "scoring_policy_version",
    "backend_package_commit",
    "frontend_url",
    "frontend_deployment_url",
    "backend_url",
    "signing_key_version",
    "smoke_status",
    "workflow_run_url",
    "recorded_at",
}


def _require_https(value: object, label: str) -> None:
    if (
        not isinstance(value, str)
        or not value.startswith("https://")
        or any(char in value for char in "\r\n")
    ):
        raise ValueError(f"{label} must be an HTTPS URL")


def _read_manifest(archive: Path) -> dict[str, object]:
    with zipfile.ZipFile(archive) as package:
        entries = package.infolist()
        if len(entries) != 1 or entries[0].filename != "release-manifest.json":
            raise ValueError("artifact must contain only root release-manifest.json")
        entry = entries[0]
        file_type = (entry.external_attr >> 16) & 0o170000
        if entry.is_dir() or file_type == stat.S_IFLNK or entry.flag_bits & 0x1:
            raise ValueError("release manifest ZIP entry is unsafe")
        if entry.file_size <= 0 or entry.file_size > MAX_MANIFEST_BYTES:
            raise ValueError("release manifest ZIP entry size is invalid")
        if entry.compress_size <= 0 or (
            entry.file_size / entry.compress_size > MAX_COMPRESSION_RATIO
        ):
            raise ValueError("release manifest ZIP compression ratio is unsafe")
        try:
            payload = json.loads(package.read(entry))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ValueError("release manifest is not valid UTF-8 JSON") from error
    if not isinstance(payload, dict):
        raise ValueError("release manifest must be a JSON object")
    return payload


def validate_manifest(
    archive: Path,
    release_sha: str,
    repository: str,
    frontend_url: str,
    backend_url: str,
    workflow_run_id: int,
) -> None:
    if SHA_PATTERN.fullmatch(release_sha) is None:
        raise ValueError("release SHA must be 40 lowercase hexadecimal characters")
    manifest = _read_manifest(archive)
    if set(manifest) != MANIFEST_KEYS:
        raise ValueError("release manifest fields do not match the frozen template")
    expected = {
        "source_sha": release_sha,
        "frontend_release_sha": release_sha,
        "backend_release_sha": release_sha,
        "contract_version": CONTRACT_VERSION,
        "assessment_version": ASSESSMENT_VERSION,
        "scoring_policy_version": SCORING_POLICY_VERSION,
        "frontend_url": frontend_url.rstrip("/"),
        "backend_url": backend_url.rstrip("/"),
        "smoke_status": "passed",
    }
    for key, value in expected.items():
        if manifest.get(key) != value:
            raise ValueError(f"release manifest mismatch for {key}")
    _require_https(manifest.get("frontend_deployment_url"), "frontend deployment URL")
    key_version = manifest.get("signing_key_version")
    if SIGNING_KEY_VERSION_PATTERN.fullmatch(key_version or "") is None:
        raise ValueError("release manifest signing-key reference is invalid")
    package_commit = manifest.get("backend_package_commit")
    if (
        not isinstance(package_commit, str)
        or SHA_PATTERN.fullmatch(package_commit) is None
    ):
        raise ValueError("release manifest backend package commit is invalid")
    workflow_url = manifest.get("workflow_run_url")
    _require_https(frontend_url, "frontend URL")
    _require_https(backend_url, "backend URL")
    if not isinstance(workflow_run_id, int) or workflow_run_id <= 0:
        raise ValueError("workflow run ID must be a positive integer")
    expected_workflow_url = (
        f"https://github.com/{repository}/actions/runs/{workflow_run_id}"
    )
    if workflow_url != expected_workflow_url:
        raise ValueError("release manifest workflow provenance is invalid")
    recorded_at = manifest.get("recorded_at")
    if (
        not isinstance(recorded_at, str)
        or TIMESTAMP_PATTERN.fullmatch(recorded_at) is None
    ):
        raise ValueError("release manifest timestamp is invalid")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--release-sha", required=True)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--frontend-url", required=True)
    parser.add_argument("--backend-url", required=True)
    parser.add_argument("--workflow-run-id", type=int, required=True)
    args = parser.parse_args()
    validate_manifest(
        args.archive,
        args.release_sha,
        args.repository,
        args.frontend_url,
        args.backend_url,
        args.workflow_run_id,
    )
    print("release manifest validated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
