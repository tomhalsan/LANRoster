from typing import Dict, Tuple
from lan_roster.domain.models import Device, ScanState
from lan_roster.ports.repository import DeviceRepositoryPort


class GetDevicesUseCase:
    """Use case for retrieving the active roster sorted numerically by IP."""

    def __init__(self, device_repo: DeviceRepositoryPort) -> None:
        self.device_repo = device_repo

    def execute(self) -> Tuple[Dict[str, Device], ScanState]:
        devices = self.device_repo.get_devices()
        state = self.device_repo.get_scan_state()

        # Sort IP addresses numerically (e.g. 10.0.0.2 before 10.0.0.10)
        def ip_sort_key(item: Tuple[str, Device]) -> list[int]:
            try:
                return [int(p) for p in item[0].split(".")]
            except ValueError:
                return [0, 0, 0, 0]

        sorted_devices = dict(sorted(devices.items(), key=ip_sort_key))
        return sorted_devices, state

