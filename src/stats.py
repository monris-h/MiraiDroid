"""
Stats - tracking de mensajes, comandos, errores, uptime
"""
import json
import time
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from src.config import BASE_DIR


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