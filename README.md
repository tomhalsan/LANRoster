# LANRoster

**LANRoster** is a lightweight, real-time local network device directory and scanner. It translates anonymous local IP and MAC addresses into human-readable computer names, device types, and hardware manufacturers.

Unlike simple ping sweeps or port scanners, LANRoster performs Layer 2 ARP sweeping coupled with multi-protocol hostname discovery (mDNS/Bonjour, NetBIOS, SSDP, and DNS) and vendor OUI fingerprinting.

---

## Features

- **Layer 2 ARP Discovery**: Rapidly discovers all active IPv4 devices on the broadcast domain using Scapy.
- **Multi-Protocol Hostname Resolution**:
  - **mDNS / Bonjour (UDP 5353)**: Discovers macOS, iOS, Android, Apple TV, PlayStation, Smart TV, and IoT hostnames (`.local`).
  - **NetBIOS Name Service (NBNS, UDP 137)**: Concurrently queries Windows computers and Samba shares for their NetBIOS computer names.
  - **SSDP / UPnP (UDP 1900)**: Discovers friendly device names for smart TVs, Google TVs, and media servers.
  - **Unicast Reverse DNS**: Fallback PTR queries when local DNS servers are configured.
- **Hardware & Vendor Fingerprinting**:
  - Recognizes hardware manufacturers (Apple, Sony PlayStation, Intel, Arris/Comcast Gateways, Amazon, Google, TP-Link, Samsung, Vizio, etc.).
  - Detects **Private / Randomized MAC** addresses used by modern mobile OS privacy features.
  - Flags firewalled Windows PCs so they can be easily identified even when in stealth mode.
- **Dynamic Subnet Control**:
  - Automatically detects the host machine's active local subnet upon launch (e.g. `10.0.0.0/24`).
  - Allows entering custom subnets and CIDR blocks (e.g., `10.0.0.0/25`, `192.168.1.0/24`) directly from the web interface for instant rescanning.
- **Modern Live Dashboard**:
  - In-place auto-refreshing UI (polls every 5 seconds without wiping input focus).
  - Protocol source badges (`mDNS`, `NetBIOS`, `SSDP`, `DNS`, `Windows (Firewalled)`).
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
cd net-scanner
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Run LANRoster

Because Scapy crafts Layer 2 Ethernet ARP packets, execute the server with root privileges:

```bash
sudo .venv/bin/python app.py
```
*(or `sudo python3 app.py`)*

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

## License

MIT License.

