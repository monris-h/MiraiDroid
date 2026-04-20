"""
Message handler - autonomous router + natural exec + AI fallback
"""
from telegram import Update
from telegram.ext import ContextTypes
from src import is_owner, memory, activity_log, stats, rate_limiter, ALIASES, file_manager
from services.ai import AI
from services.web_search import WebSearch as web_search


class AutonomousRouter:
    def __init__(self):
        self.intents = self.build_intent_map()

    def build_intent_map(self):
        return {
            "search": {
                "keywords": ["busca en internet", "busca sobre", "search for", "investiga sobre", "busca noticias"],
                "handler": "handle_search", "strict": True
            },
            "weather": {
                "keywords": ["clima en", "weather in", "temperatura en", "hace calor en", "hace frio en"],
                "handler": "handle_weather", "strict": True
            },
            "calc": {
                "keywords": ["calcula ", "cuanto es ", "="],
                "handler": "handle_calc", "strict": True
            },
            "sysmon": {
                "keywords": ["estado del sistema", "system status", "uso de cpu"],
                "handler": "handle_sysmon", "strict": True
            },
            "time": {
                "keywords": ["que hora es", "what time", "fecha hoy"],
                "handler": "handle_time", "strict": True
            },
        }

    async def route(self, text, update, ctx):
        from services.weather import weather
        text_lower = text.lower()

        for intent_name, intent_data in self.intents.items():
            for keyword in intent_data["keywords"]:
                if keyword.lower() in text_lower:
                    handler = getattr(self, intent_data["handler"], None)
                    if handler:
                        try:
                            result = await handler(text, update, ctx)
                            if result:
                                return result
                        except:
                            pass
        return None

    async def handle_search(self, text, update, ctx):
        query = text.lower()

        is_self_improve = any(kw in query for kw in ["mejorarte a ti mismo", "mejorar tu", "mejoras para ti", "como mejorarte", "improve yourself", "improve your", "mejora tu codigo", "mejora ti mismo"])

        for kw in ["busca", "buscar", "search", "investiga", "en internet"]:
            query = query.replace(kw, "").strip()

        if not query or len(query) < 2:
            return "Dime que quieres buscar. Ejemplo: busca noticias de IA"

        if is_self_improve:
            result = await web_search.search(query + " AI agent bot improvements python telegram 2026", max_results=8)
            if result:
                return "Buscando mejoras tecnicas para mi codigo...\n\n" + result
            return "No pude buscar mejoras. Intenta de nuevo."
        else:
            result = await web_search.search(query, max_results=8)
            if result:
                return result
            return "No pude hacer la busqueda. Intenta de nuevo."

    async def handle_weather(self, text, update, ctx):
        from services.weather import weather
        location = "Mexico"
        for kw in ["en ", "para "]:
            if kw in text.lower():
                parts = text.split(kw)
                if len(parts) > 1:
                    location = parts[-1].strip().split()[0]
        return await weather.get(location)

    async def handle_calc(self, text, update, ctx):
        import re, math
        expression = text.lower()
        for kw in ["calcula", "cuanto es", " cuanto es"]:
            expression = expression.replace(kw, "").strip()
        expression = re.sub(r"[^0-9+\-*/().%^√ ]", "", expression)
        expression = expression.replace("^", "**").replace("√", "sqrt").replace("por", "*")
        if not expression:
            return None
        try:
            result = eval(expression, {"__builtins__": {}, "sqrt": math.sqrt})
            return f"Resultado: {expression} = {result}"
        except:
            return None

    async def handle_sysmon(self, text, update, ctx):
        import subprocess
        try:
            disk = subprocess.check_output("df -h / | tail -1 | awk '{print $3}'", shell=True, text=True).strip()
            ram = subprocess.check_output("free -h | grep Mem | awk '{print $3}'", shell=True, text=True).strip()
            return f"Estado del Sistema:\n- Disco: {disk}\n- RAM: {ram}"
        except:
            return "No pude obtener stats"

    async def handle_time(self, text, update, ctx):
        from datetime import datetime
        now = datetime.now()
        return f"Hora actual: {now.strftime('%H:%M:%S')}\nFecha: {now.strftime('%Y-%m-%d')}"

    async def handle_notes(self, text, update, ctx):
        note = text.lower()
        for kw in ["nota", "notas", "anota", "apuntar", "recuerda"]:
            note = note.replace(kw, "").strip()
        if len(note) < 3:
            return None
        memory.data.setdefault("notes", []).append({"text": note, "date": __import__('time').strftime("%Y-%m-%d %H:%M")})
        memory.save()
        return f"Nota guardada: {note[:100]}"

    async def handle_todos(self, text, update, ctx):
        todo = text.lower()
        for kw in ["tarea", "pendiente", "necesito", "debo", "hacer"]:
            todo = todo.replace(kw, "").strip()
        if len(todo) < 3:
            return None
        memory.data.setdefault("todos", []).append({"text": todo, "done": False, "date": __import__('time').strftime("%Y-%m-%d %H:%M")})
        memory.save()
        return f"To-do agregado: {todo[:100]}"


autonomous_router = AutonomousRouter()


async def msg_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        await update.message.reply_text("❌ Solo Yerik.")
        return

    user_id = update.effective_user.id

    if not rate_limiter.is_allowed(user_id, "msg"):
        await update.message.reply_text("⏳ Demasiados mensajes. Espera un momento.")
        return

    text = update.message.text
    stats.inc("messages")

    if text.startswith("/") and " " not in text:
        cmd = text[1:].lower()
        if cmd in ALIASES:
            ALIASES[cmd]  # just to ensure it exists, real routing happens via command handlers
            text = f"/{ALIASES[cmd]}"

    memory.add_message("user", text)
    context = memory.get_context()

    await update.message.chat.send_action("typing")

    tool_result = await autonomous_router.route(text, update, ctx)
    if tool_result:
        memory.add_message("assistant", tool_result)
        await update.message.reply_text(tool_result)
        return

    from src.system_tools import natural_exec
    natural_result = await natural_exec.execute(text, file_manager)
    if natural_result:
        memory.add_message("assistant", natural_result)
        await update.message.reply_text(natural_result)
        return

    response = await AI.think(f"Usuario: '{text}'. Responde útilmente.", context)
    memory.add_message("assistant", response)
    activity_log.log("MSG", text[:50])
    await update.message.reply_text(response)