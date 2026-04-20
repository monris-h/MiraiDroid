"""
Weather - información del clima via wttr.in
"""
import aiohttp

class Weather:
    @staticmethod
    async def get(location="Mexico"):
        try:
            url = f"https://wttr.in/{location}?format=j1"
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    data = await resp.json()
                    current = data["current_condition"][0]
                    return (f"🌤️ *Clima en {location}:*\n"
                           f"• Temp: {current['temp_C']}°C\n"
                           f"• Sensación: {current['FeelsLikeC']}°C\n"
                           f"• Humedad: {current['humidity']}%\n"
                           f"• Viento: {current['windspeedKmph']} km/h")
        except Exception as e:
            return f"❌ Error: {e}"

weather = Weather()