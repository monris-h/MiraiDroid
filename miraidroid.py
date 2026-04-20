#!/usr/bin/env python3
"""
🛡️ MiraiDroid - Cellular Agent con IA
Full Featured v4.0 - Ultimate Edition Plus 2
Solo para Yerik (@Jyn_h)
"""
import os
import sys
import json
import time
import asyncio
import logging
import subprocess
import signal
import hashlib
import base64
import re
import sqlite3
import random
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Document, PhotoSize
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler, InlineQueryHandler

# ============================================================================
# CONFIG (.env support)
# ============================================================================
BASE_DIR = Path.home() / "agent"
ENV_FILE = BASE_DIR / ".env"
VERSION = "5.0.0"

def load_env():
    """Load config from .env file - ALL CREDENTIALS MUST BE IN .ENV"""
    if not ENV_FILE.exists():
        raise RuntimeError(
            ".env file not found! Copy .env.example to .env and fill in all credentials:\n"
            "- TOKEN\n- MINIMAX_KEY\n- OWNER_ID\n- TAVILY_API_KEY\n- GROQ_API_KEY"
        )
    
    config = {}
    for line in ENV_FILE.read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            key, val = line.split("=", 1)
            config[key.strip()] = val.strip().strip('"').strip("'")
    
    # Validate all required keys are present
    required = ["TOKEN", "MINIMAX_KEY", "OWNER_ID", "TAVILY_API_KEY", "GROQ_API_KEY"]
    missing = [k for k in required if k not in config or not config[k]]
    if missing:
        raise RuntimeError(f"Missing required .env keys: {missing}")
    
    return config

CONFIG = load_env()
TOKEN = CONFIG["TOKEN"]
MINIMAX_KEY = CONFIG["MINIMAX_KEY"]
OWNER_ID = CONFIG["OWNER_ID"]
TAVILY_API_KEY = CONFIG.get("TAVILY_API_KEY")  # Required in .env
GROQ_API_KEY = CONFIG.get("GROQ_API_KEY")  # Required in .env

# ============================================================================
# RATE LIMITING
# ============================================================================
class RateLimiter:
    def __init__(self):
        self.users = defaultdict(lambda: {"count": 0, "reset": time.time() + 60})
        self.max_per_minute = 20
        self.command_cooldown = {}  # user -> (command, unlock_time)
    
    def is_allowed(self, user_id, command=None):
        now = time.time()
        uid = str(user_id)
        
        # Check per-user rate limit
        if now > self.users[uid]["reset"]:
            self.users[uid] = {"count": 0, "reset": now + 60}
        
        self.users[uid]["count"] += 1
        if self.users[uid]["count"] > self.max_per_minute:
            return False
        
        # Check command-specific cooldown (5 seconds between same command)
        if command:
            key = f"{uid}:{command}"
            if key in self.command_cooldown and now < self.command_cooldown[key]:
                return False
            self.command_cooldown[key] = now + 5
        
        return True
    
    def get_remaining(self, user_id):
        uid = str(user_id)
        return max(0, self.max_per_minute - self.users[uid]["count"])

rate_limiter = RateLimiter()

# ============================================================================
# STATS
# ============================================================================
class Stats:
    def __init__(self):
        self.stats_file = BASE_DIR / "data" / "stats.json"
        self.data = self.load()
    
    def load(self):
        if self.stats_file.exists():
            try:
                return json.loads(self.stats_file.read_text())
            except:
                pass
        return {"start_time": time.time(), "messages": 0, "commands": defaultdict(int), "errors": 0}
    
    def save(self):
        self.stats_file.parent.mkdir(parents=True, exist_ok=True)
        self.stats_file.write_text(json.dumps(self.data, indent=2))
    
    def inc(self, key):
        self.data[key] = self.data.get(key, 0) + 1
        self.save()
    
    def get_uptime(self):
        seconds = int(time.time() - self.data["start_time"])
        h, rem = divmod(seconds, 3600)
        m, s = divmod(rem, 60)
        return f"{h}h {m}m {s}s"
    
    def get_summary(self):
        return (f"📊 *Stats desde inicio:*\n"
                f"• Inicio: {datetime.fromtimestamp(self.data['start_time']).strftime('%Y-%m-%d %H:%M')}\n"
                f"• Uptime: {self.get_uptime()}\n"
                f"• Mensajes: {self.data['messages']}\n"
                f"• Comandos: {sum(self.data['commands'].values())}\n"
                f"• Errores: {self.data.get('errors', 0)}")

stats = Stats()

PERSONAS = {
    "default": "Eres un asistente útil y conversacional en español.",
    "technical": "Eres un asistente técnico experto en programación y sistemas. Da respuestas técnicas detalladas.",
    "casual": "Eres un amigo informal que habla en español relaxed. Usa jerga y emojis casuales.",
    "formal": "Eres un asistente formal y profesional. Hablas en español formal."
}

ALIASES = {
    "l": "logs",
    "ls": "files",
    "cat": "read",
    "py": "python",
    "s": "status",
    "h": "help",
    "r": "rss",
    "w": "weather",
    "b": "backup",
    "p": "persona",
    "i": "improve",
    "gc": "git_commit",
    "gp": "git_pull",
    "gs": "git_status",
    "dps": "docker_ps",
    "dlog": "docker_logs",
    "hb": "heartbeat",
    "hbon": "heartbeat_on",
    "hboff": "heartbeat_off",
    "hbstats": "heartbeat_stats",
    "st": "stats",
    "rl": "rate_limit",
}

for d in [BASE_DIR, BASE_DIR/"skills", BASE_DIR/"tools", BASE_DIR/"backups", BASE_DIR/"logs", BASE_DIR/"data", BASE_DIR/"plugins", BASE_DIR/"downloads"]:
    d.mkdir(parents=True, exist_ok=True)

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s',
    handlers=[logging.FileHandler(BASE_DIR/"logs"/"miraidroid.log"), logging.StreamHandler()])
logger = logging.getLogger(__name__)

def is_owner(user_id):
    return str(user_id) == OWNER_ID

# ============================================================================
# DATABASE (SQLite)
# ============================================================================
class Database:
    def __init__(self):
        self.db_path = BASE_DIR / "data" / "miraidroid.db"
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.create_tables()
    
    def create_tables(self):
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                time TEXT, message TEXT, created TEXT
            );
            CREATE TABLE IF NOT EXISTS scheduled_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cron TEXT, message TEXT, chat_id TEXT, created TEXT
            );
            CREATE TABLE IF NOT EXISTS url_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT, short_code TEXT, created TEXT
            );
            CREATE TABLE IF NOT EXISTS pastebin (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT, content TEXT, created TEXT
            );
            CREATE TABLE IF NOT EXISTS plugins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT, enabled INTEGER DEFAULT 1
            );
        """)
        self.conn.commit()
    
    def query(self, sql, args=()):
        return self.conn.execute(sql, args).fetchall()
    
    def execute(self, sql, args=()):
        self.conn.execute(sql, args)
        self.conn.commit()
    
    def close(self):
        self.conn.close()

db = Database()

# ============================================================================
# ENCRYPTION
# ============================================================================
class Crypto:
    @staticmethod
    def encrypt(data: str, key: str = None) -> str:
        if key is None:
            key = MINIMAX_KEY[:16]
        encrypted = "".join(chr(ord(c) ^ ord(key[i % len(key)])) for i, c in enumerate(data))
        return base64.b64encode(encrypted.encode()).decode()
    
    @staticmethod
    def decrypt(data: str, key: str = None) -> str:
        if key is None:
            key = MINIMAX_KEY[:16]
        encrypted = base64.b64decode(data.encode()).decode()
        return "".join(chr(ord(c) ^ ord(key[i % len(key)])) for i, c in enumerate(encrypted))

# ============================================================================
# MEMORY
# ============================================================================
class Memory:
    def __init__(self):
        self.file = BASE_DIR / "data" / "memory.json"
        self.short_file = BASE_DIR / "data" / "memory_short.json"
        self.data = self.load()
    
    def load(self):
        if self.file.exists():
            try:
                return json.loads(self.file.read_text())
            except:
                pass
        return {"history": [], "skills": [], "tools": [], "persona": "default", "conversations": {}, "learning": [], "version": VERSION}
    
    def save(self):
        self.file.write_text(json.dumps(self.data, indent=2))
        short = {"history": self.data.get("history", [])[-10:], "persona": self.data.get("persona")}
        self.short_file.write_text(json.dumps(short))
    
    def add_message(self, role, content, conv_id="default"):
        conv = self.data.setdefault("conversations", {}).setdefault(conv_id, {"history": []})
        conv["history"].append({"role": role, "content": content, "time": time.strftime("%Y-%m-%d %H:%M")})
        conv["history"] = conv["history"][-50:]
        self.data["history"] = self.data["history"][-50:]
        self.save()
    
    def add_learning(self, wrong, correct):
        self.data.setdefault("learning", []).append({"wrong": wrong, "correct": correct, "time": time.strftime("%Y-%m-%d %H:%M")})
        self.data["learning"] = self.data["learning"][-100:]
        self.save()
    
    def apply_learning(self, prompt):
        for item in self.data.get("learning", []):
            if item["wrong"].lower() in prompt.lower():
                prompt = prompt.lower().replace(item["wrong"].lower(), item["correct"])
        return prompt
    
    def get_context(self, conv_id="default"):
        ctx = "Historial:\n"
        conv = self.data.get("conversations", {}).get(conv_id, {"history": []})
        for msg in conv.get("history", [])[-10:]:
            ctx += f"{msg['role']}: {msg['content']}\n"
        return ctx
    
    def set_persona(self, persona):
        if persona in PERSONAS:
            self.data["persona"] = persona
            self.save()
            return True
        return False
    
    def get_persona_prompt(self):
        return PERSONAS.get(self.data.get("persona", "default"), PERSONAS["default"])

memory = Memory()

# ============================================================================
# ACTIVITY LOG
# ============================================================================
class ActivityLog:
    def __init__(self):
        self.file = BASE_DIR / "data" / "activity.json"
        self.data = self.load()
    
    def load(self):
        if self.file.exists():
            try:
                return json.loads(self.file.read_text())
            except:
                pass
        return {"actions": []}
    
    def log(self, action, details=""):
        self.data["actions"].append({"action": action, "details": details, "time": time.strftime("%Y-%m-%d %H:%M:%S")})
        self.data["actions"] = self.data["actions"][-1000:]
        self.file.write_text(json.dumps(self.data, indent=2))
    
    def get_recent(self, limit=20):
        return self.data["actions"][-limit:]

activity_log = ActivityLog()

# ============================================================================
# BACKUP SYSTEM
# ============================================================================
class BackupManager:
    def __init__(self):
        self.backup_dir = BASE_DIR / "backups"
        self.max_backups = 10
    
    def create_backup(self, reason="manual"):
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        backup_file = self.backup_dir / f"v{timestamp}_{reason}.py"
        agent_file = BASE_DIR / "miraidroid.py"
        if agent_file.exists():
            with open(agent_file, "r") as src:
                with open(backup_file, "w") as dst:
                    dst.write(f"# Backup {timestamp} - {reason}\n")
                    dst.write(src.read())
        backups = sorted(self.backup_dir.glob("v*.py"))
        for old in backups[:-self.max_backups]:
            old.unlink()
        logger.info(f"Backup created: {timestamp}")
        return timestamp
    
    def restore_backup(self, timestamp):
        backup_file = self.backup_dir / f"v{timestamp}_manual.py"
        if backup_file.exists():
            content = backup_file.read_text()
            content = content.replace(f"# Backup {timestamp} - manual\n", "")
            (BASE_DIR / "miraidroid.py").write_text(content)
            return True
        return False
    
    def list_backups(self):
        return sorted([f.stem[1:] for f in self.backup_dir.glob("v*.py")], reverse=True)

backup_manager = BackupManager()

# ============================================================================
# SKILL SYSTEM
# ============================================================================
class SkillManager:
    def __init__(self):
        self.skills_dir = BASE_DIR / "skills"
    
    def create_skill(self, name, code):
        (self.skills_dir / f"{name}.py").write_text(code)
        memory.data.setdefault("skills", []).append(name)
        memory.save()
        return True
    
    def list_skills(self):
        return [f.stem for f in self.skills_dir.glob("*.py")]

skill_manager = SkillManager()

# ============================================================================
# PLUGIN SYSTEM
# ============================================================================
class PluginManager:
    def __init__(self):
        self.plugins_dir = BASE_DIR / "plugins"
        self.loaded_plugins = {}
    
    def load_plugin(self, name):
        plugin_file = self.plugins_dir / f"{name}.py"
        if not plugin_file.exists():
            return False, f"Plugin {name} no encontrado"
        
        try:
            # Clear previous imports
            if name in sys.modules:
                del sys.modules[name]
            
            import importlib.util
            spec = importlib.util.spec_from_file_location(name, plugin_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Register handlers if plugin has them
            if hasattr(module, 'register_handlers'):
                module.register_handlers(app)
            if hasattr(module, 'init'):
                module.init()
            
            self.loaded_plugins[name] = module
            db.execute("INSERT OR IGNORE INTO plugins (name) VALUES (?)", (name,))
            return True, f"Plugin {name} cargado"
        except Exception as e:
            return False, f"Error: {e}"
    
    def unload_plugin(self, name):
        if name in self.loaded_plugins:
            if hasattr(self.loaded_plugins[name], 'cleanup'):
                self.loaded_plugins[name].cleanup()
            del self.loaded_plugins[name]
            return True
        return False
    
    def list_plugins(self):
        enabled = db.query("SELECT name FROM plugins WHERE enabled=1")
        all_plugins = [f.stem for f in self.plugins_dir.glob("*.py")]
        enabled_names = [r[0] for r in enabled]
        return {"loaded": list(self.loaded_plugins.keys()), "available": all_plugins, "enabled": enabled_names}

plugin_manager = PluginManager()

# ============================================================================
# FILE MANAGER
# ============================================================================
class FileManager:
    @staticmethod
    def read(path, lines=100):
        try:
            p = Path(path).expanduser()
            if not p.exists():
                return f"❌ No encontrado: {path}"
            content = "\n".join(p.read_text().splitlines()[:lines])
            if len(content) > 4000:
                content = content[:4000] + "\n... (truncado)"
            return f"```\n{content}\n```"
        except Exception as e:
            return f"❌ Error: {e}"
    
    @staticmethod
    def write(path, content):
        try:
            p = Path(path).expanduser()
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content)
            return f"✅ Escrito: {path}"
        except Exception as e:
            return f"❌ Error: {e}"
    
    @staticmethod
    def list(path="."):
        try:
            p = Path(path).expanduser()
            if p.is_file():
                return f"📄 {p.name} ({p.stat().st_size} bytes)"
            items = [f"{'📁' if i.is_dir() else '📄'} {i.name}" for i in p.iterdir()]
            return "\n".join(items[:50]) or "📁 Vacío"
        except Exception as e:
            return f"❌ Error: {e}"
    
    @staticmethod
    def find(pattern, path="."):
        try:
            p = Path(path).expanduser()
            results = []
            for i in p.rglob(f"*{pattern}*"):
                if "/." not in str(i):
                    results.append(f"{'📁' if i.is_dir() else '📄'} {i}")
            if not results:
                return "❌ No encontrado"
            return "\n".join(results[:30])
        except Exception as e:
            return f"❌ Error: {e}"

file_manager = FileManager()

# ============================================================================
# GIT MANAGER
# ============================================================================
class GitManager:
    @staticmethod
    def run(cmd, cwd=None):
        try:
            result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True, timeout=30)
            return result.stdout or result.stderr or "(sin output)"
        except Exception as e:
            return f"❌ Error: {e}"
    
    @staticmethod
    def status(repo=None):
        return GitManager.run("git status --short", cwd=repo)
    
    @staticmethod
    def pull(repo=None):
        return GitManager.run("git pull", cwd=repo)
    
    @staticmethod
    def add(files=".", repo=None):
        return GitManager.run(f"git add {files}", cwd=repo)
    
    @staticmethod
    def commit(msg, repo=None):
        return GitManager.run(f'git commit -m "{msg}"', cwd=repo)
    
    @staticmethod
    def push(repo=None):
        return GitManager.run("git push", cwd=repo)
    
    @staticmethod
    def log(repo=None, lines=10):
        return GitManager.run(f"git log --oneline -{lines}", cwd=repo)

git_manager = GitManager()

# ============================================================================
# DOCKER MONITOR
# ============================================================================
class DockerMonitor:
    @staticmethod
    def status():
        try:
            result = subprocess.run("docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'", 
                                   shell=True, capture_output=True, text=True, timeout=10)
            return result.stdout if result.stdout else "❌ Docker no está corriendo"
        except Exception as e:
            return f"❌ Error: {e}"
    
    @staticmethod
    def logs(container, lines=20):
        try:
            result = subprocess.run(f"docker logs --tail {lines} {container}", 
                                   shell=True, capture_output=True, text=True, timeout=30)
            return result.stdout[:4000] if result.stdout else result.stderr[:4000]
        except Exception as e:
            return f"❌ Error: {e}"
    
    @staticmethod
    def stats():
        try:
            result = subprocess.run("docker stats --no-stream --format 'table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}'", 
                                   shell=True, capture_output=True, text=True, timeout=10)
            return result.stdout if result.stdout else "❌ No hay datos"
        except Exception as e:
            return f"❌ Error: {e}"

docker_monitor = DockerMonitor()

# ============================================================================
# PROCESS MANAGER
# ============================================================================
class ProcessManager:
    @staticmethod
    def list():
        try:
            result = subprocess.check_output("ps aux --sort=-pcpu | head -15", shell=True).decode()
            lines = result.split("\n")
            header = "USER\tPID\t%CPU\t%MEM\tCOMMAND"
            return f"```\n{header}\n" + "\n".join(lines[1:11]) + "\n```"
        except Exception as e:
            return f"❌ Error: {e}"
    
    @staticmethod
    def kill(pid):
        try:
            subprocess.run(f"kill -9 {pid}", shell=True)
            return f"✅ Proceso {pid} matado"
        except Exception as e:
            return f"❌ Error: {e}"
    
    @staticmethod
    def top(limit=5):
        try:
            result = subprocess.check_output(f"ps aux --sort=-pcpu | head {limit + 1}", shell=True).decode()
            return f"```\n{result}\n```"
        except Exception as e:
            return f"❌ Error: {e}"

process_manager = ProcessManager()

# ============================================================================
# NETWORK TOOLS
# ============================================================================
class NetworkTools:
    @staticmethod
    async def ping(host):
        import aiohttp
        try:
            result = subprocess.run(f"ping -c 3 {host}", shell=True, capture_output=True, text=True, timeout=10)
            return f"```\n{result.stdout}\n```"
        except Exception as e:
            return f"❌ Error: {e}"
    
    @staticmethod
    async def dns(domain):
        try:
            result = subprocess.run(f"dig {domain} +short", shell=True, capture_output=True, text=True, timeout=10)
            return result.stdout or f"❌ No resuelto: {domain}"
        except Exception as e:
            return f"❌ Error: {e}"
    
    @staticmethod
    async def ports(host, ports="22,80,443,3000"):
        try:
            import socket
            results = []
            for port in ports.split(","):
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(1)
                    result = sock.connect_ex((host, int(port.strip())))
                    if result == 0:
                        results.append(f"✅ {port.strip()} ABIERTO")
                    else:
                        results.append(f"❌ {port.strip()} cerrado")
                    sock.close()
                except:
                    results.append(f"❌ {port.strip()} error")
            return "\n".join(results)
        except Exception as e:
            return f"❌ Error: {e}"

network_tools = NetworkTools()

# ============================================================================
# BATTERY MONITOR
# ============================================================================
class BatteryMonitor:
    @staticmethod
    def status():
        try:
            result = subprocess.check_output("termux-battery-status", shell=True).decode()
            try:
                data = json.loads(result)
                pct = data.get("percentage", "?")
                status = data.get("status", "?")
                temp = data.get("temperature", "?")
                return f"🔋 *Batería*\n• {pct}%\n• Status: {status}\n• Temp: {temp}°C"
            except:
                return result[:4000]
        except Exception as e:
            return f"❌ Error: {e}"

battery_monitor = BatteryMonitor()

# ============================================================================
# APP MANAGER
# ============================================================================
class AppManager:
    @staticmethod
    def list_installed():
        try:
            result = subprocess.check_output("pm list packages -3", shell=True).decode()
            apps = result.replace("package:", "").split("\n")[:30]
            return f"📱 *Apps instaladas (30 primeras):*\n\n" + "\n".join([f"• {a}" for a in apps if a])
        except Exception as e:
            return f"❌ Error: {e}"

app_manager = AppManager()

# ============================================================================
# CODE INTERPRETER
# ============================================================================
class CodeInterpreter:
    @staticmethod
    async def execute(code, language="python"):
        if language == "python":
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w") as f:
                f.write(code)
                f.flush()
                temp_path = f.name
            
            try:
                result = subprocess.run(f"python3 {temp_path}", shell=True, capture_output=True, text=True, timeout=30)
                output = result.stdout or result.stderr
                Path(temp_path).unlink()
                return f"```python\n{output}```" if output else "✅ Ejecutado sin output"
            except Exception as e:
                return f"❌ Error: {e}"
        
        elif language == "bash" or language == "shell":
            try:
                result = subprocess.run(code, shell=True, capture_output=True, text=True, timeout=30)
                return f"```bash\n{result.stdout or result.stderr}```"
            except Exception as e:
                return f"❌ Error: {e}"
        
        return f"❌ Lenguaje no soportado: {language}"

code_interpreter = CodeInterpreter()

# ============================================================================
# NATURAL EXEC
# ============================================================================
class NaturalExec:
    @staticmethod
    async def execute(command):
        command_lower = command.lower()
        
        # Search files
        if any(k in command_lower for k in ["busca", "encuentra", "search", "find"]):
            if any(ext in command_lower for ext in [".py", ".js", ".sh", ".md"]):
                match = re.search(r"(?:busca|encuentra|search|find)\s+(?:archivos?\s+)?(\S+)", command_lower)
                if match:
                    pattern = match.group(1).replace("'", "")
                    result = file_manager.find(pattern)
                    return result
        
        # List directory
        if any(k in command_lower for k in ["lista", "ls", "list", "muestra"]):
            if any(k in command_lower for k in ["archivo", "directorio", "folder", "dir"]):
                match = re.search(r"(?:en|del|de)?\s*(~?/?[\w/.-]*)", command)
                path = match.group(1) if match else "."
                return file_manager.list(path)
        
        return None  # Couldn't interpret

natural_exec = NaturalExec()

# ============================================================================
# RSS READER
# ============================================================================
class RSSReader:
    @staticmethod
    async def fetch(url):
        import aiohttp
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    content = await resp.text()
                    titles = re.findall(r"<title><!\[CDATA\[(.*?)\]\]></title>", content)
                    return "\n".join([f"📰 {t}" for t in titles[:10]]) or "❌ No titles found"
        except Exception as e:
            return f"❌ Error: {e}"
    
    @staticmethod
    async def summarize(url):
        import aiohttp
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    content = await resp.text()
                    titles = re.findall(r"<title><!\[CDATA\[(.*?)\]\]></title>", content)
                    return f"📰 *Noticias ({len(titles)} items):*\n\n" + "\n".join([f"• {t}" for t in titles[:15]])
        except Exception as e:
            return f"❌ Error: {e}"

rss_reader = RSSReader()

# ============================================================================
# WEATHER
# ============================================================================
class Weather:
    @staticmethod
    async def get(location="Mexico"):
        import aiohttp
        try:
            url = f"https://wttr.in/{location}?format=j1"
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    data = await resp.json()
                    current = data["current_condition"][0]
                    return (f"🌤️ *Clima en {location}:*\n"
                           f"• Temp: {current['temp_C']}°C\n"
                           f"• Sensación: {current['FeelsLikeC']}°C\n"
                           f"• Humedad: {current['humidity']}%\n"
                           f"• Viento: {current['windspeedKmph']} km/h")
        except Exception as e:
            return f"❌ Error: {e}"

weather = Weather()

# ============================================================================
# URL SHORTENER & PASTEBIN
# ============================================================================
class URLShortener:
    @staticmethod
    async def shorten(url):
        import aiohttp
        try:
            api_url = "https://short.link/api/shorten"
            async with aiohttp.ClientSession() as session:
                async with session.post(api_url, json={"url": url}, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        return f"🔗 {result.get('short_url', url)}"
        except:
            pass
        # Fallback: create local short code
        code = hashlib.md5(url.encode()).hexdigest()[:8]
        db.execute("INSERT INTO url_cache (url, short_code, created) VALUES (?, ?, ?)", (url, code, time.strftime("%Y-%m-%d %H:%M")))
        return f"🔗 localhost/{code}"
    
    @staticmethod
    def resolve(code):
        result = db.query("SELECT url FROM url_cache WHERE short_code=?", (code,))
        return result[0][0] if result else None

url_shortener = URLShortener()

class Pastebin:
    @staticmethod
    def save(content, language="text"):
        code = hashlib.md5(content.encode()).hexdigest()[:12]
        db.execute("INSERT INTO pastebin (code, content, created) VALUES (?, ?, ?)", (code, content, time.strftime("%Y-%m-%d %H:%M")))
        return f"📋 Código: `{code}`"
    
    @staticmethod
    def get(code):
        result = db.query("SELECT content FROM pastebin WHERE code=?", (code,))
        return result[0][0] if result else None

pastebin = Pastebin()

# ============================================================================
# SUMMARIZER
# ============================================================================
class Summarizer:
    @staticmethod
    async def summarize_url(url):
        import aiohttp
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    content = await resp.text()
                    
                    # Extract title
                    title_match = re.search(r"<title[^>]*>([^<]+)</title>", content)
                    title = title_match.group(1) if title_match else "Sin título"
                    
                    # Extract meta description
                    desc_match = re.search(r'<meta[^>]*name="description"[^>]*content="([^"]+)"', content)
                    description = desc_match.group(1) if desc_match else ""
                    
                    # Extract main content
                    content_match = re.findall(r'<p[^>]*>([^<]+)</p>', content)
                    paragraphs = [p for p in content_match if len(p) > 50][:5]
                    
                    return f"📄 *{title}*\n\n{description}\n\n" + "\n\n".join([f"▸ {p}" for p in paragraphs])
        except Exception as e:
            return f"❌ Error: {e}"
    
    @staticmethod
    async def summarize_text(text, max_words=100):
        prompt = f"Resume el siguiente texto en máximo {max_words} palabras:\n\n{text[:2000]}"
        return await AI.think(prompt)

summarizer = Summarizer()

# ============================================================================
# REMINDERS & SCHEDULED MESSAGES
# ============================================================================
class Reminders:
    @staticmethod
    async def add(time_str, message):
        try:
            db.execute("INSERT INTO reminders (time, message, created) VALUES (?, ?, ?)", (time_str, message, time.strftime("%Y-%m-%d %H:%M")))
            return f"✅ Recordatorio creado para {time_str}"
        except Exception as e:
            return f"❌ Error: {e}"
    
    @staticmethod
    async def list_pending():
        result = db.query("SELECT id, time, message FROM reminders ORDER BY time LIMIT 10")
        if not result:
            return "📝 No hay recordatorios pendientes"
        return "📝 *Recordatorios:*\n\n" + "\n".join([f"• `{r[0]}` - {r[1]}: {r[2]}" for r in result])
    
    @staticmethod
    async def delete(id):
        try:
            db.execute("DELETE FROM reminders WHERE id=?", (id,))
            return f"✅ Recordatorio {id} eliminado"
        except Exception as e:
            return f"❌ Error: {e}"

reminders = Reminders()

class ScheduledMessages:
    @staticmethod
    async def add(cron, message):
        try:
            db.execute("INSERT INTO scheduled_messages (cron, message, created) VALUES (?, ?, ?)", (cron, message, time.strftime("%Y-%m-%d %H:%M")))
            return f"✅ Mensaje programado: {cron}"
        except Exception as e:
            return f"❌ Error: {e}"
    
    @staticmethod
    async def list_all():
        result = db.query("SELECT id, cron, message FROM scheduled_messages")
        if not result:
            return "📅 No hay mensajes programados"
        return "📅 *Mensajes programados:*\n\n" + "\n".join([f"• `{r[0]}` - {r[1]}: {r[2][:50]}" for r in result])

scheduled_messages = ScheduledMessages()

# ============================================================================
# CRON SCHEDULER
# ============================================================================
class CronScheduler:
    def __init__(self):
        self.jobs = {}
        self.running = False
    
    def add_job(self, job_id, interval_seconds, task_fn):
        self.jobs[job_id] = {"interval": interval_seconds, "last": time.time(), "task": task_fn, "enabled": True}
        logger.info(f"Cron job added: {job_id} every {interval_seconds}s")
    
    async def run(self, app):
        self.running = True
        while self.running:
            now = time.time()
            for job_id, job in list(self.jobs.items()):
                if job["enabled"] and now - job["last"] >= job["interval"]:
                    try:
                        await job["task"](app)
                        job["last"] = now
                    except Exception as e:
                        logger.error(f"Cron job error {job_id}: {e}")
            await asyncio.sleep(10)
    
    def enable(self, job_id, enabled=True):
        if job_id in self.jobs:
            self.jobs[job_id]["enabled"] = enabled
    
    def list_jobs(self):
        return [f"{jid} ({j['interval']}s, {'ON' if j['enabled'] else 'OFF'})" for jid, j in self.jobs.items()]

cron_scheduler = CronScheduler()

# ============================================================================
# HEALTH CHECK & ALERTS
# ============================================================================
class HealthChecker:
    def __init__(self):
        self.alerts = []
        self.thresholds = {"disk_percent": 90, "mem_percent": 90, "cpu_percent": 95}
    
    async def check(self, app):
        try:
            alerts = []
            result = subprocess.check_output("df -h / | tail -1 | awk '{print $5}'", shell=True).decode().strip()
            disk_pct = int(result.replace("%", ""))
            if disk_pct >= self.thresholds["disk_percent"]:
                alerts.append(f"💾 Disco al {disk_pct}%!")
            
            result = subprocess.check_output("free | grep Mem | awk '{print int($3/$2*100)}'", shell=True).decode().strip()
            if result.isdigit() and int(result) >= self.thresholds["mem_percent"]:
                alerts.append(f"📊 RAM al {result}%!")
            
            if alerts:
                msg = "🚨 *Alertas:*\n\n" + "\n".join(alerts)
                await app.bot.send_message(chat_id=OWNER_ID, text=msg, parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Health check error: {e}")
    
    def set_threshold(self, metric, value):
        if metric in self.thresholds:
            self.thresholds[metric] = value

health_checker = HealthChecker()
cron_scheduler.add_job("health_check", 1800, health_checker.check)

# ============================================================================
# HEARTBEAT SYSTEM
# ============================================================================
class Heartbeat:
    def __init__(self):
        self.enabled = True
        self.interval = 1800  # 30 min default
        self.stats_enabled = False
        self.last_beat = None
        self.start_time = time.time()
        self.beats = 0
    
    async def beat(self, app):
        """Send heartbeat to owner"""
        if not self.enabled:
            return
        
        self.beats += 1
        self.last_beat = time.strftime("%Y-%m-%d %H:%M:%S")
        
        if self.stats_enabled:
            msg = self.get_stats()
        else:
            msg = f"🛡️ *Heartbeat v{VERSION}*\n\n✅ Activo desde {self.uptime()}\n💓 Beats: {self.beats}\n⏰ {self.last_beat}"
        
        try:
            await app.bot.send_message(chat_id=OWNER_ID, text=msg, parse_mode="Markdown")
            activity_log.log("HEARTBEAT", f"Beat #{self.beats}")
        except Exception as e:
            logger.error(f"Heartbeat error: {e}")
    
    def get_stats(self):
        """Get full stats"""
        try:
            disk = subprocess.check_output("df -h / | tail -1 | awk '{print $3}'", shell=True).decode().strip()
            disk_pct = subprocess.check_output("df -h / | tail -1 | awk '{print $5}'", shell=True).decode().strip()
            ram_used = subprocess.check_output("free -h | grep Mem | awk '{print $3}'", shell=True).decode().strip()
            ram_pct = subprocess.check_output("free | grep Mem | awk '{print int($3/$2*100)}'", shell=True).decode().strip()
            uptime = subprocess.check_output("uptime | awk '{print $3}'", shell=True).decode().strip()
            load = subprocess.check_output("uptime | awk '{print $10}'", shell=True).decode().strip()
            temp = subprocess.check_output("cat /sys/class/thermal/thermal_zone0/temp 2>/dev/null || echo 'N/A'", shell=True).decode().strip()
            if temp != 'N/A' and temp.isdigit():
                temp = f"{int(temp)/1000:.1f}°C"
        except:
            disk, disk_pct, ram_used, ram_pct, uptime, load, temp = "?", "?", "?", "?", "?", "?", "?"
        
        return (f"🛡️ *Heartbeat v{VERSION}*")
    
    def uptime(self):
        seconds = int(time.time() - self.start_time)
        h, rem = divmod(seconds, 3600)
        m, s = divmod(rem, 60)
        if h > 0:
            return f"{h}h {m}m"
        return f"{m}m {s}s"
    
    def toggle(self, enabled=None):
        if enabled is None:
            self.enabled = not self.enabled
        else:
            self.enabled = enabled
        return self.enabled

heartbeat = Heartbeat()
cron_scheduler.add_job("heartbeat", 1800, heartbeat.beat)

# ============================================================================
# AI BRAIN
# ============================================================================
class AI:
    @staticmethod
    async def think(prompt: str, context: str = "", conv_id="default") -> str:
        import aiohttp
        
        prompt = memory.apply_learning(prompt)
        url = "https://api.minimax.io/anthropic/v1/messages"
        headers = {"Authorization": f"Bearer {MINIMAX_KEY}", "Content-Type": "application/json", "anthropic-version": "2023-06-01"}
        system_prompt = memory.get_persona_prompt()
        
        # Add concise directive
        user_msg = prompt
        if "Responde utilmente" in prompt:
            user_msg = prompt.replace("Responde utilmente.", "eres MiraiDroid. Respuestas concisas y directas. No narr tus acciones. Solo responde.")
        
        messages = [{"role": "system", "content": system_prompt + "\n\nIMPORTANTE: Responde de forma concisa. Maximo 3-4 lineas si es posible. Ve al grano."}]
        if context:
            messages.append({"role": "assistant", "content": context})
        messages.append({"role": "user", "content": user_msg})
        
        data = {"model": "MiniMax-M2.7", "max_tokens": 1024, "messages": messages}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=data, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                    response_text = await resp.text()
                    
                    if resp.status == 200:
                        try:
                            result = json.loads(response_text)
                        except json.JSONDecodeError:
                            return "❌ Error decodificando respuesta"
                        
                        if isinstance(result, list):
                            for item in result:
                                if isinstance(item, dict) and item.get("type") == "text":
                                    return item.get("text", "⚠️ Empty text")
                            return str(result)
                        
                        if "content" in result:
                            content = result["content"]
                            if isinstance(content, list):
                                for block in content:
                                    if isinstance(block, dict) and block.get("type") == "text":
                                        return block.get("text", "⚠️ Empty text")
                            return str(content)
                        
                        return str(result)[:500]
                    else:
                        return f"❌ AI Error ({resp.status})"
                        
        except asyncio.TimeoutError:
            return await self.groq_fallback(messages)
        except Exception as e:
            return await self.groq_fallback(messages)
    
    async def groq_fallback(self, messages):
        """Use Groq as fallback when MiniMax fails"""
        import aiohttp
        try:
            # Convert messages format for Groq
            groq_messages = []
            for msg in messages:
                groq_messages.append({"role": msg["role"], "content": msg["content"]})
            
            url = "https://api.groq.com/openai/v1/chat/completions"
            headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
            data = {
                "model": "llama-3.1-8b-instant",
                "messages": groq_messages,
                "max_tokens": 1024
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=data, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        if "choices" in result and result["choices"]:
                            return result["choices"][0]["message"]["content"]
                    return "❌ Groq fallback failed"
        except Exception as e:
            return "❌ Both MiniMax and Groq failed"

# ============================================================================
# SELF-IMPROVEMENT
# ============================================================================
class SelfImprover:
    @staticmethod
    async def improve(request: str) -> str:
        current_code = (BASE_DIR / "miraidroid.py").read_text()
        prompt = f"""Eres un programador experto en Python. El usuario quiere: {request}
Código actual (primeros 3000 caracteres):
```python
{current_code[:3000]}
```
Proporciona ONLY el código mejorado completo. Sin explicaciones."""
        
        response = await AI.think(prompt)
        
        if "import" in response and "def " in response:
            backup_manager.create_backup(f"improve: {request[:30]}")
            (BASE_DIR / "miraidroid.py").write_text(response)
            activity_log.log("SELF_IMPROVE", request)
            return f"✅ ¡Código mejorado!\n\nBackup automático creado.\n\nPreview:\n```python\n{response[:1000]}...\n```"
        
        return response

# ============================================================================
# SCREENSHOT & IMAGE ANALYSIS
# ============================================================================
class Screenshot:
    @staticmethod
    def capture(path=None):
        if path is None:
            path = BASE_DIR / "screenshot.png"
        try:
            subprocess.run("termux-screenshot -f " + str(path), shell=True, capture_output=True, timeout=10)
            if Path(path).exists():
                return str(path)
            subprocess.run("screencap -p " + str(path), shell=True, capture_output=True, timeout=10)
            return str(path) if Path(path).exists() else "❌ No se pudo capturar"
        except Exception as e:
            return f"❌ Error: {e}"

screenshot = Screenshot()

class ImageAnalyzer:
    @staticmethod
    async def analyze(image_path, prompt="Describe esta imagen"):
        import aiohttp
        try:
            with open(image_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode()
            
            url = "https://api.minimax.io/anthropic/v1/messages"
            headers = {"Authorization": f"Bearer {MINIMAX_KEY}", "Content-Type": "application/json", "anthropic-version": "2023-06-01"}
            data = {"model": "MiniMax-M2.7", "max_tokens": 512, "messages": [{"role": "user", "content": [{"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": image_data}}, {"type": "text", "text": prompt}]}]}
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=data, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        if isinstance(result, list):
                            for item in result:
                                if isinstance(item, dict) and item.get("type") == "text":
                                    return item.get("text", "⚠️ No description")
                        return str(result)[:500]
                    else:
                        return f"❌ Error: {resp.status}"
        except Exception as e:
            return f"❌ Error: {e}"

image_analyzer = ImageAnalyzer()

# ============================================================================
# CUSTOM KEYBOARD MARKUPS
# ============================================================================
def quick_actions_keyboard():
    keyboard = [
        [InlineKeyboardButton("📊 Status", callback_data="status"), InlineKeyboardButton("💾 Disco", callback_data="disk")],
        [InlineKeyboardButton("🔄 Pull", callback_data="git_pull"), InlineKeyboardButton("📝 Help", callback_data="help")],
        [InlineKeyboardButton("🔍 Search", callback_data="search"), InlineKeyboardButton("📋 Logs", callback_data="logs")],
    ]
    return InlineKeyboardMarkup(keyboard)

# ============================================================================
# GLOBAL
# ============================================================================
memory = Memory()

# ============================================================================
# HANDLERS
# ============================================================================

async def start_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        await update.message.reply_text("❌ Este bot solo responde a su dueño.")
        return
    keyboard = quick_actions_keyboard()
    await update.message.reply_text(f"🛡️ *MiraiDroid v{VERSION} activo*\n\nSolo tú. 🤖", reply_markup=keyboard, parse_mode="Markdown")

async def help_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
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
    if not is_owner(update.effective_user.id):
        return
    try:
        disk = subprocess.check_output("df -h / | tail -1 | awk '{print $3}'", shell=True).decode().strip()
        ram = subprocess.check_output("free -h | grep Mem | awk '{print $3}'", shell=True).decode().strip()
        uptime = subprocess.check_output("uptime | awk '{print $3}'", shell=True).decode().strip()
    except:
        disk, ram, uptime = "?", "?", "?"
    await update.message.reply_text(f"✅ v{VERSION} | 💾 {disk} | 📊 {ram} | ⏱️ {uptime} | 👤 {memory.data.get('persona', 'default')}")

async def version_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return
    await update.message.reply_text(f"📦 v{VERSION}")


async def restart_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Restart the bot"""
    if not is_owner(update.effective_user.id):
        return
    
    await update.message.reply_text("Reiniciando... Nos vemos en breve! 🔄")
    
    try:
        # Send restart message first
        import requests
        requests.get(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            params={"chat_id": OWNER_ID, "text": "🔄 Reiniciando...", "parse_mode": "Markdown"},
            timeout=5
        )
    except:
        pass
    
    # Close gracefully
    db.close()
    await app.stop()
    
    # Use subprocess to restart reliably
    import subprocess
    import sys
    subprocess.Popen(
        [sys.executable, str(BASE_DIR / "miraidroid.py")],
        cwd=str(BASE_DIR),
        stdout=open(str(BASE_DIR / "logs" / "miraidroid.log"), "a"),
        stderr=open(str(BASE_DIR / "logs" / "error.log"), "a")
    )
    
    # Exit this process
    sys.exit(0)

async def uptime_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return
    try:
        result = subprocess.check_output("uptime", shell=True).decode()
        await update.message.reply_text(f"⏱️ {result}")
    except Exception as e:
        await update.message.reply_text(f"❌ {e}")

# System commands
async def ps_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return
    await update.message.reply_text(process_manager.list(), parse_mode="Markdown")

async def kill_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return
    if not ctx.args:
        await update.message.reply_text("❌ Uso: /kill [pid]")
        return
    await update.message.reply_text(process_manager.kill(ctx.args[0]))

async def top_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return
    limit = int(ctx.args[0]) if ctx.args and ctx.args[0].isdigit() else 5
    await update.message.reply_text(process_manager.top(limit), parse_mode="Markdown")

async def ping_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return
    host = ctx.args[0] if ctx.args else "google.com"
    await update.message.reply_text(await network_tools.ping(host))

async def dns_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return
    if not ctx.args:
        await update.message.reply_text("❌ Uso: /dns [domain]")
        return
    await update.message.reply_text(await network_tools.dns(ctx.args[0]))

async def ports_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return
    if not ctx.args:
        await update.message.reply_text("❌ Uso: /ports [host] [puertos]")
        return
    host = ctx.args[0]
    ports = ctx.args[1] if len(ctx.args) > 1 else "22,80,443,3000"
    await update.message.reply_text(await network_tools.ports(host, ports))

async def battery_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return
    await update.message.reply_text(battery_monitor.status(), parse_mode="Markdown")

async def apps_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return
    await update.message.reply_text(app_manager.list_installed(), parse_mode="Markdown")

# File commands
async def files_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return
    path = ctx.args[0] if ctx.args else "."
    await update.message.reply_text(file_manager.list(path))

async def read_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return
    if not ctx.args:
        await update.message.reply_text("❌ Uso: /read <archivo>")
        return
    await update.message.reply_text(file_manager.read(ctx.args[0]))

async def write_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return
    if len(ctx.args) < 2:
        await update.message.reply_text("❌ Uso: /write <path> <contenido>")
        return
    await update.message.reply_text(file_manager.write(ctx.args[0], " ".join(ctx.args[1:])))

async def find_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return
    if not ctx.args:
        await update.message.reply_text("❌ Uso: /find [pattern]")
        return
    await update.message.reply_text(file_manager.find(ctx.args[0]))

# Git commands
async def git_status_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return
    await update.message.reply_text(f"```\n{git_manager.status()}\n```", parse_mode="Markdown")

async def git_pull_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return
    await update.message.reply_text(f"```\n{git_manager.pull()}\n```", parse_mode="Markdown")

async def git_commit_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return
    if not ctx.args:
        await update.message.reply_text("❌ Uso: /git_commit <msg>")
        return
    await update.message.reply_text(f"```\n{git_manager.add()}\n{git_manager.commit(' '.join(ctx.args))}\n```", parse_mode="Markdown")

async def git_push_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return
    await update.message.reply_text(f"```\n{git_manager.push()}\n```", parse_mode="Markdown")

async def git_log_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return
    await update.message.reply_text(f"```\n{git_manager.log()}\n```", parse_mode="Markdown")

# Docker
async def docker_ps_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return
    await update.message.reply_text(f"```\n{docker_monitor.status()}\n```", parse_mode="Markdown")

async def docker_stats_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return
    await update.message.reply_text(f"```\n{docker_monitor.stats()}\n```", parse_mode="Markdown")

async def docker_logs_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return
    if not ctx.args:
        await update.message.reply_text("❌ Uso: /docker_logs <nombre>")
        return
    await update.message.reply_text(f"```\n{docker_monitor.logs(ctx.args[0])}\n```", parse_mode="Markdown")

# Skills, Tools, Plugins
async def skills_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return
    skills = skill_manager.list_skills()
    await update.message.reply_text("🛠️ *Skills:*\n• " + "\n• ".join(skills) if skills else "📝 No hay skills")

async def tools_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return
    from tool_manager import tool_manager as tm
    tools = tm.list_tools()
    await update.message.reply_text("🔧 *Tools:*\n• " + "\n• ".join(tools) if tools else "📝 No hay tools")

async def plugins_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return
    info = plugin_manager.list_plugins()
    msg = f"📦 *Plugins disponibles:*\n• " + "\n• ".join(info["available"]) + f"\n\n🟢 *Cargados:* " + ", ".join(info["loaded"]) if info["loaded"] else ""
    await update.message.reply_text(msg or "📝 No hay plugins disponibles")

async def load_plugin_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return
    if not ctx.args:
        await update.message.reply_text("❌ Uso: /load_plugin [nombre]")
        return
    success, msg = plugin_manager.load_plugin(ctx.args[0])
    await update.message.reply_text(f"✅ {msg}" if success else f"❌ {msg}")

# Persona & Learning
async def persona_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
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
    if not is_owner(update.effective_user.id):
        return
    memory.data["learning"] = []
    memory.save()
    await update.message.reply_text("✅ Aprendizaje olvidado")

# AI & Code
async def improve_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return
    if not ctx.args:
        await update.message.reply_text("❌ Uso: /improve <request>")
        return
    await update.message.reply_text("🔄 Mejorando código...")
    await update.message.reply_text(await SelfImprover.improve(" ".join(ctx.args))[:4000])

async def exec_code_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return
    if not ctx.args:
        await update.message.reply_text("❌ Uso: /exec_code [python|bash] <codigo>")
        return
    lang = ctx.args[0] if ctx.args[0] in ["python", "bash", "shell"] else "python"
    code = " ".join(ctx.args[1:]) if lang in ctx.args else " ".join(ctx.args)
    await update.message.reply_text(await code_interpreter.execute(code, lang if "code" in ctx.args[0] else "python"))

async def analyze_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return
    await update.message.reply_text("🔍 Analizando...")

# RSS & Weather
async def rss_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return
    if not ctx.args:
        await update.message.reply_text("❌ Uso: /rss [url]")
        return
    await update.message.reply_text(await rss_reader.summarize(ctx.args[0]))

async def weather_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return
    loc = ctx.args[0] if ctx.args else "Mexico"
    await update.message.reply_text(await weather.get(loc))

# URL & Pastebin
async def shorten_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return
    if not ctx.args:
        await update.message.reply_text("❌ Uso: /shorten [url]")
        return
    await update.message.reply_text(await url_shortener.shorten(ctx.args[0]))

async def paste_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return
    if not ctx.args:
        await update.message.reply_text("❌ Uso: /paste [contenido]")
        return
    await update.message.reply_text(pastebin.save(" ".join(ctx.args)))

async def getpaste_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
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

# Summarize
async def summarize_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return
    if not ctx.args:
        await update.message.reply_text("❌ Uso: /summarize [url]")
        return
    await update.message.reply_text(await summarizer.summarize_url(ctx.args[0]))

# Reminders & Scheduled
async def remind_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return
    if len(ctx.args) < 2:
        await update.message.reply_text("❌ Uso: /remind [time] [mensaje]")
        return
    time_str = ctx.args[0]
    message = " ".join(ctx.args[1:])
    await update.message.reply_text(await reminders.add(time_str, message))

async def reminders_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return
    await update.message.reply_text(await reminders.list_pending())

async def schedule_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return
    if not ctx.args:
        await update.message.reply_text("❌ Uso: /schedule [cron] [mensaje]")
        return
    await update.message.reply_text(await scheduled_messages.add(ctx.args[0], " ".join(ctx.args[1:])))

# Cron
async def cron_list_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return
    jobs = cron_scheduler.list_jobs()
    await update.message.reply_text("⏰ *Cron Jobs:*\n• " + "\n• ".join(jobs) if jobs else "📝 No hay jobs")

async def cron_enable_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return
    if not ctx.args:
        await update.message.reply_text("❌ Uso: /cron_enable [job_id]")
        return
    cron_scheduler.enable(ctx.args[0], True)
    await update.message.reply_text(f"✅ Job '{ctx.args[0]}' ON")

async def cron_disable_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return
    if not ctx.args:
        await update.message.reply_text("❌ Uso: /cron_disable [job_id]")
        return
    cron_scheduler.enable(ctx.args[0], False)
    await update.message.reply_text(f"✅ Job '{ctx.args[0]}' OFF")

# Heartbeat
async def heartbeat_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return
    status = "ON ✅" if heartbeat.enabled else "OFF ❌"
    stats_status = "ON" if heartbeat.stats_enabled else "OFF"
    await heartbeat.beat(ctx._application)
    await update.message.reply_text(f"💓 Heartbeat: {status}\n📊 Stats: {stats_status}\n⏱️ Uptime: {heartbeat.uptime()}\n� beats enviados: {heartbeat.beats}")

async def heartbeat_on_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return
    heartbeat.toggle(True)
    await update.message.reply_text("✅ Heartbeat Activado (cada 30 min)")

async def heartbeat_off_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return
    heartbeat.toggle(False)
    await update.message.reply_text("❌ Heartbeat Desactivado")

async def heartbeat_stats_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return
    heartbeat.stats_enabled = not heartbeat.stats_enabled
    status = "ON" if heartbeat.stats_enabled else "OFF"
    await update.message.reply_text(f"📊 Heartbeat stats: {status}\n\nLos heartbeats ahora incluirán: CPU, RAM, disco, uptime, temperatura")

# Stats
async def stats_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return
    await update.message.reply_text(stats.get_summary(), parse_mode="Markdown")

async def rate_limit_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return
    remaining = rate_limiter.get_remaining(update.effective_user.id)
    await update.message.reply_text(f"📊 Rate limit: {remaining}/20 mensajes por minuto restantes")

# Backup
async def backup_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return
    ts = backup_manager.create_backup("manual")
    await update.message.reply_text(f"✅ Backup: {ts}")

async def backup_list_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return
    backups = backup_manager.list_backups()
    await update.message.reply_text("📦 *Backups:*\n• " + "\n• ".join(backups[:10]) if backups else "📝 No hay backups")

async def rollback_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return
    if not ctx.args:
        await update.message.reply_text("❌ Uso: /rollback [timestamp]")
        return
    if backup_manager.restore_backup(ctx.args[0]):
        await update.message.reply_text(f"✅ Restaurado. ¡Reinicia!")
    else:
        await update.message.reply_text(f"❌ Backup no encontrado")

# Activity & Security
async def activity_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return
    recent = activity_log.get_recent()
    msg = "📋 *Actividad:*\n\n" + "\n".join([f"**{a['time']}** {a['action']}" for a in recent[-10:]])
    await update.message.reply_text(msg, parse_mode="Markdown")

async def encrypt_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return
    if not ctx.args:
        await update.message.reply_text("❌ Uso: /encrypt [texto]")
        return
    await update.message.reply_text(f"🔐 `{Crypto.encrypt(' '.join(ctx.args))}`", parse_mode="Markdown")

async def decrypt_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return
    if not ctx.args:
        await update.message.reply_text("❌ Uso: /decrypt [texto]")
        return
    await update.message.reply_text(f"🔓 `{Crypto.decrypt(' '.join(ctx.args))}`", parse_mode="Markdown")

# Memory
async def memory_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return
    history = memory.data.get("history", [])
    msg = "📝 *Mensajes:*\n\n" + "\n".join([f"**{m['role']}**: {m['content'][:60]}..." for m in history[-5:]])
    await update.message.reply_text(msg or "📝 Vacío", parse_mode="Markdown")

async def clear_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return
    memory.data["history"] = []
    memory.data["conversations"] = {}
    memory.save()
    await update.message.reply_text("✅ Limpiado")

# Screenshot
async def screenshot_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return
    await update.message.reply_text("📸 Capturando...")
    path = screenshot.capture()
    if path.endswith(".png") or path.endswith(".jpg"):
        with open(path, "rb") as f:
            await update.message.reply_photo(photo=f, caption="📸")
    else:
        await update.message.reply_text(path)

# Message handler

# ============================================================================
# AUTONOMOUS ROUTER - Intent-based tool selection
# ============================================================================
# ============================================================================
# WEB SEARCH (Tavily + DuckDuckGo)
# ============================================================================
class WebSearch:
    """Web search using Tavily API with DuckDuckGo fallback"""
    
    @staticmethod
    async def search(query, max_results=8):
        import aiohttp
        import re
        
        # Try Tavily first
        if TAVILY_API_KEY:
            try:
                url = "https://api.tavily.com/search"
                headers = {"Content-Type": "application/json"}
                data = {
                    "api_key": TAVILY_API_KEY,
                    "query": query,
                    "max_results": max_results,
                    "include_answer": True
                }
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, headers=headers, json=data, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                        if resp.status == 200:
                            result = await resp.json()
                            return WebSearch.format_tavily(query, result)
            except Exception as e:
                pass
        
        # Fallback to DuckDuckGo
        return await WebSearch.ddg_search(query, max_results)
    
    @staticmethod
    def format_tavily(query, data):
        results = data.get("results", [])
        answer = data.get("answer", "")
        
        msg = f"Buscando: {query}\n\n"
        
        if answer:
            msg += f"Respuesta: {answer[:300]}\n\n"
        
        if results:
            msg += "Resultados:\n"
            for i, r in enumerate(results[:8], 1):
                title = r.get("title", "Sin titulo")[:70]
                url = r.get("url", "")
                msg += f"\n{i}. {title}\n   {url}"
        
        return msg if results else "No encontre resultados."
    
    @staticmethod
    async def ddg_search(query, max_results=8):
        import aiohttp
        import re
        
        try:
            url = "https://html.duckduckgo.com/html/"
            params = {"q": query}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    html = await resp.text()
            
            # Simple regex to find result links and titles
            # Pattern: <a class="result__a" href="URL">TITLE</a>
            pattern = r'<a class="result__a" href="([^"]+)"[^>]*>([^<]+)</a>'
            matches = re.findall(pattern, html)
            
            if not matches:
                return "No encontre resultados para esa busqueda."
            
            msg = f"Buscando: {query}\n\n"
            msg += "Resultados:\n"
            
            for i, (url, title) in enumerate(matches[:max_results], 1):
                # Clean title
                title = re.sub(r"<[^>]+>", "", title).strip()
                if len(title) > 5:
                    msg += f"\n{i}. {title}\n   {url}"
            
            return msg
            
        except Exception as e:
            return f"Error en busqueda: {e}"

web_search = WebSearch()

class AutonomousRouter:
    """Routes user requests to appropriate tools - ONLY for clear tool requests"""
    
    def __init__(self):
        self.intents = self.build_intent_map()
    
    def build_intent_map(self):
        # Only match CLEAR tool requests - not general conversation
        return {
            "search": {
                "keywords": ["busca en internet", "busca sobre", "search for", "investiga sobre", "busca noticias"],
                "handler": "handle_search",
                "strict": True
            },
            "weather": {
                "keywords": ["clima en", "weather in", "temperatura en", "hace calor en", "hace frio en"],
                "handler": "handle_weather",
                "strict": True
            },
            "calc": {
                "keywords": ["calcula ", "cuanto es ", "cuanto es ", "="],
                "handler": "handle_calc",
                "strict": True
            },
            "sysmon": {
                "keywords": ["estado del sistema", "system status", "uso de cpu"],
                "handler": "handle_sysmon",
                "strict": True
            },
            "time": {
                "keywords": ["que hora es", "what time", "fecha hoy"],
                "handler": "handle_time",
                "strict": True
            },
        }
    
    async def route(self, text, update, ctx):
        text_lower = text.lower()
        
        # Only intercept if it's a CLEAR tool request
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
        
        # Check if this is a self-improvement request
        self_improve_keywords = ["mejorarte a ti mismo", "mejorar tu", "mejoras para ti", "como mejorarte", "improve yourself", "improve your", "mejora tu codigo", "mejora ti mismo"]
        is_self_improve = any(kw in query for kw in self_improve_keywords)
        
        for kw in ["busca", "buscar", "search", "investiga", "en internet"]:
            query = query.replace(kw, "").strip()
        
        if not query or len(query) < 2:
            return "Dime que quieres buscar. Ejemplo: busca noticias de IA"
        
        if is_self_improve:
            # Search for technical improvements for AI agents/bots
            tech_query = query + " AI agent bot improvements python telegram 2026"
            result = await web_search.search(tech_query, max_results=8)
            if result:
                return "Buscando mejoras tecnicas para mi codigo...\n\n" + result
            return "No pude buscar mejoras. Intenta de nuevo."
        else:
            result = await web_search.search(query, max_results=8)
            if result:
                return result
            return "No pude hacer la busqueda. Intenta de nuevo."
    
    async def handle_weather(self, text, update, ctx):
        location = "Mexico"
        for kw in ["en ", "para "]:
            if kw in text.lower():
                parts = text.split(kw)
                if len(parts) > 1:
                    location = parts[-1].strip().split()[0]
        return await weather.get(location)
    
    async def handle_calc(self, text, update, ctx):
        import re
        expression = text.lower()
        for kw in ["calcula", "cuanto es", " cuanto es"]:
            expression = expression.replace(kw, "").strip()
        expression = re.sub(r"[^0-9+\-*/().%^√ ]", "", expression)
        expression = expression.replace("^", "**").replace("√", "sqrt").replace("por", "*")
        if not expression:
            return None
        try:
            import math
            result = eval(expression, {"__builtins__": {}, "sqrt": math.sqrt})
            return f"Resultado: {expression} = {result}"
        except:
            return None
    
    async def handle_sysmon(self, text, update, ctx):
        try:
            disk = subprocess.check_output("df -h / | tail -1 | awk '{print $3}'", shell=True).decode().strip()
            ram = subprocess.check_output("free -h | grep Mem | awk '{print $3}'", shell=True).decode().strip()
            return f"Estado del Sistema:\n- Disco: {disk}\n- RAM: {ram}"
        except:
            return "No pude obtener stats"
    
    async def handle_notes(self, text, update, ctx):
        note = text.lower()
        for kw in ["nota", "notas", "anota", "apuntar", "recuerda"]:
            note = note.replace(kw, "").strip()
        if len(note) < 3:
            return None
        memory.data.setdefault("notes", []).append({"text": note, "date": time.strftime("%Y-%m-%d %H:%M")})
        memory.save()
        return f"Nota guardada: {note[:100]}"
    
    async def handle_todos(self, text, update, ctx):
        todo = text.lower()
        for kw in ["tarea", "pendiente", "necesito", "debo", "hacer"]:
            todo = todo.replace(kw, "").strip()
        if len(todo) < 3:
            return None
        memory.data.setdefault("todos", []).append({"text": todo, "done": False, "date": time.strftime("%Y-%m-%d %H:%M")})
        memory.save()
        return f"To-do agregado: {todo[:100]}"
    
    async def handle_news(self, text, update, ctx):
        topic = text.lower().replace("noticias", "").replace("news", "").strip()
        await update.message.reply_text("Buscando noticias...")
        return await web_search.search(f"noticias {topic or 'recientes'} 2026", max_results=5)
    
    async def handle_time(self, text, update, ctx):
        now = datetime.now()
        return f"Hora actual: {now.strftime('%H:%M:%S')}\nFecha: {now.strftime('%Y-%m-%d')}"
    
    async def handle_battery(self, text, update, ctx):
        return await battery_monitor.status()

autonomous_router = AutonomousRouter()

async def msg_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        await update.message.reply_text("❌ Solo Yerik.")
        return
    
    user_id = update.effective_user.id
    
    # Rate limit check
    if not rate_limiter.is_allowed(user_id, "msg"):
        await update.message.reply_text("⏳ Demasiados mensajes. Espera un momento.")
        return
    
    text = update.message.text
    stats.inc("messages")
    
    # Check for alias
    if text.startswith("/") and " " not in text:
        cmd = text[1:].lower()
        if cmd in ALIASES:
            cmd = ALIASES[cmd]
            text = f"/{cmd}"
    
    memory.add_message("user", text)
    context = memory.get_context()
    
    # Show typing indicator
    await update.message.chat.send_action("typing")
    
    # Try autonomous router first
    tool_result = await autonomous_router.route(text, update, ctx)
    if tool_result:
        memory.add_message("assistant", tool_result)
        await update.message.reply_text(tool_result)
        return
    
    # Try natural exec
    natural_result = await natural_exec.execute(text)
    if natural_result:
        memory.add_message("assistant", natural_result)
        await update.message.reply_text(natural_result)
        return
    
    # Default to AI
    response = await AI.think(f"Usuario: '{text}'. Responde útilmente.", context)
    memory.add_message("assistant", response)
    activity_log.log("MSG", text[:50])
    await update.message.reply_text(response)

# Document handler
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

# Photo handler
async def photo_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return
    photo = update.message.photo[-1]
    await update.message.reply_text("📷 Analizando...")
    file = await photo.get_file()
    path = BASE_DIR / "downloads" / f"photo_{int(time.time())}.jpg"
    path.parent.mkdir(parents=True, exist_ok=True)
    await file.download_to_drive(path)
    result = await image_analyzer.analyze(path)
    await update.message.reply_text(result)

# Callback handler


async def voice_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Handle voice messages - transcribe and process"""
    if not is_owner(update.effective_user.id):
        return
    
    voice = update.message.voice
    await update.message.reply_text("🎤 Procesando audio...")
    
    try:
        # Download voice file
        file = await voice.get_file()
        ogg_path = BASE_DIR / "downloads" / f"voice_{int(time.time())}.ogg"
        mp3_path = BASE_DIR / "downloads" / f"voice_{int(time.time())}.mp3"
        ogg_path.parent.mkdir(parents=True, exist_ok=True)
        await file.download_to_drive(ogg_path)
        
        # Try to transcribe with Groq Whisper API first
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
        except Exception as e:
            pass
        
        # Fallback to local whisper if Groq fails
        if not text:
            try:
                import whisper
                model = whisper.load_model("base")
                result = model.transcribe(str(ogg_path))
                text = result["text"]
            except:
                pass
        
        if text:
            # Process as text message
            memory.add_message("user", f"[Audio]: {text}")
            activity_log.log("VOICE", text[:50])
            
            # Try autonomous router
            await update.message.chat.send_action("typing")
            tool_result = await autonomous_router.route(text, update, ctx)
            if tool_result:
                await update.message.reply_text(f"🎤 *Transcripcion:* {text}\n\n{tool_result}")
                return
            
            # Fallback to AI
            response = await AI.think(f"Usuario envio un audio que dice: '{text}'. Responde utilmente.", "")
            await update.message.reply_text(f"🎤 *Transcripcion:* {text}\n\n{response}")
        else:
            await update.message.reply_text("🎤 Audio recibido. Para transcribir necesito whisper instalado. Puedes enviarme el texto de lo que dijiste?")
        
        # Cleanup
        try:
            ogg_path.unlink()
        except:
            pass
            
    except Exception as e:
        await update.message.reply_text(f"Error procesando audio: {e}")

async def callback_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "status":
        await status_cmd(update, ctx)
    elif query.data == "help":
        await help_cmd(update, ctx)
    elif query.data == "disk":
        try:
            disk = subprocess.check_output("df -h / | tail -1 | awk '{print $3}'", shell=True).decode().strip()
            await update.message.reply_text(f"💾 {disk}")
        except:
            pass
    elif query.data == "git_pull":
        await git_pull_cmd(update, ctx)
    elif query.data == "logs":
        await activity_cmd(update, ctx)

# Inline query handler
async def inline_query_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query.query
    if not query:
        return
    results = [types.InlineQueryResultArticle(id="1", title="Buscar", input_message_content=types.InputTextMessageContent(message_text=f"🔍 Busqué: {query}"))]
    await update.inline_query.answer(results)

# ============================================================================
# MAIN
# ============================================================================
app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start_cmd))
app.add_handler(CommandHandler("help", help_cmd))
app.add_handler(CommandHandler("status", status_cmd))
app.add_handler(CommandHandler("version", version_cmd))
app.add_handler(CommandHandler("uptime", uptime_cmd))
async def agent_check_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Full diagnostic check of the agent"""
    if not is_owner(update.effective_user.id):
        return
    
    await update.message.reply_text("🔍 Diagnosticando...")
    
    issues = []
    ok = []
    
    # Check plugins
    plugins_dir = BASE_DIR / "plugins"
    plugins = [f.stem for f in plugins_dir.glob("*.py") if f.name not in ["__init__.py", "plugin_base.py"]]
    if plugins:
        ok.append(f"Plugins: {len(plugins)} ({', '.join(plugins)})")
    else:
        issues.append("No plugins")
    
    # Check skills
    skills_dir = BASE_DIR / "skills"
    skills = [f.stem for f in skills_dir.glob("*.py") if f.name != "__init__.py"]
    if skills:
        ok.append(f"Skills: {len(skills)}")
    else:
        issues.append("No skills")
    
    # Check memory
    memory_file = BASE_DIR / "data" / "memory.json"
    if memory_file.exists():
        size = memory_file.stat().st_size
        ok.append(f"Memory: {size}b")
    else:
        issues.append("Memory missing")
    
    # Check APIs
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
    
    # Build report
    msg = "🔍 *Diagnostic Report*\n\n"
    if ok:
        msg += "✅ *OK:*\n" + "\n".join([f"  • {x}" for x in ok]) + "\n\n"
    if issues:
        msg += "⚠️ *Issues:*\n" + "\n".join([f"  • {x}" for x in issues])
    else:
        msg += "🎉 Todo en orden!"
    msg += f"\n\n📦 v{VERSION} | Uptime: {stats.get_uptime()}"
    
    await update.message.reply_text(msg, parse_mode="Markdown")

app.add_handler(CommandHandler("restart", restart_cmd))
app.add_handler(CommandHandler("agent_check", agent_check_cmd))
app.add_handler(CommandHandler("ps", ps_cmd))
app.add_handler(CommandHandler("kill", kill_cmd))
app.add_handler(CommandHandler("top", top_cmd))
app.add_handler(CommandHandler("ping", ping_cmd))
app.add_handler(CommandHandler("dns", dns_cmd))
app.add_handler(CommandHandler("ports", ports_cmd))
app.add_handler(CommandHandler("battery", battery_cmd))
app.add_handler(CommandHandler("apps", apps_cmd))
app.add_handler(CommandHandler("files", files_cmd))
app.add_handler(CommandHandler("read", read_cmd))
app.add_handler(CommandHandler("write", write_cmd))
app.add_handler(CommandHandler("find", find_cmd))
app.add_handler(CommandHandler("git_status", git_status_cmd))
app.add_handler(CommandHandler("git_pull", git_pull_cmd))
app.add_handler(CommandHandler("git_commit", git_commit_cmd))
app.add_handler(CommandHandler("git_push", git_push_cmd))
app.add_handler(CommandHandler("git_log", git_log_cmd))
app.add_handler(CommandHandler("docker_ps", docker_ps_cmd))
app.add_handler(CommandHandler("docker_stats", docker_stats_cmd))
app.add_handler(CommandHandler("docker_logs", docker_logs_cmd))
app.add_handler(CommandHandler("skills", skills_cmd))
app.add_handler(CommandHandler("tools", tools_cmd))
app.add_handler(CommandHandler("plugins", plugins_cmd))
app.add_handler(CommandHandler("load_plugin", load_plugin_cmd))
app.add_handler(CommandHandler("persona", persona_cmd))
app.add_handler(CommandHandler("learn", learn_cmd))
app.add_handler(CommandHandler("forget", forget_cmd))
app.add_handler(CommandHandler("improve", improve_cmd))
app.add_handler(CommandHandler("exec_code", exec_code_cmd))
app.add_handler(CommandHandler("analyze", analyze_cmd))
app.add_handler(CommandHandler("rss", rss_cmd))
app.add_handler(CommandHandler("weather", weather_cmd))
app.add_handler(CommandHandler("shorten", shorten_cmd))
app.add_handler(CommandHandler("paste", paste_cmd))
app.add_handler(CommandHandler("getpaste", getpaste_cmd))
app.add_handler(CommandHandler("summarize", summarize_cmd))
app.add_handler(CommandHandler("remind", remind_cmd))
app.add_handler(CommandHandler("reminders", reminders_cmd))
app.add_handler(CommandHandler("schedule", schedule_cmd))
app.add_handler(CommandHandler("cron_list", cron_list_cmd))
app.add_handler(CommandHandler("cron_enable", cron_enable_cmd))
app.add_handler(CommandHandler("cron_disable", cron_disable_cmd))
app.add_handler(CommandHandler("heartbeat", heartbeat_cmd))
app.add_handler(CommandHandler("heartbeat_on", heartbeat_on_cmd))
app.add_handler(CommandHandler("heartbeat_off", heartbeat_off_cmd))
app.add_handler(CommandHandler("heartbeat_stats", heartbeat_stats_cmd))
app.add_handler(CommandHandler("stats", stats_cmd))
app.add_handler(CommandHandler("rate_limit", rate_limit_cmd))
app.add_handler(CommandHandler("backup", backup_cmd))
app.add_handler(CommandHandler("backup_list", backup_list_cmd))
app.add_handler(CommandHandler("rollback", rollback_cmd))
app.add_handler(CommandHandler("activity", activity_cmd))
app.add_handler(CommandHandler("encrypt", encrypt_cmd))
app.add_handler(CommandHandler("decrypt", decrypt_cmd))
app.add_handler(CommandHandler("memory", memory_cmd))
app.add_handler(CommandHandler("clear", clear_cmd))
app.add_handler(CommandHandler("screenshot", screenshot_cmd))
app.add_handler(CallbackQueryHandler(callback_handler))
app.add_handler(MessageHandler(filters.Document.ALL, doc_handler))
app.add_handler(MessageHandler(filters.PHOTO, photo_handler))
app.add_handler(MessageHandler(filters.VOICE, voice_handler))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, msg_handler))

# Global error handler - sends errors to Telegram
async def error_handler(update, context):
    """Catch and report all errors to Telegram"""
    error_msg = f"⚠️ *Error Handler*\n\n"
    error_msg += f"`{type(context.error).__name__}: {str(context.error)[:1000]}`\n\n"
    if update and update.effective_message:
        error_msg += f"📍 Chat: {update.effective_chat.id}\n"
        error_msg += f"💬 Mensaje: {update.effective_message.text[:200] if update.effective_message.text else 'N/A'}"
    error_msg += f"\n⏰ {time.strftime('%Y-%m-%d %H:%M:%S')}"
    
    logger.error(f"Telegram error: {context.error}")
    stats.data["errors"] = stats.data.get("errors", 0) + 1
    stats.save()
    
    try:
        await context.bot.send_message(chat_id=OWNER_ID, text=error_msg, parse_mode="Markdown")
    except:
        pass

app.add_error_handler(error_handler)

print(f"🛡️ MiraiDroid v{VERSION} starting...")

def signal_handler(sig, frame):
    db.close()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

# ============================================================================
# MAIN - Simple startup with crash notification
# ============================================================================

# Auto-load plugins from plugins/ folder at startup
def auto_load_plugins():
    """Load all plugins automatically"""
    plugins_dir = BASE_DIR / "plugins"
    if not plugins_dir.exists():
        return []
    loaded = []
    for plugin_file in plugins_dir.glob("*.py"):
        if plugin_file.name.startswith("_") or plugin_file.name == "plugin_base.py":
            continue
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location(f"plugin_{plugin_file.stem}", plugin_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            loaded.append(plugin_file.stem)
            print(f"Loaded plugin: {plugin_file.stem}")
        except Exception as e:
            print(f"Failed to load {plugin_file.name}: {e}")
    return loaded




if __name__ == "__main__":
    print(f"🛡️ MiraiDroid v{VERSION} starting...")
    print("Press Ctrl+C to stop")
    
    # Send startup message to owner
    try:
        import requests
        requests.get(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            params={"chat_id": OWNER_ID, "text": "🛡️ Estoy activo nuevamente! MiraiDroid v" + VERSION + " iniciado. 👋", "parse_mode": "Markdown"},
            timeout=10
        )
    except:
        pass
    
    # Auto-load plugins
    try:
        plugins = auto_load_plugins()
        if plugins:
            print(f"Plugins auto-loaded: {plugins}")
    except:
        pass
    
    # Run polling - python-telegram-bot handles the event loop
    try:
        app.run_polling(drop_pending_updates=True)
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped")
        db.close()
    except Exception as e:
        import traceback
        error_msg = f"{type(e).__name__}: {e}\n\n{traceback.format_exc()[-2000:]}"
        logger.error(f"Bot crashed: {error_msg}")
        try:
            import requests
            requests.get(f"https://api.telegram.org/bot{TOKEN}/sendMessage", params={
                "chat_id": OWNER_ID,
                "text": f"🚨 *ERROR en MiraiDroid*\n\n```\n{error_msg[:3500]}\n```\n⏰ {time.strftime('%Y-%m-%d %H:%M:%S')}",
                "parse_mode": "Markdown"
            }, timeout=10)
        except:
            pass
        print("Bot crashed. Check logs.")
