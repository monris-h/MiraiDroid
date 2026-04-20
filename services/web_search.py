"""
Web Search - Tavily API con fallback a DuckDuckGo
"""
import re
import aiohttp

class WebSearch:
    @staticmethod
    async def search(query, max_results=8):
        from src.config import TAVILY_API_KEY

        if TAVILY_API_KEY:
            try:
                url = "https://api.tavily.com/search"
                headers = {"Content-Type": "application/json"}
                data = {"api_key": TAVILY_API_KEY, "query": query, "max_results": max_results, "include_answer": True}
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, headers=headers, json=data, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                        if resp.status == 200:
                            result = await resp.json()
                            return WebSearch.format_tavily(query, result)
            except Exception:
                pass

        return await WebSearch.ddg_search(query, max_results)

    @staticmethod
    def format_tavily(query, data):
        results = data.get("results", [])
        answer = data.get("answer", "")

        msg = f"Buscando: {query}\n\n"
        if answer:
            msg += f"Respuesta: {answer[:300]}\n\n"
        if results:
            msg += "Resultados:\n"
            for i, r in enumerate(results[:8], 1):
                title = r.get("title", "Sin titulo")[:70]
                url = r.get("url", "")
                msg += f"\n{i}. {title}\n   {url}"
        return msg if results else "No encontre resultados."

    @staticmethod
    async def ddg_search(query, max_results=8):
        try:
            url = "https://html.duckduckgo.com/html/"
            params = {"q": query}

            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    html = await resp.text()

            pattern = r'<a class="result__a" href="([^"]+)"[^>]*>([^<]+)</a>'
            matches = re.findall(pattern, html)

            if not matches:
                return "No encontre resultados para esa busqueda."

            msg = f"Buscando: {query}\n\nResultados:\n"
            for i, (url, title) in enumerate(matches[:max_results], 1):
                title = re.sub(r"<[^>]+>", "", title).strip()
                if len(title) > 5:
                    msg += f"\n{i}. {title}\n   {url}"
            return msg
        except Exception as e:
            return f"Error en busqueda: {e}"