#!/usr/bin/env python3
"""
MiraiDroid - Entry point
Ejecuta: python main.py
"""
import sys
import signal
import logging

from bot import build_app
from src.config import VERSION, TOKEN, OWNER_ID
from src.database import db
from src.plugin_manager import plugin_manager

logger = logging.getLogger(__name__)


def signal_handler(sig, frame):
    logger.info("Shutting down...")
    db.close()
    sys.exit(0)


if __name__ == "__main__":
    print(f"[MiraiDroid] v{VERSION} starting...")

    signal.signal(signal.SIGINT, signal_handler)

    # Send startup notification
    try:
        import requests
        requests.get(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            params={
                "chat_id": OWNER_ID,
                "text": f"🛡️ Estoy activo nuevamente! MiraiDroid v{VERSION} iniciado. 👋",
                "parse_mode": "Markdown"
            },
            timeout=10
        )
    except Exception as e:
        logger.warning(f"Could not send startup message: {e}")

    # Auto-load plugins
    try:
        loaded = plugin_manager.auto_load_plugins()
        if loaded:
            print(f"Plugins auto-loaded: {loaded}")
    except Exception as e:
        logger.warning(f"Plugin auto-load failed: {e}")

    # Build and run
    app = build_app()

    print("Press Ctrl+C to stop")

    try:
        app.run_polling(drop_pending_updates=True)
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped")
        db.close()
    except Exception as e:
        import traceback
        error_msg = f"{type(e).__name__}: {e}\n\n{traceback.format_exc()[-2000:]}"
        logger.error(f"Bot crashed: {error_msg}")
        try:
            import requests
            requests.get(
                f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                params={
                    "chat_id": OWNER_ID,
                    "text": f"🚨 *ERROR en MiraiDroid*\n\n```\n{error_msg[:3500]}\n```\n⏰ {__import__('time').strftime('%Y-%m-%d %H:%M:%S')}",
                    "parse_mode": "Markdown"
                },
                timeout=10
            )
        except:
            pass
        print("Bot crashed. Check logs.")