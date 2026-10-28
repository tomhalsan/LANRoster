import json
import re
import socket
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Tuple
from lan_roster.domain.models import HostnameSource
from lan_roster.ports.resolver import HostnameResolverPort


class SocketSSDPResolver(HostnameResolverPort):
    """
    SSDP / UPnP resolver querying UDP 1900 and HTTP device descriptors
    for friendly device names and manufacturer/model metadata (Probe B).
    """

    def __init__(self, timeout: float = 0.8) -> None:
        self.timeout = timeout
        self._metadata: Dict[str, Dict[str, str]] = {}

    def get_metadata(self, ip: str) -> Dict[str, str]:
        """Retrieves discovered manufacturer and model metadata for an IP."""
        return self._metadata.get(ip, {})

    def get_all_metadata(self) -> Dict[str, Dict[str, str]]:
        """Retrieves all discovered device metadata."""
        return dict(self._metadata)

    def _fetch_xml_descriptor(self, ip: str, url: str) -> Tuple[str, str, str]:
        """Fetches and parses a UPnP XML device descriptor."""
        try:
            req = urllib.request.Request(
                url, headers={"User-Agent": "LANRoster/1.0"}
            )
            with urllib.request.urlopen(req, timeout=0.8) as resp:
                xml = resp.read().decode("utf-8", errors="ignore")
                m_name = re.search(r"<friendlyName>(.*?)</friendlyName>", xml, re.IGNORECASE)
                m_manuf = re.search(r"<manufacturer>(.*?)</manufacturer>", xml, re.IGNORECASE)
                m_model = re.search(r"<modelName>(.*?)</modelName>", xml, re.IGNORECASE)

                friendly_name = m_name.group(1).strip() if m_name else ""
                manufacturer = m_manuf.group(1).strip() if m_manuf else ""
                model = m_model.group(1).strip() if m_model else ""
                return friendly_name, manufacturer, model
        except Exception:
            return "", "", ""

    def _fetch_cast_info(self, ip: str) -> Tuple[str, str, str]:
        """Probes Google Cast setup API on port 8008."""
        try:
            req = urllib.request.Request(
                f"http://{ip}:8008/setup/eureka_info",
                headers={"User-Agent": "LANRoster/1.0"},
            )
            with urllib.request.urlopen(req, timeout=0.6) as resp:
                data = json.loads(resp.read().decode("utf-8", errors="ignore"))
                name = str(data.get("name", "")).strip()
                return name, "Google", "Chromecast / Google TV"
        except Exception:
            return "", "", ""

    def resolve_batch(self, ips: List[str]) -> Dict[str, Tuple[str, HostnameSource]]:
        results: Dict[str, Tuple[str, HostnameSource]] = {}
        if not ips:
            return results

        target_ips = set(ips)
        locations: Dict[str, str] = {}

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(0.2)
        msg = (
            "M-SEARCH * HTTP/1.1\r\n"
            "HOST: 239.255.255.250:1900\r\n"
            'MAN: "ssdp:discover"\r\n'
            "MX: 1\r\n"
            "ST: ssdp:all\r\n\r\n"
        ).encode()

        try:
            # 1. Send multicast discovery
            try:
                sock.sendto(msg, ("239.255.255.250", 1900))
            except Exception:
                pass

            # 2. Also send targeted unicast M-SEARCH to overcome Wi-Fi multicast filtering
            for ip in target_ips:
                try:
                    sock.sendto(msg, (ip, 1900))
                except Exception:
                    pass

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
        except Exception:
            pass
        finally:
            sock.close()

        # 3. Concurrently fetch XML device descriptors (Probe B)
        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_ip = {
                executor.submit(self._fetch_xml_descriptor, ip, url): ip
                for ip, url in locations.items()
            }
            # For target IPs not replying to SSDP, attempt Cast API check on port 8008
            for ip in target_ips:
                if ip not in locations:
                    future_to_ip[executor.submit(self._fetch_cast_info, ip)] = ip

            for future in as_completed(future_to_ip):
                ip = future_to_ip[future]
                try:
                    friendly_name, manufacturer, model = future.result()
                    if friendly_name or manufacturer:
                        self._metadata[ip] = {
                            "friendly_name": friendly_name,
                            "manufacturer": manufacturer,
                            "model": model,
                        }
                    if friendly_name:
                        results[ip] = (friendly_name, HostnameSource.SSDP)
                except Exception:
                    pass

        return results

