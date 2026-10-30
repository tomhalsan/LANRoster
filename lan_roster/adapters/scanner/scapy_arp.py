import os
import platform
from typing import List, Tuple
from scapy.layers.l2 import ARP, Ether
from scapy.sendrecv import srp
from lan_roster.ports.scanner import NetworkScannerPort


class ScapyArpScanner(NetworkScannerPort):
    """
    Network scanner adapter implementing ARP sweeps via Scapy.
    Includes automated OS detection and friendly Npcap verification on Windows.
    """

    NPCAP_DOWNLOAD_URL = "https://npcap.com"

    def __init__(self, timeout: int = 2) -> None:
        self.timeout = timeout

    @staticmethod
    def is_windows() -> bool:
        """Returns True if the current host operating system is Windows."""
        return platform.system() == "Windows"

    @classmethod
    def check_windows_npcap_installed(cls) -> bool:
        """
        Checks standard system directories for Npcap presence on Windows.
        Returns True if Npcap / WinPcap driver DLLs are found.
        """
        if not cls.is_windows():
            return True

        win_dir = os.environ.get("SystemRoot", r"C:\Windows")
        sys32 = os.path.join(win_dir, "System32")
        npcap_dir = os.path.join(sys32, "Npcap")
        wpcap_dll = os.path.join(sys32, "wpcap.dll")
        packet_dll = os.path.join(sys32, "Packet.dll")

        return (
            os.path.exists(npcap_dir)
            or os.path.exists(wpcap_dll)
            or os.path.exists(packet_dll)
        )

    def scan(self, target_subnet: str) -> List[Tuple[str, str]]:
        if self.is_windows() and not self.check_windows_npcap_installed():
            raise RuntimeError(
                f"Npcap is required for Layer 2 ARP discovery on Windows. "
                f"Please download and install Npcap from {self.NPCAP_DOWNLOAD_URL} "
                f"(be sure to check 'Install Npcap in WinPcap API-compatible Mode')."
            )

        broadcast = Ether(dst="ff:ff:ff:ff:ff:ff")
        arp_request = ARP(pdst=target_subnet)
        packet = broadcast / arp_request

        try:
            answered, _ = srp(packet, timeout=self.timeout, verbose=False)
        except Exception as e:
            err_str = str(e).lower()
            if self.is_windows():
                if any(w in err_str for w in ("winpcap", "pcap", "layer 2", "sniffing")):
                    raise RuntimeError(
                        f"Npcap packet capture driver missing or not loaded. "
                        f"Please install Npcap from {self.NPCAP_DOWNLOAD_URL} and run LANRoster as Administrator."
                    ) from e
                elif any(w in err_str for w in ("permission", "access denied")):
                    raise RuntimeError(
                        "Administrator privileges required for Layer 2 ARP scanning on Windows. "
                        "Please run PowerShell/Command Prompt as Administrator."
                    ) from e
            raise

        discovered: List[Tuple[str, str]] = []
        for _, received_packet in answered:
            ip = str(received_packet.psrc)
            mac = str(received_packet.hwsrc)
            discovered.append((ip, mac))

        return discovered
