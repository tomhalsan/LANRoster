import socket
from typing import Dict, List, Tuple
from lan_roster.domain.models import HostnameSource
from lan_roster.ports.resolver import HostnameResolverPort


class SocketDNSResolver(HostnameResolverPort):
    """Standard unicast reverse DNS resolver fallback."""

    def resolve_batch(self, ips: List[str]) -> Dict[str, Tuple[str, HostnameSource]]:
        results: Dict[str, Tuple[str, HostnameSource]] = {}
        for ip in ips:
            try:
                host, _, _ = socket.gethostbyaddr(ip)
                if host:
                    results[ip] = (host, HostnameSource.DNS)
            except Exception:
                pass
        return results
