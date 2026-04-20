"""
Voice handler - transcribe audio messages using Whisper (Groq API or local)
"""
from telegram import Update
from telegram.ext import ContextTypes
from src import is_owner, memory, activity_log
from src.config import BASE_DIR, GROQ_API_KEY


async def voice_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return

    voice = update.message.voice
    await update.message.reply_text("🎤 Procesando audio...")

    try:
        file = await voice.get_file()
        ogg_path = BASE_DIR / "downloads" / f"voice_{__import__('time').time():.0f}.ogg"
        mp3_path = BASE_DIR / "downloads" / f"voice_{__import__('time').time():.0f}.mp3"
        ogg_path.parent.mkdir(parents=True, exist_ok=True)
        await file.download_to_drive(ogg_path)

        text = None
        try:
            import aiohttp
            with open(ogg_path, "rb") as f:
                audio_data = f.read()

            async with aiohttp.ClientSession() as session:
                form = aiohttp.FormData()
                form.add_field("file", audio_data, filename="voice.ogg", content_type="audio/ogg")
                form.add_field("model", "whisper-large-v3")

                async with session.post(
                    "https://api.groq.com/openai/v1/audio/transcriptions",
                    headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
                    data=form,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        text = result.get("text", "")
        except Exception:
            pass

        if not text:
            try:
                import whisper
                model = whisper.load_model("base")
                result = model.transcribe(str(ogg_path))
                text = result["text"]
            except:
                pass

        if text:
            memory.add_message("user", f"[Audio]: {text}")
            activity_log.log("VOICE", text[:50])

            await update.message.chat.send_action("typing")

            from handlers.messages import autonomous_router
            tool_result = await autonomous_router.route(text, update, ctx)
            if tool_result:
                await update.message.reply_text(f"🎤 *Transcripcion:* {text}\n\n{tool_result}")
                return

            from services.ai import AI
            response = await AI.think(f"Usuario envio un audio que dice: '{text}'. Responde utilmente.", "")
            await update.message.reply_text(f"🎤 *Transcripcion:* {text}\n\n{response}")
        else:
            await update.message.reply_text("🎤 Audio recibido. Para transcribir necesito whisper instalado. Puedes enviarme el texto de lo que dijiste?")

        try:
            ogg_path.unlink()
        except:
            pass

    except Exception as e:
        await update.message.reply_text(f"Error procesando audio: {e}")