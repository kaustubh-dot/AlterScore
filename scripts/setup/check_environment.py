"""Preflight checks for a fresh AlterScore local setup."""

from __future__ import annotations

import shutil
import subprocess
import sys

SUPPORTED_PYTHON = (3, 12)
MIN_NODE_MAJOR = 18


def _parse_major(version_text: str) -> int | None:
    digits = []
    for char in version_text.strip():
        if char.isdigit():
            digits.append(char)
            continue
        if digits:
            break
    if not digits:
        return None
    return int("".join(digits))


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []

    if sys.version_info[:2] != SUPPORTED_PYTHON:
        errors.append(
            "Python "
            f"{sys.version_info.major}.{sys.version_info.minor} detected. "
            "AlterScore currently supports Python 3.12.x for local setup."
        )

    node_path = shutil.which("node")
    if node_path is None:
        warnings.append(
            "Node.js was not found on PATH. Install Node.js 18+ for the frontend."
        )
    else:
        try:
            completed = subprocess.run(
                [node_path, "--version"],
                check=True,
                capture_output=True,
                text=True,
            )
        except Exception as exc:  # pragma: no cover - defensive only
            warnings.append(f"Unable to query Node.js version: {exc}")
        else:
            node_major = _parse_major(completed.stdout.lstrip("v"))
            if node_major is None or node_major < MIN_NODE_MAJOR:
                warnings.append(
                    "Node.js "
                    f"{completed.stdout.strip()} detected. AlterScore expects Node.js 18+."
                )

    if errors:
        print("AlterScore environment check: FAILED")
        for item in errors:
            print(f"- {item}")
        if warnings:
            for item in warnings:
                print(f"- {item}")
        print(
            "Recommendation: install Python 3.12, create a new virtual environment, "
            "then install backend/frontend dependencies."
        )
        return 1

    print("AlterScore environment check: OK")
    print("- Python 3.12.x detected.")
    if warnings:
        for item in warnings:
            print(f"- {item}")
    else:
        print("- Node.js 18+ detected or not required for this step.")
    if sys.platform.startswith("win"):
        print(
            "- On Windows PowerShell, prefer `npm.cmd` instead of `npm` if script execution is blocked."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
