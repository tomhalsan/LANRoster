import re
import socket
import time
import urllib.request
from typing import Dict, List, Tuple
from lan_roster.domain.models import HostnameSource
from lan_roster.ports.resolver import HostnameResolverPort


class SocketSSDPResolver(HostnameResolverPort):
    """SSDP / UPnP resolver querying multicast UDP 1900 for friendly device names."""

    def __init__(self, timeout: float = 0.8) -> None:
        self.timeout = timeout

    def resolve_batch(self, ips: List[str]) -> Dict[str, Tuple[str, HostnameSource]]:
        results: Dict[str, Tuple[str, HostnameSource]] = {}
        target_ips = set(ips)

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(0.3)
        msg = (
            "M-SEARCH * HTTP/1.1\r\n"
            "HOST: 239.255.255.250:1900\r\n"
            'MAN: "ssdp:discover"\r\n'
            "MX: 1\r\n"
            "ST: ssdp:all\r\n\r\n"
        ).encode()

        locations: Dict[str, str] = {}
        try:
            sock.sendto(msg, ("239.255.255.250", 1900))
            end = time.time() + self.timeout
            while time.time() < end:
                try:
                    data, addr = sock.recvfrom(2048)
                    ip = addr[0]
                    if target_ips and ip not in target_ips:
                        continue
                    text = data.decode("latin1", errors="ignore")
                    for line in text.splitlines():
                        if line.upper().startswith("LOCATION:"):
                            loc = line.split(":", 1)[1].strip()
                            if ip not in locations:
                                locations[ip] = loc
                except socket.timeout:
                    pass
                except Exception:
                    pass

            for ip, url in list(locations.items())[:8]:
                try:
                    req = urllib.request.Request(
                        url, headers={"User-Agent": "LANRoster/1.0"}
                    )
                    with urllib.request.urlopen(req, timeout=0.5) as resp:
                        xml = resp.read().decode("utf-8", errors="ignore")
                        m = re.search(
                            r"<friendlyName>(.*?)</friendlyName>", xml, re.IGNORECASE
                        )
                        if m:
                            friendly_name = m.group(1).strip()
                            if friendly_name:
                                results[ip] = (friendly_name, HostnameSource.SSDP)
                except Exception:
                    pass
        except Exception:
            pass
        finally:
            sock.close()

        return results
