"""
Configuración central - carga .env y credenciales
"""
import os
from pathlib import Path

BASE_DIR = Path.home() / "agent"
ENV_FILE = BASE_DIR / ".env"
VERSION = "5.8.0"

def load_env():
    """Load config from .env file - ALL CREDENTIALS MUST BE IN .ENV"""
    if not ENV_FILE.exists():
        raise RuntimeError(
            ".env file not found! Copy .env.example to .env and fill in all credentials:\n"
            "- TOKEN\n- MINIMAX_KEY\n- OWNER_ID\n- TAVILY_API_KEY\n- GROQ_API_KEY"
        )

    config = {}
    for line in ENV_FILE.read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            key, val = line.split("=", 1)
            config[key.strip()] = val.strip().strip('"').strip("'")

    required = ["TOKEN", "MINIMAX_KEY", "OWNER_ID", "TAVILY_API_KEY", "GROQ_API_KEY"]
    missing = [k for k in required if k not in config or not config[k]]
    if missing:
        raise RuntimeError(f"Missing required .env keys: {missing}")

    return config

CONFIG = load_env()
TOKEN = CONFIG["TOKEN"]
MINIMAX_KEY = CONFIG["MINIMAX_KEY"]
OWNER_ID = CONFIG["OWNER_ID"]
TAVILY_API_KEY = CONFIG.get("TAVILY_API_KEY")
GROQ_API_KEY = CONFIG.get("GROQ_API_KEY")