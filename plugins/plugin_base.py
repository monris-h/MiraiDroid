"""
Plugin base class - todos los plugins deben heredar de esto
"""
from telegram import Update
from telegram.ext import ContextTypes


class PluginBase:
    """Base class para plugins de MiraiDroid"""

    name = "base"
    description = "Plugin base"

    def init(self):
        """Se llama al cargar el plugin"""
        pass

    def cleanup(self):
        """Se llama al descargar el plugin"""
        pass

    def register_handlers(self, app):
        """Registrar handlers del plugin"""
        pass

    async def handle_message(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        """Handle mensaje si el plugin intercepta"""
        pass