from concurrent.futures import ThreadPoolExecutor, as_completed
import socket
from typing import Dict, List
from lan_roster.ports.service_scanner import ServiceScannerPort


class SocketServiceScanner(ServiceScannerPort):
    """
    High-speed TCP service scanner implementing ServiceScannerPort.
    Probes standard device management and media service ports with minimal latency.
    """

    DEFAULT_PORTS: List[int] = [
        80,     # HTTP (Web Admin Console)
        443,    # HTTPS (Secure Web Console)
        22,     # SSH (Remote Shell)
        445,    # SMB (File Sharing)
        631,    # IPP (Internet Printing Protocol)
        8008,   # Google Cast / HTTP Alt
        8080,   # HTTP Alt (Web Proxy / Management)
        62078,  # Apple MobileDevice Lockdown
    ]

    def __init__(self, timeout: float = 0.2, max_workers: int = 20) -> None:
        self.timeout = timeout
        self.max_workers = max_workers

    def _probe_port(self, ip: str, port: int) -> int | None:
        """Attempts a non-blocking TCP connect. Returns port if open, else None."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(self.timeout)
                res = sock.connect_ex((ip, port))
                if res == 0:
                    return port
        except Exception:
            pass
        return None

    def scan_ports(self, ip: str, ports: List[int] | None = None) -> List[int]:
        """Probes a single IP address across target ports."""
        target_ports = ports or self.DEFAULT_PORTS
        open_ports: List[int] = []

        with ThreadPoolExecutor(max_workers=min(len(target_ports), self.max_workers)) as executor:
            future_to_port = {
                executor.submit(self._probe_port, ip, port): port
                for port in target_ports
            }
            for future in as_completed(future_to_port):
                result = future.result()
                if result is not None:
                    open_ports.append(result)

        return sorted(open_ports)

    def scan_ports_batch(
        self, ips: List[str], ports: List[int] | None = None
    ) -> Dict[str, List[int]]:
        """Concurrently probes multiple IP addresses for open ports."""
        if not ips:
            return {}

        results: Dict[str, List[int]] = {}
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_ip = {
                executor.submit(self.scan_ports, ip, ports): ip
                for ip in ips
            }
            for future in as_completed(future_to_ip):
                ip = future_to_ip[future]
                try:
                    results[ip] = future.result()
                except Exception:
                    results[ip] = []

        return results
