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
    ) -> None:
        self.mdns = mdns_resolver
        self.netbios = netbios_resolver
        self.ssdp = ssdp_resolver
        self.dns = dns_resolver

    def resolve_batch(self, ips: List[str]) -> Dict[str, Tuple[str, HostnameSource]]:
        if not ips:
            return {}

        # 1. mDNS resolution (covers Apple, Android, TVs, IoT, modern Win)
        mdns_results = self.mdns.resolve_batch(ips)

        # 2. SSDP discovery (covers Smart TVs, media renderers)
        ssdp_results = self.ssdp.resolve_batch(ips)

        # 3. NetBIOS queries (covers Windows PC names, Samba shares)
        netbios_results = self.netbios.resolve_batch(ips)

        # 4. Unicast reverse DNS fallback
        dns_results = self.dns.resolve_batch(ips)

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

        return final_map
