import ipaddress
import subprocess
from lan_roster.ports.network_config import NetworkConfigPort


class SystemNetworkConfigAdapter(NetworkConfigPort):
    """
    Cross-platform adapter detecting the local system default route and subnet.
    Supports Windows, macOS, and Linux.
    """

    def __init__(self, fallback_subnet: str = "10.0.0.0/24") -> None:
        self.fallback_subnet = fallback_subnet

    def detect_default_subnet(self) -> str:
        # 1. macOS route / ifconfig lookup (detailed netmask CIDR detection)
        try:
            out = subprocess.check_output(
                ["route", "-n", "get", "default"], timeout=2, stderr=subprocess.DEVNULL
            ).decode()
            iface = None
            for line in out.splitlines():
                if "interface:" in line:
                    iface = line.split(":")[1].strip()
                    break

            if iface:
                if_out = subprocess.check_output(
                    ["ifconfig", iface], timeout=2, stderr=subprocess.DEVNULL
                ).decode()
                for line in if_out.splitlines():
                    clean_line = line.strip()
                    if clean_line.startswith("inet "):
                        parts = clean_line.split()
                        ip = parts[1]
                        netmask_hex = parts[3]
                        netmask_int = int(netmask_hex, 16)
                        cidr = bin(netmask_int).count("1")
                        net = ipaddress.IPv4Network(f"{ip}/{cidr}", strict=False)
                        return str(net)
        except Exception:
            pass

        # 2. Cross-platform Scapy route detection (Windows, Linux, macOS)
        try:
            from scapy.all import conf
            route_tbl = getattr(conf, "route", None)
            if route_tbl is not None:
                _, local_ip, _ = route_tbl.route("0.0.0.0")
                if local_ip and local_ip != "0.0.0.0":
                    net = ipaddress.IPv4Network(f"{local_ip}/24", strict=False)
                    return str(net)
        except Exception:
            pass

        return self.fallback_subnet

    def detect_default_gateway(self) -> str | None:
        """Detects the default gateway IP address across platforms."""
        # 1. macOS route table
        try:
            out = subprocess.check_output(
                ["route", "-n", "get", "default"], timeout=2, stderr=subprocess.DEVNULL
            ).decode()
            for line in out.splitlines():
                if "gateway:" in line:
                    return line.split(":")[1].strip()
        except Exception:
            pass

        # 2. Cross-platform Scapy route detection (Windows, Linux, macOS)
        try:
            from scapy.all import conf
            route_tbl = getattr(conf, "route", None)
            if route_tbl is not None:
                _, _, gateway_ip = route_tbl.route("0.0.0.0")
                if gateway_ip and gateway_ip != "0.0.0.0":
                    return str(gateway_ip)
        except Exception:
            pass

        return None
