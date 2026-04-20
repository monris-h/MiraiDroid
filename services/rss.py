"""
RSS Reader - fetch y summarize de feeds RSS
"""
import re
import aiohttp

class RSSReader:
    @staticmethod
    async def fetch(url):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    content = await resp.text()
                    titles = re.findall(r"<title><!\[CDATA\[(.*?)\]\]></title>", content)
                    return "\n".join([f"📰 {t}" for t in titles[:10]]) or "❌ No titles found"
        except Exception as e:
            return f"❌ Error: {e}"

    @staticmethod
    async def summarize(url):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    content = await resp.text()
                    titles = re.findall(r"<title><!\[CDATA\[(.*?)\]\]></title>", content)
                    return f"📰 *Noticias ({len(titles)} items):*\n\n" + "\n".join([f"• {t}" for t in titles[:15]])
        except Exception as e:
            return f"❌ Error: {e}"

rss_reader = RSSReader()