from typing import List, Tuple
from scapy.layers.l2 import ARP, Ether
from scapy.sendrecv import srp
from lan_roster.ports.scanner import NetworkScannerPort


class ScapyArpScanner(NetworkScannerPort):
    """Network scanner adapter implementing ARP sweeps via Scapy."""

    def __init__(self, timeout: int = 2) -> None:
        self.timeout = timeout

    def scan(self, target_subnet: str) -> List[Tuple[str, str]]:
        broadcast = Ether(dst="ff:ff:ff:ff:ff:ff")
        arp_request = ARP(pdst=target_subnet)
        packet = broadcast / arp_request

        answered, _ = srp(packet, timeout=self.timeout, verbose=False)

        discovered: List[Tuple[str, str]] = []
        for _, received_packet in answered:
            ip = str(received_packet.psrc)
            mac = str(received_packet.hwsrc)
            discovered.append((ip, mac))

        return discovered
