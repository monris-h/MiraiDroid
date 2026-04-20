"""
Callback handlers - inline keyboard callbacks
"""
from telegram import Update
from telegram.ext import ContextTypes


async def callback_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    from handlers.commands import status_cmd, help_cmd, git_pull_cmd, activity_cmd
    from src.utils import is_windows
    import subprocess

    query = update.callback_query
    await query.answer()

    if query.data == "status":
        await status_cmd(update, ctx)
    elif query.data == "help":
        await help_cmd(update, ctx)
    elif query.data == "disk":
        from src.system_tools import system_info
        await update.message.reply_text(system_info.get_disk())
    elif query.data == "git_pull":
        await git_pull_cmd(update, ctx)
    elif query.data == "logs":
        await activity_cmd(update, ctx)
    elif query.data == "search":
        await update.message.reply_text("Usa /search [tema] para buscar")