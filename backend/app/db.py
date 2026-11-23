"""Small SQLite/PostgreSQL adapter. PostgreSQL is selected by DATABASE_URL."""
import sqlite3
from pathlib import Path
from .config import settings

DATABASE_URL = settings.database_url.strip()
DB_PATH = __import__("os").getenv("MARKETPILOT_DB_PATH", str(Path(__file__).resolve().parent.parent / "marketpilot.db"))

class Connection:
    def __init__(self):
        self.is_postgres = bool(DATABASE_URL)
        if self.is_postgres:
            import psycopg
            from psycopg.rows import dict_row
            self.raw = psycopg.connect(DATABASE_URL, row_factory=dict_row,
                options="-c search_path=marketpilot,public", connect_timeout=12)
        else:
            self.raw = sqlite3.connect(DB_PATH, timeout=15)
            self.raw.row_factory = sqlite3.Row
    def execute(self, sql, params=()):
        return self.raw.execute(sql.replace("?", "%s") if self.is_postgres else sql, params)
    def commit(self): self.raw.commit()
    def rollback(self): self.raw.rollback()
    def close(self): self.raw.close()
    def __enter__(self): return self
    def __exit__(self, typ, value, tb):
        if typ is None: self.commit()
        else: self.rollback()
        self.close()

def connect():
    return Connection()
