from abc import ABC, abstractmethod


class NetworkConfigPort(ABC):
    """Port for querying local network interface configurations."""

    @abstractmethod
    def detect_default_subnet(self) -> str:
        """
        Detects the active default network interface CIDR subnet.
        Returns a CIDR string such as '10.0.0.0/24'.
        """
        pass
