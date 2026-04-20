"""
Document and photo handlers - file uploads and image analysis
"""
from telegram import Update
from telegram.ext import ContextTypes
from src import is_owner, activity_log
from src.config import BASE_DIR


async def doc_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return

    doc = update.message.document
    await update.message.reply_text(f"📎 {doc.file_name}")

    file = await doc.get_file()
    path = BASE_DIR / "downloads" / doc.file_name
    path.parent.mkdir(parents=True, exist_ok=True)
    await file.download_to_drive(path)
    activity_log.log("UPLOAD", str(path))


async def photo_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    from src.system_tools import image_analyzer

    if not is_owner(update.effective_user.id):
        return

    photo = update.message.photo[-1]
    await update.message.reply_text("📷 Analizando...")

    file = await photo.get_file()
    path = BASE_DIR / "downloads" / f"photo_{__import__('time').time():.0f}.jpg"
    path.parent.mkdir(parents=True, exist_ok=True)
    await file.download_to_drive(path)

    result = await image_analyzer.analyze(path)
    await update.message.reply_text(result)