from abc import ABC, abstractmethod
from typing import Dict, List


class ServiceScannerPort(ABC):
    """
    Port interface for detecting open network ports and services.
    Abstracts direct socket connectivity from application use cases.
    """

    @abstractmethod
    def scan_ports(self, ip: str, ports: List[int] | None = None) -> List[int]:
        """Probes a single IP address and returns a list of open ports."""
        pass

    @abstractmethod
    def scan_ports_batch(
        self, ips: List[str], ports: List[int] | None = None
    ) -> Dict[str, List[int]]:
        """Concurrently probes multiple IP addresses for open ports."""
        pass
