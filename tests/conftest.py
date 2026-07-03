"""
Shared pytest fixtures and path setup for the MiraiDroid test suite.

Adding this file means individual test_*.py files no longer need to
muck with sys.path manually.
"""
import os
import sys
from pathlib import Path

import pytest

# Add project root to sys.path once, so `from src.x import y` works.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture
def tmp_data_dir(tmp_path, monkeypatch):
    """Redirect all data/* paths to a temp dir for the duration of the test.

    Tests that touch memory.json / activity.json / stats.json / the SQLite
    database should use this fixture to avoid polluting the real data dir.
    """
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    # Patch BASE_DIR-derived paths at the module level.
    # Each module computes its own path on import, so we patch the source
    # of truth: src.config.BASE_DIR.
    monkeypatch.setattr("src.config.BASE_DIR", tmp_path)
    return data_dir
