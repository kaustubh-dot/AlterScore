from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path
from typing import Iterator

import pytest


REPO_ROOT = Path(__file__).resolve().parent.parent
TEST_TMP_ROOT = REPO_ROOT / ".tmp" / "pytest-workspace"

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


@pytest.fixture
def tmp_path() -> Iterator[Path]:
    """Provide a workspace-local temp directory without relying on global temp paths."""

    TEST_TMP_ROOT.mkdir(parents=True, exist_ok=True)
    path = Path(tempfile.mkdtemp(prefix="pytest-", dir=TEST_TMP_ROOT))
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)
