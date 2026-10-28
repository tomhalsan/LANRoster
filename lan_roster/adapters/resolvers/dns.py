import socket
import struct
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Tuple
from lan_roster.domain.models import HostnameSource
from lan_roster.ports.resolver import HostnameResolverPort


class SocketDNSResolver(HostnameResolverPort):
    """
    Unicast reverse DNS resolver combining local system resolution
    and direct local gateway router PTR queries.
    """

    def __init__(self, gateway_ip: str | None = None, timeout: float = 0.3) -> None:
        self.gateway_ip = gateway_ip
        self.timeout = timeout

    @staticmethod
    def _query_gateway_ptr(ip: str, gateway: str, timeout: float = 0.3) -> str | None:
        """Sends a DNS PTR query directly to the network gateway/DHCP router."""
        try:
            parts = ip.split(".")
            rev = f"{parts[3]}.{parts[2]}.{parts[1]}.{parts[0]}.in-addr.arpa"
            header = struct.pack(">HHHHHH", 0x1234, 0x0100, 1, 0, 0, 0)
            q = b"".join(bytes([len(p)]) + p.encode("ascii") for p in rev.split(".")) + b"\x00"
            q += struct.pack(">HH", 12, 1)  # PTR, IN
            pkt = header + q

            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(timeout)
            sock.sendto(pkt, (gateway, 53))
            resp, _ = sock.recvfrom(512)
            sock.close()

            if len(resp) > 12:
                num_ans = struct.unpack(">H", resp[6:8])[0]
                curr = 12
                while curr < len(resp) and resp[curr] != 0:
                    curr += 1 + resp[curr]
                curr += 5  # 0x00 + QTYPE(2) + QCLASS(2)

                for _ in range(num_ans):
                    if curr >= len(resp):
                        break
                    if (resp[curr] & 0xC0) == 0xC0:
                        curr += 2
                    else:
                        while curr < len(resp) and resp[curr] != 0:
                            curr += 1 + resp[curr]
                        curr += 1
                    rtype, _, _, rdlen = struct.unpack(">HHIH", resp[curr : curr + 10])
                    curr += 10
                    if rtype == 12:  # PTR
                        labels = []
                        p = curr
                        end_rdata = curr + rdlen
                        while p < end_rdata:
                            length = resp[p]
                            if length == 0:
                                break
                            if (length & 0xC0) == 0xC0:
                                break
                            labels.append(resp[p + 1 : p + 1 + length].decode("utf-8", errors="ignore"))
                            p += 1 + length
                        name = ".".join(labels)
                        if name:
                            return name
                    curr += rdlen
        except Exception:
            pass
        return None

    def _resolve_single_ip(self, ip: str) -> Tuple[str, str | None]:
        # 1. Try local system DNS
        try:
            host, _, _ = socket.gethostbyaddr(ip)
            if host:
                return ip, host
        except Exception:
            pass

        # 2. Try gateway DNS router (e.g. 10.0.0.1 or <first-3-octets>.1)
        gw = self.gateway_ip
        if not gw:
            parts = ip.split(".")
            if len(parts) == 4:
                gw = f"{parts[0]}.{parts[1]}.{parts[2]}.1"

        if gw:
            gw_host = self._query_gateway_ptr(ip, gw, timeout=self.timeout)
            if gw_host:
                return ip, gw_host

        return ip, None

    def resolve_batch(self, ips: List[str]) -> Dict[str, Tuple[str, HostnameSource]]:
        results: Dict[str, Tuple[str, HostnameSource]] = {}
        if not ips:
            return results

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(self._resolve_single_ip, ip) for ip in ips]
            for f in as_completed(futures):
                try:
                    ip, hostname = f.result()
                    if hostname:
                        results[ip] = (hostname, HostnameSource.DNS)
                except Exception:
                    pass

        return results

