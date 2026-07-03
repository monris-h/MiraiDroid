"""
Constantes compartidas del proyecto
"""
from pathlib import Path
from .config import BASE_DIR, VERSION

PERSONAS = {
    "default": "Eres un asistente útil y conversacional en español.",
    "technical": "Eres un asistente técnico experto en programación y sistemas. Da respuestas técnicas detalladas.",
    "casual": "Eres un amigo informal que habla en español relaxed. Usa jerga y emojis casuales.",
    "formal": "Eres un asistente formal y profesional. Hablas en español formal."
}

ALIASES = {
    "l": "logs", "ls": "files", "cat": "read", "py": "python", "s": "status",
    "h": "help", "r": "rss", "w": "weather", "b": "backup", "p": "persona",
    "i": "improve", "gc": "git_commit", "gp": "git_pull", "gs": "git_status",
    "dps": "docker_ps", "dlog": "docker_logs", "hb": "heartbeat",
    "hbon": "heartbeat_on", "hboff": "heartbeat_off", "hbstats": "heartbeat_stats",
    "st": "stats", "rl": "rate_limit",
}

# Centralized model identifiers (Item 20 of audit 2026-07-02).
# Change here, not scattered across services/ai.py and src/system_tools.py.
MODELS = {
    "primary": "MiniMax-M2.7",        # text generation (MiniMax)
    "fallback": "llama-3.1-8b-instant",  # Groq fallback
    "vision": "MiniMax-M2.7",         # image analysis
    "whisper": "whisper-large-v3",    # Groq transcription
}

# Directorios del proyecto
DIRS = [
    BASE_DIR / "skills", BASE_DIR / "tools", BASE_DIR / "backups",
    BASE_DIR / "logs", BASE_DIR / "data", BASE_DIR / "plugins",
    BASE_DIR / "downloads"
]