from abc import ABC, abstractmethod
from typing import List, Tuple


class NetworkScannerPort(ABC):
    """Port for Layer 2 network scanning."""

    @abstractmethod
    def scan(self, target_subnet: str) -> List[Tuple[str, str]]:
        """
        Broadcasts ARP requests across target_subnet.
        Returns a list of discovered (ip, mac) tuples.
        """
        pass
