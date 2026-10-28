from abc import ABC, abstractmethod


class ManufacturerRepositoryPort(ABC):
    """Port for querying hardware manufacturer/vendor data by MAC address."""

    @abstractmethod
    def get_manufacturer(self, mac_address: str, ip: str | None = None) -> str:
        """
        Resolves the hardware manufacturer or device type for a given MAC address and optional IP.
        Returns a descriptive string (e.g. 'Apple', 'Intel (Windows PC)').
        """
        pass

