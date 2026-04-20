"""
Health Checker - alertas de disco, RAM, CPU
"""
import subprocess
from src.utils import is_windows

class HealthChecker:
    def __init__(self):
        self.alerts = []
        self.thresholds = {"disk_percent": 90, "mem_percent": 90, "cpu_percent": 95}

    def _get_disk_percent(self):
        """Get disk usage percentage - platform agnostic"""
        try:
            if is_windows():
                result = subprocess.check_output(
                    'wmic logicaldisk get size,freespace,caption /format:list',
                    shell=True, text=True, stderr=subprocess.DEVNULL
                )
                for line in result.split("\n"):
                    if 'FreeSpace' in line and 'C:' in result:
                        try:
                            freespace = int(line.split("=")[-1].strip())
                            for l2 in result.split("\n"):
                                if 'Size' in l2 and 'FreeSpace' not in l2:
                                    totalspace = int(l2.split("=")[-1].strip())
                                    if totalspace > 0:
                                        return int((1 - freespace/totalspace) * 100)
                        except:
                            pass
                        break
            else:
                result = subprocess.check_output(
                    "df -h / | tail -1 | awk '{print $5}'",
                    shell=True, text=True
                ).strip()
                return int(result.replace("%", ""))
        except:
            pass
        return None

    def _get_mem_percent(self):
        """Get memory usage percentage - platform agnostic"""
        try:
            if is_windows():
                result = subprocess.check_output(
                    'wmic OS get FreePhysicalMemory,TotalVisibleMemorySize /format:list',
                    shell=True, text=True
                )
                free_mem, total_mem = 0, 1
                for line in result.split("\n"):
                    if 'FreePhysicalMemory' in line:
                        free_mem = int(line.split("=")[-1].strip())
                    if 'TotalVisibleMemorySize' in line:
                        total_mem = int(line.split("=")[-1].strip())
                if total_mem > 0:
                    return int((1 - free_mem/total_mem) * 100)
            else:
                result = subprocess.check_output(
                    "free | grep Mem | awk '{print int($3/$2*100)}'",
                    shell=True, text=True
                ).strip()
                if result.isdigit():
                    return int(result)
        except:
            pass
        return None

    async def check(self, app):
        from src.config import OWNER_ID

        try:
            alerts = []
            disk_pct = self._get_disk_percent()
            if disk_pct is not None and disk_pct >= self.thresholds["disk_percent"]:
                alerts.append(f"💾 Disco al {disk_pct}%!")

            mem_pct = self._get_mem_percent()
            if mem_pct is not None and mem_pct >= self.thresholds["mem_percent"]:
                alerts.append(f"📊 RAM al {mem_pct}%!")

            if alerts:
                msg = "🚨 *Alertas:*\n\n" + "\n".join(alerts)
                await app.bot.send_message(chat_id=OWNER_ID, text=msg, parse_mode="Markdown")
        except Exception as e:
            pass

    def set_threshold(self, metric, value):
        if metric in self.thresholds:
            self.thresholds[metric] = value

health_checker = HealthChecker()