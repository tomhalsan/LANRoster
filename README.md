# LANRoster

**LANRoster v0.2.0** is the current early working release. It is a lightweight, real-time local network device directory and scanner. It translates anonymous local IP and MAC addresses into human-readable computer names, device types, and hardware manufacturers.

See [ROADMAP.md](ROADMAP.md) for the milestone plan from v0.2.0 toward v1.0. GitHub issues and milestones are authoritative if the roadmap and GitHub ever differ.

Unlike simple ping sweeps or port scanners, LANRoster performs Layer 2 ARP sweeping coupled with multi-protocol hostname discovery (mDNS/Bonjour, NetBIOS, SSDP, and DNS) and vendor OUI fingerprinting.

---

## Features

- **Layer 2 ARP Discovery**: Rapidly discovers all active IPv4 devices on the broadcast domain using Scapy.
- **Multi-Protocol Hostname Resolution**:
  - **mDNS / Bonjour (UDP 5353, Probes C & E)**: Discovers macOS, iOS, Android, Apple TV, PlayStation, Smart TV, and IoT hostnames (`.local`), parsing PTR, A records, Apple Continuity (`_companion-link`), AirPlay, and Bonjour Sleep Proxy (`_sleep-proxy`).
  - **NetBIOS Name Service (NBNS, UDP 137)**: Concurrently queries Windows computers and Samba shares for their NetBIOS computer names.
  - **SSDP / UPnP & Google Cast (UDP 1900 / TCP 8008, Probe B)**: Discovers friendly device names, manufacturers, and model descriptions for Smart TVs, media renderers, and Google Cast/Chromecast devices.
  - **Unicast & Gateway Reverse DNS**: Queries local resolver and sends direct PTR queries to the network gateway router (UDP 53) to discover DHCP client names (e.g. `example-host`).
  - **HTTP Banner & Title Inspection (Probe D)**: Probes ports 80/8080 for web-managed appliances, IP cameras, printers, and routers.
- **Hardware & Vendor Fingerprinting**:
  - Recognizes hardware manufacturers (Apple, Sony PlayStation, Intel, gateway manufacturers, Amazon, Google, TP-Link, Samsung, TCL, Vizio, etc.).
  - **Apple Lockdown Probe (Probe A)**: Fingerprints Apple iOS / iPadOS devices via port 62078 (`apple-mobdev`), identifying iPhones even when using **Private / Randomized MAC** addresses.
  - **UPnP / Cast Metadata Extraction (Probe B)**: Extracts manufacturer and model names directly from device XML/JSON descriptors.
  - Detects **Private / Randomized MAC** addresses used by modern mobile OS privacy features.
  - Flags firewalled Windows PCs so they can be easily identified even when in stealth mode.
- **Smart Device Categorization & Visual Icons**:
  - Automatically classifies nodes into 📱 **Mobile**, 💻 **Computer**, 📺 **Smart TV**, 🔊 **Smart Home / IoT**, 🖨️ **Printer**, 🌐 **Network Infrastructure**, 🎮 **Gaming Console**, and 📟 **Generic** using domain heuristics.
  - Live category summary breakdown chips in the dashboard header.
- **Real-Time Presence Tracking & New Device Alerts**:
  - Live visual presence dots: pulsing green (🟢 **Online**) for active nodes answering sweeps; muted grey (⚪ **Asleep**) for inactive/sleeping devices preserved via roster retention.
  - **"✨ New" Badge**: Automatically tags devices joining the network for the first time in the current session.
  - Header counters displaying real-time online vs. asleep device tallies.
- **SQLite Database Persistence**:
  - Automatically stores discovered device identities, hostnames, categories, and first/last seen timestamps in `~/.lan_roster/lan_roster.db` using WAL mode.
  - Device records, vendor identifications, and "✨ New Device" history survive computer reboots and process restarts.
- **Expandable Device Drawer & Port Shortcuts**:
  - Clicking a device row opens an inspection drawer with copy shortcuts for addresses, web/SSH shortcuts where applicable, detected services, and an on-demand port re-scan.
- **Custom Device Nicknames & Notes**:
  - User-assigned nicknames and notes keyed by MAC address, shown in the roster and edited from the device drawer.
  - Aliases persist in SQLite alongside the device roster and survive restarts and subnet changes.
- **Dynamic Subnet Control**:
  - Automatically detects the host machine's active local subnet upon launch (e.g. `192.0.2.0/24`, a documentation-only example).
  - Allows entering custom subnets and CIDR blocks (e.g., `192.0.2.0/25`, `192.0.2.0/24`) directly from the web interface for instant rescanning.
- **Modern Live Dashboard**:
  - In-place auto-refreshing UI (polls every 5 seconds without wiping input focus).
  - Protocol source badges (`mDNS`, `NetBIOS`, `SSDP`, `DNS`, `HTTP`, `Windows (Firewalled)`).
  - Built-in guidance for configuring Windows network discovery.
- **Web Routes**:
  - `GET /`: Renders the live dashboard.
  - `POST /scan`: Form route that updates the target subnet and triggers a sweep.
- **JSON API**:
  - `GET /api/devices`: Returns the active device registry and scan state.
  - `POST /api/set-subnet`: Updates the target subnet and triggers a sweep.
  - `POST /api/device/<ip>/scan-ports`: Probes open ports and services for a device already in the roster.
  - `POST /api/device/alias`: Saves a user-assigned nickname and notes for a device MAC address.

---

## Requirements

- Python 3.10+
- Root / Administrator privileges (required by Scapy for Layer 2 raw packet access via macOS BPF / Linux raw sockets).

---

## Quickstart

### 1. Clone & Set Up Virtual Environment

```bash
git clone https://github.com/tomhalsan/LANRoster.git
cd LANRoster
python3 -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
```

`pyproject.toml` is the authoritative dependency declaration. `requirements.txt` is a thin compatibility shim that installs the same development extra.

### 2. Run LANRoster

Because Scapy crafts Layer 2 Ethernet ARP packets, execute the server with root privileges:

```bash
sudo .venv/bin/python app.py
```
*(or via package execution: `sudo .venv/bin/python -m lan_roster`)*

### 3. Open the Dashboard

Navigate to:
```
http://localhost:8000
```

The current v0.2.0 entry points bind the Flask development server to all host interfaces (`0.0.0.0:8000`), so the dashboard and API may be reachable, depending on the host firewall and network configuration, from other devices on the local network while it runs. LANRoster does not currently provide application-level authentication or CSRF protection for its state-changing routes. Run it only on a trusted local network. Localhost-first binding and protection for state-changing operations are planned v0.3 work in [ROADMAP.md](ROADMAP.md), not implemented behavior in v0.2.0.

---

## Subnet Configuration Notes

- **Subnet Guidance (provider-neutral)**: Check your router's LAN settings for the subnet and gateway address in use on your network, and enter that subnet in LANRoster. For illustration only, consider a hypothetical network using `192.0.2.0/24` with a hypothetical gateway at `192.0.2.1`, with DHCP addresses allocated from the remaining host addresses in the subnet.
- **Narrower Scans**: If you only want to scan a specific portion of your subnet, enter CIDR blocks like `192.0.2.0/25` (host addresses 1–126) or `192.0.2.128/25` (host addresses 129–254) in the target subnet field and click **Update & Scan Now**. These are documentation-only examples; substitute your own subnet.

---

## Troubleshooting Windows Hostnames

If Windows computers show up with their hostname as `Unknown` and a `Windows (Firewalled)` badge:
1. Windows Defender Firewall defaults new Wi-Fi networks to the **Public network** profile, which operates in stealth mode and silently drops all inbound discovery packets (mDNS, NetBIOS, ICMP ping).
2. **Fix**:
   - On the Windows PC, go to **Settings → Network & Internet → Wi-Fi** (or Ethernet) and click the network name.
   - Change the profile from **Public network** to **Private network**.
   - Under **Advanced network settings → Advanced sharing settings**, ensure **Network discovery** is turned **ON**.
   - Click **Update & Scan Now** in the LANRoster dashboard to populate the computer name.

---

## Clean Architecture Structure

LANRoster is engineered following the **Clean Architecture** (Hexagonal / Ports and Adapters) methodology:

- **Enterprise Business Rules (Domain)** have zero third-party dependencies.
- **Application Business Rules (Use Cases)** orchestrate workflows and communicate exclusively through Port interfaces.
- **Interface Adapters** bridge external systems (Scapy, raw sockets, OS commands, Flask) to domain contracts.
- **Dependency Rule**: Source code dependencies point strictly inward toward the domain core.
- **Testability**: The entire business logic can be tested without root (`sudo`) privileges or live network packets.

For a detailed walkthrough, sequence flows, and design diagrams, consult [ARCHITECTURE.md](ARCHITECTURE.md).

```text
lan_roster/
├── domain/                      # Enterprise Business Rules (zero external dependencies)
│   ├── models.py                # Device, DeviceAlias, ScanState, HostnameSource, DeviceCategory
│   ├── classifier.py            # DeviceClassifier heuristics
│   └── exceptions.py            # Domain exceptions (InvalidSubnetException, etc.)
├── ports/                       # Contract Interfaces (Abstract Base Classes)
│   ├── scanner.py               # NetworkScannerPort
│   ├── resolver.py              # HostnameResolverPort
│   ├── manufacturer.py          # ManufacturerRepositoryPort
│   ├── repository.py            # DeviceRepositoryPort
│   ├── alias_repository.py      # DeviceAliasRepositoryPort
│   ├── service_scanner.py       # ServiceScannerPort
│   └── network_config.py        # NetworkConfigPort
├── use_cases/                   # Application Business Rules (Workflows)
│   ├── scan_network.py          # ScanNetworkUseCase (orchestration & firewall heuristics)
│   ├── get_devices.py           # GetDevicesUseCase (retrieval & numeric IP sorting)
│   ├── update_subnet.py         # UpdateSubnetUseCase (CIDR validation & state management)
│   ├── scan_device_ports.py     # ScanDevicePortsUseCase (on-demand port probing)
│   └── update_device_alias.py   # UpdateDeviceAliasUseCase (nicknames & notes)
├── adapters/                    # Interface Adapters (Secondary / Driven)
│   ├── scanner/                 # Scapy ARP sweeper & socket service scanner
│   ├── resolvers/               # Socket mDNS, NetBIOS, SSDP, DNS, & HTTP banner adapters
│   ├── manufacturer/            # Hybrid OUI dictionary + online cache adapter
│   ├── repository/              # SQLite (active) & in-memory device/alias repositories
│   └── network/system_config.py # macOS/Linux route and ifconfig adapter
├── ui/                          # Presentation Layer (Primary / Driving Adapter)
│   ├── web.py                   # Flask controller & API routes
│   └── templates.py             # Responsive HTML/CSS/JS dashboard
├── bootstrap.py                 # Composition Root: Dependency Injection & background worker
└── __main__.py                  # Package execution entry point (`python -m lan_roster`)

app.py                           # Root runner maintaining backwards compatibility
tests/                           # Isolated unit tests with mock ports
```

---

## Running Tests

Run the unit test suite without needing root privileges or network hardware:
```bash
.venv/bin/python -m unittest discover tests
```

Verify lint and static typing:
```bash
.venv/bin/python -m ruff check .
.venv/bin/pyrefly check
```

Validate the distributable builds (wheel and source archive):
```bash
.venv/bin/python -m build
.venv/bin/python -m twine check dist/*
```

---

## Roadmap & Backlog

See [ROADMAP.md](ROADMAP.md) for the milestone roadmap to v1.0 and [TODO.md](TODO.md) for the historical v0.2 feature backlog. Features 1 through 4 are complete in v0.2.0. Remaining work is tracked in GitHub issues and milestones, which are authoritative for scope and scheduling.

---

## License

This project is licensed under the **GNU General Public License v2.0 (GPL-2.0)**. See the [LICENSE](LICENSE) file for the full license text.

