from typing import Dict, List, Tuple
from lan_roster.domain.models import HostnameSource
from lan_roster.ports.resolver import HostnameResolverPort


class CompositeHostnameResolver(HostnameResolverPort):
    """
    Composite resolver that runs multiple resolver strategies in parallel
    and synthesizes results based on priority (mDNS > NetBIOS > SSDP > DNS).
    """

    def __init__(
        self,
        mdns_resolver: HostnameResolverPort,
        netbios_resolver: HostnameResolverPort,
        ssdp_resolver: HostnameResolverPort,
        dns_resolver: HostnameResolverPort,
        http_resolver: HostnameResolverPort | None = None,
    ) -> None:
        self.mdns = mdns_resolver
        self.netbios = netbios_resolver
        self.ssdp = ssdp_resolver
        self.dns = dns_resolver
        self.http = http_resolver

    def resolve_batch(self, ips: List[str]) -> Dict[str, Tuple[str, HostnameSource]]:
        if not ips:
            return {}

        # 1. mDNS resolution (covers Apple, Android, TVs, IoT, modern Win)
        mdns_results = self.mdns.resolve_batch(ips)

        # 2. SSDP discovery (covers Smart TVs, media renderers)
        ssdp_results = self.ssdp.resolve_batch(ips)

        # 3. NetBIOS queries (covers Windows PC names, Samba shares)
        netbios_results = self.netbios.resolve_batch(ips)

        # 4. Unicast reverse DNS fallback (including Gateway router DHCP)
        dns_results = self.dns.resolve_batch(ips)

        # 5. HTTP Banner & Title probe (Probe D)
        http_results = self.http.resolve_batch(ips) if self.http else {}

        # Synthesize in priority order
        final_map: Dict[str, Tuple[str, HostnameSource]] = {}
        for ip in ips:
            if ip in mdns_results:
                final_map[ip] = mdns_results[ip]
            elif ip in netbios_results:
                final_map[ip] = netbios_results[ip]
            elif ip in ssdp_results:
                final_map[ip] = ssdp_results[ip]
            elif ip in dns_results:
                final_map[ip] = dns_results[ip]
            elif ip in http_results:
                final_map[ip] = http_results[ip]

        return final_map

    def get_device_metadata(self, ip: str) -> Dict[str, str]:
        """Retrieves discovered metadata from child resolvers."""
        data: Dict[str, str] = {}
        if hasattr(self.ssdp, "get_metadata"):
            data.update(self.ssdp.get_metadata(ip))
        if self.http and hasattr(self.http, "get_metadata"):
            data.update(self.http.get_metadata(ip))
        return data

    def get_all_metadata(self) -> Dict[str, Dict[str, str]]:
        """Retrieves all discovered metadata from child resolvers."""
        combined: Dict[str, Dict[str, str]] = {}
        if hasattr(self.ssdp, "get_all_metadata"):
            for ip, m in self.ssdp.get_all_metadata().items():
                combined.setdefault(ip, {}).update(m)
        if self.http and hasattr(self.http, "get_all_metadata"):
            for ip, m in self.http.get_all_metadata().items():
                combined.setdefault(ip, {}).update(m)
        return combined

