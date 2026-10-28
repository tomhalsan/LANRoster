from abc import ABC, abstractmethod
from typing import Dict, List, Tuple
from lan_roster.domain.models import HostnameSource


class HostnameResolverPort(ABC):
    """Port for discovering advertised hostnames for network nodes."""

    @abstractmethod
    def resolve_batch(
        self, ips: List[str]
    ) -> Dict[str, Tuple[str, HostnameSource]]:
        """
        Resolves hostnames for a collection of IP addresses.
        Returns a mapping of {ip: (hostname, source)}.
        """
        pass
