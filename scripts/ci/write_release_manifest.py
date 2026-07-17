"""Write the concrete manifest for one verified paired release."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path


SHA_PATTERN = re.compile(r"[0-9a-f]{40}")
SIGNING_KEY_VERSION_PATTERN = re.compile(r"[A-Za-z0-9._:-]{1,100}")
CONTRACT_VERSION = "2.0"
ASSESSMENT_VERSION = "india-en-3.0.0"
SCORING_POLICY_VERSION = "readiness-rubric-1.1.0"
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


def _template_path() -> Path:
    return (
        Path(__file__).resolve().parents[2] / "docs" / "RELEASE_MANIFEST_TEMPLATE.json"
    )


def _load_template() -> dict[str, object]:
    template = json.loads(_template_path().read_text(encoding="utf-8"))
    if not isinstance(template, dict) or set(template) != MANIFEST_KEYS:
        raise ValueError("release manifest template keys are invalid")
    return template


def _require_https(value: str, label: str) -> str:
    if not value.startswith("https://") or any(char in value for char in "\r\n"):
        raise ValueError(f"{label} must be an HTTPS URL")
    return value.rstrip("/")


def write_manifest(
    output: Path,
    source_sha: str,
    frontend_url: str,
    frontend_deployment_url: str,
    backend_url: str,
    backend_package_commit: str,
    signing_key_version: str,
    workflow_run_url: str,
) -> None:
    if SHA_PATTERN.fullmatch(source_sha) is None:
        raise ValueError("source SHA must be 40 lowercase hexadecimal characters")
    if SHA_PATTERN.fullmatch(backend_package_commit) is None:
        raise ValueError(
            "backend package commit must be 40 lowercase hexadecimal characters"
        )
    if SIGNING_KEY_VERSION_PATTERN.fullmatch(signing_key_version or "") is None:
        raise ValueError("signing key version must be a safe non-empty reference")
    workflow_run_url = _require_https(workflow_run_url, "workflow run URL")
    manifest = _load_template()
    manifest.update(
        {
            "source_sha": source_sha,
            "frontend_release_sha": source_sha,
            "backend_release_sha": source_sha,
            "contract_version": CONTRACT_VERSION,
            "assessment_version": ASSESSMENT_VERSION,
            "scoring_policy_version": SCORING_POLICY_VERSION,
            "backend_package_commit": backend_package_commit,
            "frontend_url": _require_https(frontend_url, "frontend URL"),
            "frontend_deployment_url": _require_https(
                frontend_deployment_url, "frontend deployment URL"
            ),
            "backend_url": _require_https(backend_url, "backend URL"),
            "signing_key_version": signing_key_version,
            "smoke_status": "passed",
            "workflow_run_url": workflow_run_url,
            "recorded_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
    )
    output.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--frontend-url", required=True)
    parser.add_argument("--frontend-deployment-url", required=True)
    parser.add_argument("--backend-url", required=True)
    parser.add_argument("--backend-package-commit", required=True)
    parser.add_argument("--signing-key-version", required=True)
    parser.add_argument("--workflow-run-url", required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit("refusing to overwrite an existing release manifest")
    write_manifest(
        args.output,
        args.source_sha,
        args.frontend_url,
        args.frontend_deployment_url,
        args.backend_url,
        args.backend_package_commit,
        args.signing_key_version,
        args.workflow_run_url,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
