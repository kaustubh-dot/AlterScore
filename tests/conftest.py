from __future__ import annotations

import shutil
import sys
import tempfile
from os import environ
from pathlib import Path
from typing import Iterator

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


@pytest.fixture
def tmp_path() -> Iterator[Path]:
    """Use an explicit scratch root when available without model generation."""

    configured_root = environ.get("ALTERSCORE_TEST_TMP_ROOT")
    roots = (
        [Path(configured_root)] if configured_root else [Path(tempfile.gettempdir())]
    )
    path = None
    for root in roots:
        try:
            root.mkdir(parents=True, exist_ok=True)
            path = Path(tempfile.mkdtemp(prefix="alterscore-pytest-", dir=root))
            break
        except OSError:
            continue
    if path is None:
        path = Path(tempfile.mkdtemp(prefix="alterscore-pytest-"))
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)
