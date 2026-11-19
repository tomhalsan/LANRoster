# LANRoster Architecture

This document describes the architectural principles, layer boundaries, dependency rules, and design patterns governing **LANRoster**.

---

## 1. Architectural Philosophy

LANRoster is structured around the principles of **Clean Architecture** (Robert C. Martin / Uncle Bob), also known as **Hexagonal Architecture** / **Ports and Adapters** (Alistair Cockburn) and **Onion Architecture** (Jeffrey Palermo).

### Core Goals

1. **Framework Independence**: The application business rules do not depend on external frameworks like Flask, Scapy, or operating system shells. Frameworks serve strictly as outer delivery mechanisms and replaceable plugins.
2. **UI Independence**: The core network scanning and device roster logic can be operated via web UI, REST API, CLI, or automated batch jobs without altering use cases.
3. **Database / Persistence Independence**: Devices and scanner state are decoupled through repository interfaces. The storage mechanism can transition from in-memory caches to SQLite, PostgreSQL, or Redis without business logic changes.
4. **Hardware & Network Independence**: Layer 2 ARP sweeps and multi-protocol name resolution are isolated behind contract ports. They can be substituted with simulated fixtures, alternative scanning engines (such as `arp-scan` or Nmap), or mocks during unit testing.
5. **Testability Without Privileges**: Enterprise rules and use case workflows can be validated in milliseconds without requiring root (`sudo`) permissions, active network interfaces, or live hardware.

---

## 2. The Dependency Rule

```mermaid
flowchart TD
    subgraph Presentation["Frameworks & Drivers / Presentation"]
        UI["Flask Web UI (lan_roster.ui)"]
        ScapyDriver["Scapy ARP Driver"]
        Sockets["Raw UDP/TCP Sockets (mDNS, NetBIOS, SSDP, DNS)"]
        SysCommands["OS route / ifconfig"]
    end

    subgraph Adapters["Interface Adapters (lan_roster.adapters)"]
        ScannerAdapter["ScapyArpScanner"]
        ResolverAdapters["CompositeHostnameResolver & Socket Resolvers"]
        ManufAdapter["HybridManufacturerRepository"]
        RepoAdapter["SqliteDeviceRepository (active) / InMemoryDeviceRepository"]
        AliasRepoAdapter["SqliteAliasRepository (active) / InMemoryAliasRepository"]
        ServiceScannerAdapter["SocketServiceScanner"]
        NetConfigAdapter["SystemNetworkConfigAdapter"]
    end

    subgraph UseCases["Application Business Rules (lan_roster.use_cases)"]
        ScanUC["ScanNetworkUseCase"]
        GetUC["GetDevicesUseCase"]
        UpdateUC["UpdateSubnetUseCase"]
        ScanPortsUC["ScanDevicePortsUseCase"]
        UpdateAliasUC["UpdateDeviceAliasUseCase"]
    end

    subgraph Ports["Ports / Contract Interfaces (lan_roster.ports)"]
        ScannerPort["NetworkScannerPort"]
        ResolverPort["HostnameResolverPort"]
        ManufPort["ManufacturerRepositoryPort"]
        RepoPort["DeviceRepositoryPort"]
        AliasRepoPort["DeviceAliasRepositoryPort"]
        ServiceScannerPort["ServiceScannerPort"]
        NetConfigPort["NetworkConfigPort"]
    end

    subgraph Domain["Enterprise Business Rules / Domain (lan_roster.domain)"]
        Models["Models: Device, DeviceAlias, ScanState, HostnameSource, DeviceCategory"]
        Exceptions["Exceptions: LANRosterException, etc."]
    end

    UI --> UpdateUC
    UI --> GetUC
    UI --> ScanPortsUC
    UI --> UpdateAliasUC
    ScanUC --> ScannerPort
    ScanUC --> ResolverPort
    ScanUC --> ManufPort
    ScanUC --> RepoPort
    ScanUC --> ServiceScannerPort
    ScanUC --> AliasRepoPort
    GetUC --> RepoPort
    UpdateUC --> RepoPort
    ScanPortsUC --> ServiceScannerPort
    ScanPortsUC --> RepoPort
    UpdateAliasUC --> AliasRepoPort
    UpdateAliasUC --> RepoPort

    ScannerAdapter -. implements .-> ScannerPort
    ResolverAdapters -. implements .-> ResolverPort
    ManufAdapter -. implements .-> ManufPort
    RepoAdapter -. implements .-> RepoPort
    AliasRepoAdapter -. implements .-> AliasRepoPort
    ServiceScannerAdapter -. implements .-> ServiceScannerPort
    NetConfigAdapter -. implements .-> NetConfigPort

    ScanUC --> Models
    GetUC --> Models
    UpdateUC --> Exceptions
    Ports --> Models
```

> **The Golden Rule**: Source code dependencies must point **strictly inward**. 
> - Nothing in an inner circle can know anything about something in an outer circle.
> - The Domain knows nothing of Use Cases, Ports, Adapters, or Flask.
> - Use Cases know only the Domain and Port interfaces.
> - Adapters know the Ports and Domain, translating external mechanisms into domain-compatible operations.
> - Composition occurs at the outermost boundary: the **Composition Root** ([`lan_roster.bootstrap`](lan_roster/bootstrap.py)).

---

## 3. Package Structure

```text
lan_roster/
├── domain/                      # Enterprise Business Rules (Zero external dependencies)
│   ├── models.py                # Core entities: Device, DeviceAlias, ScanState, HostnameSource, DeviceCategory
│   ├── classifier.py            # DeviceClassifier heuristics
│   └── exceptions.py            # Base & specific domain exceptions
│
├── ports/                       # Contract Interfaces (Abstract Base Classes)
│   ├── scanner.py               # NetworkScannerPort
│   ├── resolver.py              # HostnameResolverPort
│   ├── manufacturer.py          # ManufacturerRepositoryPort
│   ├── repository.py            # DeviceRepositoryPort
│   ├── alias_repository.py      # DeviceAliasRepositoryPort
│   ├── service_scanner.py       # ServiceScannerPort
│   └── network_config.py        # NetworkConfigPort
│
├── use_cases/                   # Application Business Rules (Workflows)
│   ├── scan_network.py          # ScanNetworkUseCase (orchestration & firewall heuristics)
│   ├── get_devices.py           # GetDevicesUseCase (retrieval & IP numeric ordering)
│   ├── update_subnet.py         # UpdateSubnetUseCase (CIDR validation & state updates)
│   ├── scan_device_ports.py     # ScanDevicePortsUseCase (on-demand port probing)
│   └── update_device_alias.py   # UpdateDeviceAliasUseCase (nicknames & notes)
│
├── adapters/                    # Interface Adapters (Secondary / Driven)
│   ├── scanner/
│   │   ├── scapy_arp.py         # Scapy ARP sweeping implementation
│   │   └── socket_service_scanner.py # Concurrent TCP service scanner
│   ├── resolvers/
│   │   ├── composite.py         # Priority composite resolver
│   │   ├── mdns.py              # Multicast DNS (UDP 5353) unicast query
│   │   ├── netbios.py           # NetBIOS Name Service (UDP 137) query
│   │   ├── ssdp.py              # SSDP / UPnP M-SEARCH (UDP 1900) query
│   │   ├── dns.py               # Standard reverse DNS PTR query
│   │   └── http_banner.py       # HTTP banner/title resolver
│   ├── manufacturer/
│   │   └── hybrid_repo.py       # Offline OUI map + privacy bit detection + cache
│   ├── repository/
│   │   ├── sqlite.py            # Active SQLite device & state repository
│   │   ├── sqlite_alias.py      # Active SQLite alias repository
│   │   ├── memory.py            # In-memory device repository (test/development)
│   │   └── memory_alias.py      # In-memory alias repository (test/development)
│   └── network/
│       └── system_config.py     # Subprocess route/ifconfig default subnet detection
│
├── ui/                          # Presentation Layer (Primary / Driving Adapter)
│   ├── web.py                   # Flask controller, API routes, and request handling
│   └── templates.py             # Embedded HTML/CSS/JS responsive dashboard
│
├── bootstrap.py                 # Composition Root (Dependency Injection wiring)
└── __main__.py                  # Package executable entry point (`python -m lan_roster`)

app.py                           # Root runner maintaining backwards compatibility
tests/                           # Isolated unit tests with mock ports
```

---

## 4. Layer Deep-Dive

### 4.1 Domain Layer (`lan_roster.domain`)

The domain layer encapsulates critical enterprise entities and core rules. It has **zero dependencies** on any library outside Python's standard library (`dataclasses`, `enum`, `typing`).

- **[`Device`](lan_roster/domain/models.py)**: Represents an active network node on the broadcast domain with IP, MAC address, hostname, discovery source, hardware vendor, category, first/last-seen timestamps, presence, open ports, and user nickname/notes.
- **[`DeviceAlias`](lan_roster/domain/models.py)**: User-assigned nickname and notes for a device, keyed by MAC address.
- **[`DeviceCategory`](lan_roster/domain/models.py)** and **[`DeviceClassifier`](lan_roster/domain/classifier.py)**: Category values (Mobile, Computer, Smart TV, Smart Home, Printer, Network, Gaming, Generic) and the domain heuristics that assign them.
- **[`ScanState`](lan_roster/domain/models.py)**: Tracks current scanner lifecycle (target subnet, scanning status, last scan timestamp, error messages, and online/offline/total device counts).
- **[`HostnameSource`](lan_roster/domain/models.py)**: Enumeration of discovery protocols (`mDNS`, `NetBIOS`, `SSDP`, `DNS`, `HTTP`, `Firewalled`, `Unknown`).
- **[`Domain Exceptions`](lan_roster/domain/exceptions.py)**: Includes [`LANRosterException`](lan_roster/domain/exceptions.py), [`InvalidSubnetException`](lan_roster/domain/exceptions.py), and [`ScanExecutionException`](lan_roster/domain/exceptions.py).

### 4.2 Ports Layer (`lan_roster.ports`)

Ports define abstract boundaries using Python's `abc.ABC`. These contracts allow use cases to execute without binding to concrete technologies:

- **[`NetworkScannerPort`](lan_roster/ports/scanner.py)**: Contract for broadcasting ARP requests over a target CIDR subnet and yielding `(ip, mac)` pairs.
- **[`HostnameResolverPort`](lan_roster/ports/resolver.py)**: Contract for resolving hostnames across an IP batch: `resolve_batch(ips) -> Dict[ip, (hostname, source)]`.
- **[`ManufacturerRepositoryPort`](lan_roster/ports/manufacturer.py)**: Contract for querying hardware vendors by MAC address.
- **[`DeviceRepositoryPort`](lan_roster/ports/repository.py)**: Contract for atomic saving, retrieving, and updating the scan state and device roster.
- **[`DeviceAliasRepositoryPort`](lan_roster/ports/alias_repository.py)**: Contract for persisting user-defined nicknames and notes by MAC address.
- **[`ServiceScannerPort`](lan_roster/ports/service_scanner.py)**: Contract for probing open ports and services on single devices or batches.
- **[`NetworkConfigPort`](lan_roster/ports/network_config.py)**: Contract for inspecting the operating system's default network route.

### 4.3 Use Cases Layer (`lan_roster.use_cases`)

Use cases represent application workflows. They coordinate domain entities and communicate exclusively through port interfaces:

- **[`ScanNetworkUseCase`](lan_roster/use_cases/scan_network.py)**:
  1. Sets scanning state to `True`.
  2. Executes ARP discovery via [`NetworkScannerPort`](lan_roster/ports/scanner.py).
  3. Triggers concurrent multi-protocol hostname resolution via [`HostnameResolverPort`](lan_roster/ports/resolver.py).
  4. Resolves MAC vendor via [`ManufacturerRepositoryPort`](lan_roster/ports/manufacturer.py).
  5. Applies business heuristic: Flags unidentified devices belonging to known PC vendors (Intel, Microsoft, Dell, Lenovo, HP, Asus, Acer) as `HostnameSource.FIREWALLED`.
  6. Classifies each device with [`DeviceClassifier`](lan_roster/domain/classifier.py), optionally probes services via [`ServiceScannerPort`](lan_roster/ports/service_scanner.py), and applies any stored alias from [`DeviceAliasRepositoryPort`](lan_roster/ports/alias_repository.py).
  7. Atomically commits the roster to [`DeviceRepositoryPort`](lan_roster/ports/repository.py) and updates scan metrics.
- **[`GetDevicesUseCase`](lan_roster/use_cases/get_devices.py)**:
  - Fetches devices from [`DeviceRepositoryPort`](lan_roster/ports/repository.py).
  - Sorts IP addresses numerically by octet (e.g., `192.0.2.2` preceding `192.0.2.10`, using documentation-only examples).
  - Returns the sorted roster alongside the current [`ScanState`](lan_roster/domain/models.py).
- **[`UpdateSubnetUseCase`](lan_roster/use_cases/update_subnet.py)**:
  - Validates and sanitizes raw input CIDR notation using `ipaddress.ip_network`.
  - Automatically appends `/24` if the user omitted a CIDR mask.
  - Updates repository state or raises [`InvalidSubnetException`](lan_roster/domain/exceptions.py).
- **[`ScanDevicePortsUseCase`](lan_roster/use_cases/scan_device_ports.py)**:
  - Verifies the target IP is in the active roster, probes it via [`ServiceScannerPort`](lan_roster/ports/service_scanner.py), and saves the detected open ports back to [`DeviceRepositoryPort`](lan_roster/ports/repository.py).
- **[`UpdateDeviceAliasUseCase`](lan_roster/use_cases/update_device_alias.py)**:
  - Validates and normalizes a MAC address, saves the nickname/notes via [`DeviceAliasRepositoryPort`](lan_roster/ports/alias_repository.py), and propagates them to matching devices in [`DeviceRepositoryPort`](lan_roster/ports/repository.py).

### 4.4 Adapters Layer (`lan_roster.adapters`)

Adapters implement the port contracts to interact with specific infrastructure:

- **[`ScapyArpScanner`](lan_roster/adapters/scanner/scapy_arp.py)**: Crafts Layer 2 Ethernet broadcast frames containing ARP requests using Scapy's `srp`.
- **[`CompositeHostnameResolver`](lan_roster/adapters/resolvers/composite.py)**: Combines specialized resolvers using a priority cascade:
  $$\text{mDNS} \succ \text{NetBIOS} \succ \text{SSDP} \succ \text{DNS} \succ \text{HTTP}$$
  - [`SocketMDNSResolver`](lan_roster/adapters/resolvers/mdns.py): Sends unicast PTR queries, service queries (**Probe C** for `_companion-link`, `_airplay`, `_googlecast`, `_ipp`), and Bonjour Sleep Proxy queries (**Probe E** for `_sleep-proxy`) over UDP 5353, extracting clean instance names and parsing `A` records.
  - [`SocketNetBIOSResolver`](lan_roster/adapters/resolvers/netbios.py): Sends NBNS node status queries (`*` wildcard name) to UDP port 137.
  - [`SocketSSDPResolver`](lan_roster/adapters/resolvers/ssdp.py): Issues multicast and targeted unicast `M-SEARCH` requests (UDP 1900) and concurrent HTTP fetches (**Probe B**) to parse UPnP XML device descriptions and Google Cast API (`/setup/eureka_info` on port 8008) for `<friendlyName>`, `<manufacturer>`, and `<modelName>`.
  - [`SocketDNSResolver`](lan_roster/adapters/resolvers/dns.py): Queries local PTR records via `socket.gethostbyaddr` and issues direct DNS PTR queries to the local network gateway router (UDP port 53) to retrieve DHCP client hostnames.
  - [`SocketHTTPBannerResolver`](lan_roster/adapters/resolvers/http_banner.py): Concurrently probes HTTP ports 80/8080 (**Probe D**) to extract web administration page titles and server banners for cameras, switches, and routers.
- **[`HybridManufacturerRepository`](lan_roster/adapters/manufacturer/hybrid_repo.py)**:
  1. Inspects active UPnP/SSDP metadata registered by Probe B.
  2. Executes **Probe A (Apple Lockdown Check)**: Performs a sub-second TCP connect check on port 62078 (`apple-mobdev`/`iphone-sync`). If open, identifies the device as `Apple iOS Device (Private MAC)` or `Apple iOS Device`, cutting through randomized MAC addresses.
  3. Inspects the IEEE 802 locally-administered MAC address bit (bit 1 of first byte) to flag `Private/Randomized MAC` addresses.
  4. Queries an offline dictionary of common OUIs (Apple, Sony, Intel, Arris, Google, Samsung, etc.).
  5. Consults an in-memory runtime cache.
  6. Queries an external vendor API with timeout fallback.
- **[`SocketServiceScanner`](lan_roster/adapters/scanner/socket_service_scanner.py)**: Concurrent TCP service scanner implementing [`ServiceScannerPort`](lan_roster/ports/service_scanner.py) for roster-wide and on-demand port probing.
- **[`SqliteDeviceRepository`](lan_roster/adapters/repository/sqlite.py)**: Active runtime device and scan-state repository. Persists devices to SQLite (WAL mode) at `~/.lan_roster/lan_roster.db` by default.
- **[`SqliteAliasRepository`](lan_roster/adapters/repository/sqlite_alias.py)**: Active runtime alias repository. Persists nicknames and notes in the same SQLite database file as the device repository.
- **[`InMemoryDeviceRepository`](lan_roster/adapters/repository/memory.py)** and **[`InMemoryAliasRepository`](lan_roster/adapters/repository/memory_alias.py)**: Thread-safe in-memory alternatives retained for tests and development; they are not wired in the current bootstrap composition.
- **[`SystemNetworkConfigAdapter`](lan_roster/adapters/network/system_config.py)**: Inspects the OS routing table using `route -n get default` and `ifconfig` to automatically detect the local broadcast subnet.

### 4.5 Presentation / Primary Adapter (`lan_roster.ui`)

- **[`create_web_app`](lan_roster/ui/web.py)**: A factory function creating the Flask application.
  - Acts as a **Driving Adapter**: Translates incoming HTTP requests into use case calls.
  - Exposes web routes (`GET /`, `POST /scan`) and JSON API routes (`GET /api/devices`, `POST /api/set-subnet`, `POST /api/device/<ip>/scan-ports`, `POST /api/device/alias`).
  - Never accesses storage, Scapy, or low-level sockets directly.

---

## 5. Composition Root & Dependency Injection

The **Composition Root** is the single location where concrete components are instantiated and wired together:

- **[`lan_roster.bootstrap.bootstrap()`](lan_roster/bootstrap.py)**:
  1. Instantiates secondary adapters (`SystemNetworkConfigAdapter`, `SqliteDeviceRepository`, `SqliteAliasRepository` sharing the device repository database path, `HybridManufacturerRepository`, `ScapyArpScanner`, `SocketServiceScanner`, `CompositeHostnameResolver`).
  2. Injects adapters into use cases (`ScanNetworkUseCase`, `GetDevicesUseCase`, `UpdateSubnetUseCase`, `ScanDevicePortsUseCase`, `UpdateDeviceAliasUseCase`).
  3. Spawns a background worker thread governed by a `threading.Event` synchronization trigger.
  4. Passes use cases to the Flask primary adapter factory (`create_web_app`).
- **Entry Points**:
  - [`lan_roster/__main__.py`](lan_roster/__main__.py): Standard package entry point (`python -m lan_roster`).
  - [`app.py`](app.py): Top-level convenience runner invoking `bootstrap()`.

---

## 6. Execution Flow & Sequence Diagrams

### 6.1 Background Sweep & Roster Assembly

```mermaid
sequenceDiagram
    autonumber
    participant Worker as Background Worker
    participant UC as ScanNetworkUseCase
    participant Repo as DeviceRepositoryPort
    participant Scanner as NetworkScannerPort (Scapy)
    participant Resolver as HostnameResolverPort (Composite)
    participant Manuf as ManufacturerRepositoryPort

    Worker->>UC: execute()
    UC->>Repo: get_scan_state()
    Repo-->>UC: ScanState(subnet="192.0.2.0/24")
    UC->>Repo: update_scan_state(is_scanning=True)
    
    UC->>Scanner: scan("192.0.2.0/24")
    Scanner-->>UC: [(192.0.2.1, MAC1), (192.0.2.20, MAC2)]
    
    UC->>Resolver: resolve_batch([192.0.2.1, 192.0.2.20])
    Resolver-->>UC: {192.0.2.1: ("example-host", mDNS)}
    
    loop Each Discovered Node
        UC->>Manuf: get_manufacturer(MAC)
        Manuf-->>UC: Vendor Name
        Note over UC: Apply heuristics (Firewall check)
    end
    
    UC->>Repo: save_devices(device_entities)
    UC->>Repo: update_scan_state(is_scanning=False, total_found=2)
```

### 6.2 User Updates Subnet via Web UI / API

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant Web as Flask UI (web.py)
    participant UC as UpdateSubnetUseCase
    participant Repo as DeviceRepositoryPort
    participant Trigger as scan_trigger (threading.Event)
    participant Worker as Background Worker

    User->>Web: POST /scan { subnet: "192.0.2.0/25" }
    Web->>UC: execute("192.0.2.0/25")
    UC->>UC: Validate & normalize CIDR
    UC->>Repo: update_scan_state(subnet="192.0.2.0/25")
    UC-->>Web: normalized_subnet
    Web->>Trigger: set()
    Web-->>User: 302 Redirect to /
    
    Note over Worker,Trigger: Worker wakes up immediately
    Trigger->>Worker: scan_trigger.wait() released
    Worker->>Worker: Trigger immediate network sweep
```

---

## 7. Key Design Patterns

| Pattern | Clean Architecture Manifestation | File Location |
| :--- | :--- | :--- |
| **Ports & Adapters** | Decouples business rules from external technology via abstract interfaces. | [`lan_roster.ports`](lan_roster/ports/) |
| **Composite** | `CompositeHostnameResolver` presents a uniform `HostnameResolverPort` interface while coordinating multiple protocol resolvers. | [`CompositeHostnameResolver`](lan_roster/adapters/resolvers/composite.py) |
| **Repository** | Abstracts device persistence and scanner state from memory or persistent storage. | [`DeviceRepositoryPort`](lan_roster/ports/repository.py) |
| **Dependency Injection** | Instantiates dependencies externally and supplies them via constructor arguments. | [`lan_roster.bootstrap`](lan_roster/bootstrap.py) |
| **Composition Root** | Centralizes application assembly and wiring into a single module. | [`lan_roster.bootstrap`](lan_roster/bootstrap.py) |
| **Factory Method** | Produces configured Flask instances decoupled from module-level state. | [`create_web_app`](lan_roster/ui/web.py) |

---

## 8. Testability & Quality Assurance

By decoupling external dependencies through Ports, LANRoster achieves complete unit test isolation:

- **Rootless Testing**: Tests run in non-root user environments without raw packet permissions or active interfaces.
- **Deterministic Test Doubles**: Mock scanners and resolvers provide deterministic inputs (e.g. testing the Windows firewall heuristic and CIDR boundary conditions).
- See [VALIDATION.md](VALIDATION.md) for the recorded validation baseline; this document does not state a current test count or execution time.

```bash
# Run unit tests
.venv/bin/python -m unittest discover tests

# Verify lint and static typing
.venv/bin/python -m ruff check .
.venv/bin/pyrefly check

# Validate distributable builds (wheel and source archive)
.venv/bin/python -m build
.venv/bin/python -m twine check dist/*
```

---

## 9. Extensibility Guide

### Adding a New Hostname Resolver Protocol (e.g., LLMNR or WSD)
1. Create a class implementing [`HostnameResolverPort`](lan_roster/ports/resolver.py).
2. Implement the `resolve_batch(ips: List[str])` method.
3. Pass the new resolver into [`CompositeHostnameResolver`](lan_roster/adapters/resolvers/composite.py) in [`lan_roster.bootstrap`](lan_roster/bootstrap.py).
4. No domain models or use cases need to be modified.

### Storage Adapters
SQLite storage is the current runtime implementation: [`SqliteDeviceRepository`](lan_roster/adapters/repository/sqlite.py) and [`SqliteAliasRepository`](lan_roster/adapters/repository/sqlite_alias.py) are wired in [`lan_roster.bootstrap`](lan_roster/bootstrap.py). [`InMemoryDeviceRepository`](lan_roster/adapters/repository/memory.py) and [`InMemoryAliasRepository`](lan_roster/adapters/repository/memory_alias.py) remain available as test and development alternatives behind the same ports. Adding another storage adapter follows the same pattern: implement the relevant port and wire it in the composition root.

---

## 10. Planned Architecture (Not Implemented in v0.2.0)

The items below are planned work from [ROADMAP.md](ROADMAP.md). They are **not** current v0.2.0 behavior and must not be read as implemented architecture.

### Planned v0.3: Security and stabilization
- Localhost-first default binding, restricted subnet and device targets, and protection for state-changing operations. In v0.2.0 the server binds all host interfaces and state-changing routes have no application-level authentication or CSRF protection.
- UTC-aware durable timestamps, separation of presence scanning from enrichment, standard packaging and CI, and privacy-safe diagnostics.

### Planned v0.4: Durable identity and recovery
- Distinguishing network observations from logical devices, preserving identity evidence, provenance, confidence, and conflicts.
- Versioned SQLite migrations, backup/export/restore and failure recovery, a versioned public API, and sanitized diagnostic exports.

