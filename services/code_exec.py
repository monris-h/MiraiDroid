"""
Code Execution - ejecuta código python o bash
"""
import subprocess
from pathlib import Path

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

        elif language in ("bash", "shell"):
            try:
                result = subprocess.run(code, shell=True, capture_output=True, text=True, timeout=30)
                return f"```bash\n{result.stdout or result.stderr}```"
            except Exception as e:
                return f"❌ Error: {e}"

        return f"❌ Lenguaje no soportado: {language}"

code_interpreter = CodeInterpreter()