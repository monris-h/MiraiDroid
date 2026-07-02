"""
Tests for src/rate_limiter.py - per-minute and per-command throttling.
"""
import os
import sys
import time
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_allows_under_limit():
    """First N messages within a minute should be allowed."""
    from src.rate_limiter import RateLimiter
    rl = RateLimiter()
    rl.max_per_minute = 5

    for i in range(5):
        assert rl.is_allowed("user1") is True, f"Message {i+1} should be allowed"


def test_blocks_over_limit():
    """Once over the per-minute limit, further messages should be blocked."""
    from src.rate_limiter import RateLimiter
    rl = RateLimiter()
    rl.max_per_minute = 3

    assert rl.is_allowed("user1") is True
    assert rl.is_allowed("user1") is True
    assert rl.is_allowed("user1") is True
    assert rl.is_allowed("user1") is False, "4th message should be blocked"


def test_per_user_isolation():
    """Rate limit should be per-user, not global."""
    from src.rate_limiter import RateLimiter
    rl = RateLimiter()
    rl.max_per_minute = 2

    assert rl.is_allowed("alice") is True
    assert rl.is_allowed("alice") is True
    assert rl.is_allowed("alice") is False
    # bob still has his full quota
    assert rl.is_allowed("bob") is True
    assert rl.is_allowed("bob") is True


def test_command_cooldown():
    """Same command within 5s should be blocked."""
    from src.rate_limiter import RateLimiter
    rl = RateLimiter()

    assert rl.is_allowed("user1", "status") is True
    assert rl.is_allowed("user1", "status") is False, "Same command within 5s should be blocked"


def test_different_commands_no_cooldown():
    """Different commands should not trigger the cooldown."""
    from src.rate_limiter import RateLimiter
    rl = RateLimiter()

    assert rl.is_allowed("user1", "status") is True
    assert rl.is_allowed("user1", "help") is True
    assert rl.is_allowed("user1", "ping") is True


def test_remaining_count():
    """get_remaining() should report remaining quota."""
    from src.rate_limiter import RateLimiter
    rl = RateLimiter()
    rl.max_per_minute = 10

    assert rl.get_remaining("user1") == 10
    rl.is_allowed("user1")
    rl.is_allowed("user1")
    assert rl.get_remaining("user1") == 8


if __name__ == "__main__":
    test_allows_under_limit()
    test_blocks_over_limit()
    test_per_user_isolation()
    test_command_cooldown()
    test_different_commands_no_cooldown()
    test_remaining_count()
    print("✅ All rate_limiter tests passed")