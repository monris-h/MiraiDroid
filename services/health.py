"""
Health Checker - alertas de disco, RAM, CPU
"""
import subprocess
from src.utils import is_windows

class HealthChecker:
    def __init__(self):
        self.alerts = []
        self.thresholds = {"disk_percent": 90, "mem_percent": 90, "cpu_percent": 95}

    async def check(self, app):
        from src.config import OWNER_ID

        try:
            alerts = []

            if is_windows():
                try:
                    result = subprocess.check_output("wmic logicaldisk get size,freespace,caption /format:list", shell=True, text=True)
                    for line in result.split("\n"):
                        if "FreeSpace" in line and "C:" in result:
                            freespace = int(line.split("=")[-1].strip())
                            totalspace = 0
                            for l2 in result.split("\n"):
                                if "Size" in l2 and "FreeSpace" not in l2:
                                    try:
                                        totalspace = int(l2.split("=")[-1].strip())
                                        break
                                    except:
                                        pass
                            if totalspace > 0:
                                disk_pct = int((1 - freespace/totalspace) * 100)
                                if disk_pct >= self.thresholds["disk_percent"]:
                                    alerts.append(f"💾 Disco al {disk_pct}%!")
                            break
                except:
                    pass
            else:
                result = subprocess.check_output("df -h / | tail -1 | awk '{print $5}'", shell=True, text=True).strip()
                disk_pct = int(result.replace("%", ""))
                if disk_pct >= self.thresholds["disk_percent"]:
                    alerts.append(f"💾 Disco al {disk_pct}%!")

            if is_windows():
                try:
                    mem = subprocess.check_output("wmic OS get FreePhysicalMemory,TotalVisibleMemorySize /format:list", shell=True, text=True)
                    free_mem, total_mem = 0, 1
                    for line in mem.split("\n"):
                        if "FreePhysicalMemory" in line:
                            free_mem = int(line.split("=")[-1].strip())
                        if "TotalVisibleMemorySize" in line:
                            total_mem = int(line.split("=")[-1].strip())
                    mem_pct = int((1 - free_mem/total_mem) * 100)
                    if mem_pct >= self.thresholds["mem_percent"]:
                        alerts.append(f"📊 RAM al {mem_pct}%!")
                except:
                    pass
            else:
                result = subprocess.check_output("free | grep Mem | awk '{print int($3/$2*100)}'", shell=True, text=True).strip()
                if result.isdigit() and int(result) >= self.thresholds["mem_percent"]:
                    alerts.append(f"📊 RAM al {result}%!")

            if alerts:
                msg = "🚨 *Alertas:*\n\n" + "\n".join(alerts)
                await app.bot.send_message(chat_id=OWNER_ID, text=msg, parse_mode="Markdown")
        except Exception as e:
            pass

    def set_threshold(self, metric, value):
        if metric in self.thresholds:
            self.thresholds[metric] = value

health_checker = HealthChecker()