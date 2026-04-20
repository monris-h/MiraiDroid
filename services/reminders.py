"""
Reminders - sistema de recordatorios
"""
import time
from src.database import db

class Reminders:
    @staticmethod
    async def add(time_str, message):
        try:
            db.execute("INSERT INTO reminders (time, message, created) VALUES (?, ?, ?)",
                      (time_str, message, time.strftime("%Y-%m-%d %H:%M")))
            return f"✅ Recordatorio creado para {time_str}"
        except Exception as e:
            return f"❌ Error: {e}"

    @staticmethod
    async def list_pending():
        result = db.query("SELECT id, time, message FROM reminders ORDER BY time LIMIT 10")
        if not result:
            return "📝 No hay recordatorios pendientes"
        return "📝 *Recordatorios:*\n\n" + "\n".join([f"• `{r[0]}` - {r[1]}: {r[2]}" for r in result])

    @staticmethod
    async def delete(id):
        try:
            db.execute("DELETE FROM reminders WHERE id=?", (id,))
            return f"✅ Recordatorio {id} eliminado"
        except Exception as e:
            return f"❌ Error: {e}"

reminders = Reminders()