"""
Tests for src/utils.py - platform detection and owner check.
"""
import os
import sys
from unittest.mock import patch

# Add parent directory to path so we can import src
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_is_windows_on_windows():
    """is_windows() should return True on Windows."""
    with patch("platform.system", return_value="Windows"):
        from src.utils import is_windows
        assert is_windows() is True


def test_is_windows_on_linux():
    """is_windows() should return False on Linux."""
    with patch("platform.system", return_value="Linux"):
        from src.utils import is_windows
        assert is_windows() is False


def test_is_android_on_termux():
    """is_android() should return True on Termux (Linux + /data/data/com.termux)."""
    with patch("platform.system", return_value="Linux"), \
         patch("os.path.exists", return_value=True):
        from src.utils import is_android
        assert is_android() is True


def test_is_android_on_regular_linux():
    """is_android() should return False on regular Linux."""
    with patch("platform.system", return_value="Linux"), \
         patch("os.path.exists", return_value=False):
        from src.utils import is_android
        assert is_android() is False


def test_is_android_on_windows():
    """is_android() should return False on Windows even if the path exists."""
    with patch("platform.system", return_value="Windows"), \
         patch("os.path.exists", return_value=True):
        from src.utils import is_android
        assert is_android() is False


def test_is_owner_match():
    """is_owner() should match when user_id equals OWNER_ID."""
    with patch("src.utils.OWNER_ID", "123456"):
        from src.utils import is_owner
        assert is_owner("123456") is True
        assert is_owner(123456) is True


def test_is_owner_no_match():
    """is_owner() should not match when user_id differs."""
    with patch("src.utils.OWNER_ID", "123456"):
        from src.utils import is_owner
        assert is_owner("999") is False
        assert is_owner(123) is False


if __name__ == "__main__":
    test_is_windows_on_windows()
    test_is_windows_on_linux()
    test_is_android_on_termux()
    test_is_android_on_regular_linux()
    test_is_android_on_windows()
    test_is_owner_match()
    test_is_owner_no_match()
    print("✅ All utils tests passed")