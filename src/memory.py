"""
Memory - persistencia de conversación, learning, notas, y actividad
"""
import json
import time
from pathlib import Path
from .config import BASE_DIR, VERSION
from .constants import PERSONAS

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