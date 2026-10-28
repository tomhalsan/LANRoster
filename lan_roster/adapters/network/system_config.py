import ipaddress
import subprocess
from lan_roster.ports.network_config import NetworkConfigPort


class SystemNetworkConfigAdapter(NetworkConfigPort):
    """Adapter detecting the local system default route and subnet configuration."""

    def __init__(self, fallback_subnet: str = "10.0.0.0/24") -> None:
        self.fallback_subnet = fallback_subnet

    def detect_default_subnet(self) -> str:
        try:
            out = subprocess.check_output(
                ["route", "-n", "get", "default"], timeout=2
            ).decode()
            iface = None
            for line in out.splitlines():
                if "interface:" in line:
                    iface = line.split(":")[1].strip()
                    break

            if iface:
                if_out = subprocess.check_output(
                    ["ifconfig", iface], timeout=2
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

        return self.fallback_subnet

