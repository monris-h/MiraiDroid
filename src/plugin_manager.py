"""
Plugin Manager - auto-load y gestión de plugins
"""
import sys
import logging
from pathlib import Path
from src.config import BASE_DIR
from src.database import db

logger = logging.getLogger(__name__)


class PluginManager:
    def __init__(self):
        self.plugins_dir = BASE_DIR / "plugins"
        self.loaded_plugins = {}

    def load_plugin(self, name):
        plugin_file = self.plugins_dir / f"{name}.py"
        if not plugin_file.exists():
            return False, f"Plugin {name} no encontrado"

        try:
            if name in sys.modules:
                del sys.modules[name]

            import importlib.util
            spec = importlib.util.spec_from_file_location(name, plugin_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            if hasattr(module, 'register_handlers'):
                module.register_handlers(app)
            if hasattr(module, 'init'):
                module.init()

            self.loaded_plugins[name] = module
            db.execute("INSERT OR IGNORE INTO plugins (name) VALUES (?)", (name,))
            return True, f"Plugin {name} cargado"
        except Exception as e:
            return False, f"Error: {e}"

    def unload_plugin(self, name):
        if name in self.loaded_plugins:
            if hasattr(self.loaded_plugins[name], 'cleanup'):
                self.loaded_plugins[name].cleanup()
            del self.loaded_plugins[name]
            return True
        return False

    def list_plugins(self):
        enabled = db.query("SELECT name FROM plugins WHERE enabled=1")
        all_plugins = [f.stem for f in self.plugins_dir.glob("*.py")]
        enabled_names = [r[0] for r in enabled]
        return {"loaded": list(self.loaded_plugins.keys()), "available": all_plugins, "enabled": enabled_names}

    def auto_load_plugins(self):
        """Load all plugins automatically at startup"""
        if not self.plugins_dir.exists():
            return []
        loaded = []
        for plugin_file in self.plugins_dir.glob("*.py"):
            if plugin_file.name.startswith("_") or plugin_file.name == "plugin_base.py":
                continue
            try:
                import importlib.util
                spec = importlib.util.spec_from_file_location(f"plugin_{plugin_file.stem}", plugin_file)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                loaded.append(plugin_file.stem)
                logger.info(f"Loaded plugin: {plugin_file.stem}")
            except Exception as e:
                logger.error(f"Failed to load {plugin_file.name}: {e}")
        return loaded


plugin_manager = PluginManager()