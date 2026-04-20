"""
Global error handler - catches all errors and reports to Telegram
"""
from telegram import Update
from telegram.ext import ContextTypes
import time
import traceback


async def error_handler(update, context):
    from src.config import OWNER_ID, VERSION
    from src.memory import stats

    error_msg = f"⚠️ *Error Handler*\n\n"
    error_msg += f"`{type(context.error).__name__}: {str(context.error)[:1000]}`\n\n"
    if update and update.effective_message:
        error_msg += f"📍 Chat: {update.effective_chat.id}\n"
        error_msg += f"💬 Mensaje: {update.effective_message.text[:200] if update.effective_message.text else 'N/A'}"
    error_msg += f"\n⏰ {time.strftime('%Y-%m-%d %H:%M:%S')}"

    import logging
    logger = logging.getLogger(__name__)
    logger.error(f"Telegram error: {context.error}")

    stats.data["errors"] = stats.data.get("errors", 0) + 1
    stats.save()

    try:
        await context.bot.send_message(chat_id=OWNER_ID, text=error_msg, parse_mode="Markdown")
    except:
        pass