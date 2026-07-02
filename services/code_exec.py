"""
Code Execution - ejecuta código python o bash
"""
import subprocess
import sys
import tempfile
from pathlib import Path


class CodeInterpreter:
    @staticmethod
    async def execute(code, language="python"):
        """
        Execute code in a subprocess and return the output.

        Languages:
            - python: uses `sys.executable` (works on both Windows and Unix)
            - bash: shell-only (Unix/Termux). On Windows, falls back to cmd.
        """
        if language == "python":
            tmp = None
            try:
                # NamedTemporaryFile needs to be closed on Windows before
                # another process can open it
                with tempfile.NamedTemporaryFile(
                    suffix=".py", delete=False, mode="w", encoding="utf-8"
                ) as f:
                    f.write(code)
                    f.flush()
                    tmp = f.name

                result = subprocess.run(
                    [sys.executable, tmp],
                    capture_output=True, text=True, timeout=30
                )
                output = (result.stdout or "") + (result.stderr or "")
                output = output.strip() or "✅ Ejecutado sin output"
                return f"```python\n{output[:3500]}\n```"
            except subprocess.TimeoutExpired:
                return "❌ Timeout: el código tardó más de 30 segundos"
            except Exception as e:
                return f"❌ Error: {e}"
            finally:
                if tmp:
                    try:
                        Path(tmp).unlink()
                    except Exception:
                        pass

        elif language in ("bash", "shell"):
            try:
                # shell=True is required for pipe/redirection, but we accept
                # the security tradeoff because this command is owner-only.
                result = subprocess.run(
                    code, shell=True,
                    capture_output=True, text=True, timeout=30
                )
                output = (result.stdout or "") + (result.stderr or "")
                output = output.strip() or "✅ Ejecutado sin output"
                return f"```bash\n{output[:3500]}\n```"
            except subprocess.TimeoutExpired:
                return "❌ Timeout: el comando tardó más de 30 segundos"
            except Exception as e:
                return f"❌ Error: {e}"

        return f"❌ Lenguaje no soportado: {language}"


code_interpreter = CodeInterpreter()