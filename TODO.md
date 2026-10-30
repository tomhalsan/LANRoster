# LANRoster - Product Roadmap & Backlog

This document tracks upcoming planned features and architectural enhancements for LANRoster.

---

## ✅ Completed Features

- **Feature 1: Smart Device Categorization & Visual Icons**: Automatic node classification into 8 categories with visual emoji icons and summary breakdown chips.
- **Feature 2: Device Presence Tracking (Online vs. Last Seen & New Device Alert)**:
  - **Dynamic Status Indicator**: Pulsing green dot (🟢 Online) for nodes answering sweeps; muted grey dot (⚪ Asleep) for inactive/sleeping devices.
  - **"✨ New" Badge**: Automatically tags devices joining the network for the first time in the current session.
  - **Dual Timestamping**: Tracks `first_seen` and `last_seen` timestamps.
  - **Real-Time Counters**: Displays online vs. asleep counts in the dashboard header.

---

## 📋 Feature Backlog

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

---

### Feature 7: "Powered by Google" AI & Search Device Identification
- **Automatic Signature Resolution**: Resolves cryptic hardware models (e.g. `V505M-K09`, `SM-G998U`, `ESP_2A4F10`) and obscure component OUI vendors (e.g. `Liteon`, `Chongqing Fugui`) into exact commercial product names, brands, and categories using Google Search grounding.
- **100% Free-Tier Compatible**: Designed for Google AI Studio's free tier (1,500 queries/day, 15 RPM) using `gemini-2.0-flash`.
- **Persistent Local Cache**: Results stored in `~/.lan_roster/device_cache.json`. Each obscure signature is queried to Google **only once ever**, using 0 API calls on subsequent passes.
- **Three-Tier User Experience**:
  - **Tier 1 (No API Key)**: Runs 100% locally with Probes A–E + client-side 1-click **"🔍 Search Google"** deep-link button on unknown devices.
  - **Tier 2 (Free Google AI Studio Key)**: Automatic silent background enrichment with Google Search Grounding.
  - **Tier 3 (Paid/Enterprise Key)**: High-speed resolution across large multi-subnet environments.
- **Clean Architecture Plan**:
  - `ports/enricher.py`: `DeviceEnrichmentPort` contract.
  - `adapters/enricher/gemini_enricher.py`: Adapter calling Gemini API with search grounding.
  - `adapters/enricher/cached_enricher.py`: File-backed cache decorator.
  - `ui/templates.py`: Display `✨ Google Identified` badge and 1-click Google search button for unknown devices.

