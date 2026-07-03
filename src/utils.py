"""
Utilities compartidas - helpers usados en todo el proyecto
"""
import functools
import os
import sys
import platform
import logging
from pathlib import Path
from .config import BASE_DIR, OWNER_ID

logger = logging.getLogger(__name__)


def owner_only(fn):
    """Decorator: silently drop non-owner updates.

    Use on Telegram handler coroutines. The handler still runs for the
    owner; for everyone else it returns without replying (consistent with
    the original `if not is_owner: return` pattern).
    """
    @functools.wraps(fn)
    async def wrapper(update, ctx, *args, **kwargs):
        from .utils import is_owner
        if update and update.effective_user and not is_owner(update.effective_user.id):
            return None
        return await fn(update, ctx, *args, **kwargs)
    return wrapper


def is_windows():
    return platform.system() == "Windows"

def is_android():
    return platform.system() == "Linux" and os.path.exists("/data/data/com.termux")

def is_owner(user_id):
    """Owner check. Accepts int or str, returns False on mismatch.

    Compares as int to avoid silent mismatch if OWNER_ID comes in as a
    different type than user_id (e.g. one str and one int).
    """
    try:
        return int(user_id) == int(OWNER_ID)
    except (ValueError, TypeError):
        return False

def ensure_dirs():
    """Crear todos los directorios necesarios"""
    from .constants import DIRS
    for d in DIRS:
        d.mkdir(parents=True, exist_ok=True)

def setup_logging():
    """Configurar logging con archivo + consola"""
    ensure_dirs()
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s %(message)s',
        handlers=[
            logging.FileHandler(BASE_DIR / "logs" / "miraidroid.log"),
            logging.StreamHandler()
        ]
    )

def ensure_data_dir():
    """Alias simple para ensure_dirs"""
    ensure_dirs()