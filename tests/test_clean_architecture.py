import unittest
from typing import Dict, List, Tuple
from lan_roster.domain.models import Device, HostnameSource, ScanState
from lan_roster.domain.exceptions import InvalidSubnetException
from lan_roster.ports.scanner import NetworkScannerPort
from lan_roster.ports.resolver import HostnameResolverPort
from lan_roster.ports.manufacturer import ManufacturerRepositoryPort
from lan_roster.adapters.repository.memory import InMemoryDeviceRepository
from lan_roster.adapters.manufacturer.hybrid_repo import HybridManufacturerRepository
from lan_roster.use_cases.scan_network import ScanNetworkUseCase
from lan_roster.use_cases.get_devices import GetDevicesUseCase
from lan_roster.use_cases.update_subnet import UpdateSubnetUseCase


class DummyScanner(NetworkScannerPort):
    def __init__(self, nodes: List[Tuple[str, str]]) -> None:
        self.nodes = nodes

    def scan(self, target_subnet: str) -> List[Tuple[str, str]]:
        return self.nodes


class DummyResolver(HostnameResolverPort):
    def __init__(self, mapping: Dict[str, Tuple[str, HostnameSource]]) -> None:
        self.mapping = mapping

    def resolve_batch(self, ips: List[str]) -> Dict[str, Tuple[str, HostnameSource]]:
        return {ip: self.mapping[ip] for ip in ips if ip in self.mapping}


class DummyManufacturerRepo(ManufacturerRepositoryPort):
    def get_manufacturer(self, mac_address: str, ip: str | None = None) -> str:
        if mac_address.startswith("CC:15:31"):
            return "Intel (Windows PC)"
        if mac_address.startswith("5C:9B:A6"):
            return "Apple"
        return "Generic Device"


class TestCleanArchitecture(unittest.TestCase):
    def setUp(self):
        self.repo = InMemoryDeviceRepository(initial_subnet="10.0.0.0/24")

    def test_update_subnet_valid(self):
        use_case = UpdateSubnetUseCase(device_repo=self.repo)
        normalized = use_case.execute("10.0.0.1")
        self.assertEqual(normalized, "10.0.0.0/24")
        self.assertEqual(self.repo.get_scan_state().subnet, "10.0.0.0/24")

        normalized2 = use_case.execute("10.0.0.0/25")
        self.assertEqual(normalized2, "10.0.0.0/25")

    def test_update_subnet_invalid(self):
        use_case = UpdateSubnetUseCase(device_repo=self.repo)
        with self.assertRaises(InvalidSubnetException):
            use_case.execute("invalid_subnet_cidr")

    def test_scan_network_use_case_with_firewall_heuristics(self):
        nodes = [
            ("10.0.0.117", "5C:9B:A6:8B:9C:03"),  # Apple
            ("10.0.0.139", "CC:15:31:E5:BB:DB"),  # Intel PC, unresolvable
        ]
        scanner = DummyScanner(nodes)
        resolver = DummyResolver({
            "10.0.0.117": ("Toms-MBP.local", HostnameSource.MDNS)
        })
        manuf_repo = DummyManufacturerRepo()

        use_case = ScanNetworkUseCase(
            scanner=scanner,
            resolver=resolver,
            manufacturer_repo=manuf_repo,
            device_repo=self.repo,
        )

        devices = use_case.execute()
        self.assertEqual(len(devices), 2)

        apple_dev = next(d for d in devices if d.ip == "10.0.0.117")
        self.assertEqual(apple_dev.hostname, "Toms-MBP.local")
        self.assertEqual(apple_dev.source, HostnameSource.MDNS)
        self.assertEqual(apple_dev.vendor, "Apple")

        win_dev = next(d for d in devices if d.ip == "10.0.0.139")
        self.assertEqual(win_dev.hostname, "Unknown")
        self.assertEqual(win_dev.source, HostnameSource.FIREWALLED)
        self.assertEqual(win_dev.vendor, "Intel (Windows PC)")

    def test_get_devices_use_case_sorting(self):
        # Insert out of order
        self.repo.save_devices([
            Device(ip="10.0.0.100", mac="AA:AA:AA:AA:AA:01"),
            Device(ip="10.0.0.2", mac="AA:AA:AA:AA:AA:02"),
            Device(ip="10.0.0.20", mac="AA:AA:AA:AA:AA:03"),
        ])

        use_case = GetDevicesUseCase(device_repo=self.repo)
        sorted_devs, state = use_case.execute()
        ips = list(sorted_devs.keys())
        self.assertEqual(ips, ["10.0.0.2", "10.0.0.20", "10.0.0.100"])

    def test_manufacturer_repo_privacy_detection(self):
        repo = HybridManufacturerRepository()
        # Randomized MAC (bit 1 of 1st byte is 1): e.g. 02:..., ca:..., f6:...
        self.assertEqual(repo.get_manufacturer("ca:e4:3b:56:ce:62"), "Private/Randomized MAC")
        self.assertEqual(repo.get_manufacturer("5c:9b:a6:8b:9c:03"), "Apple")
        self.assertEqual(repo.get_manufacturer("cc:15:31:e5:bb:db"), "Intel (Windows PC)")

    def test_probe_a_apple_lockdown_detection(self):
        repo = HybridManufacturerRepository()
        # Patch check_apple_lockdown to return True for simulated iPhone IP
        repo.check_apple_lockdown = staticmethod(lambda ip, timeout=0.3: ip == "10.0.0.18")

        # Randomized MAC on iPhone IP -> identifies as Apple iOS Device (Private MAC)
        vendor = repo.get_manufacturer("82:11:02:26:fa:0f", ip="10.0.0.18")
        self.assertEqual(vendor, "Apple iOS Device (Private MAC)")

        # Other IP with randomized MAC -> remains Private/Randomized MAC
        vendor_other = repo.get_manufacturer("82:11:02:26:fa:0f", ip="10.0.0.99")
        self.assertEqual(vendor_other, "Private/Randomized MAC")

    def test_probe_b_upnp_metadata_registration(self):
        repo = HybridManufacturerRepository()
        repo.register_device_metadata("10.0.0.119", "TCL", "Smart TV")

        # Unknown or generic MAC resolves via UPnP descriptor
        vendor = repo.get_manufacturer("AA:BB:CC:DD:EE:FF", ip="10.0.0.119")
        self.assertEqual(vendor, "TCL (Smart TV)")


if __name__ == "__main__":
    unittest.main()

