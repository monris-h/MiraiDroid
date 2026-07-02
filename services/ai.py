"""
AI Service - MiniMax API con fallback a Groq
"""
import json
import asyncio
import aiohttp
from src.memory import memory

class AI:
    @staticmethod
    async def think(prompt: str, context: str = "", conv_id="default") -> str:
        from src.config import MINIMAX_KEY, GROQ_API_KEY

        prompt = memory.apply_learning(prompt)
        url = "https://api.minimax.io/anthropic/v1/messages"
        headers = {"Authorization": f"Bearer {MINIMAX_KEY}", "Content-Type": "application/json", "anthropic-version": "2023-06-01"}
        system_prompt = memory.get_persona_prompt()

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

        except (asyncio.TimeoutError, Exception):
            return await AI.groq_fallback(messages)

    @staticmethod
    async def groq_fallback(messages):
        from src.config import GROQ_API_KEY

        try:
            groq_messages = [{"role": msg["role"], "content": msg["content"]} for msg in messages]

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


class SelfImprover:
    """Self-improvement via AI - modifica archivos del proyecto"""
    @staticmethod
    async def improve(request: str) -> str:
        """
        Improve a specific source file based on a user request.
        Usage: /improve <filename> <request>
        Defaults to improving bot.py if no filename is provided.
        """
        from src.config import BASE_DIR

        # Parse: /improve <filename> <rest of request>
        # or just /improve <request> -> defaults to bot.py
        parts = request.split(maxsplit=1) if request else []
        if parts and (BASE_DIR / parts[0]).is_file() and parts[0].endswith(".py"):
            filename = parts[0]
            actual_request = parts[1] if len(parts) > 1 else "improve this code"
        else:
            filename = "bot.py"
            actual_request = request or "improve this code"

        target_file = BASE_DIR / filename
        if not target_file.exists():
            return f"❌ Archivo no encontrado: {filename}"

        current_code = target_file.read_text()
        prompt = f"""Eres un programador experto en Python. El usuario quiere: {actual_request}
Archivo a modificar: {filename}
Código actual (primeros 3000 caracteres):
```python
{current_code[:3000]}
```
Proporciona ONLY el código mejorado completo del archivo. Sin explicaciones."""

        response = await AI.think(prompt)

        if "import" in response and "def " in response:
            from src.memory import activity_log
            from services.backup import backup_manager

            backup_manager.create_backup(f"{filename}:improve")
            target_file.write_text(response)
            activity_log.log("SELF_IMPROVE", f"{filename}: {actual_request[:50]}")
            return (f"✅ ¡Código mejorado en `{filename}`!\n\n"
                    f"Backup automático creado.\n\n"
                    f"Preview:\n```python\n{response[:1000]}...\n```\n\n"
                    f"⚠️ Reinicia el bot con /restart para aplicar los cambios.")

        return response