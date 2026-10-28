import time
from typing import List
from lan_roster.domain.models import Device, HostnameSource
from lan_roster.domain.exceptions import ScanExecutionException
from lan_roster.ports.scanner import NetworkScannerPort
from lan_roster.ports.resolver import HostnameResolverPort
from lan_roster.ports.manufacturer import ManufacturerRepositoryPort
from lan_roster.ports.repository import DeviceRepositoryPort


class ScanNetworkUseCase:
    """Use case coordinating the network sweep and entity assembly."""

    PC_VENDORS = ("Intel", "Microsoft", "Dell", "Lenovo", "HP", "Asus", "Acer")

    def __init__(
        self,
        scanner: NetworkScannerPort,
        resolver: HostnameResolverPort,
        manufacturer_repo: ManufacturerRepositoryPort,
        device_repo: DeviceRepositoryPort,
    ) -> None:
        self.scanner = scanner
        self.resolver = resolver
        self.manufacturer_repo = manufacturer_repo
        self.device_repo = device_repo

    def execute(self) -> List[Device]:
        state = self.device_repo.get_scan_state()
        self.device_repo.update_scan_state(is_scanning=True, error_message=None)

        try:
            # 1. Hardware ARP sweep
            discovered_nodes = self.scanner.scan(state.subnet)
            current_time = time.strftime("%H:%M:%S")
            all_ips = [ip for ip, _ in discovered_nodes]

            # 2. Multi-protocol hostname resolution
            resolved_hosts = self.resolver.resolve_batch(all_ips)

            # Sync discovered UPnP / SSDP metadata (Probe B) to manufacturer repository
            if hasattr(self.resolver, "get_all_metadata") and hasattr(self.manufacturer_repo, "register_device_metadata"):
                for m_ip, meta in self.resolver.get_all_metadata().items():
                    if meta.get("manufacturer"):
                        self.manufacturer_repo.register_device_metadata(
                            ip=m_ip,
                            manufacturer=meta["manufacturer"],
                            model=meta.get("model", ""),
                        )

            # 3. Assemble domain entities
            device_entities: List[Device] = []
            for ip, mac in discovered_nodes:
                vendor = self.manufacturer_repo.get_manufacturer(mac, ip=ip)
                hostname, source = resolved_hosts.get(
                    ip, ("Unknown", HostnameSource.UNKNOWN)
                )

                # Heuristic: If unidentified host belongs to PC maker, flag firewalled state
                if hostname == "Unknown" and any(
                    w in vendor for w in self.PC_VENDORS
                ):
                    source = HostnameSource.FIREWALLED

                device_entities.append(
                    Device(
                        ip=ip,
                        mac=mac,
                        hostname=hostname,
                        source=source,
                        vendor=vendor,
                        last_seen=current_time,
                    )
                )

            # 4. Persist and merge updated roster
            self.device_repo.save_devices(device_entities)
            all_devices = self.device_repo.get_devices()
            self.device_repo.update_scan_state(
                is_scanning=False,
                last_scan_time=current_time,
                total_found=len(all_devices),
            )
            return list(all_devices.values())

        except Exception as e:
            self.device_repo.update_scan_state(
                is_scanning=False,
                error_message=str(e),
            )
            raise ScanExecutionException(f"Failed to complete network scan: {e}") from e

