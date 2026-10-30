import os
import sqlite3
import threading
from typing import Dict, List
from lan_roster.domain.models import Device, DeviceCategory, HostnameSource, ScanState
from lan_roster.ports.repository import DeviceRepositoryPort


class SqliteDeviceRepository(DeviceRepositoryPort):
    """
    SQLite persistent storage adapter for network devices and scanner state.
    Provides durable storage across application restarts while preserving
    clean architecture contracts.
    """

    def __init__(self, db_path: str | None = None, initial_subnet: str = "10.0.0.0/24") -> None:
        self.db_path = db_path or os.path.expanduser("~/.lan_roster/lan_roster.db")
        if self.db_path != ":memory:":
            db_dir = os.path.dirname(os.path.abspath(self.db_path))
            os.makedirs(db_dir, exist_ok=True)

        self._lock = threading.Lock()
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row

        with self._lock:
            # Enable WAL mode for high concurrency between web threads and background scanner
            if self.db_path != ":memory:":
                self._conn.execute("PRAGMA journal_mode=WAL;")
            self._conn.execute("PRAGMA synchronous=NORMAL;")
            self._init_schema(initial_subnet)

    def _init_schema(self, initial_subnet: str) -> None:
        """Creates devices and scan_state tables if they do not exist."""
        cursor = self._conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS devices (
                ip TEXT PRIMARY KEY,
                mac TEXT NOT NULL,
                hostname TEXT NOT NULL DEFAULT 'Unknown',
                source TEXT NOT NULL DEFAULT '',
                vendor TEXT NOT NULL DEFAULT 'Generic Device',
                last_seen TEXT NOT NULL DEFAULT '',
                category TEXT NOT NULL DEFAULT 'Generic',
                first_seen TEXT NOT NULL DEFAULT '',
                is_online INTEGER NOT NULL DEFAULT 1,
                is_new INTEGER NOT NULL DEFAULT 0
            );
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scan_state (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                subnet TEXT NOT NULL,
                is_scanning INTEGER NOT NULL DEFAULT 0,
                last_scan_time TEXT NOT NULL DEFAULT 'Never',
                error_message TEXT,
                total_found INTEGER NOT NULL DEFAULT 0,
                online_count INTEGER NOT NULL DEFAULT 0,
                offline_count INTEGER NOT NULL DEFAULT 0
            );
        """)

        cursor.execute("""
            INSERT OR IGNORE INTO scan_state (id, subnet, is_scanning, last_scan_time, error_message, total_found, online_count, offline_count)
            VALUES (1, ?, 0, 'Never', NULL, 0, 0, 0);
        """, (initial_subnet,))
        self._conn.commit()

    def _row_to_device(self, row: sqlite3.Row) -> Device:
        """Constructs a domain Device entity from an SQLite Row."""
        raw_source = row["source"] or ""
        source = HostnameSource(raw_source) if raw_source in HostnameSource._value2member_map_ else HostnameSource.UNKNOWN

        raw_category = row["category"] or "Generic"
        category = DeviceCategory(raw_category) if raw_category in DeviceCategory._value2member_map_ else DeviceCategory.GENERIC

        return Device(
            ip=row["ip"],
            mac=row["mac"],
            hostname=row["hostname"],
            source=source,
            vendor=row["vendor"],
            last_seen=row["last_seen"],
            category=category,
            first_seen=row["first_seen"],
            is_online=bool(row["is_online"]),
            is_new=bool(row["is_new"]),
        )

    def get_devices(self) -> Dict[str, Device]:
        with self._lock:
            cursor = self._conn.cursor()
            cursor.execute("SELECT * FROM devices")
            rows = cursor.fetchall()
            return {row["ip"]: self._row_to_device(row) for row in rows}

    def save_devices(self, devices: List[Device]) -> None:
        """
        Merges discovered devices into SQLite database.
        Applies sticky identity retention and real-time presence transitions.
        """
        with self._lock:
            cursor = self._conn.cursor()
            cursor.execute("SELECT * FROM devices")
            existing_devs = {row["ip"]: self._row_to_device(row) for row in cursor.fetchall()}
            active_ips = {dev.ip for dev in devices}

            # 1. Update active devices
            for dev in devices:
                if dev.ip in existing_devs:
                    existing = existing_devs[dev.ip]
                    hostname = dev.hostname if dev.hostname != "Unknown" else existing.hostname
                    source = dev.source if dev.hostname != "Unknown" else existing.source

                    if dev.vendor in ("Generic Device", "Private/Randomized MAC") and existing.vendor not in ("Generic Device", "Private/Randomized MAC"):
                        vendor = existing.vendor
                    else:
                        vendor = dev.vendor

                    if dev.category != DeviceCategory.GENERIC:
                        category = dev.category
                    else:
                        category = existing.category

                    first_seen = existing.first_seen or dev.first_seen or dev.last_seen

                    cursor.execute("""
                        INSERT OR REPLACE INTO devices
                        (ip, mac, hostname, source, vendor, last_seen, category, first_seen, is_online, is_new)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
                    """, (
                        dev.ip,
                        dev.mac or existing.mac,
                        hostname,
                        source.value,
                        vendor,
                        dev.last_seen or existing.last_seen,
                        category.value,
                        first_seen,
                        1 if existing.is_new else 0,
                    ))
                else:
                    first_seen = dev.first_seen or dev.last_seen
                    cursor.execute("""
                        INSERT OR REPLACE INTO devices
                        (ip, mac, hostname, source, vendor, last_seen, category, first_seen, is_online, is_new)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, 1)
                    """, (
                        dev.ip,
                        dev.mac,
                        dev.hostname,
                        dev.source.value,
                        dev.vendor,
                        dev.last_seen,
                        dev.category.value,
                        first_seen,
                    ))

            # 2. Mark devices that missed this sweep as offline/asleep
            for ip in existing_devs:
                if ip not in active_ips:
                    cursor.execute("UPDATE devices SET is_online = 0 WHERE ip = ?", (ip,))

            self._conn.commit()

    def clear_devices(self) -> None:
        """Clears all devices (called when switching target subnet)."""
        with self._lock:
            self._conn.execute("DELETE FROM devices")
            self._conn.commit()

    def get_scan_state(self) -> ScanState:
        with self._lock:
            cursor = self._conn.cursor()
            cursor.execute("SELECT * FROM scan_state WHERE id = 1")
            row = cursor.fetchone()
            if not row:
                return ScanState(subnet="10.0.0.0/24")

            return ScanState(
                subnet=row["subnet"],
                is_scanning=bool(row["is_scanning"]),
                last_scan_time=row["last_scan_time"],
                error_message=row["error_message"],
                total_found=row["total_found"],
                online_count=row["online_count"],
                offline_count=row["offline_count"],
            )

    def update_scan_state(
        self,
        subnet: str | None = None,
        is_scanning: bool | None = None,
        last_scan_time: str | None = None,
        error_message: str | None = None,
        total_found: int | None = None,
        online_count: int | None = None,
        offline_count: int | None = None,
    ) -> ScanState:
        with self._lock:
            cursor = self._conn.cursor()
            cursor.execute("SELECT * FROM scan_state WHERE id = 1")
            current = cursor.fetchone()

            new_subnet = subnet if subnet is not None else (current["subnet"] if current else "10.0.0.0/24")
            new_is_scanning = 1 if is_scanning else (0 if is_scanning is False else (current["is_scanning"] if current else 0))
            new_last_scan_time = last_scan_time if last_scan_time is not None else (current["last_scan_time"] if current else "Never")
            
            if error_message is not None:
                new_error_message = error_message
            elif is_scanning is True:
                new_error_message = None
            else:
                new_error_message = current["error_message"] if current else None

            new_total_found = total_found if total_found is not None else (current["total_found"] if current else 0)
            new_online_count = online_count if online_count is not None else (current["online_count"] if current else 0)
            new_offline_count = offline_count if offline_count is not None else (current["offline_count"] if current else 0)

            cursor.execute("""
                UPDATE scan_state SET
                    subnet = ?,
                    is_scanning = ?,
                    last_scan_time = ?,
                    error_message = ?,
                    total_found = ?,
                    online_count = ?,
                    offline_count = ?
                WHERE id = 1
            """, (
                new_subnet,
                new_is_scanning,
                new_last_scan_time,
                new_error_message,
                new_total_found,
                new_online_count,
                new_offline_count,
            ))
            self._conn.commit()

            return ScanState(
                subnet=new_subnet,
                is_scanning=bool(new_is_scanning),
                last_scan_time=new_last_scan_time,
                error_message=new_error_message,
                total_found=new_total_found,
                online_count=new_online_count,
                offline_count=new_offline_count,
            )

    def close(self) -> None:
        """Closes the underlying SQLite database connection."""
        with self._lock:
            self._conn.close()
