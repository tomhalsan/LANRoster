from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict


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
class Device:
    """
    Domain entity representing an individual network node.

    Tracks identity (IP, MAC, Hostname, Source, Vendor, Category)
    and real-time connection presence (first_seen, last_seen, is_online, is_new).
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
