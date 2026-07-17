"""Select a rollback artifact only from the approved successful deploy workflow."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


SHA_PATTERN = re.compile(r"[0-9a-f]{40}")
TRUSTED_WORKFLOW_NAME = "Deploy AlterScore backend after CI"
TRUSTED_WORKFLOW_PATH = ".github/workflows/deploy-hf.yml"
MAX_ARTIFACT_BYTES = 1_000_000
MAX_FILTERED_WORKFLOW_RUNS = 1_000


def _require_mapping(value: object, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a JSON object")
    return value


def _require_repository(value: object, repository: str, label: str) -> int:
    payload = _require_mapping(value, label)
    repository_id = payload.get("id")
    if payload.get("full_name") != repository or not isinstance(repository_id, int):
        raise ValueError(f"{label} does not match the trusted repository")
    return repository_id


def validate_workflow_metadata(payload: object) -> int:
    workflow = _require_mapping(payload, "workflow metadata")
    workflow_id = workflow.get("id")
    if not isinstance(workflow_id, int) or workflow_id <= 0:
        raise ValueError("trusted workflow ID is invalid")
    if workflow.get("name") != TRUSTED_WORKFLOW_NAME:
        raise ValueError("trusted workflow name does not match")
    if workflow.get("path") != TRUSTED_WORKFLOW_PATH:
        raise ValueError("trusted workflow path does not match")
    if workflow.get("state") != "active":
        raise ValueError("trusted workflow is not active")
    return workflow_id


def merge_workflow_run_pages(payloads: list[object]) -> dict[str, object]:
    """Combine a complete filtered GitHub run search without silent truncation."""

    if not payloads or len(payloads) > 10:
        raise ValueError("one to ten workflow-run pages are required")
    expected_total: int | None = None
    combined: list[object] = []
    seen_ids: set[int] = set()
    for payload in payloads:
        document = _require_mapping(payload, "workflow-runs page")
        total_count = document.get("total_count")
        runs = document.get("workflow_runs")
        if not isinstance(total_count, int) or not isinstance(runs, list):
            raise ValueError("workflow-runs page is malformed")
        if not 0 <= total_count <= MAX_FILTERED_WORKFLOW_RUNS:
            raise ValueError("workflow-runs total exceeds the filtered search limit")
        if expected_total is None:
            expected_total = total_count
        elif total_count != expected_total:
            raise ValueError("workflow-runs total changed during pagination")
        for run in runs:
            if not isinstance(run, dict):
                raise ValueError("workflow-runs page contains a malformed run")
            run_id = run.get("id")
            if not isinstance(run_id, int) or run_id <= 0 or run_id in seen_ids:
                raise ValueError("workflow-runs pagination contains invalid duplicates")
            seen_ids.add(run_id)
            combined.append(run)
    if expected_total is None or len(combined) != expected_total:
        raise ValueError("workflow-runs response is truncated")
    return {"total_count": expected_total, "workflow_runs": combined}


def select_trusted_run(
    workflow_payload: object,
    runs_payload: object,
    *,
    release_sha: str,
    repository: str,
) -> dict[str, object]:
    if SHA_PATTERN.fullmatch(release_sha) is None:
        raise ValueError("release SHA must be 40 lowercase hexadecimal characters")
    workflow_id = validate_workflow_metadata(workflow_payload)
    runs_document = _require_mapping(runs_payload, "workflow runs")
    runs = runs_document.get("workflow_runs")
    total_count = runs_document.get("total_count")
    if not isinstance(runs, list) or not isinstance(total_count, int):
        raise ValueError("workflow-runs response is malformed")
    if total_count != len(runs):
        raise ValueError("workflow-runs response is truncated")

    trusted: list[dict[str, object]] = []
    expected_url_prefix = f"https://github.com/{repository}/actions/runs/"
    for value in runs:
        if not isinstance(value, dict):
            continue
        run_id = value.get("id")
        if not isinstance(run_id, int) or run_id <= 0:
            continue
        try:
            repository_id = _require_repository(
                value.get("repository"), repository, "run repository"
            )
            head_repository_id = _require_repository(
                value.get("head_repository"), repository, "run head repository"
            )
        except ValueError:
            continue
        expected_url = f"{expected_url_prefix}{run_id}"
        if (
            value.get("workflow_id") == workflow_id
            and value.get("name") == TRUSTED_WORKFLOW_NAME
            and value.get("path") == TRUSTED_WORKFLOW_PATH
            and value.get("status") == "completed"
            and value.get("conclusion") == "success"
            and value.get("event") == "workflow_run"
            and value.get("head_branch") == "main"
            and value.get("head_sha") == release_sha
            and value.get("html_url") == expected_url
            and repository_id == head_repository_id
        ):
            trusted.append(
                {
                    "run_id": run_id,
                    "workflow_id": workflow_id,
                    "repository_id": repository_id,
                    "workflow_run_url": expected_url,
                }
            )
    if not trusted:
        raise ValueError("no successful trusted deploy run matches the release")
    return max(trusted, key=lambda item: int(item["run_id"]))


def select_trusted_artifact(
    selection: object,
    artifacts_payload: object,
    *,
    release_sha: str,
    repository: str,
) -> dict[str, object]:
    selected = _require_mapping(selection, "trusted run selection")
    run_id = selected.get("run_id")
    repository_id = selected.get("repository_id")
    if not isinstance(run_id, int) or not isinstance(repository_id, int):
        raise ValueError("trusted run selection is malformed")
    artifacts_document = _require_mapping(artifacts_payload, "run artifacts")
    artifacts = artifacts_document.get("artifacts")
    total_count = artifacts_document.get("total_count")
    if not isinstance(artifacts, list) or not isinstance(total_count, int):
        raise ValueError("run-artifacts response is malformed")
    if total_count > len(artifacts):
        raise ValueError("run-artifacts response is truncated")

    expected_name = f"release-manifest-{release_sha}"
    expected_archive_prefix = (
        f"https://api.github.com/repos/{repository}/actions/artifacts/"
    )
    trusted: list[dict[str, object]] = []
    for value in artifacts:
        if not isinstance(value, dict) or value.get("name") != expected_name:
            continue
        workflow_run = value.get("workflow_run")
        if not isinstance(workflow_run, dict):
            continue
        artifact_id = value.get("id")
        size = value.get("size_in_bytes")
        archive_url = value.get("archive_download_url")
        if (
            isinstance(artifact_id, int)
            and artifact_id > 0
            and value.get("expired") is False
            and isinstance(size, int)
            and 0 < size <= MAX_ARTIFACT_BYTES
            and isinstance(archive_url, str)
            and archive_url.startswith(expected_archive_prefix)
            and archive_url.endswith(f"/{artifact_id}/zip")
            and workflow_run.get("id") == run_id
            and workflow_run.get("repository_id") == repository_id
            and workflow_run.get("head_repository_id") == repository_id
            and workflow_run.get("head_branch") == "main"
            and workflow_run.get("head_sha") == release_sha
        ):
            trusted.append(
                {
                    **selected,
                    "artifact_id": artifact_id,
                    "archive_download_url": archive_url,
                }
            )
    if len(trusted) != 1:
        raise ValueError("trusted deploy run must contain exactly one release manifest")
    return trusted[0]


def _load_json(path: Path) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(f"invalid JSON input: {path}") from error


def _write_json(path: Path, payload: object) -> None:
    if path.exists():
        raise ValueError(f"refusing to overwrite output: {path}")
    path.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("trusted-run")
    run_parser.add_argument("--workflow-json", type=Path, required=True)
    run_parser.add_argument(
        "--runs-json", type=Path, action="append", required=True
    )
    run_parser.add_argument("--release-sha", required=True)
    run_parser.add_argument("--repository", required=True)
    run_parser.add_argument("--output", type=Path, required=True)

    artifact_parser = subparsers.add_parser("trusted-artifact")
    artifact_parser.add_argument("--selection-json", type=Path, required=True)
    artifact_parser.add_argument("--artifacts-json", type=Path, required=True)
    artifact_parser.add_argument("--release-sha", required=True)
    artifact_parser.add_argument("--repository", required=True)
    artifact_parser.add_argument("--output", type=Path, required=True)

    args = parser.parse_args()
    if args.command == "trusted-run":
        result = select_trusted_run(
            _load_json(args.workflow_json),
            merge_workflow_run_pages([_load_json(path) for path in args.runs_json]),
            release_sha=args.release_sha,
            repository=args.repository,
        )
    else:
        result = select_trusted_artifact(
            _load_json(args.selection_json),
            _load_json(args.artifacts_json),
            release_sha=args.release_sha,
            repository=args.repository,
        )
    _write_json(args.output, result)
    print("release provenance validated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
