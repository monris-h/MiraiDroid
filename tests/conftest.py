"""
Shared pytest fixtures and path setup for the MiraiDroid test suite.

Adding this file means individual test_*.py files no longer need to
muck with sys.path manually.
"""
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

    Note on isolation: src.database, src.memory, src.stats all create
    module-level singletons at import time, so reloading them mid-test
    is fragile (consumers keep stale references). Instead, this fixture
    is paired with a `clean_db` autouse fixture that wipes tables between
    tests — simpler and works regardless of import order.
    """
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    monkeypatch.setattr("src.config.BASE_DIR", tmp_path)
    return data_dir


@pytest.fixture(autouse=True)
def _clean_state(tmp_data_dir):
    """Auto-applied: clear all mutable singletons before each test.

    Prevents cross-test contamination when tests share the same singleton
    (e.g. src.database.db) and the same on-disk path.
    """
    try:
        from src.database import db
        for table in ("reminders", "scheduled_messages", "url_cache", "pastebin", "plugins"):
            try:
                db.execute(f"DELETE FROM {table}")
            except Exception:
                pass
    except Exception:
        pass  # src.database not yet imported or init failed

    try:
        from src.memory import memory, activity_log
        memory.data = {"history": [], "skills": [], "tools": [], "persona": "default", "conversations": {}, "learning": [], "version": memory.data.get("version", "test")}
        activity_log.data = {"actions": []}
    except Exception:
        pass

    yield
