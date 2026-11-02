from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List


COMMON_SERVICES: Dict[int, str] = {
    80: "HTTP (Web Admin)",
    443: "HTTPS (Secure Web)",
    22: "SSH (Terminal)",
    445: "SMB (File Sharing)",
    631: "IPP (Printer)",
    8008: "Google Cast",
    8080: "HTTP-Alt (Web Admin)",
    62078: "Apple Lockdown",
}


class HostnameSource(str, Enum):
    MDNS = "mDNS"
    NETBIOS = "NetBIOS"
    SSDP = "SSDP"
    DNS = "DNS"
    HTTP = "HTTP"
    FIREWALLED = "Firewalled"
    UNKNOWN = ""


class DeviceCategory(str, Enum):
    MOBILE = "Mobile"
    COMPUTER = "Computer"
    SMART_TV = "Smart TV"
    SMART_HOME = "Smart Home"
    PRINTER = "Printer"
    NETWORK = "Network"
    GAMING = "Gaming"
    GENERIC = "Generic"

    @property
    def icon(self) -> str:
        icons = {
            DeviceCategory.MOBILE: "📱",
            DeviceCategory.COMPUTER: "💻",
            DeviceCategory.SMART_TV: "📺",
            DeviceCategory.SMART_HOME: "🔊",
            DeviceCategory.PRINTER: "🖨️",
            DeviceCategory.NETWORK: "🌐",
            DeviceCategory.GAMING: "🎮",
            DeviceCategory.GENERIC: "📟",
        }
        return icons.get(self, "📟")


@dataclass
class DeviceAlias:
    """User-assigned friendly nickname and persistent notes for a device by MAC address."""

    mac: str
    nickname: str = ""
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mac": self.mac,
            "nickname": self.nickname,
            "notes": self.notes,
        }


@dataclass
class Device:
    """
    Domain entity representing an individual network node.

    Tracks identity (IP, MAC, Hostname, Source, Vendor, Category)
    and real-time connection presence (first_seen, last_seen, is_online, is_new),
    as well as user customizations (nickname, notes).
    """

    ip: str
    mac: str
    hostname: str = "Unknown"
    source: HostnameSource = HostnameSource.UNKNOWN
    vendor: str = "Generic Device"
    last_seen: str = ""
    category: DeviceCategory = DeviceCategory.GENERIC
    first_seen: str = ""
    is_online: bool = True
    is_new: bool = False
    open_ports: List[int] = field(default_factory=list)
    nickname: str = ""
    notes: str = ""

    @property
    def display_name(self) -> str:
        """Returns user-assigned nickname if set, else auto-discovered hostname."""
        return self.nickname if self.nickname else self.hostname

    @property
    def detected_services(self) -> Dict[int, str]:
        """Returns map of open port -> readable service name."""
        return {p: COMMON_SERVICES.get(p, f"Port {p}") for p in sorted(self.open_ports)}

    def to_dict(self) -> Dict[str, Any]:
        """Serializes entity to dictionary for JSON API responses and template rendering."""
        return {
            "ip": self.ip,
            "mac": self.mac,
            "hostname": self.hostname,
            "source": self.source.value,
            "vendor": self.vendor,
            "last_seen": self.last_seen,
            "first_seen": self.first_seen,
            "is_online": self.is_online,
            "is_new": self.is_new,
            "category": self.category.value,
            "category_icon": self.category.icon,
            "open_ports": list(self.open_ports),
            "services": self.detected_services,
            "nickname": self.nickname,
            "notes": self.notes,
            "display_name": self.display_name,
        }


@dataclass
class ScanState:
    """
    Domain model tracking current subnet, scanner progress, timestamps,
    and cumulative vs. real-time online/offline device counts.
    """

    subnet: str
    is_scanning: bool = False
    last_scan_time: str = "Never"
    error_message: str | None = None
    total_found: int = 0
    online_count: int = 0
    offline_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Serializes scanner state to dictionary."""
        return {
            "subnet": self.subnet,
            "scanning": self.is_scanning,
            "last_scan_time": self.last_scan_time,
            "error_message": self.error_message,
            "total_found": self.total_found,
            "online_count": self.online_count,
            "offline_count": self.offline_count,
        }
