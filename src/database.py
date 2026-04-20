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
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
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
        return self.conn.execute(sql, args).fetchall()

    def execute(self, sql, args=()):
        self.conn.execute(sql, args)
        self.conn.commit()

    def close(self):
        self.conn.close()

db = Database()