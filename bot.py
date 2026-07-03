"""
Bot assembly - construye el telegram.ext.Application y registra todos los handlers
"""
import asyncio
import logging
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler

from src.config import TOKEN, VERSION
from src import setup_logging, ensure_dirs, db, plugin_manager, stats
from src.utils import is_owner

# Import all handlers
from handlers.commands import (
    start_cmd, help_cmd, status_cmd, version_cmd, uptime_cmd, restart_cmd,
    ps_cmd, kill_cmd, top_cmd, ping_cmd, dns_cmd, ports_cmd, battery_cmd, apps_cmd,
    files_cmd, read_cmd, write_cmd, find_cmd,
    git_status_cmd, git_pull_cmd, git_commit_cmd, git_push_cmd, git_log_cmd,
    docker_ps_cmd, docker_stats_cmd, docker_logs_cmd,
    plugins_cmd, load_plugin_cmd,
    persona_cmd, learn_cmd, forget_cmd, improve_cmd, exec_code_cmd,
    weather_cmd, shorten_cmd, paste_cmd, getpaste_cmd,
    backup_cmd, backup_list_cmd, rollback_cmd,
    encrypt_cmd, decrypt_cmd, memory_cmd, clear_cmd, activity_cmd,
    stats_cmd, rate_limit_cmd,
    heartbeat_cmd, heartbeat_on_cmd, heartbeat_off_cmd, heartbeat_stats_cmd,
    cron_list_cmd, cron_enable_cmd, cron_disable_cmd,
    agent_check_cmd, screenshot_cmd,
    rss_cmd, summarize_cmd, remind_cmd, reminders_cmd,
)
from handlers.callbacks import callback_handler
from handlers.messages import msg_handler
from handlers.documents import doc_handler, photo_handler
from handlers.voice import voice_handler
from handlers.errors import error_handler

# Import services for cron
from services.scheduler import cron_scheduler
from services.heartbeat import heartbeat
from services.health import health_checker

# Declarative command registry. Adding a new command = one line here.
# (cmd_name, handler) — see handlers/commands.py for handler bodies.
COMMAND_REGISTRY = [
    # Info
    ("start", start_cmd), ("help", help_cmd), ("status", status_cmd),
    ("version", version_cmd), ("uptime", uptime_cmd), ("agent_check", agent_check_cmd),
    # System
    ("ps", ps_cmd), ("kill", kill_cmd), ("top", top_cmd), ("ping", ping_cmd),
    ("dns", dns_cmd), ("ports", ports_cmd), ("battery", battery_cmd), ("apps", apps_cmd),
    # Files
    ("files", files_cmd), ("read", read_cmd), ("write", write_cmd), ("find", find_cmd),
    # Git
    ("git_status", git_status_cmd), ("git_pull", git_pull_cmd), ("git_commit", git_commit_cmd),
    ("git_push", git_push_cmd), ("git_log", git_log_cmd),
    # Docker
    ("docker_ps", docker_ps_cmd), ("docker_stats", docker_stats_cmd), ("docker_logs", docker_logs_cmd),
    # Plugin
    ("plugins", plugins_cmd), ("load_plugin", load_plugin_cmd),
    # AI & Learning
    ("persona", persona_cmd), ("learn", learn_cmd), ("forget", forget_cmd),
    ("improve", improve_cmd), ("exec_code", exec_code_cmd),
    # Web
    ("weather", weather_cmd), ("shorten", shorten_cmd), ("rss", rss_cmd), ("summarize", summarize_cmd),
    # Data
    ("paste", paste_cmd), ("getpaste", getpaste_cmd),
    ("remind", remind_cmd), ("reminders", reminders_cmd),
    # Backup
    ("backup", backup_cmd), ("backup_list", backup_list_cmd), ("rollback", rollback_cmd),
    # Security
    ("encrypt", encrypt_cmd), ("decrypt", decrypt_cmd), ("memory", memory_cmd),
    ("clear", clear_cmd), ("activity", activity_cmd),
    # Stats
    ("stats", stats_cmd), ("rate_limit", rate_limit_cmd),
    # Heartbeat
    ("heartbeat", heartbeat_cmd), ("heartbeat_on", heartbeat_on_cmd),
    ("heartbeat_off", heartbeat_off_cmd), ("heartbeat_stats", heartbeat_stats_cmd),
    # Cron
    ("cron_list", cron_list_cmd), ("cron_enable", cron_enable_cmd), ("cron_disable", cron_disable_cmd),
    # Misc
    ("screenshot", screenshot_cmd), ("restart", restart_cmd),
]


def build_app():
    """Build and configure the Application using COMMAND_REGISTRY."""
    setup_logging()
    ensure_dirs()
    logger = logging.getLogger(__name__)

    logger.info(f"Building MiraiDroid v{VERSION}...")

    app = Application.builder().token(TOKEN).build()

    # Register all commands from the declarative list
    for cmd_name, handler in COMMAND_REGISTRY:
        app.add_handler(CommandHandler(cmd_name, handler))

    # Callbacks
    app.add_handler(CallbackQueryHandler(callback_handler))

    # Message handlers (order matters: more specific first)
    app.add_handler(MessageHandler(filters.Document.ALL, doc_handler))
    app.add_handler(MessageHandler(filters.PHOTO, photo_handler))
    app.add_handler(MessageHandler(filters.VOICE, voice_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, msg_handler))

    # Error handler
    app.add_error_handler(error_handler)

    # Register cron jobs
    cron_scheduler.add_job("heartbeat", 1800, heartbeat.beat)
    cron_scheduler.add_job("health_check", 1800, health_checker.check)

    # Start cron scheduler as a background task (runs alongside the bot)
    async def post_init(application):
        asyncio.create_task(cron_scheduler.run(application))
        logger.info("Cron scheduler started in background")

    async def post_shutdown(application):
        cron_scheduler.running = False
        logger.info("Cron scheduler stopped")

    app.post_init = post_init
    app.post_shutdown = post_shutdown

    logger.info(f"MiraiDroid built successfully ({len(COMMAND_REGISTRY)} commands registered)")
    return app


def get_app():
    return build_app()