"""
Database wrapper - SQLite para reminders, pastebin, plugins, url_cache
"""
import sqlite3
import logging
from pathlib import Path
from .config import BASE_DIR

logger = logging.getLogger(__name__)


class Database:
    def __init__(self):
        self.db_path = BASE_DIR / "data" / "miraidroid.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        # check_same_thread=False is required because python-telegram-bot's
        # update handlers and the cron scheduler run on different threads.
        # WAL mode + a short busy_timeout let concurrent readers/writers
        # coexist without locking up the bot.
        self.conn = sqlite3.connect(
            self.db_path,
            check_same_thread=False,
            timeout=10.0,
        )
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA synchronous=NORMAL")
        self.conn.execute("PRAGMA foreign_keys=ON")
        self.create_tables()

    def create_tables(self):
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                time TEXT, message TEXT, created TEXT
            );
            CREATE TABLE IF NOT EXISTS scheduled_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cron TEXT, message TEXT, chat_id TEXT, created TEXT
            );
            CREATE TABLE IF NOT EXISTS url_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT, short_code TEXT, created TEXT
            );
            CREATE TABLE IF NOT EXISTS pastebin (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT, content TEXT, created TEXT
            );
            CREATE TABLE IF NOT EXISTS plugins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT, enabled INTEGER DEFAULT 1
            );
        """)
        self.conn.commit()

    def query(self, sql, args=()):
        try:
            return self.conn.execute(sql, args).fetchall()
        except sqlite3.Error as e:
            logger.error(f"DB query failed: {e} | SQL: {sql[:100]}")
            return []

    def execute(self, sql, args=()):
        try:
            self.conn.execute(sql, args)
            self.conn.commit()
        except sqlite3.Error as e:
            logger.error(f"DB execute failed: {e} | SQL: {sql[:100]}")
            raise

    def close(self):
        try:
            self.conn.close()
        except sqlite3.Error as e:
            logger.warning(f"DB close failed: {e}")


db = Database()