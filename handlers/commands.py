"""
Commands handlers - todos los comandos del bot
Un archivo, agrupados por función, delegation a services
"""
import subprocess
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes


def quick_actions_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 Status", callback_data="status"), InlineKeyboardButton("💾 Disco", callback_data="disk")],
        [InlineKeyboardButton("🔄 Pull", callback_data="git_pull"), InlineKeyboardButton("📝 Help", callback_data="help")],
        [InlineKeyboardButton("🔍 Search", callback_data="search"), InlineKeyboardButton("📋 Logs", callback_data="logs")],
    ])


async def start_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    from src import is_owner
    if not is_owner(update.effective_user.id):
        await update.message.reply_text("❌ Este bot solo responde a su dueño.")
        return
    from src.config import VERSION
    keyboard = quick_actions_keyboard()
    await update.message.reply_text(f"🛡️ *MiraiDroid v{VERSION} activo*\n\nSolo tú. 🤖", reply_markup=keyboard, parse_mode="Markdown")


async def help_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    from src import is_owner
    if not is_owner(update.effective_user.id):
        return
    await update.message.reply_text("""📚 *Comandos completos:*

*🌐 Info:* /start, /help, /status, /version, /uptime
*📁 Archivos:* /files, /read, /write, /find
*🐱 Git:* /git_status, /git_pull, /git_commit, /git_push, /git_log
*🐳 Docker:* /docker_ps, /docker_stats, /docker_logs
*⚙️ System:* /ps (procesos), /kill [pid], /top, /ping [host], /dns [domain], /ports [host], /battery, /apps
*💓 Heartbeat:* /heartbeat, /heartbeat_on, /heartbeat_off, /heartbeat_stats
*🛠️ Dev:* /skills, /create_skill, /tools, /plugins
*🧠 AI:* /improve, /persona, /learn, /forget, /analyze, /exec_code
*🌐 Web:* /rss, /weather, /shorten [url], /summarize [url]
*📋 Data:* /paste [content], /getpaste [code], /remind [time] [msg]
*🔒 Security:* /activity, /encrypt, /decrypt
*⏰ Schedule:* /cron_list, /cron_enable, /cron_disable, /reminders
*💾 Backup:* /backup, /backup_list, /rollback
*💬 Natural:* Escribe naturalmente y el bot interpreta""", parse_mode="Markdown")


async def status_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    from src import is_owner, is_windows
    if not is_owner(update.effective_user.id):
        return
    from src.config import VERSION
    from src.memory import memory
    try:
        if is_windows():
            disk = subprocess.check_output("wmic logicaldisk get size,freespace,caption /format:list 2>nul | findstr C:", shell=True, text=True).strip()
            disk = "?"
        else:
            disk = subprocess.check_output("df -h / | tail -1 | awk '{print $3}'", shell=True, text=True).strip()
            ram = subprocess.check_output("free -h | grep Mem | awk '{print $3}'", shell=True, text=True).strip()
            uptime = subprocess.check_output("uptime | awk '{print $3}'", shell=True, text=True).strip()
    except:
        disk, ram, uptime = "?", "?", "?"
    await update.message.reply_text(f"✅ v{VERSION} | 💾 {disk} | 📊 {ram if 'ram' in dir() else '?'} | ⏱️ {uptime if 'uptime' in dir() else '?'} | 👤 {memory.data.get('persona', 'default')}")


async def version_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    from src import is_owner
    from src.config import VERSION
    if not is_owner(update.effective_user.id):
        return
    await update.message.reply_text(f"📦 v{VERSION}")


async def uptime_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    from src import is_owner
    if not is_owner(update.effective_user.id):
        return
    try:
        result = subprocess.check_output("uptime", shell=True, text=True)
        await update.message.reply_text(f"⏱️ {result}")
    except Exception as e:
        await update.message.reply_text(f"❌ {e}")


async def restart_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    from src import is_owner, db
    from src.config import TOKEN, OWNER_ID, BASE_DIR, VERSION
    if not is_owner(update.effective_user.id):
        return

    await update.message.reply_text("Reiniciando... Nos vemos en breve! 🔄")
    import requests
    try:
        requests.get(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            params={"chat_id": OWNER_ID, "text": "🔄 Reiniciando...", "parse_mode": "Markdown"},
            timeout=5
        )
    except:
        pass

    db.close()
    await ctx.application.stop()

    import sys
    subprocess.Popen(
        [sys.executable, str(BASE_DIR / "miraidroid.py")],
        cwd=str(BASE_DIR),
        stdout=open(str(BASE_DIR / "logs" / "miraidroid.log"), "a"),
        stderr=open(str(BASE_DIR / "logs" / "error.log"), "a")
    )
    sys.exit(0)


async def ps_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    from src import is_owner, is_windows, process_manager
    if not is_owner(update.effective_user.id):
        return
    await update.message.reply_text(process_manager.list(), parse_mode="Markdown")


async def kill_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    from src import is_owner, process_manager
    if not is_owner(update.effective_user.id):
        return
    if not ctx.args:
        await update.message.reply_text("❌ Uso: /kill [pid]")
        return
    await update.message.reply_text(process_manager.kill(ctx.args[0]))


async def top_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    from src import is_owner, process_manager
    if not is_owner(update.effective_user.id):
        return
    limit = int(ctx.args[0]) if ctx.args and ctx.args[0].isdigit() else 5
    await update.message.reply_text(process_manager.top(limit), parse_mode="Markdown")


async def battery_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    from src import is_owner, battery_monitor
    if not is_owner(update.effective_user.id):
        return
    await update.message.reply_text(battery_monitor.status(), parse_mode="Markdown")


async def apps_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    from src import is_owner, app_manager
    if not is_owner(update.effective_user.id):
        return
    await update.message.reply_text(app_manager.list_installed(), parse_mode="Markdown")


async def files_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    from src import is_owner, file_manager
    if not is_owner(update.effective_user.id):
        return
    path = ctx.args[0] if ctx.args else "."
    await update.message.reply_text(file_manager.list(path))


async def read_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    from src import is_owner, file_manager
    if not is_owner(update.effective_user.id):
        return
    if not ctx.args:
        await update.message.reply_text("❌ Uso: /read <archivo>")
        return
    await update.message.reply_text(file_manager.read(ctx.args[0]))


async def write_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    from src import is_owner, file_manager
    if not is_owner(update.effective_user.id):
        return
    if len(ctx.args) < 2:
        await update.message.reply_text("❌ Uso: /write <path> <contenido>")
        return
    await update.message.reply_text(file_manager.write(ctx.args[0], " ".join(ctx.args[1:])))


async def find_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    from src import is_owner, file_manager
    if not is_owner(update.effective_user.id):
        return
    if not ctx.args:
        await update.message.reply_text("❌ Uso: /find [pattern]")
        return
    await update.message.reply_text(file_manager.find(ctx.args[0]))


async def git_status_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    from src import is_owner, git_manager
    if not is_owner(update.effective_user.id):
        return
    await update.message.reply_text(f"```\n{git_manager.status()}\n```", parse_mode="Markdown")


async def git_pull_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    from src import is_owner, git_manager
    if not is_owner(update.effective_user.id):
        return
    await update.message.reply_text(f"```\n{git_manager.pull()}\n```", parse_mode="Markdown")


async def git_commit_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    from src import is_owner, git_manager
    if not is_owner(update.effective_user.id):
        return
    if not ctx.args:
        await update.message.reply_text("❌ Uso: /git_commit <msg>")
        return
    await update.message.reply_text(f"```\n{git_manager.add()}\n{git_manager.commit(' '.join(ctx.args))}\n```", parse_mode="Markdown")


async def git_push_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    from src import is_owner, git_manager
    if not is_owner(update.effective_user.id):
        return
    await update.message.reply_text(f"```\n{git_manager.push()}\n```", parse_mode="Markdown")


async def git_log_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    from src import is_owner, git_manager
    if not is_owner(update.effective_user.id):
        return
    await update.message.reply_text(f"```\n{git_manager.log()}\n```", parse_mode="Markdown")


async def docker_ps_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    from src import is_owner, docker_monitor
    if not is_owner(update.effective_user.id):
        return
    await update.message.reply_text(f"```\n{docker_monitor.status()}\n```", parse_mode="Markdown")


async def docker_stats_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    from src import is_owner, docker_monitor
    if not is_owner(update.effective_user.id):
        return
    await update.message.reply_text(f"```\n{docker_monitor.stats()}\n```", parse_mode="Markdown")


async def docker_logs_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    from src import is_owner, docker_monitor
    if not is_owner(update.effective_user.id):
        return
    if not ctx.args:
        await update.message.reply_text("❌ Uso: /docker_logs <nombre>")
        return
    await update.message.reply_text(f"```\n{docker_monitor.logs(ctx.args[0])}\n```", parse_mode="Markdown")


async def plugins_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    from src import is_owner, plugin_manager
    if not is_owner(update.effective_user.id):
        return
    info = plugin_manager.list_plugins()
    msg = f"📦 *Plugins disponibles:*\n• " + "\n• ".join(info["available"]) + f"\n\n🟢 *Cargados:* " + ", ".join(info["loaded"]) if info["loaded"] else ""
    await update.message.reply_text(msg or "📝 No hay plugins disponibles")


async def load_plugin_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    from src import is_owner, plugin_manager
    if not is_owner(update.effective_user.id):
        return
    if not ctx.args:
        await update.message.reply_text("❌ Uso: /load_plugin [nombre]")
        return
    success, msg = plugin_manager.load_plugin(ctx.args[0])
    await update.message.reply_text(f"✅ {msg}" if success else f"❌ {msg}")


async def persona_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    from src import is_owner, memory, PERSONAS
    if not is_owner(update.effective_user.id):
        return
    if not ctx.args:
        await update.message.reply_text(f"👤 Actual: {memory.data.get('persona', 'default')}\nDisponibles: {', '.join(PERSONAS.keys())}")
        return
    if memory.set_persona(ctx.args[0]):
        await update.message.reply_text(f"✅ Persona: {ctx.args[0]}")
    else:
        await update.message.reply_text(f"❌ '{ctx.args[0]}' no disponible")


async def learn_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    from src import is_owner, memory
    if not is_owner(update.effective_user.id):
        return
    if not ctx.args or "→" not in " ".join(ctx.args):
        await update.message.reply_text("❌ Uso: /learn wrong → correct")
        return
    text = " ".join(ctx.args)
    wrong, correct = text.split("→")
    memory.add_learning(wrong.strip(), correct.strip())
    await update.message.reply_text(f"✅ Aprendido: '{wrong}' → '{correct}'")


async def forget_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    from src import is_owner, memory
    if not is_owner(update.effective_user.id):
        return
    memory.data["learning"] = []
    memory.save()
    await update.message.reply_text("✅ Aprendizaje olvidado")


async def improve_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    from src import is_owner
    from services.ai import SelfImprover
    if not is_owner(update.effective_user.id):
        return
    if not ctx.args:
        await update.message.reply_text("❌ Uso: /improve <request>")
        return
    await update.message.reply_text("🔄 Mejorando código...")
    await update.message.reply_text(await SelfImprover.improve(" ".join(ctx.args))[:4000])


async def exec_code_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    from src import is_owner
    from services.code_exec import code_interpreter
    if not is_owner(update.effective_user.id):
        return
    if not ctx.args:
        await update.message.reply_text("❌ Uso: /exec_code [python|bash] <codigo>")
        return
    lang = ctx.args[0] if ctx.args[0] in ["python", "bash", "shell"] else "python"
    code = " ".join(ctx.args[1:]) if lang in ctx.args else " ".join(ctx.args)
    await update.message.reply_text(await code_interpreter.execute(code, lang if "code" in ctx.args[0] else "python"))


async def weather_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    from src import is_owner
    from services.weather import weather
    if not is_owner(update.effective_user.id):
        return
    loc = ctx.args[0] if ctx.args else "Mexico"
    await update.message.reply_text(await weather.get(loc))


async def shorten_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    from src import is_owner
    from services.url_shortener import url_shortener
    if not is_owner(update.effective_user.id):
        return
    if not ctx.args:
        await update.message.reply_text("❌ Uso: /shorten [url]")
        return
    await update.message.reply_text(await url_shortener.shorten(ctx.args[0]))


async def paste_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    from src import is_owner, pastebin
    if not is_owner(update.effective_user.id):
        return
    if not ctx.args:
        await update.message.reply_text("❌ Uso: /paste [contenido]")
        return
    await update.message.reply_text(pastebin.save(" ".join(ctx.args)))


async def getpaste_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    from src import is_owner, pastebin
    if not is_owner(update.effective_user.id):
        return
    if not ctx.args:
        await update.message.reply_text("❌ Uso: /getpaste [codigo]")
        return
    content = pastebin.get(ctx.args[0])
    if content:
        await update.message.reply_text(f"```\n{content[:4000]}\n```", parse_mode="Markdown")
    else:
        await update.message.reply_text("❌ Código no encontrado")


async def backup_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    from src import is_owner
    from services.backup import backup_manager
    if not is_owner(update.effective_user.id):
        return
    ts = backup_manager.create_backup("manual")
    await update.message.reply_text(f"✅ Backup: {ts}")


async def backup_list_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    from src import is_owner
    from services.backup import backup_manager
    if not is_owner(update.effective_user.id):
        return
    backups = backup_manager.list_backups()
    await update.message.reply_text("📦 *Backups:*\n• " + "\n• ".join(backups[:10]) if backups else "📝 No hay backups")


async def rollback_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    from src import is_owner
    from services.backup import backup_manager
    if not is_owner(update.effective_user.id):
        return
    if not ctx.args:
        await update.message.reply_text("❌ Uso: /rollback [timestamp]")
        return
    if backup_manager.restore_backup(ctx.args[0]):
        await update.message.reply_text(f"✅ Restaurado. ¡Reinicia!")
    else:
        await update.message.reply_text(f"❌ Backup no encontrado")


async def encrypt_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    from src import is_owner, Crypto
    if not is_owner(update.effective_user.id):
        return
    if not ctx.args:
        await update.message.reply_text("❌ Uso: /encrypt [texto]")
        return
    await update.message.reply_text(f"🔐 `{Crypto.encrypt(' '.join(ctx.args))}`", parse_mode="Markdown")


async def decrypt_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    from src import is_owner, Crypto
    if not is_owner(update.effective_user.id):
        return
    if not ctx.args:
        await update.message.reply_text("❌ Uso: /decrypt [texto]")
        return
    await update.message.reply_text(f"🔓 `{Crypto.decrypt(' '.join(ctx.args))}`", parse_mode="Markdown")


async def memory_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    from src import is_owner, memory
    if not is_owner(update.effective_user.id):
        return
    history = memory.data.get("history", [])
    msg = "📝 *Mensajes:*\n\n" + "\n".join([f"**{m['role']}**: {m['content'][:60]}..." for m in history[-5:]])
    await update.message.reply_text(msg or "📝 Vacío", parse_mode="Markdown")


async def clear_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    from src import is_owner, memory
    if not is_owner(update.effective_user.id):
        return
    memory.data["history"] = []
    memory.data["conversations"] = {}
    memory.save()
    await update.message.reply_text("✅ Limpiado")


async def activity_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    from src import is_owner, activity_log
    if not is_owner(update.effective_user.id):
        return
    recent = activity_log.get_recent()
    msg = "📋 *Actividad:*\n\n" + "\n".join([f"**{a['time']}** {a['action']}" for a in recent[-10:]])
    await update.message.reply_text(msg, parse_mode="Markdown")


async def stats_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    from src import is_owner, stats
    if not is_owner(update.effective_user.id):
        return
    await update.message.reply_text(stats.get_summary(), parse_mode="Markdown")


async def rate_limit_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    from src import is_owner, rate_limiter
    if not is_owner(update.effective_user.id):
        return
    remaining = rate_limiter.get_remaining(update.effective_user.id)
    await update.message.reply_text(f"📊 Rate limit: {remaining}/20 mensajes por minuto restantes")


async def heartbeat_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    from src import is_owner
    from services.heartbeat import heartbeat
    if not is_owner(update.effective_user.id):
        return
    status = "ON ✅" if heartbeat.enabled else "OFF ❌"
    stats_status = "ON" if heartbeat.stats_enabled else "OFF"
    await heartbeat.beat(ctx._application)
    await update.message.reply_text(f"💓 Heartbeat: {status}\n📊 Stats: {stats_status}\n⏱️ Uptime: {heartbeat.uptime()}\n💓 beats enviados: {heartbeat.beats}")


async def heartbeat_on_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    from src import is_owner
    from services.heartbeat import heartbeat
    if not is_owner(update.effective_user.id):
        return
    heartbeat.toggle(True)
    await update.message.reply_text("✅ Heartbeat Activado (cada 30 min)")


async def heartbeat_off_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    from src import is_owner
    from services.heartbeat import heartbeat
    if not is_owner(update.effective_user.id):
        return
    heartbeat.toggle(False)
    await update.message.reply_text("❌ Heartbeat Desactivado")


async def heartbeat_stats_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    from src import is_owner
    from services.heartbeat import heartbeat
    if not is_owner(update.effective_user.id):
        return
    heartbeat.stats_enabled = not heartbeat.stats_enabled
    status = "ON" if heartbeat.stats_enabled else "OFF"
    await update.message.reply_text(f"📊 Heartbeat stats: {status}\n\nLos heartbeats ahora incluirán: CPU, RAM, disco, uptime, temperatura")


async def cron_list_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    from src import is_owner
    from services.scheduler import cron_scheduler
    if not is_owner(update.effective_user.id):
        return
    jobs = cron_scheduler.list_jobs()
    await update.message.reply_text("⏰ *Cron Jobs:*\n• " + "\n• ".join(jobs) if jobs else "📝 No hay jobs")


async def cron_enable_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    from src import is_owner
    from services.scheduler import cron_scheduler
    if not is_owner(update.effective_user.id):
        return
    if not ctx.args:
        await update.message.reply_text("❌ Uso: /cron_enable [job_id]")
        return
    cron_scheduler.enable(ctx.args[0], True)
    await update.message.reply_text(f"✅ Job '{ctx.args[0]}' ON")


async def cron_disable_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    from src import is_owner
    from services.scheduler import cron_scheduler
    if not is_owner(update.effective_user.id):
        return
    if not ctx.args:
        await update.message.reply_text("❌ Uso: /cron_disable [job_id]")
        return
    cron_scheduler.enable(ctx.args[0], False)
    await update.message.reply_text(f"✅ Job '{ctx.args[0]}' OFF")


async def agent_check_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    from src import is_owner, is_windows
    from src.config import VERSION, MINIMAX_KEY, TAVILY_API_KEY, GROQ_API_KEY, BASE_DIR
    from src.memory import memory
    from src.database import db

    if not is_owner(update.effective_user.id):
        return

    await update.message.reply_text("🔍 Diagnosticando...")

    issues, ok = [], []

    plugins_dir = BASE_DIR / "plugins"
    plugins = [f.stem for f in plugins_dir.glob("*.py") if f.name not in ["__init__.py", "plugin_base.py"]]
    if plugins:
        ok.append(f"Plugins: {len(plugins)} ({', '.join(plugins)})")
    else:
        issues.append("No plugins")

    skills_dir = BASE_DIR / "skills"
    skills = [f.stem for f in skills_dir.glob("*.py") if f.name != "__init__.py"]
    if skills:
        ok.append(f"Skills: {len(skills)}")
    else:
        issues.append("No skills")

    memory_file = BASE_DIR / "data" / "memory.json"
    if memory_file.exists():
        size = memory_file.stat().st_size
        ok.append(f"Memory: {size}b")
    else:
        issues.append("Memory missing")

    if MINIMAX_KEY and len(MINIMAX_KEY) > 10:
        ok.append("MiniMax: OK")
    else:
        issues.append("MiniMax missing")

    if TAVILY_API_KEY and len(TAVILY_API_KEY) > 10:
        ok.append("Tavily: OK")
    else:
        issues.append("Tavily missing")

    if GROQ_API_KEY and len(GROQ_API_KEY) > 10:
        ok.append("Groq: OK")
    else:
        issues.append("Groq missing")

    from src import stats
    msg = "🔍 *Diagnostic Report*\n\n"
    if ok:
        msg += "✅ *OK:*\n" + "\n".join([f"  • {x}" for x in ok]) + "\n\n"
    if issues:
        msg += "⚠️ *Issues:*\n" + "\n".join([f"  • {x}" for x in issues])
    else:
        msg += "🎉 Todo en orden!"
    msg += f"\n\n📦 v{VERSION} | Uptime: {stats.get_uptime()}"

    await update.message.reply_text(msg, parse_mode="Markdown")


async def screenshot_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    from src import is_owner, screenshot
    if not is_owner(update.effective_user.id):
        return
    await update.message.reply_text("📸 Capturando...")
    path = screenshot.capture()
    if path.endswith(".png") or path.endswith(".jpg"):
        with open(path, "rb") as f:
            await update.message.reply_photo(photo=f, caption="📸")
    else:
        await update.message.reply_text(path)


async def ping_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    from src import is_owner, network_tools
    if not is_owner(update.effective_user.id):
        return
    host = ctx.args[0] if ctx.args else "google.com"
    await update.message.reply_text(await network_tools.ping(host))


async def dns_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    from src import is_owner, network_tools
    if not is_owner(update.effective_user.id):
        return
    if not ctx.args:
        await update.message.reply_text("❌ Uso: /dns [domain]")
        return
    await update.message.reply_text(await network_tools.dns(ctx.args[0]))


async def ports_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    from src import is_owner, network_tools
    if not is_owner(update.effective_user.id):
        return
    if not ctx.args:
        await update.message.reply_text("❌ Uso: /ports [host] [puertos]")
        return
    host = ctx.args[0]
    ports = ctx.args[1] if len(ctx.args) > 1 else "22,80,443,3000"
    await update.message.reply_text(await network_tools.ports(host, ports))


async def rss_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    from src import is_owner
    from services.rss import rss_reader
    if not is_owner(update.effective_user.id):
        return
    if not ctx.args:
        await update.message.reply_text("❌ Uso: /rss [url]")
        return
    await update.message.reply_text(await rss_reader.summarize(ctx.args[0]))


async def summarize_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    from src import is_owner
    from services.summarizer import summarizer
    if not is_owner(update.effective_user.id):
        return
    if not ctx.args:
        await update.message.reply_text("❌ Uso: /summarize [url]")
        return
    await update.message.reply_text(await summarizer.summarize_url(ctx.args[0]))


async def remind_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    from src import is_owner
    from services.reminders import reminders
    if not is_owner(update.effective_user.id):
        return
    if len(ctx.args) < 2:
        await update.message.reply_text("❌ Uso: /remind [time] [mensaje]")
        return
    time_str = ctx.args[0]
    message = " ".join(ctx.args[1:])
    await update.message.reply_text(await reminders.add(time_str, message))


async def reminders_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    from src import is_owner
    from services.reminders import reminders
    if not is_owner(update.effective_user.id):
        return
    await update.message.reply_text(await reminders.list_pending())