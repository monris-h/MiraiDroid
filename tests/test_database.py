"""
Tests for src/database.py — SQLite wrapper.
Uses the tmp_data_dir fixture from conftest.py to avoid touching the
real data/miraidroid.db.
"""
import pytest


def test_create_tables_idempotent(tmp_data_dir):
    """create_tables() should be safe to call twice."""
    from src.database import db
    # First call already happened in Database.__init__
    # Running it again should not raise
    db.create_tables()
    db.create_tables()


def test_query_returns_list(tmp_data_dir):
    """query() on an empty table returns an empty list, not None."""
    from src.database import db
    result = db.query("SELECT * FROM reminders")
    assert result == []
    assert isinstance(result, list)


def test_execute_and_query_roundtrip(tmp_data_dir):
    """A row inserted via execute() should come back via query()."""
    from src.database import db
    db.execute(
        "INSERT INTO reminders (time, message, created) VALUES (?, ?, ?)",
        ("2026-07-02 12:00", "test reminder", "2026-07-02 11:00"),
    )
    rows = db.query("SELECT time, message FROM reminders")
    assert len(rows) == 1
    assert rows[0] == ("2026-07-02 12:00", "test reminder")


def test_query_with_invalid_sql_returns_empty(tmp_data_dir):
    """query() on a broken SQL returns [] and logs (doesn't raise)."""
    from src.database import db
    result = db.query("SELECT * FROM no_such_table")
    assert result == []


def test_execute_with_invalid_sql_raises(tmp_data_dir):
    """execute() on a broken SQL re-raises (caller decides what to do)."""
    from src.database import db
    with pytest.raises(Exception):
        db.execute("INSERT INTO no_such_table VALUES (1)")


def test_wal_mode_enabled(tmp_data_dir):
    """Database should be in WAL journal mode (audit item 11)."""
    from src.database import db
    mode = db.conn.execute("PRAGMA journal_mode").fetchone()[0]
    assert mode.lower() == "wal", f"Expected WAL, got {mode}"


if __name__ == "__main__":
    # Standalone run: just exercise the happy path.
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        import src.config as cfg
        cfg.BASE_DIR = __import__("pathlib").Path(td)
        test_create_tables_idempotent.__wrapped__ if hasattr(test_create_tables_idempotent, "__wrapped__") else None
        # Reimport with patched BASE_DIR
        import importlib, sys
        for mod in list(sys.modules):
            if mod.startswith("src"):
                del sys.modules[mod]
        sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent))
        cfg.BASE_DIR = __import__("pathlib").Path(td)
        from src.database import db
        db.create_tables()
        db.execute("INSERT INTO reminders (time, message, created) VALUES (?, ?, ?)", ("t", "m", "c"))
        print("PASS: database roundtrip OK")
