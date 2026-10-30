import threading
from lan_roster.adapters.scanner.scapy_arp import ScapyArpScanner
from lan_roster.adapters.resolvers.composite import CompositeHostnameResolver
from lan_roster.adapters.resolvers.mdns import SocketMDNSResolver
from lan_roster.adapters.resolvers.netbios import SocketNetBIOSResolver
from lan_roster.adapters.resolvers.ssdp import SocketSSDPResolver
from lan_roster.adapters.resolvers.dns import SocketDNSResolver
from lan_roster.adapters.resolvers.http_banner import SocketHTTPBannerResolver
from lan_roster.adapters.manufacturer.hybrid_repo import HybridManufacturerRepository
from lan_roster.adapters.repository.sqlite import SqliteDeviceRepository
from lan_roster.adapters.network.system_config import SystemNetworkConfigAdapter
from lan_roster.use_cases.scan_network import ScanNetworkUseCase
from lan_roster.use_cases.get_devices import GetDevicesUseCase
from lan_roster.use_cases.update_subnet import UpdateSubnetUseCase
from lan_roster.ui.web import create_web_app


def bootstrap():
    """
    Composition Root: Instantiates adapters, wires up ports to use cases,
    and initializes the background worker and presentation layer.
    """
    # 1. Secondary / Outbound Adapters
    network_config = SystemNetworkConfigAdapter()
    default_subnet = network_config.detect_default_subnet()
    default_gateway = network_config.detect_default_gateway()

    device_repository = SqliteDeviceRepository(initial_subnet=default_subnet)
    manufacturer_repository = HybridManufacturerRepository()
    network_scanner = ScapyArpScanner(timeout=2)

    composite_resolver = CompositeHostnameResolver(
        mdns_resolver=SocketMDNSResolver(timeout=1.5),
        netbios_resolver=SocketNetBIOSResolver(timeout=0.4, max_workers=20),
        ssdp_resolver=SocketSSDPResolver(timeout=0.8),
        dns_resolver=SocketDNSResolver(gateway_ip=default_gateway),
        http_resolver=SocketHTTPBannerResolver(timeout=0.5),
    )

    # 2. Use Cases (Application Services)
    scan_network_use_case = ScanNetworkUseCase(
        scanner=network_scanner,
        resolver=composite_resolver,
        manufacturer_repo=manufacturer_repository,
        device_repo=device_repository,
    )
    get_devices_use_case = GetDevicesUseCase(device_repo=device_repository)
    update_subnet_use_case = UpdateSubnetUseCase(device_repo=device_repository)

    # 3. Scanner synchronization trigger
    scan_trigger = threading.Event()

    def scan_worker():
        """Periodic background sweep daemon."""
        while True:
            try:
                scan_network_use_case.execute()
            except Exception as e:
                print(f"[!] Background sweep error: {e}")

            # Sleep 30s or wake immediately upon user trigger
            scan_trigger.wait(timeout=30)
            scan_trigger.clear()

    worker_thread = threading.Thread(target=scan_worker, daemon=True)
    worker_thread.start()

    # 4. Primary / Inbound Adapter (Flask Web UI)
    flask_app = create_web_app(
        get_devices_use_case=get_devices_use_case,
        update_subnet_use_case=update_subnet_use_case,
        scan_trigger=scan_trigger,
    )

    return flask_app
