import io
import threading
import unittest
from typing import Dict, List, Tuple
from unittest.mock import MagicMock, patch

from lan_roster.domain.models import Device, DeviceCategory, HostnameSource, ScanState
from lan_roster.domain.classifier import DeviceClassifier
from lan_roster.domain.exceptions import (
    LANRosterException,
    InvalidSubnetException,
    ScanExecutionException,
)
from lan_roster.ports.scanner import NetworkScannerPort
from lan_roster.ports.resolver import HostnameResolverPort
from lan_roster.ports.manufacturer import ManufacturerRepositoryPort
from lan_roster.adapters.repository.memory import InMemoryDeviceRepository
from lan_roster.adapters.repository.sqlite import SqliteDeviceRepository
from lan_roster.adapters.manufacturer.hybrid_repo import HybridManufacturerRepository
from lan_roster.adapters.resolvers.composite import CompositeHostnameResolver
from lan_roster.adapters.resolvers.mdns import SocketMDNSResolver
from lan_roster.adapters.resolvers.netbios import SocketNetBIOSResolver
from lan_roster.adapters.resolvers.ssdp import SocketSSDPResolver
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
            category=DeviceCategory.MOBILE,
        )
        data = dev.to_dict()
        self.assertEqual(data["ip"], "10.0.0.18")
        self.assertEqual(data["mac"], "82:11:02:26:FA:0F")
        self.assertEqual(data["hostname"], "iPhone-7544")
        self.assertEqual(data["source"], "DNS")
        self.assertEqual(data["vendor"], "Apple iOS Device (Private MAC)")
        self.assertEqual(data["category"], "Mobile")
        self.assertEqual(data["category_icon"], "📱")
        self.assertTrue(data["is_online"])
        self.assertFalse(data["is_new"])

    def test_device_classifier_all_categories(self):
        # 1. Network
        cat = DeviceClassifier.classify(ip="10.0.0.1", vendor="ARRIS Group, Inc.")
        self.assertEqual(cat, DeviceCategory.NETWORK)
        self.assertEqual(cat.icon, "🌐")

        # 2. Mobile
        cat = DeviceClassifier.classify(ip="10.0.0.18", hostname="Badunkadunk", vendor="Apple, Inc. (iOS)")
        self.assertEqual(cat, DeviceCategory.MOBILE)
        self.assertEqual(cat.icon, "📱")

        # 3. Computer
        cat = DeviceClassifier.classify(ip="10.0.0.139", hostname="PAPPA-CPPC", source=HostnameSource.NETBIOS)
        self.assertEqual(cat, DeviceCategory.COMPUTER)
        cat_mac = DeviceClassifier.classify(ip="10.0.0.28", hostname="Tom's MacBook Pro", vendor="Apple, Inc.")
        self.assertEqual(cat_mac, DeviceCategory.COMPUTER)
        self.assertEqual(cat.icon, "💻")

        # 4. Smart TV
        cat = DeviceClassifier.classify(ip="10.0.0.45", hostname="Living-Room-Apple-TV", vendor="Apple, Inc.")
        self.assertEqual(cat, DeviceCategory.SMART_TV)
        cat_cast = DeviceClassifier.classify(ip="10.0.0.46", hostname="Chromecast", vendor="Google Cast")
        self.assertEqual(cat_cast, DeviceCategory.SMART_TV)
        self.assertEqual(cat.icon, "📺")

        # 5. Smart Home / Audio
        cat = DeviceClassifier.classify(ip="10.0.0.70", hostname="Sonos-Beam", vendor="Sonos, Inc.")
        self.assertEqual(cat, DeviceCategory.SMART_HOME)
        cat_iot = DeviceClassifier.classify(ip="10.0.0.71", hostname="Smart-Plug", vendor="Espressif Inc.")
        self.assertEqual(cat_iot, DeviceCategory.SMART_HOME)
        self.assertEqual(cat.icon, "🔊")

        # 6. Printer
        cat = DeviceClassifier.classify(ip="10.0.0.60", hostname="HP-LaserJet-Pro", vendor="HP Inc.")
        self.assertEqual(cat, DeviceCategory.PRINTER)
        cat_epson = DeviceClassifier.classify(ip="10.0.0.61", vendor="Brother Industries")
        self.assertEqual(cat_epson, DeviceCategory.PRINTER)
        self.assertEqual(cat.icon, "🖨️")

        # 7. Gaming
        cat = DeviceClassifier.classify(ip="10.0.0.80", hostname="PlayStation-5", vendor="Sony Interactive")
        self.assertEqual(cat, DeviceCategory.GAMING)
        self.assertEqual(cat.icon, "🎮")

        # 8. Generic / Unknown
        cat = DeviceClassifier.classify(ip="10.0.0.99", hostname="Unknown", vendor="Generic Device")
        self.assertEqual(cat, DeviceCategory.GENERIC)
        self.assertEqual(cat.icon, "📟")

    def test_scan_state_to_dict(self):
        state = ScanState(
            subnet="10.0.0.0/24",
            is_scanning=True,
            total_found=5,
            online_count=4,
            offline_count=1,
        )
        data = state.to_dict()
        self.assertEqual(data["subnet"], "10.0.0.0/24")
        self.assertTrue(data["scanning"])
        self.assertEqual(data["total_found"], 5)
        self.assertEqual(data["online_count"], 4)
        self.assertEqual(data["offline_count"], 1)

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
        self.assertEqual(win_dev.category, DeviceCategory.COMPUTER)

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
        self.assertEqual(devices[0].category, DeviceCategory.SMART_TV)

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

    def test_update_subnet_clears_devices_only_when_changed(self):
        use_case = UpdateSubnetUseCase(device_repo=self.repo)
        self.repo.save_devices([Device(ip="10.0.0.18", mac="AA:BB:CC:DD:EE:01", hostname="iPhone")])
        self.assertEqual(len(self.repo.get_devices()), 1)

        # 1. Update with the SAME subnet (or equivalent IP normalizing to 10.0.0.0/24)
        use_case.execute("10.0.0.1")
        self.assertEqual(len(self.repo.get_devices()), 1, "Same subnet must retain devices")

        # 2. Update with a DIFFERENT subnet (e.g. 192.168.1.0/24)
        use_case.execute("192.168.1.0/24")
        self.assertEqual(len(self.repo.get_devices()), 0, "Changing subnet must clear old subnet devices")
        self.assertEqual(self.repo.get_scan_state().subnet, "192.168.1.0/24")

    def test_get_devices_empty_and_state(self):
        use_case = GetDevicesUseCase(device_repo=self.repo)
        devs, state = use_case.execute()
        self.assertEqual(devs, {})
        self.assertEqual(state.subnet, "10.0.0.0/24")
        self.assertFalse(state.is_scanning)

    def test_scan_network_full_network_spectrum(self):
        nodes = [
            ("10.0.0.1", "00:1D:D5:11:22:33"),    # Gateway router
            ("10.0.0.18", "82:11:02:26:FA:0F"),   # iPhone (Apple Lockdown + mDNS)
            ("10.0.0.139", "CC:15:31:E5:BB:DB"),  # Windows PC (NetBIOS)
            ("10.0.0.119", "AA:BB:CC:DD:EE:FF"),  # Smart TV (UPnP/Cast)
            ("10.0.0.60", "00:1E:68:01:02:03"),   # Printer (HTTP banner)
            ("10.0.0.95", "00:50:56:00:11:22"),   # Generic node
        ]
        scanner = DummyScanner(nodes)
        resolver = DummyResolver(
            mapping={
                "10.0.0.1": ("gateway", HostnameSource.DNS),
                "10.0.0.18": ("Badunkadunk", HostnameSource.MDNS),
                "10.0.0.139": ("PAPPA-CPPC", HostnameSource.NETBIOS),
                "10.0.0.119": ("Living-Room-TV", HostnameSource.SSDP),
                "10.0.0.60": ("HP-LaserJet-Pro", HostnameSource.HTTP),
            },
            metadata={
                "10.0.0.119": {"manufacturer": "TCL", "model": "Roku TV"},
            },
        )
        manuf_repo = DummyManufacturerRepo()
        # Mock Arris router and Apple iOS probe
        manuf_repo.get_manufacturer = lambda mac_address, ip=None: (
            "ARRIS Group, Inc." if ip == "10.0.0.1"
            else "Apple, Inc. (iOS)" if ip == "10.0.0.18"
            else "Intel (Windows PC)" if ip == "10.0.0.139"
            else "TCL (Roku TV)" if ip == "10.0.0.119"
            else "HP Inc." if ip == "10.0.0.60"
            else "Generic Device"
        )

        use_case = ScanNetworkUseCase(
            scanner=scanner,
            resolver=resolver,
            manufacturer_repo=manuf_repo,
            device_repo=self.repo,
        )
        devices = use_case.execute()
        self.assertEqual(len(devices), 6)

        by_ip = {d.ip: d for d in devices}
        self.assertEqual(by_ip["10.0.0.1"].category, DeviceCategory.NETWORK)
        self.assertEqual(by_ip["10.0.0.18"].category, DeviceCategory.MOBILE)
        self.assertEqual(by_ip["10.0.0.139"].category, DeviceCategory.COMPUTER)
        self.assertEqual(by_ip["10.0.0.119"].category, DeviceCategory.SMART_TV)
        self.assertEqual(by_ip["10.0.0.60"].category, DeviceCategory.PRINTER)
        self.assertEqual(by_ip["10.0.0.95"].category, DeviceCategory.GENERIC)

        # Ensure total_found in scan state reflects active registry
        state = self.repo.get_scan_state()
        self.assertEqual(state.total_found, 6)
        self.assertFalse(state.is_scanning)

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

    @patch("shutil.which")
    @patch("subprocess.check_output")
    def test_netbios_smbutil_output_parsing(self, mock_check_output, mock_which):
        mock_which.side_effect = lambda cmd: "/usr/bin/smbutil" if cmd == "smbutil" else None
        mock_check_output.return_value = (
            b"Using IP address of 10.0.0.139: 10.0.0.139\n"
            b"NetBIOS Name                     Number  Type    Description\n"
            b"PAPPA-CPPC                       0x00    UNIQUE  [Workstation Service]\n"
            b"PAPPA-CPPC                       0x20    UNIQUE  [File/Print Server Service]\n"
            b"WORKGROUP                        0x00    GROUP   [Domain Name]\n"
        )
        resolver = SocketNetBIOSResolver(timeout=0.5)
        name = resolver._query_ip("10.0.0.139")
        self.assertEqual(name, "PAPPA-CPPC")

    @patch("shutil.which")
    @patch("subprocess.check_output")
    def test_netbios_nbtstat_output_parsing(self, mock_check_output, mock_which):
        mock_which.side_effect = lambda cmd: "C:\\Windows\\System32\\nbtstat.exe" if cmd == "nbtstat" else None
        mock_check_output.return_value = (
            b"       NetBIOS Remote Machine Name Table\n\n"
            b"   Name               Type         Status\n"
            b"---------------------------------------------\n"
            b"PAPPA-CPPC     <00>  UNIQUE      Registered\n"
            b"WORKGROUP      <00>  GROUP       Registered\n"
            b"PAPPA-CPPC     <20>  UNIQUE      Registered\n"
        )
        resolver = SocketNetBIOSResolver(timeout=0.5)
        name = resolver._query_ip("10.0.0.139")
        self.assertEqual(name, "PAPPA-CPPC")

    @patch("shutil.which")
    @patch("subprocess.check_output")
    def test_netbios_nmblookup_output_parsing(self, mock_check_output, mock_which):
        mock_which.side_effect = lambda cmd: "/usr/bin/nmblookup" if cmd == "nmblookup" else None
        mock_check_output.return_value = (
            b"Looking up status of 10.0.0.139\n"
            b"\tPAPPA-CPPC      <00> -         B <ACTIVE> \n"
            b"\tWORKGROUP       <00> - <GROUP> B <ACTIVE> \n"
        )
        resolver = SocketNetBIOSResolver(timeout=0.5)
        name = resolver._query_ip("10.0.0.139")
        self.assertEqual(name, "PAPPA-CPPC")

    @patch("urllib.request.urlopen")
    def test_ssdp_xml_descriptor_parsing(self, mock_urlopen):
        xml_content = (
            b"<?xml version='1.0'?>\n"
            b"<root xmlns='urn:schemas-upnp-org:device-1-0'>\n"
            b"  <device>\n"
            b"    <friendlyName>Living Room TV</friendlyName>\n"
            b"    <manufacturer>LG Electronics</manufacturer>\n"
            b"    <modelName>OLED55C1PUB</modelName>\n"
            b"  </device>\n"
            b"</root>"
        )
        mock_resp = MagicMock()
        mock_resp.read.return_value = xml_content
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        resolver = SocketSSDPResolver()
        name, manuf, model = resolver._fetch_xml_descriptor("10.0.0.50", "http://10.0.0.50:8088/desc.xml")
        self.assertEqual(name, "Living Room TV")
        self.assertEqual(manuf, "LG Electronics")
        self.assertEqual(model, "OLED55C1PUB")

    @patch("urllib.request.urlopen")
    def test_ssdp_google_cast_parsing(self, mock_urlopen):
        cast_json = b'{"name": "Den Chromecast", "build_version": "1.56"}'
        mock_resp = MagicMock()
        mock_resp.read.return_value = cast_json
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        resolver = SocketSSDPResolver()
        name, manuf, model = resolver._fetch_cast_info("10.0.0.55")
        self.assertEqual(name, "Den Chromecast")
        self.assertEqual(manuf, "Google")
        self.assertEqual(model, "Chromecast / Google TV")

    @patch("urllib.request.urlopen")
    def test_http_banner_title_extraction(self, mock_urlopen):
        html_content = b"<html><head><title>Brother HL-L2350DW series</title></head><body>OK</body></html>"
        mock_resp = MagicMock()
        mock_resp.headers = {"Server": "Brother-Embedded-Server"}
        mock_resp.read.return_value = html_content
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        resolver = SocketHTTPBannerResolver()
        ip, title, server = resolver._probe_single_ip("10.0.0.60")
        self.assertEqual(ip, "10.0.0.60")
        self.assertEqual(title, "Brother HL-L2350DW series")
        self.assertEqual(server, "Brother-Embedded-Server")

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
            category=DeviceCategory.MOBILE,
        )
        repo.save_devices([dev1])
        self.assertEqual(repo.get_devices()["10.0.0.18"].hostname, "Badunkadunk")
        self.assertEqual(repo.get_devices()["10.0.0.18"].category, DeviceCategory.MOBILE)

        # Pass 2: Phone screen locked, returns Unknown hostname & Private MAC & Generic
        dev2 = Device(
            ip="10.0.0.18",
            mac="82:11:02:26:FA:0F",
            hostname="Unknown",
            source=HostnameSource.UNKNOWN,
            vendor="Private/Randomized MAC",
            last_seen="01:00:30",
            category=DeviceCategory.GENERIC,
        )
        repo.save_devices([dev2])

        # Roster MUST retain Badunkadunk, Apple iOS Device, and Mobile category!
        retained = repo.get_devices()["10.0.0.18"]
        self.assertEqual(retained.hostname, "Badunkadunk")
        self.assertEqual(retained.vendor, "Apple iOS Device (Private MAC)")
        self.assertEqual(retained.category, DeviceCategory.MOBILE)
        self.assertEqual(retained.last_seen, "01:00:30")

        # Pass 3: Phone Wi-Fi in DTIM sleep during 2-second sweep window (misses ARP)
        repo.save_devices([Device(ip="10.0.0.2", mac="AA:BB:CC:DD:EE:FF")])
        # Phone is NOT wiped out!
        self.assertIn("10.0.0.18", repo.get_devices())
        self.assertEqual(len(repo.get_devices()), 2)
        # Verify presence state transition (Feature 2)
        self.assertFalse(repo.get_devices()["10.0.0.18"].is_online, "Phone missing ARP sweep should be marked offline/asleep")
        self.assertTrue(repo.get_devices()["10.0.0.2"].is_online, "Active device must be online")
        self.assertTrue(repo.get_devices()["10.0.0.2"].is_new, "Brand new device must have is_new=True")

        # Clear devices resets for subnet change
        repo.clear_devices()
        self.assertEqual(len(repo.get_devices()), 0)

    def test_sqlite_repository_initialization_and_schema(self):
        repo = SqliteDeviceRepository(db_path=":memory:", initial_subnet="10.0.0.0/24")
        state = repo.get_scan_state()
        self.assertEqual(state.subnet, "10.0.0.0/24")
        self.assertFalse(state.is_scanning)
        self.assertEqual(len(repo.get_devices()), 0)
        repo.close()

    def test_sqlite_repository_merging_retention_and_presence(self):
        repo = SqliteDeviceRepository(db_path=":memory:", initial_subnet="10.0.0.0/24")

        # Pass 1: Phone is awake, identified as Badunkadunk
        dev1 = Device(
            ip="10.0.0.18",
            mac="82:11:02:26:FA:0F",
            hostname="Badunkadunk",
            source=HostnameSource.MDNS,
            vendor="Apple iOS Device (Private MAC)",
            last_seen="01:00:00",
            category=DeviceCategory.MOBILE,
        )
        repo.save_devices([dev1])
        devs1 = repo.get_devices()
        self.assertEqual(devs1["10.0.0.18"].hostname, "Badunkadunk")
        self.assertEqual(devs1["10.0.0.18"].category, DeviceCategory.MOBILE)
        self.assertTrue(devs1["10.0.0.18"].is_online)
        self.assertTrue(devs1["10.0.0.18"].is_new)

        # Pass 2: Phone screen locked, returns Unknown hostname
        dev2 = Device(
            ip="10.0.0.18",
            mac="82:11:02:26:FA:0F",
            hostname="Unknown",
            source=HostnameSource.UNKNOWN,
            vendor="Private/Randomized MAC",
            last_seen="01:00:30",
            category=DeviceCategory.GENERIC,
        )
        repo.save_devices([dev2])
        devs2 = repo.get_devices()
        self.assertEqual(devs2["10.0.0.18"].hostname, "Badunkadunk")
        self.assertEqual(devs2["10.0.0.18"].vendor, "Apple iOS Device (Private MAC)")
        self.assertEqual(devs2["10.0.0.18"].category, DeviceCategory.MOBILE)
        self.assertEqual(devs2["10.0.0.18"].last_seen, "01:00:30")
        self.assertTrue(devs2["10.0.0.18"].is_online)

        # Pass 3: Phone misses sweep; another device active
        repo.save_devices([Device(ip="10.0.0.139", mac="CC:15:31:E5:BB:DB", hostname="PAPPA-CPPC")])
        devs3 = repo.get_devices()
        self.assertEqual(len(devs3), 2)
        self.assertFalse(devs3["10.0.0.18"].is_online, "Sleeping device must transition to is_online=False")
        self.assertEqual(devs3["10.0.0.18"].hostname, "Badunkadunk")
        self.assertTrue(devs3["10.0.0.139"].is_online)

        # Test state updates
        updated_state = repo.update_scan_state(
            total_found=2,
            online_count=1,
            offline_count=1,
            last_scan_time="01:01:00",
        )
        self.assertEqual(updated_state.total_found, 2)
        self.assertEqual(updated_state.online_count, 1)
        self.assertEqual(updated_state.offline_count, 1)

        # Test clear
        repo.clear_devices()
        self.assertEqual(len(repo.get_devices()), 0)
        repo.close()

    def test_sqlite_repository_persistence_across_instances(self):
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".db") as tmp:
            db_file = tmp.name

            # Instance 1: Write device
            repo1 = SqliteDeviceRepository(db_path=db_file, initial_subnet="10.0.0.0/24")
            repo1.save_devices([
                Device(
                    ip="10.0.0.18",
                    mac="82:11:02:26:FA:0F",
                    hostname="Badunkadunk",
                    source=HostnameSource.MDNS,
                    vendor="Apple, Inc. (iOS)",
                    category=DeviceCategory.MOBILE,
                    last_seen="12:00:00",
                    first_seen="11:50:00",
                )
            ])
            repo1.update_scan_state(total_found=1, online_count=1, offline_count=0, last_scan_time="12:00:00")
            repo1.close()

            # Instance 2: Open same DB file (simulating app restart)
            repo2 = SqliteDeviceRepository(db_path=db_file, initial_subnet="10.0.0.0/24")
            devs = repo2.get_devices()
            self.assertEqual(len(devs), 1)
            self.assertIn("10.0.0.18", devs)
            self.assertEqual(devs["10.0.0.18"].hostname, "Badunkadunk")
            self.assertEqual(devs["10.0.0.18"].vendor, "Apple, Inc. (iOS)")
            self.assertEqual(devs["10.0.0.18"].category, DeviceCategory.MOBILE)
            self.assertEqual(devs["10.0.0.18"].first_seen, "11:50:00")
            self.assertEqual(devs["10.0.0.18"].last_seen, "12:00:00")

            state = repo2.get_scan_state()
            self.assertEqual(state.total_found, 1)
            self.assertEqual(state.online_count, 1)
            self.assertEqual(state.last_scan_time, "12:00:00")
            repo2.close()

    def test_sqlite_repository_thread_safety(self):
        repo = SqliteDeviceRepository(db_path=":memory:", initial_subnet="10.0.0.0/24")

        def writer():
            for i in range(50):
                repo.save_devices([Device(ip=f"10.0.0.{i}", mac="AA:AA:AA:AA:AA:AA")])

        def reader():
            for _ in range(50):
                _ = repo.get_devices()

        threads = [threading.Thread(target=writer), threading.Thread(target=reader)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertIsInstance(repo.get_devices(), dict)
        repo.close()


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
        self.assertIn("category", json_data["devices"]["10.0.0.18"])
        self.assertIn("category_icon", json_data["devices"]["10.0.0.18"])
        self.assertIn("is_online", json_data["devices"]["10.0.0.18"])
        self.assertIn("is_new", json_data["devices"]["10.0.0.18"])
        self.assertEqual(json_data["state"]["subnet"], "10.0.0.0/24")
        self.assertIn("online_count", json_data["state"])
        self.assertIn("offline_count", json_data["state"])

    def test_api_set_subnet_valid(self):
        resp = self.client.post("/api/set-subnet", json={"subnet": "10.0.0.0/25"})
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(self.scan_trigger.is_set())
        self.assertEqual(self.repo.get_scan_state().subnet, "10.0.0.0/25")

    def test_api_set_subnet_invalid(self):
        resp = self.client.post("/api/set-subnet", json={"subnet": "invalid-cidr"})
        self.assertEqual(resp.status_code, 400)
        self.assertIn("error", resp.get_json())

    def test_index_dashboard_renders_html_with_categories_and_chips(self):
        self.repo.save_devices([
            Device(
                ip="10.0.0.18",
                mac="82:11:02:26:FA:0F",
                hostname="Badunkadunk",
                source=HostnameSource.MDNS,
                vendor="Apple iOS Device (Private MAC)",
                category=DeviceCategory.MOBILE,
                last_seen="12:00:00",
            ),
            Device(
                ip="10.0.0.139",
                mac="CC:15:31:E5:BB:DB",
                hostname="PAPPA-CPPC",
                source=HostnameSource.NETBIOS,
                vendor="Intel (Windows PC)",
                category=DeviceCategory.COMPUTER,
                last_seen="12:00:05",
            ),
        ])
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        html = resp.data.decode("utf-8")
        self.assertIn("LANRoster", html)
        self.assertIn("Badunkadunk", html)
        self.assertIn("PAPPA-CPPC", html)
        self.assertIn("cat-mobile", html)
        self.assertIn("cat-computer", html)
        self.assertIn("📱", html)
        self.assertIn("💻", html)
        self.assertIn("badge-mdns", html)
        self.assertIn("badge-netbios", html)
        self.assertIn("summary-chip", html)
        self.assertIn("status-indicator-dot online", html)
        self.assertIn("✨ New", html)


class TestEndToEndWorkflow(unittest.TestCase):
    """5. End-to-End Tests: Complete multi-pass lifecycles and subnet transitions."""

    def test_full_application_lifecycle_and_roster_retention(self):
        repo = InMemoryDeviceRepository(initial_subnet="10.0.0.0/24")
        scan_trigger = threading.Event()
        update_subnet_uc = UpdateSubnetUseCase(device_repo=repo)
        get_devices_uc = GetDevicesUseCase(device_repo=repo)

        # -------------------------------------------------------------
        # Phase 1: Initial Sweep on 10.0.0.0/24
        # -------------------------------------------------------------
        nodes_pass1 = [
            ("10.0.0.1", "00:1D:D5:AA:BB:01"),   # Gateway router
            ("10.0.0.18", "82:11:02:26:FA:0F"),  # iPhone awake
            ("10.0.0.139", "CC:15:31:E5:BB:DB"), # Windows PC
        ]
        scanner = DummyScanner(nodes_pass1)
        resolver = DummyResolver({
            "10.0.0.1": ("gateway", HostnameSource.DNS),
            "10.0.0.18": ("Badunkadunk", HostnameSource.MDNS),
            "10.0.0.139": ("PAPPA-CPPC", HostnameSource.NETBIOS),
        })
        manuf_repo = DummyManufacturerRepo()
        manuf_repo.get_manufacturer = lambda mac_address, ip=None: (
            "ARRIS Group, Inc." if ip == "10.0.0.1"
            else "Apple, Inc. (iOS)" if ip == "10.0.0.18"
            else "Intel (Windows PC)" if ip == "10.0.0.139"
            else "Generic Device"
        )

        scan_uc = ScanNetworkUseCase(
            scanner=scanner,
            resolver=resolver,
            manufacturer_repo=manuf_repo,
            device_repo=repo,
        )

        # Execute sweep
        scan_uc.execute()

        # Verify via GetDevicesUseCase
        devs, state = get_devices_uc.execute()
        self.assertEqual(len(devs), 3)
        self.assertEqual(list(devs.keys()), ["10.0.0.1", "10.0.0.18", "10.0.0.139"])
        self.assertEqual(devs["10.0.0.1"].category, DeviceCategory.NETWORK)
        self.assertEqual(devs["10.0.0.18"].category, DeviceCategory.MOBILE)
        self.assertEqual(devs["10.0.0.139"].category, DeviceCategory.COMPUTER)
        self.assertEqual(state.total_found, 3)

        # Verify via Flask REST API
        app = create_web_app(get_devices_uc, update_subnet_uc, scan_trigger)
        client = app.test_client()
        api_resp = client.get("/api/devices")
        self.assertEqual(api_resp.status_code, 200)
        api_data = api_resp.get_json()
        self.assertEqual(len(api_data["devices"]), 3)
        self.assertEqual(api_data["devices"]["10.0.0.18"]["hostname"], "Badunkadunk")
        self.assertEqual(api_data["devices"]["10.0.0.18"]["category_icon"], "📱")

        # -------------------------------------------------------------
        # Phase 2: Second Sweep — Sleeping devices & Screen lock
        # iPhone: Screen locked (mDNS returns Unknown, vendor returns Private/Randomized)
        # Windows PC: Asleep (drops off ARP sweep entirely)
        # -------------------------------------------------------------
        nodes_pass2 = [
            ("10.0.0.1", "00:1D:D5:AA:BB:01"),
            ("10.0.0.18", "82:11:02:26:FA:0F"), # Only router and phone answer ARP
        ]
        scanner.nodes = nodes_pass2
        resolver.mapping = {
            "10.0.0.1": ("gateway", HostnameSource.DNS),
            # iPhone has locked screen: mDNS probe returns Unknown
            "10.0.0.18": ("Unknown", HostnameSource.UNKNOWN),
        }
        manuf_repo.get_manufacturer = lambda mac_address, ip=None: (
            "ARRIS Group, Inc." if ip == "10.0.0.1"
            else "Private/Randomized MAC" if ip == "10.0.0.18"
            else "Generic Device"
        )

        scan_uc.execute()

        # Verify Sticky Retention across sweeps
        devs_pass2, state_pass2 = get_devices_uc.execute()
        # All 3 devices are retained!
        self.assertEqual(len(devs_pass2), 3)
        # iPhone retained its human name and Mobile category!
        self.assertEqual(devs_pass2["10.0.0.18"].hostname, "Badunkadunk")
        self.assertEqual(devs_pass2["10.0.0.18"].vendor, "Apple, Inc. (iOS)")
        self.assertEqual(devs_pass2["10.0.0.18"].category, DeviceCategory.MOBILE)
        # Windows PC was retained even though it missed the ARP pass!
        self.assertEqual(devs_pass2["10.0.0.139"].hostname, "PAPPA-CPPC")
        self.assertEqual(devs_pass2["10.0.0.139"].category, DeviceCategory.COMPUTER)

        # Verify Presence Tracking (Feature 2)
        self.assertTrue(devs_pass2["10.0.0.1"].is_online, "Router must be online")
        self.assertTrue(devs_pass2["10.0.0.18"].is_online, "Phone answering ARP must be online")
        self.assertFalse(devs_pass2["10.0.0.139"].is_online, "Sleeping PC missing ARP must be offline/asleep")
        self.assertEqual(state_pass2.online_count, 2)
        self.assertEqual(state_pass2.offline_count, 1)

        # -------------------------------------------------------------
        # Phase 3: Subnet Transition to 192.168.1.0/24
        # -------------------------------------------------------------
        update_subnet_uc.execute("192.168.1.0/24")

        # Old subnet devices must be cleared
        devs_cleared, state_cleared = get_devices_uc.execute()
        self.assertEqual(len(devs_cleared), 0)
        self.assertEqual(state_cleared.subnet, "192.168.1.0/24")

        # Sweep on new subnet
        scanner.nodes = [("192.168.1.1", "E4:F0:42:01:02:03")]
        resolver.mapping = {"192.168.1.1": ("netgear-router", HostnameSource.DNS)}
        manuf_repo.get_manufacturer = lambda mac_address, ip=None: "Netgear Inc."

        scan_uc.execute()

        devs_new, state_new = get_devices_uc.execute()
        self.assertEqual(len(devs_new), 1)
        self.assertEqual(devs_new["192.168.1.1"].category, DeviceCategory.NETWORK)
        self.assertEqual(state_new.total_found, 1)


if __name__ == "__main__":
    unittest.main()
