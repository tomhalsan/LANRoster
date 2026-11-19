# LANRoster - Historical v0.2 Feature Backlog

This document records the feature backlog as it stood for the v0.2.0 release. It is historical: Features 1 through 4 below are complete in v0.2.0.

For current planning, see [ROADMAP.md](ROADMAP.md). **GitHub issues and milestones are authoritative** for remaining scope, sequencing, and scheduling. If this document and GitHub differ, GitHub wins.

---

## ✅ Completed Features

- **Feature 1: Smart Device Categorization & Visual Icons**: Automatic node classification into 8 categories with visual emoji icons and summary breakdown chips.
- **Feature 2: Device Presence Tracking (Online vs. Last Seen & New Device Alert)**:
  - **Dynamic Status Indicator**: Pulsing green dot (🟢 Online) for nodes answering sweeps; muted grey dot (⚪ Asleep) for inactive/sleeping devices.
  - **"✨ New" Badge**: Automatically tags devices joining the network for the first time in the current session.
  - **Dual Timestamping**: Tracks `first_seen` and `last_seen` timestamps.
  - **Real-Time Counters**: Displays online vs. asleep counts in the dashboard header.
- **SQLite Database Persistence**:
  - `SqliteDeviceRepository`: Durable SQLite storage at `~/.lan_roster/lan_roster.db` with WAL mode.
  - Device identities, hostnames, timestamps, and detected open ports survive app restarts.
- **Feature 3: Expandable Device Drawer & One-Click Port Shortcuts**:
  - **Interactive Drawer**: Clicking any device row smoothly toggles an inspection panel below it.
  - **1-Click Copy Shortcuts**: Copy buttons for IP and MAC address with visual "✓ Copied!" feedback.
  - **1-Click Web Launch**: One-click shortcuts to web admin consoles (HTTP/HTTPS) and SSH copy.
  - **Verified Services & Port Scanner**: High-speed concurrent TCP service scanner (`SocketServiceScanner`) detecting HTTP, HTTPS, SSH, SMB, IPP, Cast, and Apple Lockdown.
  - **On-Demand Inspection**: `POST /api/device/<ip>/scan-ports` endpoint and "⚡ Re-scan" button in drawer with real-time UI updates.
- **Feature 4: Custom Device Nicknames & Notes (Persistent Aliases)**:
  - **User-Defined Aliases**: Assign friendly nicknames (e.g. "Living Room Apple TV", "Dad's PC") and notes/tags (e.g. "Reserved IP in router", "2.4GHz only") keyed by hardware MAC address.
  - **Prominent Display**: Custom nicknames display prominently in the device table with auto-discovered hostnames shown secondary; custom notes are visible with a hoverable `📝` indicator.
  - **Drawer Customization Card**: Inline editing form in the expandable device drawer with asynchronous `POST /api/device/alias` saving without page reloads.
  - **Durable Persistence**: `DeviceAliasRepositoryPort` with SQLite (`SqliteAliasRepository`) and in-memory (`InMemoryAliasRepository`) adapters, surviving reboots and subnet changes.

---

## 📋 Remaining Work (Tracked in GitHub)

The former Features 5 through 8 are no longer planned in this document. Their current scope, acceptance criteria, and sequencing live in GitHub:

| Historical feature | Current tracking | Milestone |
| :--- | :--- | :--- |
| Feature 5: Wake-on-LAN (WoL) Integration | [#26](https://github.com/tomhalsan/LANRoster/issues/26) | v0.8 |
| Feature 6: Real-Time Ping Latency & Connection Quality (now bounded latency measurement) | [#27](https://github.com/tomhalsan/LANRoster/issues/27) | v0.8 |
| Feature 7: External device identification / search enrichment (now an external vendor and optional AI enrichment architecture decision) | [#28](https://github.com/tomhalsan/LANRoster/issues/28) | v0.8 |
| Feature 8: Dashboard UI/UX Redesign & Modern Layout | [#24](https://github.com/tomhalsan/LANRoster/issues/24) | v0.5 |

Notes:

- No provider-specific model, quota, or free-tier promises are made here. Any external lookup or enrichment remains optional, transparent, and separate from local authoritative state, and requires the architecture decision in [#28](https://github.com/tomhalsan/LANRoster/issues/28) before implementation.
- Latency measurement, if implemented, is opt-in and rate-limited as described in [#27](https://github.com/tomhalsan/LANRoster/issues/27) and the v0.8 milestone in [ROADMAP.md](ROADMAP.md).
- Wake-on-LAN, if implemented, is limited to authorized, known eligible devices as described in [#26](https://github.com/tomhalsan/LANRoster/issues/26).
