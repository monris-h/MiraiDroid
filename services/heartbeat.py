"""
Heartbeat - mensajes periódicos al owner con stats opcionales
"""
import time
from src.memory import activity_log

class Heartbeat:
    def __init__(self):
        self.enabled = True
        self.interval = 1800
        self.stats_enabled = False
        self.last_beat = None
        self.start_time = time.time()
        self.beats = 0

    async def beat(self, app):
        from src.config import OWNER_ID, VERSION

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
            pass

    def get_stats(self):
        from src.system_tools import system_info
        return f"🛡️ *Heartbeat v{self.get_version()}*\n\n{system_info.get_all()}"

    def get_version(self):
        from src.config import VERSION
        return VERSION

    def uptime(self):
        seconds = int(time.time() - self.start_time)
        h, rem = divmod(seconds, 3600)
        m, s = divmod(rem, 60)
        return f"{h}h {m}m" if h > 0 else f"{m}m {s}s"

    def toggle(self, enabled=None):
        if enabled is None:
            self.enabled = not self.enabled
        else:
            self.enabled = enabled
        return self.enabled

heartbeat = Heartbeat()