"""
System tools - utilities de sistema (file, git, docker, process, network, battery, etc)
"""
import os
import sys
import subprocess
import hashlib
import re
import sqlite3
from pathlib import Path
from src.utils import is_windows, is_android


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


class ProcessManager:
    @staticmethod
    def list():
        try:
            if is_windows():
                result = subprocess.check_output("tasklist /FO TABLE /NH", shell=True, text=True)
                lines = [l for l in result.split("\n") if l.strip()][:15]
                header = "NAME\t\tPID\tMEM"
                return f"```\n{header}\n" + "\n".join(lines[:10]) + "\n```"
            else:
                result = subprocess.check_output("ps aux --sort=-pcpu | head -15", shell=True, text=True)
                lines = result.split("\n")
                header = "USER\tPID\t%CPU\t%MEM\tCOMMAND"
                return f"```\n{header}\n" + "\n".join(lines[1:11]) + "\n```"
        except Exception as e:
            return f"❌ Error: {e}"

    @staticmethod
    def kill(pid):
        try:
            if is_windows():
                subprocess.run(f"taskkill /F /PID {pid}", shell=True, capture_output=True)
                return f"✅ Proceso {pid} terminado (Windows)"
            else:
                subprocess.run(f"kill -9 {pid}", shell=True)
                return f"✅ Proceso {pid} matado"
        except Exception as e:
            return f"❌ Error: {e}"

    @staticmethod
    def top(limit=5):
        try:
            if is_windows():
                cpu = subprocess.check_output("wmic cpu get loadpercentage /format:list", shell=True, stderr=subprocess.DEVNULL, text=True)
                cpu_pct = "N/A"
                for line in cpu.split("\n"):
                    if "LoadPercentage" in line:
                        cpu_pct = line.split("=")[-1].strip() + "%"

                mem_cmd = subprocess.check_output("wmic OS get FreePhysicalMemory,TotalVisibleMemorySize /format:list", shell=True, text=True)
                free_mem, total_mem = 0, 1
                for line in mem_cmd.split("\n"):
                    if "FreePhysicalMemory" in line:
                        free_mem = int(line.split("=")[-1].strip())
                    if "TotalVisibleMemorySize" in line:
                        total_mem = int(line.split("=")[-1].strip())
                used_pct = int((1 - free_mem/total_mem) * 100)

                result = f"Windows System:\nCPU: {cpu_pct}\nMemory: {used_pct}%"
                return f"```\n{result}\n```"
            else:
                result = subprocess.check_output(f"ps aux --sort=-pcpu | head {limit + 1}", shell=True, text=True)
                return f"```\n{result}\n```"
        except Exception as e:
            return f"❌ Error: {e}"

process_manager = ProcessManager()


class BatteryMonitor:
    @staticmethod
    def status():
        if is_android():
            try:
                result = subprocess.check_output("termux-battery-status", shell=True, text=True)
                try:
                    import json
                    data = json.loads(result)
                    pct = data.get("percentage", "?")
                    status = data.get("status", "?")
                    temp = data.get("temperature", "?")
                    return f"🔋 *Batería*\n• {pct}%\n• Status: {status}\n• Temp: {temp}°C"
                except:
                    return result[:4000]
            except Exception as e:
                return f"❌ Error: {e}"
        elif is_windows():
            try:
                result = subprocess.check_output("wmic path Win32_Battery get EstimatedChargeRemaining,Status,Temperature /format:list", shell=True, text=True)
                pct, status, temp = "?", "?", "?"
                for line in result.split("\n"):
                    if "EstimatedChargeRemaining" in line:
                        pct = line.split("=")[-1].strip()
                    if "Status" in line:
                        status = line.split("=")[-1].strip()
                    if "Temperature" in line:
                        temp = line.split("=")[-1].strip()
                return f"🔋 *Batería (Windows)*\n• {pct}%\n• Status: {status}\n• Temp: {temp}°C"
            except Exception as e:
                return f"❌ Error: {e}"
        else:
            return "🔋 _Batería solo disponible en Android/Windows_"

battery_monitor = BatteryMonitor()


class AppManager:
    @staticmethod
    def list_installed():
        if is_android():
            try:
                result = subprocess.check_output("pm list packages -3", shell=True, text=True)
                apps = result.replace("package:", "").split("\n")[:30]
                return f"📱 *Apps instaladas (30 primeras):*\n\n" + "\n".join([f"• {a}" for a in apps if a])
            except Exception as e:
                return f"❌ Error: {e}"
        elif is_windows():
            try:
                result = subprocess.check_output("wmic product get name /format:list", shell=True, stderr=subprocess.DEVNULL, text=True)
                apps = [line.replace("Name=", "").strip() for line in result.split("\n") if "Name=" in line][:30]
                return f"📱 *Programas instalados (30 primeros):*\n\n" + "\n".join([f"• {a}" for a in apps if a])
            except Exception as e:
                return f"❌ Error: {e}"
        else:
            return "📱 _Apps solo en Android/Windows_"

app_manager = AppManager()


class NetworkTools:
    @staticmethod
    async def ping(host):
        try:
            if is_windows():
                result = subprocess.run(f"ping -n 3 {host}", shell=True, capture_output=True, text=True, timeout=10)
            else:
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


class Screenshot:
    @staticmethod
    def capture(path=None):
        from src.config import BASE_DIR
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
        from src.config import MINIMAX_KEY
        import base64
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


class NaturalExec:
    @staticmethod
    async def execute(command, file_manager):
        command_lower = command.lower()

        if any(k in command_lower for k in ["busca", "encuentra", "search", "find"]):
            if any(ext in command_lower for ext in [".py", ".js", ".sh", ".md"]):
                match = re.search(r"(?:busca|encuentra|search|find)\s+(?:archivos?\s+)?(\S+)", command_lower)
                if match:
                    pattern = match.group(1).replace("'", "")
                    result = file_manager.find(pattern)
                    return result

        if any(k in command_lower for k in ["lista", "ls", "list", "muestra"]):
            if any(k in command_lower for k in ["archivo", "directorio", "folder", "dir"]):
                match = re.search(r"(?:en|del|de)?\s*(~?/?[\w/.-]*)", command)
                path = match.group(1) if match else "."
                return file_manager.list(path)

        return None

natural_exec = NaturalExec()