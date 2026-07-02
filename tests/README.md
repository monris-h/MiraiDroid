# Tests for MiraiDroid

Run all tests with:
    pytest tests/

Or individually:
    python tests/test_utils.py
    python tests/test_rate_limiter.py
    python tests/test_crypto.py

## What's covered

- `test_utils.py` - platform detection (`is_windows`, `is_android`) and owner check
- `test_rate_limiter.py` - per-minute throttling, per-command cooldown, per-user isolation
- `test_crypto.py` - Fernet encrypt/decrypt roundtrip, wrong-key handling, unicode

## What's NOT covered yet

- `src/database.py` - SQLite wrapper (needs temp file fixture)
- `src/memory.py` - JSON persistence (needs temp dir fixture)
- `src/plugin_manager.py` - plugin auto-loading (needs plugins/ fixture)
- `services/ai.py` - MiniMax + Groq integration (network-dependent)
- `services/web_search.py` - Tavily + DDG (network-dependent)

Network-dependent tests should be marked with `@pytest.mark.skipif` or
gated behind an env var to avoid running them in CI without credentials.