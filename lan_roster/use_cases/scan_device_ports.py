from typing import List
from lan_roster.domain.exceptions import LANRosterException
from lan_roster.ports.repository import DeviceRepositoryPort
from lan_roster.ports.service_scanner import ServiceScannerPort


class ScanDevicePortsUseCase:
    """Use case for on-demand probing of open ports and services on a specific network node."""

    def __init__(
        self,
        service_scanner: ServiceScannerPort,
        device_repo: DeviceRepositoryPort,
    ) -> None:
        self.service_scanner = service_scanner
        self.device_repo = device_repo

    def execute(self, ip: str, ports: List[int] | None = None) -> List[int]:
        devices = self.device_repo.get_devices()
        if ip not in devices:
            raise LANRosterException(f"Device with IP '{ip}' not found in active roster.")

        open_ports = self.service_scanner.scan_ports(ip, ports=ports)

        # Update entity in repository
        device = devices[ip]
        device.open_ports = open_ports
        self.device_repo.save_devices([device])

        return open_ports

