"""MiraiDroid src package"""
from .config import TOKEN, MINIMAX_KEY, OWNER_ID, TAVILY_API_KEY, GROQ_API_KEY, BASE_DIR, VERSION, CONFIG
from .constants import PERSONAS, ALIASES, DIRS
from .database import db, Database
from .crypto import Crypto
from .memory import memory, activity_log, Memory, ActivityLog
from .utils import is_owner, is_windows, is_android, ensure_dirs, setup_logging
from .rate_limiter import rate_limiter, RateLimiter
from .stats import stats, Stats
from .system_tools import (
    file_manager, git_manager, docker_monitor, process_manager,
    battery_monitor, app_manager, network_tools, screenshot, image_analyzer, natural_exec,
    system_info, SystemInfo
)
from .plugin_manager import plugin_manager, PluginManager
from .skill_manager import skill_manager, SkillManager

__all__ = [
    # config
    "TOKEN", "MINIMAX_KEY", "OWNER_ID", "TAVILY_API_KEY", "GROQ_API_KEY", "BASE_DIR", "VERSION", "CONFIG",
    # constants
    "PERSONAS", "ALIASES", "DIRS",
    # database
    "db", "Database",
    # crypto
    "Crypto",
    # memory
    "memory", "activity_log", "Memory", "ActivityLog",
    # utils
    "is_owner", "is_windows", "is_android", "ensure_dirs", "setup_logging",
    # rate limiter
    "rate_limiter", "RateLimiter",
    # stats
    "stats", "Stats",
    # system tools
    "file_manager", "git_manager", "docker_monitor", "process_manager",
    "battery_monitor", "app_manager", "network_tools", "screenshot", "image_analyzer", "natural_exec",
    # managers
    "plugin_manager", "PluginManager",
    "skill_manager", "SkillManager",
]