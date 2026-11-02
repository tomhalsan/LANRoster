import os
import sqlite3
import threading
import time
from typing import Dict
from lan_roster.domain.models import DeviceAlias
from lan_roster.ports.alias_repository import DeviceAliasRepositoryPort


class SqliteAliasRepository(DeviceAliasRepositoryPort):
    """
    SQLite persistent storage adapter for user-defined device nicknames and notes.
    Persists aliases keyed by normalized MAC address across restarts and subnet switches.
    """

    def __init__(self, db_path: str | None = None) -> None:
        self.db_path = db_path or os.path.expanduser("~/.lan_roster/lan_roster.db")
        if self.db_path != ":memory:":
            db_dir = os.path.dirname(os.path.abspath(self.db_path))
            os.makedirs(db_dir, exist_ok=True)

        self._lock = threading.Lock()
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row

        with self._lock:
            if self.db_path != ":memory:":
                self._conn.execute("PRAGMA journal_mode=WAL;")
            self._conn.execute("PRAGMA synchronous=NORMAL;")
            self._init_schema()

    def _init_schema(self) -> None:
        cursor = self._conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS device_aliases (
                mac TEXT PRIMARY KEY,
                nickname TEXT NOT NULL DEFAULT '',
                notes TEXT NOT NULL DEFAULT '',
                updated_at TEXT NOT NULL DEFAULT ''
            );
        """)
        self._conn.commit()

    def get_alias(self, mac: str) -> DeviceAlias | None:
        norm = mac.strip().upper()
        with self._lock:
            cursor = self._conn.cursor()
            cursor.execute("SELECT mac, nickname, notes FROM device_aliases WHERE mac = ?", (norm,))
            row = cursor.fetchone()
            if row:
                return DeviceAlias(mac=row["mac"], nickname=row["nickname"], notes=row["notes"])
            return None

    def get_all_aliases(self) -> Dict[str, DeviceAlias]:
        with self._lock:
            cursor = self._conn.cursor()
            cursor.execute("SELECT mac, nickname, notes FROM device_aliases")
            rows = cursor.fetchall()
            return {
                row["mac"]: DeviceAlias(mac=row["mac"], nickname=row["nickname"], notes=row["notes"])
                for row in rows
            }

    def save_alias(self, mac: str, nickname: str, notes: str) -> DeviceAlias:
        norm = mac.strip().upper()
        now = time.strftime("%Y-%m-%d %H:%M:%S")
        with self._lock:
            cursor = self._conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO device_aliases (mac, nickname, notes, updated_at)
                VALUES (?, ?, ?, ?)
            """, (norm, nickname.strip(), notes.strip(), now))
            self._conn.commit()
            return DeviceAlias(mac=norm, nickname=nickname.strip(), notes=notes.strip())

    def delete_alias(self, mac: str) -> None:
        norm = mac.strip().upper()
        with self._lock:
            cursor = self._conn.cursor()
            cursor.execute("DELETE FROM device_aliases WHERE mac = ?", (norm,))
            self._conn.commit()

    def close(self) -> None:
        with self._lock:
            self._conn.close()
