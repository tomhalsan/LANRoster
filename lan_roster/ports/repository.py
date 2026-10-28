from abc import ABC, abstractmethod
from typing import Dict, List
from lan_roster.domain.models import Device, ScanState


class DeviceRepositoryPort(ABC):
    """Port for persisting and retrieving discovered devices and scanner state."""

    @abstractmethod
    def get_devices(self) -> Dict[str, Device]:
        """Retrieves all currently stored devices mapped by IP address."""
        pass

    @abstractmethod
    def save_devices(self, devices: List[Device]) -> None:
        """Atomically replaces the active device registry."""
        pass

    @abstractmethod
    def get_scan_state(self) -> ScanState:
        """Retrieves the current scanner state."""
        pass

    @abstractmethod
    def update_scan_state(
        self,
        subnet: str | None = None,
        is_scanning: bool | None = None,
        last_scan_time: str | None = None,
        error_message: str | None = None,
        total_found: int | None = None,
    ) -> ScanState:
        """Updates specific fields of the current scanner state."""
        pass

