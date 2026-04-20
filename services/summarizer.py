"""
Summarizer - resume URLs y texto
"""
import re
import aiohttp

class Summarizer:
    @staticmethod
    async def summarize_url(url):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    content = await resp.text()

                    title_match = re.search(r"<title[^>]*>([^<]+)</title>", content)
                    title = title_match.group(1) if title_match else "Sin título"

                    desc_match = re.search(r'<meta[^>]*name="description"[^>]*content="([^"]+)"', content)
                    description = desc_match.group(1) if desc_match else ""

                    content_match = re.findall(r'<p[^>]*>([^<]+)</p>', content)
                    paragraphs = [p for p in content_match if len(p) > 50][:5]

                    return f"📄 *{title}*\n\n{description}\n\n" + "\n\n".join([f"▸ {p}" for p in paragraphs])
        except Exception as e:
            return f"❌ Error: {e}"

    @staticmethod
    async def summarize_text(text, max_words=100):
        from services.ai import AI
        prompt = f"Resume el siguiente texto en máximo {max_words} palabras:\n\n{text[:2000]}"
        return await AI.think(prompt)

summarizer = Summarizer()