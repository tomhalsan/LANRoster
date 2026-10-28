# LANRoster - Product Roadmap & Backlog

This document tracks upcoming planned features and architectural enhancements for LANRoster.

---

## 📋 Feature Backlog

### Feature 2: Device Presence Tracking (Online vs. Last Seen & New Device Alert)
- **Status Indicator**: Dynamic pulsing green dot for devices responding to current ARP sweeps; muted grey indicator for asleep/offline devices.
- **Timestamp Tracking**: Track `first_seen` and `last_seen` timestamps in `Device` domain model.
- **"New Device" Badge**: Visual highlight for devices detected on the network for the first time within a configurable window (e.g., past 2 hours), alerting users to new connections or unknown devices.
- **Clean Architecture Plan**:
  - `domain/models.py`: Add `first_seen: datetime`, `last_seen: datetime`, and `is_online: bool` to `Device`.
  - `adapters/repository/memory.py`: Update timestamp tracking during roster merge.
  - `ui/templates.py`: Add presence status badges and time-ago formatting.

---

### Feature 3: Expandable Device Drawer & One-Click Port Shortcuts
- **Interactive Device Drawer**: Click on any device row to slide open an inspection panel.
- **Detected Services Badges**: Display verified active services (HTTP, HTTPS, SSH, SMB, Apple Lockdown, Google Cast, IPP).
- **One-Click Web Launch**: Render clickable links directly to administrative consoles (e.g. `http://10.0.0.1` for router, printer web UI, NAS portals).
- **Quick Clipboard Copy**: One-click copy buttons for MAC address and IP address for quick router DHCP reservation setup.
- **Clean Architecture Plan**:
  - `ports/scanner.py` & `use_cases`: Expose detected open ports/services on `Device`.
  - `ui/templates.py`: HTMX or CSS-based collapsible drawer with action buttons.

---

### Feature 4: Custom Device Nicknames & Notes (Persistent Aliases)
- **User Overrides**: Allow users to assign friendly custom names (e.g. "Dad's Gaming Rig", "Living Room Apple TV", "Basement Thermostat") overriding or augmenting auto-discovered hostnames.
- **Static Notes**: Add custom tags or notes per device (e.g. "Static IP assigned in router", "Kids' tablet").
- **Persistence Adapter**: Store user aliases in a lightweight JSON or SQLite storage file (`~/.lan_roster/aliases.json`).
- **Clean Architecture Plan**:
  - `ports/alias_repository.py`: Interface for reading and saving custom device aliases and notes.
  - `adapters/repository/json_alias.py`: File-based persistence adapter.
  - `use_cases/update_device_alias.py`: Use case for mutating and persisting alias records.

---

### Feature 5: Wake-on-LAN (WoL) Integration
- **One-Click Wake**: Send Ethernet Magic Packets (`FF:FF:FF:FF:FF:FF` + 16x MAC repeat) over UDP port 9 to wake sleeping computers (e.g. `PAPPA-CPPC`).
- **Clean Architecture Plan**:
  - `ports/wol.py`: Port definition for dispatching Wake-on-LAN packets.
  - `adapters/wol/socket_wol.py`: UDP socket implementation broadcasting to subnet `x.x.x.255`.
  - `use_cases/wake_device.py`: Use case validating MAC address and invoking WoL port.
  - `ui/`: Action button in device table or drawer.

---

### Feature 6: Real-Time Ping Latency & Connection Quality
- **Round-Trip Latency**: Measure and display latency (e.g. `1.2 ms`, `38 ms`) next to each active device.
- **Quality Indicator**: Color-code latency (Green: < 10ms wired/strong Wi-Fi; Yellow: 10–50ms; Red: > 50ms or packet loss).
- **Clean Architecture Plan**:
  - `ports/latency.py`: Interface for pinging network nodes.
  - `adapters/latency/socket_ping.py`: Multi-threaded TCP/ICMP ping prober.
  - `domain/models.py`: Store `latency_ms: float | None`.
  - `ui/templates.py`: Add latency badge column with color-coding.

