"""
URL Shortener y Pastebin - servicios de datos
"""
import hashlib
from src.database import db

class URLShortener:
    @staticmethod
    async def shorten(url):
        import aiohttp
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post("https://short.link/api/shorten", json={"url": url}, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        return f"🔗 {result.get('short_url', url)}"
        except:
            pass
        code = hashlib.md5(url.encode()).hexdigest()[:8]
        db.execute("INSERT INTO url_cache (url, short_code, created) VALUES (?, ?, ?)", (url, code, __import__('time').strftime("%Y-%m-%d %H:%M")))
        return f"🔗 localhost/{code}"

    @staticmethod
    def resolve(code):
        result = db.query("SELECT url FROM url_cache WHERE short_code=?", (code,))
        return result[0][0] if result else None

url_shortener = URLShortener()


class Pastebin:
    @staticmethod
    def save(content, language="text"):
        import time
        code = hashlib.md5(content.encode()).hexdigest()[:12]
        db.execute("INSERT INTO pastebin (code, content, created) VALUES (?, ?, ?)", (code, content, time.strftime("%Y-%m-%d %H:%M")))
        return f"📋 Código: `{code}`"

    @staticmethod
    def get(code):
        result = db.query("SELECT content FROM pastebin WHERE code=?", (code,))
        return result[0][0] if result else None

pastebin = Pastebin()