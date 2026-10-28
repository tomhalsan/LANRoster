import threading
import unittest
from typing import Dict, List, Tuple

from lan_roster.domain.models import Device, HostnameSource, ScanState
from lan_roster.domain.exceptions import (
    LANRosterException,
    InvalidSubnetException,
    ScanExecutionException,
)
from lan_roster.ports.scanner import NetworkScannerPort
from lan_roster.ports.resolver import HostnameResolverPort
from lan_roster.ports.manufacturer import ManufacturerRepositoryPort
from lan_roster.adapters.repository.memory import InMemoryDeviceRepository
from lan_roster.adapters.manufacturer.hybrid_repo import HybridManufacturerRepository
from lan_roster.adapters.resolvers.composite import CompositeHostnameResolver
from lan_roster.adapters.resolvers.mdns import SocketMDNSResolver
from lan_roster.adapters.resolvers.http_banner import SocketHTTPBannerResolver
from lan_roster.use_cases.scan_network import ScanNetworkUseCase
from lan_roster.use_cases.get_devices import GetDevicesUseCase
from lan_roster.use_cases.update_subnet import UpdateSubnetUseCase
from lan_roster.ui.web import create_web_app


# ---------------------------------------------------------------------------
# Test Doubles / Mock Ports
# ---------------------------------------------------------------------------

class DummyScanner(NetworkScannerPort):
    def __init__(self, nodes: List[Tuple[str, str]] | None = None, raise_error: bool = False) -> None:
        self.nodes = nodes or []
        self.raise_error = raise_error

    def scan(self, target_subnet: str) -> List[Tuple[str, str]]:
        if self.raise_error:
            raise RuntimeError("Underlying socket error during ARP sweep")
        return self.nodes


class DummyResolver(HostnameResolverPort):
    def __init__(
        self,
        mapping: Dict[str, Tuple[str, HostnameSource]] | None = None,
        metadata: Dict[str, Dict[str, str]] | None = None,
    ) -> None:
        self.mapping = mapping or {}
        self.metadata = metadata or {}

    def resolve_batch(self, ips: List[str]) -> Dict[str, Tuple[str, HostnameSource]]:
        return {ip: self.mapping[ip] for ip in ips if ip in self.mapping}

    def get_all_metadata(self) -> Dict[str, Dict[str, str]]:
        return self.metadata


class DummyManufacturerRepo(ManufacturerRepositoryPort):
    def __init__(self) -> None:
        self.registered_metadata: Dict[str, Dict[str, str]] = {}

    def register_device_metadata(self, ip: str, manufacturer: str, model: str = "") -> None:
        self.registered_metadata[ip] = {"manufacturer": manufacturer, "model": model}

    def get_manufacturer(self, mac_address: str, ip: str | None = None) -> str:
        if ip and ip in self.registered_metadata:
            m = self.registered_metadata[ip]
            return f"{m['manufacturer']} ({m['model']})" if m.get("model") else m["manufacturer"]
        if mac_address.startswith("CC:15:31"):
            return "Intel (Windows PC)"
        if mac_address.startswith("5C:9B:A6"):
            return "Apple"
        return "Generic Device"


# ---------------------------------------------------------------------------
# Test Suite: Clean Architecture Layer Isolation
# ---------------------------------------------------------------------------

class TestDomainLayer(unittest.TestCase):
    """1. Domain Layer Tests: Pure business entities & exceptions."""

    def test_device_model_to_dict(self):
        dev = Device(
            ip="10.0.0.18",
            mac="82:11:02:26:FA:0F",
            hostname="iPhone-7544",
            source=HostnameSource.DNS,
            vendor="Apple iOS Device (Private MAC)",
            last_seen="12:00:00",
        )
        data = dev.to_dict()
        self.assertEqual(data["mac"], "82:11:02:26:FA:0F")
        self.assertEqual(data["hostname"], "iPhone-7544")
        self.assertEqual(data["source"], "DNS")
        self.assertEqual(data["vendor"], "Apple iOS Device (Private MAC)")

    def test_scan_state_to_dict(self):
        state = ScanState(subnet="10.0.0.0/24", is_scanning=True, total_found=5)
        data = state.to_dict()
        self.assertEqual(data["subnet"], "10.0.0.0/24")
        self.assertTrue(data["scanning"])
        self.assertEqual(data["total_found"], 5)

    def test_domain_exception_hierarchy(self):
        self.assertTrue(issubclass(InvalidSubnetException, LANRosterException))
        self.assertTrue(issubclass(ScanExecutionException, LANRosterException))


class TestUseCasesLayer(unittest.TestCase):
    """2. Use Cases Layer Tests: Orchestration via contract ports."""

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
        self.assertIn("Invalid subnet", self.repo.get_scan_state().error_message or "")

    def test_scan_network_success_with_heuristics(self):
        nodes = [
            ("10.0.0.117", "5C:9B:A6:8B:9C:03"),
            ("10.0.0.139", "CC:15:31:E5:BB:DB"),
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
        self.assertEqual(apple_dev.vendor, "Apple")

        win_dev = next(d for d in devices if d.ip == "10.0.0.139")
        self.assertEqual(win_dev.source, HostnameSource.FIREWALLED)
        self.assertEqual(win_dev.vendor, "Intel (Windows PC)")

    def test_scan_network_syncs_upnp_metadata(self):
        nodes = [("10.0.0.119", "AA:BB:CC:DD:EE:FF")]
        scanner = DummyScanner(nodes)
        resolver = DummyResolver(
            mapping={"10.0.0.119": ("GoogleTV2625", HostnameSource.SSDP)},
            metadata={"10.0.0.119": {"manufacturer": "TCL", "model": "Smart TV"}},
        )
        manuf_repo = DummyManufacturerRepo()

        use_case = ScanNetworkUseCase(
            scanner=scanner,
            resolver=resolver,
            manufacturer_repo=manuf_repo,
            device_repo=self.repo,
        )
        devices = use_case.execute()
        self.assertEqual(len(devices), 1)
        self.assertEqual(devices[0].vendor, "TCL (Smart TV)")

    def test_scan_network_failure_handling(self):
        scanner = DummyScanner(raise_error=True)
        resolver = DummyResolver()
        manuf_repo = DummyManufacturerRepo()

        use_case = ScanNetworkUseCase(
            scanner=scanner,
            resolver=resolver,
            manufacturer_repo=manuf_repo,
            device_repo=self.repo,
        )
        with self.assertRaises(ScanExecutionException):
            use_case.execute()

        state = self.repo.get_scan_state()
        self.assertFalse(state.is_scanning)
        self.assertIn("Underlying socket error", state.error_message or "")

    def test_get_devices_numeric_sorting(self):
        self.repo.save_devices([
            Device(ip="10.0.0.100", mac="AA:AA:AA:AA:AA:01"),
            Device(ip="10.0.0.2", mac="AA:AA:AA:AA:AA:02"),
            Device(ip="10.0.0.20", mac="AA:AA:AA:AA:AA:03"),
        ])
        use_case = GetDevicesUseCase(device_repo=self.repo)
        sorted_devs, _ = use_case.execute()
        self.assertEqual(list(sorted_devs.keys()), ["10.0.0.2", "10.0.0.20", "10.0.0.100"])


class TestAdaptersLayer(unittest.TestCase):
    """3. Adapters Layer Tests: Implementations of port interfaces."""

    def test_manufacturer_repo_privacy_detection(self):
        repo = HybridManufacturerRepository()
        self.assertEqual(repo.get_manufacturer("ca:e4:3b:56:ce:62"), "Private/Randomized MAC")
        self.assertEqual(repo.get_manufacturer("5c:9b:a6:8b:9c:03"), "Apple")
        self.assertEqual(repo.get_manufacturer("cc:15:31:e5:bb:db"), "Intel (Windows PC)")

    def test_probe_a_apple_lockdown_detection(self):
        repo = HybridManufacturerRepository()
        repo.check_apple_lockdown = staticmethod(lambda ip, timeout=0.3: ip == "10.0.0.18")

        vendor = repo.get_manufacturer("82:11:02:26:fa:0f", ip="10.0.0.18")
        self.assertEqual(vendor, "Apple iOS Device (Private MAC)")

        vendor_other = repo.get_manufacturer("82:11:02:26:fa:0f", ip="10.0.0.99")
        self.assertEqual(vendor_other, "Private/Randomized MAC")

    def test_probe_b_upnp_metadata_registration(self):
        repo = HybridManufacturerRepository()
        repo.register_device_metadata("10.0.0.119", "TCL", "Smart TV")
        vendor = repo.get_manufacturer("AA:BB:CC:DD:EE:FF", ip="10.0.0.119")
        self.assertEqual(vendor, "TCL (Smart TV)")

    def test_composite_resolver_priority_cascade(self):
        mdns = DummyResolver({"10.0.0.1": ("mdns-name", HostnameSource.MDNS)})
        netbios = DummyResolver({
            "10.0.0.1": ("nbns-name", HostnameSource.NETBIOS),
            "10.0.0.2": ("nbns-name-2", HostnameSource.NETBIOS),
        })
        ssdp = DummyResolver({
            "10.0.0.2": ("ssdp-name", HostnameSource.SSDP),
            "10.0.0.3": ("ssdp-name-3", HostnameSource.SSDP),
        })
        dns = DummyResolver({"10.0.0.4": ("dns-name", HostnameSource.DNS)})
        http = DummyResolver({
            "10.0.0.4": ("http-ignored", HostnameSource.HTTP),
            "10.0.0.5": ("IP Camera Web Admin", HostnameSource.HTTP),
        })

        composite = CompositeHostnameResolver(
            mdns_resolver=mdns,
            netbios_resolver=netbios,
            ssdp_resolver=ssdp,
            dns_resolver=dns,
            http_resolver=http,
        )
        res = composite.resolve_batch(["10.0.0.1", "10.0.0.2", "10.0.0.3", "10.0.0.4", "10.0.0.5"])

        # 10.0.0.1: mDNS beats NetBIOS
        self.assertEqual(res["10.0.0.1"], ("mdns-name", HostnameSource.MDNS))
        # 10.0.0.2: NetBIOS beats SSDP
        self.assertEqual(res["10.0.0.2"], ("nbns-name-2", HostnameSource.NETBIOS))
        # 10.0.0.3: SSDP fallback
        self.assertEqual(res["10.0.0.3"], ("ssdp-name-3", HostnameSource.SSDP))
        # 10.0.0.4: DNS beats HTTP
        self.assertEqual(res["10.0.0.4"], ("dns-name", HostnameSource.DNS))
        # 10.0.0.5: HTTP fallback (Probe D)
        self.assertEqual(res["10.0.0.5"], ("IP Camera Web Admin", HostnameSource.HTTP))

    def test_probe_c_human_name_filtering(self):
        # Valid names pass
        self.assertTrue(SocketMDNSResolver._is_clean_human_name("Tom’s MBP"))
        self.assertTrue(SocketMDNSResolver._is_clean_human_name("Badunkadunk"))
        self.assertTrue(SocketMDNSResolver._is_clean_human_name("Kayla’s MacBook Pro"))
        # Raw UUIDs and device hashes are filtered
        self.assertFalse(SocketMDNSResolver._is_clean_human_name("e7ac5f06-e7ef-290a-b33b-36638a5c8af9"))
        self.assertFalse(SocketMDNSResolver._is_clean_human_name("V505M-K09-4d628ccfea58bdc57e374f16b1840b88"))

    def test_probe_d_http_banner_generic_filtering(self):
        resolver = SocketHTTPBannerResolver()
        self.assertIn("login", resolver.GENERIC_TITLES)
        self.assertIn("404 not found", resolver.GENERIC_TITLES)

    def test_in_memory_repository_thread_safety(self):
        repo = InMemoryDeviceRepository()

        def writer():
            for i in range(100):
                repo.save_devices([Device(ip=f"10.0.0.{i}", mac="AA:AA:AA:AA:AA:AA")])

        def reader():
            for _ in range(100):
                _ = repo.get_devices()

        threads = [threading.Thread(target=writer), threading.Thread(target=reader)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertIsInstance(repo.get_devices(), dict)

    def test_device_repository_merging_and_retention(self):
        repo = InMemoryDeviceRepository()

        # Pass 1: Phone is awake, identified as Badunkadunk
        dev1 = Device(
            ip="10.0.0.18",
            mac="82:11:02:26:FA:0F",
            hostname="Badunkadunk",
            source=HostnameSource.MDNS,
            vendor="Apple iOS Device (Private MAC)",
            last_seen="01:00:00",
        )
        repo.save_devices([dev1])
        self.assertEqual(repo.get_devices()["10.0.0.18"].hostname, "Badunkadunk")

        # Pass 2: Phone screen locked, returns Unknown hostname & Private MAC
        dev2 = Device(
            ip="10.0.0.18",
            mac="82:11:02:26:FA:0F",
            hostname="Unknown",
            source=HostnameSource.UNKNOWN,
            vendor="Private/Randomized MAC",
            last_seen="01:00:30",
        )
        repo.save_devices([dev2])

        # Roster MUST retain Badunkadunk and Apple iOS Device!
        retained = repo.get_devices()["10.0.0.18"]
        self.assertEqual(retained.hostname, "Badunkadunk")
        self.assertEqual(retained.vendor, "Apple iOS Device (Private MAC)")
        self.assertEqual(retained.last_seen, "01:00:30")

        # Pass 3: Phone Wi-Fi in DTIM sleep during 2-second sweep window (misses ARP)
        repo.save_devices([Device(ip="10.0.0.2", mac="AA:BB:CC:DD:EE:FF")])
        # Phone is NOT wiped out!
        self.assertIn("10.0.0.18", repo.get_devices())
        self.assertEqual(len(repo.get_devices()), 2)

        # Clear devices resets for subnet change
        repo.clear_devices()
        self.assertEqual(len(repo.get_devices()), 0)


class TestPresentationLayer(unittest.TestCase):
    """4. Presentation / Primary Driving Adapter Tests: Flask Web UI & REST API."""

    def setUp(self):
        self.repo = InMemoryDeviceRepository(initial_subnet="10.0.0.0/24")
        self.get_uc = GetDevicesUseCase(self.repo)
        self.up_uc = UpdateSubnetUseCase(self.repo)
        self.scan_trigger = threading.Event()
        self.app = create_web_app(
            get_devices_use_case=self.get_uc,
            update_subnet_use_case=self.up_uc,
            scan_trigger=self.scan_trigger,
        )
        self.client = self.app.test_client()

    def test_api_devices_endpoint(self):
        self.repo.save_devices([
            Device(
                ip="10.0.0.18",
                mac="82:11:02:26:FA:0F",
                hostname="iPhone-7544",
                vendor="Apple iOS Device (Private MAC)",
            )
        ])
        resp = self.client.get("/api/devices")
        self.assertEqual(resp.status_code, 200)
        json_data = resp.get_json()
        self.assertIn("10.0.0.18", json_data["devices"])
        self.assertEqual(json_data["devices"]["10.0.0.18"]["hostname"], "iPhone-7544")
        self.assertEqual(json_data["state"]["subnet"], "10.0.0.0/24")

    def test_api_set_subnet_valid(self):
        resp = self.client.post("/api/set-subnet", json={"subnet": "10.0.0.0/25"})
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(self.scan_trigger.is_set())
        self.assertEqual(self.repo.get_scan_state().subnet, "10.0.0.0/25")

    def test_api_set_subnet_invalid(self):
        resp = self.client.post("/api/set-subnet", json={"subnet": "invalid-cidr"})
        self.assertEqual(resp.status_code, 400)
        self.assertIn("error", resp.get_json())

    def test_index_dashboard_renders_html(self):
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"LANRoster", resp.data)


if __name__ == "__main__":
    unittest.main()
