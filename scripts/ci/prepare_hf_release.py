"""Prepare a secret-free Hugging Face release package for one Git SHA."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
from pathlib import Path


SHA_PATTERN = re.compile(r"[0-9a-f]{40}")
CONTRACT_VERSION = "2.0"
ASSESSMENT_VERSION = "india-en-3.0.0"
SCORING_POLICY_VERSION = "readiness-rubric-1.0.0"


def _validate_sha(value: str) -> str:
    if SHA_PATTERN.fullmatch(value) is None:
        raise ValueError("release SHA must be 40 lowercase hexadecimal characters")
    return value


def _git(source_root: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    """Run a Git query without exposing repository output in raised errors."""

    try:
        return subprocess.run(
            ("git", "-C", str(source_root), *arguments),
            check=False,
            capture_output=True,
            encoding="utf-8",
            text=True,
        )
    except OSError as error:
        raise ValueError("release source must be a Git checkout") from error


def _require_exact_clean_source(
    source_root: Path, release_sha: str
) -> tuple[Path, ...]:
    """Return tracked serving modules for exactly the requested clean commit.

    Packaging every ``*.py`` found in a working tree would let an ignored or
    untracked module enter the public image.  The deployment identity must
    instead be the checked-out Git tree named by ``release_sha``.
    """

    root = _git(source_root, "rev-parse", "--show-toplevel")
    if root.returncode != 0 or Path(root.stdout.strip()).resolve() != source_root:
        raise ValueError("release source must be the root of a Git checkout")

    head = _git(source_root, "rev-parse", "HEAD")
    if head.returncode != 0 or head.stdout.strip() != release_sha:
        raise ValueError("release SHA must match the checked-out Git commit")

    for arguments in (
        (
            "diff",
            "--quiet",
            "--",
            "Dockerfile",
            "backend/app",
            "backend/requirements.txt",
        ),
        (
            "diff",
            "--cached",
            "--quiet",
            "--",
            "Dockerfile",
            "backend/app",
            "backend/requirements.txt",
        ),
    ):
        clean = _git(source_root, *arguments)
        if clean.returncode not in {0, 1}:
            raise ValueError("could not inspect release source cleanliness")
        if clean.returncode != 0:
            raise ValueError("release source has uncommitted serving inputs")

    tracked = _git(
        source_root,
        "ls-files",
        "-z",
        "--",
        "Dockerfile",
        "backend/requirements.txt",
        "backend/app",
    )
    if tracked.returncode != 0:
        raise ValueError("could not enumerate tracked serving inputs")
    tracked_names = tuple(name for name in tracked.stdout.split("\0") if name)
    required_names = {"Dockerfile", "backend/requirements.txt"}
    if not required_names.issubset(tracked_names):
        raise ValueError("Dockerfile and backend requirements must be Git tracked")

    modules: list[Path] = []
    for name in tracked_names:
        relative = Path(name)
        if not name.startswith("backend/app/") or relative.suffix != ".py":
            continue
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("tracked serving module path is invalid")
        modules.append(source_root / relative)
    if not modules:
        raise ValueError("serving application must contain tracked Python modules")
    return tuple(modules)


def _copy_serving_application(
    source_root: Path, output_dir: Path, modules: tuple[Path, ...]
) -> None:
    """Copy only regular Python modules needed by the public serving graph.

    This release package is uploaded to a public provider.  It must never
    inherit ignored working-tree content such as local environments, caches,
    archived research, runtime output, or dotenv files merely because they are
    beneath ``backend/``.
    """

    source_backend = source_root / "backend"
    source_app = source_backend / "app"
    requirements = source_backend / "requirements.txt"
    if (
        not source_app.is_dir()
        or source_app.is_symlink()
        or not requirements.is_file()
        or requirements.is_symlink()
    ):
        raise ValueError(
            "source root must contain regular backend/app and requirements.txt"
        )

    destination_backend = output_dir / "backend"
    destination_app = destination_backend / "app"
    destination_backend.mkdir(parents=True)
    shutil.copy2(requirements, destination_backend / "requirements.txt")

    for source_path in modules:
        if source_path.is_symlink() or not source_path.is_file():
            raise ValueError("serving application must not contain Python symlinks")
        if not source_path.resolve().is_relative_to(source_app.resolve()):
            raise ValueError("serving application path escapes backend/app")
        destination = destination_app / source_path.relative_to(source_app)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, destination)

    if not (destination_app / "main.py").is_file():
        raise ValueError("serving application must contain backend/app/main.py")


def prepare_package(
    source_root: Path, output_dir: Path, release_sha: str, signing_key_version: str
) -> None:
    release_sha = _validate_sha(release_sha)
    if not signing_key_version or any(char in signing_key_version for char in "\r\n"):
        raise ValueError("signing key version must be a non-empty single line")
    if output_dir.exists():
        raise ValueError(
            f"refusing to overwrite existing output directory: {output_dir}"
        )

    modules = _require_exact_clean_source(source_root, release_sha)
    output_dir.mkdir(parents=True)
    _copy_serving_application(source_root, output_dir, modules)
    dockerfile = (source_root / "Dockerfile").read_text(encoding="utf-8")
    release_marker = "ARG ALTERSCORE_RELEASE_SHA=local"
    signing_key_marker = "ARG ALTERSCORE_SIGNING_KEY_VERSION=local"
    if dockerfile.count(release_marker) != 1:
        raise ValueError("Dockerfile must contain exactly one local release SHA marker")
    if dockerfile.count(signing_key_marker) != 1:
        raise ValueError(
            "Dockerfile must contain exactly one local signing key version marker"
        )
    (output_dir / "Dockerfile").write_text(
        dockerfile.replace(
            release_marker, f"ARG ALTERSCORE_RELEASE_SHA={release_sha}"
        ).replace(
            signing_key_marker,
            f"ARG ALTERSCORE_SIGNING_KEY_VERSION={signing_key_version}",
        ),
        encoding="utf-8",
    )

    metadata = {
        "source_sha": release_sha,
        "frontend_release_sha": release_sha,
        "backend_release_sha": release_sha,
        "contract_version": CONTRACT_VERSION,
        "assessment_version": ASSESSMENT_VERSION,
        "scoring_policy_version": SCORING_POLICY_VERSION,
        "signing_key_version": signing_key_version,
    }
    (output_dir / "release-metadata.json").write_text(
        json.dumps(metadata, indent=2) + "\n", encoding="utf-8"
    )
    (output_dir / "README.md").write_text(
        "\n".join(
            [
                "---",
                "title: AlterScore Public API",
                "emoji: 📊",
                "colorFrom: green",
                "colorTo: blue",
                "sdk: docker",
                "app_port: 7860",
                "pinned: false",
                "---",
                "",
                "# AlterScore Public API",
                "",
                "Artifact-free deterministic v2 assessment API for AlterScore.",
                "",
                f"Release source SHA: {release_sha}",
                "",
                "The deployment must provide ALTERSCORE_SIGNING_SECRET,",
                "and the approved CORS settings as runtime configuration. The",
                "package binds its non-secret signing-key version; no signing",
                "secret is stored in this package.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--release-sha", required=True)
    parser.add_argument("--signing-key-version", required=True)
    args = parser.parse_args()
    prepare_package(
        args.source_root.resolve(),
        args.output.resolve(),
        args.release_sha,
        args.signing_key_version,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
