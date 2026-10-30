# LANRoster

**LANRoster** is a lightweight, real-time local network device directory and scanner. It translates anonymous local IP and MAC addresses into human-readable computer names, device types, and hardware manufacturers.

Unlike simple ping sweeps or port scanners, LANRoster performs Layer 2 ARP sweeping coupled with multi-protocol hostname discovery (mDNS/Bonjour, NetBIOS, SSDP, and DNS) and vendor OUI fingerprinting.

---

## Features

- **Layer 2 ARP Discovery**: Rapidly discovers all active IPv4 devices on the broadcast domain using Scapy.
- **Multi-Protocol Hostname Resolution**:
  - **mDNS / Bonjour (UDP 5353, Probes C & E)**: Discovers macOS, iOS, Android, Apple TV, PlayStation, Smart TV, and IoT hostnames (`.local`), parsing PTR, A records, Apple Continuity (`_companion-link`), AirPlay, and Bonjour Sleep Proxy (`_sleep-proxy`).
  - **NetBIOS Name Service (NBNS, UDP 137)**: Concurrently queries Windows computers and Samba shares for their NetBIOS computer names.
  - **SSDP / UPnP & Google Cast (UDP 1900 / TCP 8008, Probe B)**: Discovers friendly device names, manufacturers, and model descriptions for Smart TVs, media renderers, and Google Cast/Chromecast devices.
  - **Unicast & Gateway Reverse DNS**: Queries local resolver and sends direct PTR queries to the network gateway router (UDP 53) to discover DHCP client names (e.g. `iPhone-7544`).
  - **HTTP Banner & Title Inspection (Probe D)**: Probes ports 80/8080 for web-managed appliances, IP cameras, printers, and routers.
- **Hardware & Vendor Fingerprinting**:
  - Recognizes hardware manufacturers (Apple, Sony PlayStation, Intel, Arris/Comcast Gateways, Amazon, Google, TP-Link, Samsung, TCL, Vizio, etc.).
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
- **Dynamic Subnet Control**:
  - Automatically detects the host machine's active local subnet upon launch (e.g. `10.0.0.0/24`).
  - Allows entering custom subnets and CIDR blocks (e.g., `10.0.0.0/25`, `192.168.1.0/24`) directly from the web interface for instant rescanning.
- **Modern Live Dashboard**:
  - In-place auto-refreshing UI (polls every 5 seconds without wiping input focus).
  - Protocol source badges (`mDNS`, `NetBIOS`, `SSDP`, `DNS`, `HTTP`, `Windows (Firewalled)`).
  - Built-in guidance for configuring Windows network discovery.
- **JSON REST API**:
  - `GET /api/devices`: Returns active device registry and scan state.
  - `POST /api/set-subnet`: Programmatically updates the target subnet and triggers a sweep.

---

## Requirements

- Python 3.10+
- Root / Administrator privileges (required by Scapy for Layer 2 raw packet access via macOS BPF / Linux raw sockets).

---

## Quickstart

### 1. Clone & Set Up Virtual Environment

```bash
git clone <repository-url>
cd LANRoster
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

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
or access it from any device on your LAN at `http://<your-mac-ip>:8000`.

---

## Subnet Configuration Notes

- **Comcast / Xfinity Gateways**: Typically use subnet `10.0.0.0/24` with the gateway at `10.0.0.1` and DHCP allocation between `10.0.0.2` and `10.0.0.253`.
- **Narrower Scans**: If you only want to scan a specific portion of your subnet, enter CIDR blocks like `10.0.0.0/25` (IPs 1–126) or `10.0.0.128/25` (IPs 129–254) in the target subnet field and click **Update & Scan Now**.

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
│   ├── models.py                # Device, ScanState, HostnameSource entities
│   └── exceptions.py            # Domain exceptions (InvalidSubnetException, etc.)
├── ports/                       # Contract Interfaces (Abstract Base Classes)
│   ├── scanner.py               # NetworkScannerPort
│   ├── resolver.py              # HostnameResolverPort
│   ├── manufacturer.py          # ManufacturerRepositoryPort
│   ├── repository.py            # DeviceRepositoryPort
│   └── network_config.py        # NetworkConfigPort
├── use_cases/                   # Application Business Rules (Workflows)
│   ├── scan_network.py          # ScanNetworkUseCase (orchestration & firewall heuristics)
│   ├── get_devices.py           # GetDevicesUseCase (retrieval & numeric IP sorting)
│   └── update_subnet.py         # UpdateSubnetUseCase (CIDR validation & state management)
├── adapters/                    # Interface Adapters (Secondary / Driven)
│   ├── scanner/scapy_arp.py     # Scapy ARP packet sweeper
│   ├── resolvers/               # Socket mDNS, NetBIOS, SSDP, DNS, & HTTP banner adapters
│   ├── manufacturer/            # Hybrid OUI dictionary + online cache adapter
│   ├── repository/memory.py     # Thread-safe in-memory device repository
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
python3 -m unittest discover tests
```

Verify static typing with Pyrefly:
```bash
pyrefly check
```

---

## Roadmap & Backlog

See [TODO.md](TODO.md) for planned features including:
- **Feature 2**: Device Presence Tracking (Online vs. Last Seen & New Device Alert)
- **Feature 3**: Expandable Device Drawer & One-Click Port Shortcuts
- **Feature 4**: Custom Device Nicknames & Notes (Persistent Aliases)
- **Feature 5**: Wake-on-LAN (WoL) Integration
- **Feature 6**: Real-Time Ping Latency & Connection Quality
- **Feature 7**: "Powered by Google" AI & Search Device Identification

---

## License

This project is licensed under the **GNU General Public License v2.0 (GPL-2.0)**. See the [LICENSE](LICENSE) file for the full license text.

