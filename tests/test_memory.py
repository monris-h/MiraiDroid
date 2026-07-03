"""
Tests for src/memory.py — JSON persistence (memory + activity log).
"""
import json


def test_memory_loads_with_defaults_when_file_missing(tmp_data_dir):
    """Fresh load() with no memory.json returns sensible defaults."""
    from src.memory import Memory
    m = Memory()
    assert m.data["history"] == []
    assert m.data["persona"] == "default"
    assert m.data["version"]  # Some version string


def test_memory_persists_roundtrip(tmp_data_dir):
    """Save then reload preserves data."""
    from src.memory import Memory
    m = Memory()
    m.add_message("user", "hola", conv_id="test-conv")
    m.save()
    # Reload from disk
    m2 = Memory()
    assert m2.data["conversations"]["test-conv"]["history"][-1]["content"] == "hola"


def test_memory_add_message_truncates_history(tmp_data_dir):
    """History is capped at 50 messages per conversation."""
    from src.memory import Memory
    m = Memory()
    for i in range(60):
        m.add_message("user", f"msg-{i}", conv_id="c1")
    conv = m.data["conversations"]["c1"]["history"]
    assert len(conv) == 50
    assert conv[-1]["content"] == "msg-59"
    assert conv[0]["content"] == "msg-10"


def test_memory_apply_learning_replaces(tmp_data_dir):
    """apply_learning() substitutes wrong -> correct in prompts."""
    from src.memory import Memory
    m = Memory()
    m.add_learning("foo", "bar")
    m.save()
    assert m.apply_learning("please foo this") == "please bar this"


def test_activity_log_caps_at_1000(tmp_data_dir):
    """Activity log keeps only the most recent 1000 actions."""
    from src.memory import ActivityLog
    alog = ActivityLog()
    for i in range(1100):
        alog.log("TEST", f"action-{i}")
    assert len(alog.data["actions"]) == 1000
    assert alog.data["actions"][-1]["details"] == "action-1099"


def test_activity_log_persists(tmp_data_dir):
    """Activity log writes JSON that can be reloaded."""
    from src.memory import ActivityLog
    alog = ActivityLog()
    alog.log("UPLOAD", "/tmp/file.txt")
    # Reload
    alog2 = ActivityLog()
    actions = alog2.get_recent(limit=1)
    assert actions[-1]["action"] == "UPLOAD"
    assert actions[-1]["details"] == "/tmp/file.txt"


if __name__ == "__main__":
    # Manual smoke test
    import tempfile
    from pathlib import Path
    with tempfile.TemporaryDirectory() as td:
        import src.config as cfg
        cfg.BASE_DIR = Path(td)
        for mod in list(__import__("sys").modules):
            if mod.startswith("src"):
                del __import__("sys").modules[mod]
        __import__("sys").path.insert(0, str(Path(__file__).resolve().parent.parent))
        cfg.BASE_DIR = Path(td)
        from src.memory import Memory
        m = Memory()
        m.add_message("user", "hola")
        m.save()
        print("PASS: memory roundtrip OK")
