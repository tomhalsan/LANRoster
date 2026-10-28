import threading
from typing import Dict, List
from lan_roster.domain.models import Device, ScanState
from lan_roster.ports.repository import DeviceRepositoryPort


class InMemoryDeviceRepository(DeviceRepositoryPort):
    """Thread-safe in-memory repository for devices and scanner state."""

    def __init__(self, initial_subnet: str = "10.0.0.0/24") -> None:
        self._lock = threading.Lock()
        self._devices: Dict[str, Device] = {}
        self._state = ScanState(subnet=initial_subnet)

    def get_devices(self) -> Dict[str, Device]:
        with self._lock:
            return dict(self._devices)

    def save_devices(self, devices: List[Device]) -> None:
        with self._lock:
            self._devices.clear()
            for dev in devices:
                self._devices[dev.ip] = dev

    def get_scan_state(self) -> ScanState:
        with self._lock:
            return ScanState(
                subnet=self._state.subnet,
                is_scanning=self._state.is_scanning,
                last_scan_time=self._state.last_scan_time,
                error_message=self._state.error_message,
                total_found=self._state.total_found,
            )

    def update_scan_state(
        self,
        subnet: str | None = None,
        is_scanning: bool | None = None,
        last_scan_time: str | None = None,
        error_message: str | None = None,
        total_found: int | None = None,
    ) -> ScanState:
        with self._lock:
            if subnet is not None:
                self._state.subnet = subnet
            if is_scanning is not None:
                self._state.is_scanning = is_scanning
            if last_scan_time is not None:
                self._state.last_scan_time = last_scan_time
            if error_message is not None:
                self._state.error_message = error_message
            elif is_scanning is True:
                self._state.error_message = None
            if total_found is not None:
                self._state.total_found = total_found

            return ScanState(
                subnet=self._state.subnet,
                is_scanning=self._state.is_scanning,
                last_scan_time=self._state.last_scan_time,
                error_message=self._state.error_message,
                total_found=self._state.total_found,
            )
