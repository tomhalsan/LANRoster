from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict


class HostnameSource(str, Enum):
    MDNS = "mDNS"
    NETBIOS = "NetBIOS"
    SSDP = "SSDP"
    DNS = "DNS"
    FIREWALLED = "Firewalled"
    UNKNOWN = ""


@dataclass
class Device:
    ip: str
    mac: str
    hostname: str = "Unknown"
    source: HostnameSource = HostnameSource.UNKNOWN
    vendor: str = "Generic Device"
    last_seen: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mac": self.mac,
            "hostname": self.hostname,
            "source": self.source.value,
            "vendor": self.vendor,
            "last_seen": self.last_seen,
        }


@dataclass
class ScanState:
    subnet: str
    is_scanning: bool = False
    last_scan_time: str = "Never"
    error_message: str | None = None
    total_found: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "subnet": self.subnet,
            "scanning": self.is_scanning,
            "last_scan_time": self.last_scan_time,
            "error_message": self.error_message,
            "total_found": self.total_found,
        }

