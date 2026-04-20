"""
Bot assembly - construye el telegram.ext.Application y registra todos los handlers
"""
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
    rss_cmd, summarize_cmd, remind_cmd, reminders_cmd
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


def build_app():
    """Construye y configura el Application"""
    setup_logging()
    ensure_dirs()
    logger = logging.getLogger(__name__)

    logger.info(f"Building MiraiDroid v{VERSION}...")

    app = Application.builder().token(TOKEN).build()

    # Info commands
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("status", status_cmd))
    app.add_handler(CommandHandler("version", version_cmd))
    app.add_handler(CommandHandler("uptime", uptime_cmd))
    app.add_handler(CommandHandler("restart", restart_cmd))
    app.add_handler(CommandHandler("agent_check", agent_check_cmd))

    # System commands
    app.add_handler(CommandHandler("ps", ps_cmd))
    app.add_handler(CommandHandler("kill", kill_cmd))
    app.add_handler(CommandHandler("top", top_cmd))
    app.add_handler(CommandHandler("ping", ping_cmd))
    app.add_handler(CommandHandler("dns", dns_cmd))
    app.add_handler(CommandHandler("ports", ports_cmd))
    app.add_handler(CommandHandler("battery", battery_cmd))
    app.add_handler(CommandHandler("apps", apps_cmd))

    # File commands
    app.add_handler(CommandHandler("files", files_cmd))
    app.add_handler(CommandHandler("read", read_cmd))
    app.add_handler(CommandHandler("write", write_cmd))
    app.add_handler(CommandHandler("find", find_cmd))

    # Git commands
    app.add_handler(CommandHandler("git_status", git_status_cmd))
    app.add_handler(CommandHandler("git_pull", git_pull_cmd))
    app.add_handler(CommandHandler("git_commit", git_commit_cmd))
    app.add_handler(CommandHandler("git_push", git_push_cmd))
    app.add_handler(CommandHandler("git_log", git_log_cmd))

    # Docker commands
    app.add_handler(CommandHandler("docker_ps", docker_ps_cmd))
    app.add_handler(CommandHandler("docker_stats", docker_stats_cmd))
    app.add_handler(CommandHandler("docker_logs", docker_logs_cmd))

    # Plugin commands
    app.add_handler(CommandHandler("plugins", plugins_cmd))
    app.add_handler(CommandHandler("load_plugin", load_plugin_cmd))

    # AI & Learning commands
    app.add_handler(CommandHandler("persona", persona_cmd))
    app.add_handler(CommandHandler("learn", learn_cmd))
    app.add_handler(CommandHandler("forget", forget_cmd))
    app.add_handler(CommandHandler("improve", improve_cmd))
    app.add_handler(CommandHandler("exec_code", exec_code_cmd))

    # Web commands
    app.add_handler(CommandHandler("weather", weather_cmd))
    app.add_handler(CommandHandler("shorten", shorten_cmd))
    app.add_handler(CommandHandler("rss", rss_cmd))
    app.add_handler(CommandHandler("summarize", summarize_cmd))

    # Data commands
    app.add_handler(CommandHandler("paste", paste_cmd))
    app.add_handler(CommandHandler("getpaste", getpaste_cmd))
    app.add_handler(CommandHandler("remind", remind_cmd))
    app.add_handler(CommandHandler("reminders", reminders_cmd))

    # Backup commands
    app.add_handler(CommandHandler("backup", backup_cmd))
    app.add_handler(CommandHandler("backup_list", backup_list_cmd))
    app.add_handler(CommandHandler("rollback", rollback_cmd))

    # Security commands
    app.add_handler(CommandHandler("encrypt", encrypt_cmd))
    app.add_handler(CommandHandler("decrypt", decrypt_cmd))
    app.add_handler(CommandHandler("memory", memory_cmd))
    app.add_handler(CommandHandler("clear", clear_cmd))
    app.add_handler(CommandHandler("activity", activity_cmd))

    # Stats commands
    app.add_handler(CommandHandler("stats", stats_cmd))
    app.add_handler(CommandHandler("rate_limit", rate_limit_cmd))

    # Heartbeat commands
    app.add_handler(CommandHandler("heartbeat", heartbeat_cmd))
    app.add_handler(CommandHandler("heartbeat_on", heartbeat_on_cmd))
    app.add_handler(CommandHandler("heartbeat_off", heartbeat_off_cmd))
    app.add_handler(CommandHandler("heartbeat_stats", heartbeat_stats_cmd))

    # Cron commands
    app.add_handler(CommandHandler("cron_list", cron_list_cmd))
    app.add_handler(CommandHandler("cron_enable", cron_enable_cmd))
    app.add_handler(CommandHandler("cron_disable", cron_disable_cmd))

    # Screenshot
    app.add_handler(CommandHandler("screenshot", screenshot_cmd))

    # Callbacks
    app.add_handler(CallbackQueryHandler(callback_handler))

    # Message handlers
    app.add_handler(MessageHandler(filters.Document.ALL, doc_handler))
    app.add_handler(MessageHandler(filters.PHOTO, photo_handler))
    app.add_handler(MessageHandler(filters.VOICE, voice_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, msg_handler))

    # Error handler
    app.add_error_handler(error_handler)

    # Register cron jobs
    cron_scheduler.add_job("heartbeat", 1800, heartbeat.beat)
    cron_scheduler.add_job("health_check", 1800, health_checker.check)

    logger.info("MiraiDroid built successfully")

    return app


# Export app builder
def get_app():
    return build_app()