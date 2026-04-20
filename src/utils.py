"""
Utilities compartidas - helpers usados en todo el proyecto
"""
import os
import sys
import platform
import logging
from pathlib import Path
from .config import BASE_DIR, OWNER_ID

logger = logging.getLogger(__name__)

def is_windows():
    return platform.system() == "Windows"

def is_android():
    return platform.system() == "Linux" and os.path.exists("/data/data/com.termux")

def is_owner(user_id):
    return str(user_id) == OWNER_ID

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