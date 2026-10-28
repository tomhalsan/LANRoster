import socket
import struct
import time
from typing import Dict, List, Tuple
from lan_roster.domain.models import HostnameSource
from lan_roster.ports.resolver import HostnameResolverPort


class SocketMDNSResolver(HostnameResolverPort):
    """mDNS resolver sending reverse PTR queries via multicast UDP 5353."""

    def __init__(self, timeout: float = 1.5) -> None:
        self.timeout = timeout

    @staticmethod
    def _make_mdns_ptr(ip: str) -> bytes:
        parts = ip.split(".")
        rev = f"{parts[3]}.{parts[2]}.{parts[1]}.{parts[0]}.in-addr.arpa"
        header = struct.pack(">HHHHHH", 0, 0, 1, 0, 0, 0)
        q = b""
        for p in rev.split("."):
            q += bytes([len(p)]) + p.encode("ascii")
        q += b"\x00"
        q += struct.pack(">HH", 12, 1)  # PTR, IN
        return header + q

    @staticmethod
    def _parse_dns_name(data: bytes, offset: int) -> Tuple[str, int]:
        parts: List[str] = []
        visited = set()
        orig = None
        while offset < len(data):
            length = data[offset]
            if length == 0:
                if orig is None:
                    orig = offset + 1
                break
            elif (length & 0xC0) == 0xC0:
                if orig is None:
                    orig = offset + 2
                ptr = struct.unpack(">H", data[offset : offset + 2])[0] & 0x3FFF
                if ptr in visited:
                    break
                visited.add(ptr)
                offset = ptr
            else:
                offset += 1
                parts.append(data[offset : offset + length].decode("utf-8", errors="ignore"))
                offset += length
        return ".".join(parts), (orig if orig is not None else offset)

    def resolve_batch(self, ips: List[str]) -> Dict[str, Tuple[str, HostnameSource]]:
        results: Dict[str, Tuple[str, HostnameSource]] = {}
        if not ips:
            return results

        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            s.bind(("", 5353))
            mreq = struct.pack("4sL", socket.inet_aton("224.0.0.251"), socket.INADDR_ANY)
            s.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
            s.settimeout(0.3)

            for ip in ips:
                pkt = self._make_mdns_ptr(ip)
                s.sendto(pkt, ("224.0.0.251", 5353))
                try:
                    s.sendto(pkt, (ip, 5353))
                except Exception:
                    pass

            end = time.time() + self.timeout
            while time.time() < end:
                try:
                    data, _ = s.recvfrom(4096)
                    if len(data) > 12:
                        num_ans = struct.unpack(">H", data[6:8])[0]
                        num_q = struct.unpack(">H", data[4:6])[0]
                        curr = 12
                        for _ in range(num_q):
                            _, curr = self._parse_dns_name(data, curr)
                            curr += 4
                        for _ in range(num_ans):
                            if curr >= len(data):
                                break
                            qname, curr = self._parse_dns_name(data, curr)
                            if curr + 10 > len(data):
                                break
                            rtype, _, _, rdlen = struct.unpack(">HHIH", data[curr : curr + 10])
                            curr += 10
                            if rtype == 12:  # PTR
                                target, _ = self._parse_dns_name(data, curr)
                                if "in-addr.arpa" in qname:
                                    p = qname.replace(".in-addr.arpa", "").split(".")
                                    orig_ip = f"{p[3]}.{p[2]}.{p[1]}.{p[0]}"
                                    clean_target = target.rstrip(".")
                                    if clean_target:
                                        results[orig_ip] = (clean_target, HostnameSource.MDNS)
                            elif rtype == 1 and rdlen == 4:  # A record (e.g. device.local -> IPv4)
                                try:
                                    ip_ans = socket.inet_ntoa(data[curr : curr + 4])
                                    clean_name = qname.rstrip(".")
                                    if clean_name and ip_ans in ips:
                                        results[ip_ans] = (clean_name, HostnameSource.MDNS)
                                except Exception:
                                    pass
                            curr += rdlen
                except socket.timeout:
                    pass
                except Exception:
                    pass
            s.close()
        except Exception:
            pass

        return results

