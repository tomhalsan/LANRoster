import re
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Tuple
from lan_roster.domain.models import HostnameSource
from lan_roster.ports.resolver import HostnameResolverPort


class SocketHTTPBannerResolver(HostnameResolverPort):
    """
    HTTP Banner and Page Title Resolver (Probe D).
    Queries common HTTP ports (80, 8080) for web-managed appliances,
    IP cameras, printers, and router interfaces.
    """

    GENERIC_TITLES = {
        "login", "welcome", "home", "index", "404 not found",
        "403 forbidden", "document moved", "error", "unauthorized",
        "router", "management", "loading...", "web application",
    }

    def __init__(self, timeout: float = 0.5, max_workers: int = 15) -> None:
        self.timeout = timeout
        self.max_workers = max_workers
        self._metadata: Dict[str, Dict[str, str]] = {}

    def get_metadata(self, ip: str) -> Dict[str, str]:
        return self._metadata.get(ip, {})

    def get_all_metadata(self) -> Dict[str, Dict[str, str]]:
        return dict(self._metadata)

    def _probe_single_ip(self, ip: str) -> Tuple[str, str | None, str | None]:
        for port in (80, 8080):
            try:
                req = urllib.request.Request(
                    f"http://{ip}:{port}/",
                    headers={"User-Agent": "Mozilla/5.0 (LANRoster Discovery)"},
                )
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    server = resp.headers.get("Server", "").strip()
                    content = resp.read(2048).decode("utf-8", errors="ignore")
                    m = re.search(r"<title>(.*?)</title>", content, re.IGNORECASE)
                    title = m.group(1).strip() if m else ""

                    if title or server:
                        return ip, title, server
            except Exception:
                pass
        return ip, None, None

    def resolve_batch(self, ips: List[str]) -> Dict[str, Tuple[str, HostnameSource]]:
        results: Dict[str, Tuple[str, HostnameSource]] = {}
        if not ips:
            return results

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [executor.submit(self._probe_single_ip, ip) for ip in ips]
            for f in as_completed(futures):
                try:
                    ip, title, server = f.result()
                    if title or server:
                        self._metadata[ip] = {
                            "title": title or "",
                            "server": server or "",
                        }
                    # Evaluate title for hostname usage
                    if title and title.lower() not in self.GENERIC_TITLES and len(title) <= 50:
                        results[ip] = (title, HostnameSource.HTTP)
                    elif server and len(server) <= 40 and "apache" not in server.lower() and "nginx" not in server.lower():
                        results[ip] = (server, HostnameSource.HTTP)
                except Exception:
                    pass

        return results
