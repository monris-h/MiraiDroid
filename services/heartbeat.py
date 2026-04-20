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
        from src.utils import is_windows
        import subprocess

        if is_windows():
            return f"🛡️ *Heartbeat v{self.get_version()}*"
        else:
            try:
                disk = subprocess.check_output("df -h / | tail -1 | awk '{print $3}'", shell=True, text=True).strip()
                disk_pct = subprocess.check_output("df -h / | tail -1 | awk '{print $5}'", shell=True, text=True).strip()
                ram_used = subprocess.check_output("free -h | grep Mem | awk '{print $3}'", shell=True, text=True).strip()
                ram_pct = subprocess.check_output("free | grep Mem | awk '{print int($3/$2*100)}'", shell=True, text=True).strip()
                uptime = subprocess.check_output("uptime | awk '{print $3}'", shell=True, text=True).strip()
                load = subprocess.check_output("uptime | awk '{print $10}'", shell=True, text=True).strip()
                temp = subprocess.check_output("cat /sys/class/thermal/thermal_zone0/temp 2>/dev/null || echo 'N/A'", shell=True, text=True).strip()
                if temp.isdigit():
                    temp = f"{int(temp)/1000:.1f}°C"
            except:
                return f"🛡️ *Heartbeat v{self.get_version()}*"

        return f"🛡️ *Heartbeat v{self.get_version()}*"

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