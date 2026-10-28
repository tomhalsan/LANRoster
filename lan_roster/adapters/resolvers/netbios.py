import concurrent.futures
import socket
import struct
from typing import Dict, List, Tuple
from lan_roster.domain.models import HostnameSource
from lan_roster.ports.resolver import HostnameResolverPort


class SocketNetBIOSResolver(HostnameResolverPort):
    """NetBIOS Name Service resolver querying node status over UDP 137."""

    def __init__(self, timeout: float = 0.4, max_workers: int = 20) -> None:
        self.timeout = timeout
        self.max_workers = max_workers

    def _query_ip(self, ip: str) -> str | None:
        name = "*" + " " * 14 + "\x00"
        encoded: List[str] = []
        for c in name:
            b = ord(c)
            encoded.append(chr(((b >> 4) & 0xF) + ord("A")))
            encoded.append(chr((b & 0xF) + ord("A")))
        encoded_name = "".join(encoded).encode("ascii")

        header = struct.pack(">HHHHHH", 0x1337, 0x0000, 1, 0, 0, 0)
        question = b"\x20" + encoded_name + b"\x00" + struct.pack(">HH", 0x0021, 0x0001)
        packet = header + question

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(self.timeout)
        try:
            sock.sendto(packet, (ip, 137))
            data, _ = sock.recvfrom(1024)
            if len(data) > 56:
                num_names = data[56]
                offset = 57
                for _ in range(num_names):
                    if offset + 18 <= len(data):
                        raw_name = (
                            data[offset : offset + 15]
                            .decode("latin1", errors="ignore")
                            .strip()
                        )
                        name_type = data[offset + 15]
                        flags = struct.unpack(">H", data[offset + 16 : offset + 18])[0]
                        is_group = bool(flags & 0x8000)
                        if not is_group and name_type in (0x00, 0x20) and raw_name:
                            return raw_name
                        offset += 18
        except Exception:
            pass
        finally:
            sock.close()
        return None

    def resolve_batch(self, ips: List[str]) -> Dict[str, Tuple[str, HostnameSource]]:
        results: Dict[str, Tuple[str, HostnameSource]] = {}
        if not ips:
            return results

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_ip = {executor.submit(self._query_ip, ip): ip for ip in ips}
            for future in concurrent.futures.as_completed(future_to_ip):
                ip = future_to_ip[future]
                try:
                    name = future.result()
                    if name:
                        results[ip] = (name, HostnameSource.NETBIOS)
                except Exception:
                    pass

        return results
