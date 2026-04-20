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
        try:
            if is_windows():
                disk = subprocess.check_output("wmic logicaldisk get size,freespace,caption /format:list 2>nul | findstr C:", shell=True, text=True).strip()
            else:
                disk = subprocess.check_output("df -h / | tail -1 | awk '{print $3}'", shell=True, text=True).strip()
            await update.message.reply_text(f"💾 {disk}")
        except:
            pass
    elif query.data == "git_pull":
        await git_pull_cmd(update, ctx)
    elif query.data == "logs":
        await activity_cmd(update, ctx)
    elif query.data == "search":
        await update.message.reply_text("Usa /search [tema] para buscar")
    elif query.data == "search":
        pass