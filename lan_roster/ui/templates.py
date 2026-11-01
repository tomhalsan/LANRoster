HTML_DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>LANRoster — Local Device Registry</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        :root {
            --bg: #f8fafc;
            --card-bg: #ffffff;
            --text-main: #0f172a;
            --text-muted: #64748b;
            --border: #e2e8f0;
            --primary: #2563eb;
            --primary-hover: #1d4ed8;
            --success: #16a34a;
            --purple: #7c3aed;
            --blue: #0284c7;
            --orange: #ea580c;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background: var(--bg);
            color: var(--text-main);
            padding: 32px 20px;
            display: flex;
            justify-content: center;
        }
        .container {
            width: 100%;
            max-width: 1160px;
        }
        header {
            margin-bottom: 24px;
        }
        .header-title {
            display: flex;
            align-items: baseline;
            gap: 10px;
            margin-bottom: 6px;
        }
        .header-title h1 {
            margin-bottom: 0;
        }
        .version-tag {
            font-size: 0.8rem;
            font-weight: 600;
            color: var(--text-muted);
            background: #e2e8f0;
            padding: 2px 8px;
            border-radius: 9999px;
            letter-spacing: 0.02em;
            line-height: 1.2;
        }
        h1 {
            font-size: 1.75rem;
            font-weight: 700;
            color: #1e293b;
            margin-bottom: 6px;
        }
        .subtitle {
            color: var(--text-muted);
            font-size: 0.95rem;
        }
        .control-panel {
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 24px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }
        .form-row {
            display: flex;
            gap: 12px;
            align-items: center;
            flex-wrap: wrap;
        }
        .input-group {
            flex: 1;
            min-width: 260px;
        }
        .input-group label {
            display: block;
            font-size: 0.82rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--text-muted);
            margin-bottom: 6px;
        }
        input[type="text"] {
            width: 100%;
            padding: 10px 14px;
            font-size: 1rem;
            font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
            border: 1.5px solid var(--border);
            border-radius: 8px;
            outline: none;
            transition: border-color 0.15s;
        }
        input[type="text"]:focus {
            border-color: var(--primary);
            box-shadow: 0 0 0 3px rgba(37,99,235,0.12);
        }
        button {
            padding: 11px 22px;
            font-size: 0.95rem;
            font-weight: 600;
            background: var(--primary);
            color: #ffffff;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            transition: background 0.15s;
            margin-top: 22px;
        }
        button:hover {
            background: var(--primary-hover);
        }
        .hint {
            font-size: 0.85rem;
            color: var(--text-muted);
            margin-top: 12px;
            line-height: 1.45;
        }
        .hint strong {
            color: #334155;
        }
        .status-bar {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 10px 16px;
            background: #f1f5f9;
            border-radius: 8px;
            margin-top: 14px;
            font-size: 0.88rem;
        }
        .status-indicator {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            font-weight: 600;
        }
        .dot {
            width: 9px;
            height: 9px;
            border-radius: 50%;
            background: var(--success);
            display: inline-block;
        }
        .dot.scanning {
            background: var(--orange);
            animation: pulse 1s infinite alternate;
        }
        @keyframes pulse {
            0% { opacity: 0.4; transform: scale(0.9); }
            100% { opacity: 1; transform: scale(1.1); }
        }
        .card {
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 12px;
            box-shadow: 0 2px 6px rgba(0,0,0,0.04);
            overflow: hidden;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            text-align: left;
        }
        th, td {
            padding: 13px 16px;
            border-bottom: 1px solid var(--border);
            vertical-align: middle;
        }
        th {
            background: #f8fafc;
            font-size: 0.82rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: #475569;
            font-weight: 600;
        }
        tr:last-child td {
            border-bottom: none;
        }
        tr:hover td {
            background: #fbfcfe;
        }
        .ip {
            font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
            font-weight: 600;
            color: var(--primary);
        }
        .mac {
            font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
            font-size: 0.85rem;
            color: var(--text-muted);
        }
        .hostname-cell {
            display: flex;
            align-items: center;
            gap: 8px;
            flex-wrap: nowrap;
        }
        .hostname {
            font-weight: 600;
            color: #1e293b;
            white-space: nowrap;
        }
        .badge {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            height: 20px;
            box-sizing: border-box;
            font-size: 0.72rem;
            font-weight: 600;
            padding: 0 6px;
            border-radius: 4px;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            white-space: nowrap;
            flex-shrink: 0;
            line-height: 1;
        }
        .badge-mdns { background: #ede9fe; color: var(--purple); }
        .badge-netbios { background: #e0f2fe; color: var(--blue); }
        .badge-ssdp { background: #ffedd5; color: var(--orange); }
        .badge-dns { background: #dcfce7; color: var(--success); }
        .badge-http { background: #e0e7ff; color: #4338ca; }
        .badge-firewalled { background: #fef3c7; color: #b45309; }
        .badge-new {
            background: #fef08a;
            color: #854d0e;
            border: 1px solid #fde047;
            height: 20px;
            line-height: 1;
        }
        .ip-cell {
            display: inline-flex;
            align-items: center;
            gap: 9px;
        }
        .status-indicator-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            display: inline-block;
            flex-shrink: 0;
        }
        .status-indicator-dot.online {
            background: #16a34a;
            box-shadow: 0 0 0 2px rgba(22, 163, 74, 0.25);
            animation: pulse-online 2.2s infinite ease-in-out;
        }
        .status-indicator-dot.offline {
            background: #94a3b8;
            box-shadow: 0 0 0 1px #cbd5e1;
        }
        @keyframes pulse-online {
            0%, 100% { transform: scale(1); opacity: 1; }
            50% { transform: scale(1.25); opacity: 0.8; }
        }
        .time-online {
            color: #16a34a;
            font-weight: 600;
            font-size: 0.84rem;
        }
        .time-offline {
            color: #64748b;
            font-size: 0.84rem;
        }
        .cat-badge {
            display: inline-flex;
            align-items: center;
            height: 24px;
            box-sizing: border-box;
            gap: 6px;
            font-size: 0.78rem;
            font-weight: 600;
            padding: 0 8px;
            border-radius: 6px;
            background: #f1f5f9;
            color: #334155;
            white-space: nowrap;
            flex-shrink: 0;
        }
        .cat-icon {
            font-size: 0.95rem;
            line-height: 1;
        }
        .cat-mobile { background: #fdf2f8; color: #be185d; }
        .cat-computer { background: #eff6ff; color: #1d4ed8; }
        .cat-smart-tv { background: #f5f3ff; color: #6d28d9; }
        .cat-smart-home { background: #fefce8; color: #a16207; }
        .cat-printer { background: #f0fdf4; color: #15803d; }
        .cat-network { background: #f0fdfa; color: #0f766e; }
        .cat-gaming { background: #fdf4ff; color: #a21caf; }
        .cat-generic { background: #f8fafc; color: #64748b; }
        .category-summary {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-top: 12px;
            padding-top: 12px;
            border-top: 1px dashed var(--border);
        }
        .summary-chip {
            display: inline-flex;
            align-items: center;
            gap: 5px;
            font-size: 0.78rem;
            font-weight: 600;
            padding: 3px 9px;
            border-radius: 9999px;
            background: #f8fafc;
            color: #475569;
            border: 1px solid var(--border);
        }
        .vendor {
            font-size: 0.88rem;
            color: #334155;
            font-weight: 500;
        }
        .vendor-private {
            color: #94a3b8;
            font-style: italic;
        }
        .time {
            font-size: 0.88rem;
            color: var(--text-muted);
        }
        .empty-state {
            padding: 40px 20px;
            text-align: center;
            color: var(--text-muted);
        }
        .error-banner {
            background: #fee2e2;
            color: #991b1b;
            padding: 12px 16px;
            border-radius: 8px;
            margin-bottom: 16px;
            font-size: 0.9rem;
            font-weight: 500;
        }
        .windows-card {
            background: #ffffff;
            border: 1px solid #fed7aa;
            border-left: 4px solid #f97316;
            border-radius: 10px;
            padding: 18px 22px;
            margin-top: 24px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.04);
            font-size: 0.92rem;
            line-height: 1.5;
        }
        .windows-card h3 {
            font-size: 1.02rem;
            color: #9a3412;
            margin-bottom: 8px;
        }
        .windows-steps {
            background: #fff7ed;
            padding: 12px 16px;
            border-radius: 8px;
            margin-top: 10px;
        }
        .windows-steps ol {
            margin-left: 20px;
            margin-top: 6px;
        }
        .windows-steps li {
            margin-bottom: 5px;
        }
        .legend-card {
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 20px 24px;
            margin-top: 24px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.03);
        }
        .legend-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        .legend-header h3 {
            font-size: 1.02rem;
            color: #1e293b;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .legend-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
            gap: 14px 28px;
            margin-top: 16px;
            padding-top: 16px;
            border-top: 1px solid var(--border);
        }
        .legend-item {
            display: flex;
            align-items: flex-start;
            gap: 10px;
            font-size: 0.86rem;
            line-height: 1.45;
        }
        .legend-item .badge {
            margin-top: 1px;
        }
        .legend-desc {
            color: #475569;
        }
        .legend-desc strong {
            color: #1e293b;
        }
        .legend-desc code {
            font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
            font-size: 0.82rem;
            background: #f1f5f9;
            padding: 1px 4px;
            border-radius: 4px;
        }

        /* Feature 3: Expandable Device Drawer */
        tbody tr.device-row {
            cursor: pointer;
            user-select: none;
            transition: background 0.15s ease;
        }
        tbody tr.device-row:hover {
            background: #f8fafc;
        }
        tbody tr.device-row.expanded {
            background: #f1f5f9;
        }
        .drawer-chevron {
            display: inline-block;
            font-size: 0.75rem;
            color: #94a3b8;
            transition: transform 0.2s ease, color 0.2s ease;
            width: 14px;
            text-align: center;
        }
        .drawer-chevron.open, tbody tr.device-row.expanded .drawer-chevron {
            transform: rotate(90deg);
            color: var(--primary);
        }
        .drawer-row td {
            padding: 0 !important;
            background: #f8fafc;
            border-bottom: 2px solid var(--border);
        }
        .drawer-panel {
            padding: 16px 20px 20px 24px;
            border-left: 4px solid var(--primary);
            background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
        }
        .drawer-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 16px;
        }
        .drawer-card {
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 14px 16px;
            box-shadow: 0 1px 2px rgba(0,0,0,0.03);
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }
        .drawer-card-title {
            font-size: 0.78rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--text-muted);
            margin-bottom: 12px;
        }
        .drawer-action-group {
            display: flex;
            flex-direction: column;
            gap: 8px;
        }
        .action-btn {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            font-size: 0.82rem;
            font-weight: 600;
            padding: 6px 12px;
            border-radius: 6px;
            border: 1px solid #cbd5e1;
            background: #ffffff;
            color: #1e293b;
            text-decoration: none;
            cursor: pointer;
            transition: all 0.15s ease;
            box-sizing: border-box;
            width: 100%;
        }
        .action-btn:hover {
            background: #f8fafc;
            border-color: #94a3b8;
        }
        .action-btn.web-btn {
            background: #eff6ff;
            color: #1d4ed8;
            border-color: #bfdbfe;
        }
        .action-btn.web-btn:hover {
            background: #dbeafe;
            border-color: #93c5fd;
        }
        .action-btn.copy-btn.copied {
            background: #dcfce7 !important;
            color: #15803d !important;
            border-color: #86efac !important;
        }
        .services-container {
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
            align-items: center;
            min-height: 32px;
        }
        .service-pill {
            display: inline-flex;
            align-items: center;
            gap: 5px;
            font-size: 0.76rem;
            font-weight: 600;
            padding: 4px 8px;
            border-radius: 6px;
            white-space: nowrap;
        }
        .service-http, .service-httpalt { background: #ecfdf5; color: #047857; border: 1px solid #a7f3d0; }
        .service-https { background: #eff6ff; color: #1d4ed8; border: 1px solid #bfdbfe; }
        .service-ssh { background: #faf5ff; color: #7e22ce; border: 1px solid #e9d5ff; }
        .service-smb { background: #fff7ed; color: #c2410c; border: 1px solid #fed7aa; }
        .service-ipp { background: #f0fdf4; color: #15803d; border: 1px solid #bbf7d0; }
        .service-cast { background: #fdf2f8; color: #be185d; border: 1px solid #fbcfe8; }
        .service-apple { background: #f1f5f9; color: #334155; border: 1px solid #cbd5e1; }
        .service-other { background: #f8fafc; color: #475569; border: 1px solid #e2e8f0; }
        .service-empty {
            color: #94a3b8;
            font-size: 0.82rem;
            font-style: italic;
        }
        .btn-rescan-ports {
            font-size: 0.74rem;
            font-weight: 600;
            background: #f1f5f9;
            border: 1px solid #cbd5e1;
            color: #475569;
            padding: 3px 8px;
            border-radius: 4px;
            cursor: pointer;
            transition: all 0.15s ease;
        }
        .btn-rescan-ports:hover {
            background: #e2e8f0;
            color: #0f172a;
        }
        .timeline-details {
            font-size: 0.83rem;
            color: #475569;
            display: flex;
            flex-direction: column;
            gap: 8px;
        }
        .timeline-details div {
            display: flex;
            justify-content: space-between;
            border-bottom: 1px dashed #f1f5f9;
            padding-bottom: 4px;
        }
        .timeline-details div:last-child {
            border-bottom: none;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div class="header-title">
                <h1>LANRoster</h1>
                <span class="version-tag">v{{ version | default('0.2.0') }}</span>
            </div>
            <p class="subtitle">Real-time local device discovery with mDNS, NetBIOS, SSDP, and hardware fingerprinting</p>
        </header>

        {% if error %}
        <div class="error-banner">
            ⚠️ {{ error | safe }}
        </div>
        {% endif %}

        <div class="control-panel">
            <form method="POST" action="/scan">
                <div class="form-row">
                    <div class="input-group">
                        <label for="subnet">Target Subnet (CIDR)</label>
                        <input type="text" id="subnet" name="subnet" value="{{ state.subnet }}" placeholder="e.g. 10.0.0.0/24">
                    </div>
                    <button type="submit" id="submitBtn">Update & Scan Now</button>
                </div>
            </form>
            <div class="hint">
                💡 <strong>Comcast / Xfinity Gateways</strong> default to <code>10.0.0.0/24</code> (gateway is usually <code>10.0.0.1</code>, with DHCP leases between <code>10.0.0.2</code> and <code>10.0.0.253</code>). If you only want to scan a specific portion, you can enter narrower CIDR blocks like <code>10.0.0.0/25</code> (IPs 1–126) or <code>10.0.0.128/25</code> (IPs 129–254).
            </div>
            <div class="status-bar">
                <div class="status-indicator">
                    <span class="dot {% if state.is_scanning %}scanning{% endif %}" id="statusDot"></span>
                    <span id="statusText">
                        {% if state.is_scanning %}
                            Scanning subnet {{ state.subnet }}...
                        {% else %}
                            Ready — Monitoring {{ state.subnet }}
                        {% endif %}
                    </span>
                </div>
                <div style="color: var(--text-muted); font-size: 0.85rem;" id="metaText">
                    Discovered: <strong id="deviceCount">{{ devices|length }}</strong> devices 
                    (<span id="onlineCount" style="color: #16a34a; font-weight: 600;">{{ state.online_count }} online</span>, 
                    <span id="offlineCount" style="color: #64748b;">{{ state.offline_count }} asleep</span>) | 
                    Last updated: <span id="lastSeen">{{ state.last_scan_time }}</span>
                </div>
            </div>
            <div class="category-summary" id="categorySummary">
                {% set counts = {} %}
                {% for dev in devices.values() %}
                    {% set cat_val = dev.category.value if dev.category else 'Generic' %}
                    {% set cat_icn = dev.category.icon if dev.category else '📟' %}
                    {% if cat_val not in counts %}
                        {% set _ = counts.update({cat_val: {'count': 1, 'icon': cat_icn}}) %}
                    {% else %}
                        {% set _ = counts.update({cat_val: {'count': counts[cat_val]['count'] + 1, 'icon': cat_icn}}) %}
                    {% endif %}
                {% endfor %}
                {% for cat_val, cinfo in counts.items() %}
                <span class="summary-chip">
                    <span>{{ cinfo.icon }}</span> {{ cinfo.count }} {{ cat_val }}
                </span>
                {% endfor %}
            </div>
        </div>

        <div class="card">
            <table>
                <thead>
                    <tr>
                        <th style="width: 130px;">Type</th>
                        <th style="width: 145px;">IP Address</th>
                        <th>Hostname</th>
                        <th>Device / Manufacturer</th>
                        <th style="width: 155px;">MAC Address</th>
                        <th style="width: 135px;">Status / Last Seen</th>
                    </tr>
                </thead>
                <tbody id="devicesTable">
                    {% for ip, device in devices.items() %}
                    <tr class="device-row" onclick="toggleDrawer('{{ ip }}')" id="row-{{ ip }}">
                        <td>
                            <div style="display: flex; align-items: center; gap: 6px;">
                                <span class="drawer-chevron" id="chevron-{{ ip }}">▸</span>
                                <span class="cat-badge cat-{{ device.category.value.lower().replace(' ', '-') if device.category else 'generic' }}">
                                    <span class="cat-icon">{{ device.category.icon if device.category else '📟' }}</span>
                                    <span>{{ device.category.value if device.category else 'Generic' }}</span>
                                </span>
                            </div>
                        </td>
                        <td class="ip">
                            <div class="ip-cell">
                                <span class="status-indicator-dot {% if device.is_online %}online{% else %}offline{% endif %}" 
                                      title="{% if device.is_online %}Online (Confirmed responding to sweeps){% else %}Asleep / Offline (Preserved in roster){% endif %}"></span>
                                <span>{{ ip }}</span>
                            </div>
                        </td>
                        <td>
                            <div class="hostname-cell">
                                <span class="hostname">{{ device.hostname }}</span>
                                {% if device.is_new %}
                                <span class="badge badge-new" title="First detected at {{ device.first_seen }}">New</span>
                                {% endif %}
                                {% if device.source.value %}
                                <span class="badge badge-{{ device.source.value.lower() }}">
                                    {% if device.source.value == 'Firewalled' %}Windows (Firewalled){% else %}{{ device.source.value }}{% endif %}
                                </span>
                                {% endif %}
                            </div>
                        </td>
                        <td class="vendor {% if 'Private' in device.vendor %}vendor-private{% endif %}">{{ device.vendor }}</td>
                        <td class="mac">{{ device.mac }}</td>
                        <td class="time">
                            {% if device.is_online %}
                            <span class="time-online" title="Last active at {{ device.last_seen }}">🟢 Online</span>
                            {% else %}
                            <span class="time-offline" title="Last seen at {{ device.last_seen }}">⚪ Asleep ({{ device.last_seen }})</span>
                            {% endif %}
                        </td>
                    </tr>
                    <tr class="drawer-row" id="drawer-{{ ip }}" style="display: none;" onclick="event.stopPropagation()">
                        <td colspan="6">
                            <div class="drawer-panel">
                                <div class="drawer-grid">
                                    <div class="drawer-card">
                                        <div class="drawer-card-title">Quick Actions & Shortcuts</div>
                                        <div class="drawer-action-group">
                                            <button type="button" class="action-btn copy-btn" onclick="copyText('{{ ip }}', this)">📋 Copy IP ({{ ip }})</button>
                                            <button type="button" class="action-btn copy-btn" onclick="copyText('{{ device.mac }}', this)">📋 Copy MAC</button>
                                            {% if 80 in device.open_ports or 8080 in device.open_ports or ip.endswith('.1') %}
                                            <a href="http://{{ ip }}" target="_blank" rel="noopener noreferrer" class="action-btn web-btn">🌐 Open Web Admin (http://{{ ip }}) ↗</a>
                                            {% endif %}
                                            {% if 443 in device.open_ports %}
                                            <a href="https://{{ ip }}" target="_blank" rel="noopener noreferrer" class="action-btn web-btn">🔒 Open HTTPS Admin (https://{{ ip }}) ↗</a>
                                            {% endif %}
                                            {% if 22 in device.open_ports %}
                                            <button type="button" class="action-btn" onclick="copyText('ssh {{ ip }}', this)">💻 Copy SSH: ssh {{ ip }}</button>
                                            {% endif %}
                                        </div>
                                    </div>
                                    <div class="drawer-card">
                                        <div class="drawer-card-title" style="display: flex; justify-content: space-between; align-items: center;">
                                            <span>Verified Services & Ports</span>
                                            <button type="button" class="btn-rescan-ports" id="rescan-{{ ip }}" onclick="scanPorts('{{ ip }}', this)">⚡ Re-scan</button>
                                        </div>
                                        <div class="services-container" id="services-{{ ip }}">
                                            {% if device.open_ports %}
                                                {% for p in device.open_ports %}
                                                <span class="service-pill service-{{ 'http' if p in (80, 8080) else ('https' if p == 443 else ('ssh' if p == 22 else ('smb' if p == 445 else ('ipp' if p == 631 else ('cast' if p == 8008 else ('apple' if p == 62078 else 'other')))))) }}">
                                                    {{ '🌐' if p in (80, 8080) else ('🔒' if p == 443 else ('💻' if p == 22 else ('📁' if p == 445 else ('🖨️' if p == 631 else ('📺' if p == 8008 else ('📱' if p == 62078 else '⚡')))))) }} {{ p }} / {{ device.detected_services.get(p, 'Port ' ~ p) }}
                                                </span>
                                                {% endfor %}
                                            {% else %}
                                                <span class="service-empty">No standard ports open</span>
                                            {% endif %}
                                        </div>
                                    </div>
                                    <div class="drawer-card">
                                        <div class="drawer-card-title">Discovery Timeline</div>
                                        <div class="timeline-details">
                                            <div><strong>First Seen:</strong> <span>{{ device.first_seen or 'Current Session' }}</span></div>
                                            <div><strong>Last Seen:</strong> <span>{{ device.last_seen or 'Unknown' }}</span></div>
                                            <div><strong>Protocol Source:</strong> <span>{{ device.source.value or 'Standard Discovery' }}</span></div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </td>
                    </tr>
                    {% else %}
                    <tr>
                        <td colspan="6" class="empty-state">
                            Scanning subnet range... devices will populate automatically.
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>

        <div class="legend-card">
            <div class="legend-header">
                <h3>📖 Protocol & Status Legend</h3>
            </div>
            <div class="legend-grid">
                <div class="legend-item">
                    <span class="badge badge-new">New</span>
                    <div class="legend-desc">
                        <strong>New Device:</strong> Joined the network for the first time during this monitoring session.
                    </div>
                </div>
                <div class="legend-item">
                    <span class="badge badge-mdns">mDNS</span>
                    <div class="legend-desc">
                        <strong>Multicast DNS / Bonjour:</strong> Apple Zeroconf probe capturing human names (<code>.local</code>, AirPlay, Continuity).
                    </div>
                </div>
                <div class="legend-item">
                    <span class="badge badge-netbios">NetBIOS</span>
                    <div class="legend-desc">
                        <strong>NetBIOS Name Service:</strong> Windows workstation and Samba computer name query over UDP 137.
                    </div>
                </div>
                <div class="legend-item">
                    <span class="badge badge-ssdp">SSDP</span>
                    <div class="legend-desc">
                        <strong>UPnP / Google Cast:</strong> XML device descriptors and Cast setup discovery on ports 1900 / 8008.
                    </div>
                </div>
                <div class="legend-item">
                    <span class="badge badge-dns">DNS</span>
                    <div class="legend-desc">
                        <strong>Gateway Reverse DNS:</strong> Direct PTR queries against local router (port 53) for DHCP client names.
                    </div>
                </div>
                <div class="legend-item">
                    <span class="badge badge-http">HTTP</span>
                    <div class="legend-desc">
                        <strong>Web Banner / Title:</strong> HTML page title and Server header inspection from embedded web interfaces (ports 80/8080).
                    </div>
                </div>
                <div class="legend-item">
                    <span class="badge badge-firewalled">Windows (Firewalled)</span>
                    <div class="legend-desc">
                        <strong>Stealth Firewall:</strong> Known PC manufacturer whose firewall dropped discovery probes without answering.
                    </div>
                </div>
                <div class="legend-item">
                    <div style="display: flex; align-items: center; gap: 8px; margin-top: 2px;">
                        <span class="status-indicator-dot online"></span>
                        <span class="time-online">Online</span>
                    </div>
                    <div class="legend-desc">
                        <strong>Active Node:</strong> Device actively responded to the most recent Layer 2 ARP sweep.
                    </div>
                </div>
                <div class="legend-item">
                    <div style="display: flex; align-items: center; gap: 8px; margin-top: 2px;">
                        <span class="status-indicator-dot offline"></span>
                        <span class="time-offline">Asleep</span>
                    </div>
                    <div class="legend-desc">
                        <strong>Asleep / Preserved:</strong> Known device retained in roster, currently sleeping or inactive.
                    </div>
                </div>
            </div>
        </div>

        <div class="windows-card">
            <h3>💡 Why are Windows computers showing as "Unknown" or Firewalled?</h3>
            <p>Windows Defender Firewall operates in <strong>"Stealth Mode"</strong> by default on Wi-Fi (Public network profile). It silently drops all incoming discovery requests (mDNS, NetBIOS, ICMP ping) without answering.</p>
            <div class="windows-steps">
                <strong>To make a Windows PC broadcast its hostname on your network:</strong>
                <ol>
                    <li>On the Windows PC, go to <strong>Settings → Network & Internet → Wi-Fi</strong> (or Ethernet) and click your connected network name.</li>
                    <li>Change the network profile from <strong>Public network</strong> to <strong>Private network</strong>.</li>
                    <li>In <strong>Advanced network settings → Advanced sharing settings</strong>, ensure <strong>Network discovery</strong> is turned <strong>ON</strong>.</li>
                </ol>
                <div style="margin-top: 8px; font-size: 0.86rem; color: #64748b;">
                    Once enabled on the Windows computer, click <strong>"Update & Scan Now"</strong> above and its computer name will immediately appear.
                </div>
            </div>
        </div>
    </div>

    <script>
        const expandedIps = new Set();

        function toggleDrawer(ip) {
            if (expandedIps.has(ip)) {
                expandedIps.delete(ip);
            } else {
                expandedIps.add(ip);
            }
            const drawer = document.getElementById(`drawer-${ip}`);
            const row = document.getElementById(`row-${ip}`);
            const chevron = document.getElementById(`chevron-${ip}`);
            const isExp = expandedIps.has(ip);
            if (drawer) drawer.style.display = isExp ? 'table-row' : 'none';
            if (row) row.classList.toggle('expanded', isExp);
            if (chevron) chevron.classList.toggle('open', isExp);
        }

        function copyText(text, btn) {
            if (window.event) window.event.stopPropagation();
            navigator.clipboard.writeText(text).then(() => {
                const orig = btn.innerHTML;
                btn.innerHTML = '✓ Copied!';
                btn.classList.add('copied');
                setTimeout(() => {
                    btn.innerHTML = orig;
                    btn.classList.remove('copied');
                }, 1500);
            }).catch(err => {
                console.error("Copy failed", err);
            });
        }

        function scanPorts(ip, btn) {
            if (window.event) window.event.stopPropagation();
            btn.disabled = true;
            const orig = btn.innerHTML;
            btn.innerHTML = '⏳ Scanning...';
            fetch(`/api/device/${encodeURIComponent(ip)}/scan-ports`, { method: 'POST' })
                .then(res => res.json())
                .then(data => {
                    btn.disabled = false;
                    btn.innerHTML = '⚡ Done!';
                    setTimeout(() => { btn.innerHTML = orig; }, 2000);
                    if (data.success && data.open_ports) {
                        const container = document.getElementById(`services-${ip}`);
                        if (container) {
                            if (data.open_ports.length === 0) {
                                container.innerHTML = '<span class="service-empty">No standard ports open</span>';
                            } else {
                                container.innerHTML = renderServicesList(data.open_ports, data.services);
                            }
                        }
                    }
                })
                .catch(err => {
                    console.error("Scan ports error:", err);
                    btn.disabled = false;
                    btn.innerHTML = '⚠️ Error';
                    setTimeout(() => { btn.innerHTML = orig; }, 2000);
                });
        }

        function renderServicesList(ports, services) {
            if (!ports || ports.length === 0) {
                return '<span class="service-empty">No standard ports open</span>';
            }
            return ports.map(p => {
                const sName = (services && services[p]) ? services[p] : `Port ${p}`;
                let sClass = 'other';
                let icon = '⚡';
                if (p === 80 || p === 8080) { sClass = 'http'; icon = '🌐'; }
                else if (p === 443) { sClass = 'https'; icon = '🔒'; }
                else if (p === 22) { sClass = 'ssh'; icon = '💻'; }
                else if (p === 445) { sClass = 'smb'; icon = '📁'; }
                else if (p === 631) { sClass = 'ipp'; icon = '🖨️'; }
                else if (p === 8008) { sClass = 'cast'; icon = '📺'; }
                else if (p === 62078) { sClass = 'apple'; icon = '📱'; }
                return `<span class="service-pill service-${sClass}">${icon} ${p} / ${sName}</span>`;
            }).join('');
        }

        async function refreshData() {
            try {
                const res = await fetch('/api/devices');
                if (!res.ok) return;
                const data = await res.json();
                
                const statusDot = document.getElementById('statusDot');
                const statusText = document.getElementById('statusText');
                const deviceCount = document.getElementById('deviceCount');
                const lastSeen = document.getElementById('lastSeen');
                
                if (data.state.scanning) {
                    statusDot.className = 'dot scanning';
                    statusText.textContent = `Scanning subnet ${data.state.subnet}...`;
                } else {
                    statusDot.className = 'dot';
                    statusText.textContent = `Ready — Monitoring ${data.state.subnet}`;
                }
                
                deviceCount.textContent = Object.keys(data.devices).length;
                lastSeen.textContent = data.state.last_scan_time;

                const onlineCountEl = document.getElementById('onlineCount');
                const offlineCountEl = document.getElementById('offlineCount');
                if (onlineCountEl) onlineCountEl.textContent = `${data.state.online_count || 0} online`;
                if (offlineCountEl) offlineCountEl.textContent = `${data.state.offline_count || 0} asleep`;

                const tbody = document.getElementById('devicesTable');
                const sortedIps = Object.keys(data.devices).sort((a, b) => {
                    const pa = a.split('.').map(Number);
                    const pb = b.split('.').map(Number);
                    for (let i = 0; i < 4; i++) {
                        if (pa[i] !== pb[i]) return pa[i] - pb[i];
                    }
                    return 0;
                });

                if (sortedIps.length === 0) {
                    tbody.innerHTML = `<tr><td colspan="6" class="empty-state">No devices discovered yet.</td></tr>`;
                    const summaryEl = document.getElementById('categorySummary');
                    if (summaryEl) summaryEl.innerHTML = '';
                    return;
                }

                // Build category summary counts
                const catCounts = {};
                for (const ip of sortedIps) {
                    const cat = data.devices[ip].category || 'Generic';
                    const icon = data.devices[ip].category_icon || '📟';
                    if (!catCounts[cat]) {
                        catCounts[cat] = { count: 0, icon: icon };
                    }
                    catCounts[cat].count++;
                }

                let sumHtml = '';
                for (const [cat, cinfo] of Object.entries(catCounts)) {
                    sumHtml += `<span class="summary-chip"><span>${cinfo.icon}</span> ${cinfo.count} ${cat}</span>`;
                }
                const summaryEl = document.getElementById('categorySummary');
                if (summaryEl) summaryEl.innerHTML = sumHtml;

                let html = '';
                for (const ip of sortedIps) {
                    const info = data.devices[ip];
                    const isPrivate = info.vendor.includes('Private') ? 'vendor-private' : '';
                    let badgeLabel = info.source;
                    if (info.source === 'Firewalled') {
                        badgeLabel = 'Windows (Firewalled)';
                    }
                    const badgeHtml = info.source 
                        ? `<span class="badge badge-${info.source.toLowerCase()}">${badgeLabel}</span>` 
                        : '';

                    const catClass = (info.category || 'Generic').toLowerCase().replace(/\\s+/g, '-');
                    const catIcon = info.category_icon || '📟';
                    const catVal = info.category || 'Generic';

                    const isOnline = info.is_online !== false;
                    const dotClass = isOnline ? 'online' : 'offline';
                    const dotTitle = isOnline ? 'Online (Confirmed responding to sweeps)' : 'Asleep / Offline (Preserved in roster)';
                    const newBadge = info.is_new ? `<span class="badge badge-new" title="First detected at ${info.first_seen}">New</span>` : '';
                    const timeHtml = isOnline 
                        ? `<span class="time-online" title="Last active at ${info.last_seen}">🟢 Online</span>` 
                        : `<span class="time-offline" title="Last seen at ${info.last_seen}">⚪ Asleep (${info.last_seen})</span>`;

                    const isExp = expandedIps.has(ip);
                    const openPorts = info.open_ports || [];
                    const hasHttp = openPorts.includes(80) || openPorts.includes(8080) || ip.endsWith('.1');
                    const hasHttps = openPorts.includes(443);
                    const hasSsh = openPorts.includes(22);
                    const servicesHtml = renderServicesList(openPorts, info.services);

                    html += `<tr class="device-row ${isExp ? 'expanded' : ''}" onclick="toggleDrawer('${ip}')" id="row-${ip}">
                        <td>
                            <div style="display: flex; align-items: center; gap: 6px;">
                                <span class="drawer-chevron ${isExp ? 'open' : ''}" id="chevron-${ip}">▸</span>
                                <span class="cat-badge cat-${catClass}">
                                    <span class="cat-icon">${catIcon}</span>
                                    <span>${catVal}</span>
                                </span>
                            </div>
                        </td>
                        <td class="ip">
                            <div class="ip-cell">
                                <span class="status-indicator-dot ${dotClass}" title="${dotTitle}"></span>
                                <span>${ip}</span>
                            </div>
                        </td>
                        <td>
                            <div class="hostname-cell">
                                <span class="hostname">${info.hostname}</span>
                                ${newBadge}
                                ${badgeHtml}
                            </div>
                        </td>
                        <td class="vendor ${isPrivate}">${info.vendor}</td>
                        <td class="mac">${info.mac}</td>
                        <td class="time">${timeHtml}</td>
                    </tr>
                    <tr class="drawer-row" id="drawer-${ip}" style="display: ${isExp ? 'table-row' : 'none'};" onclick="event.stopPropagation()">
                        <td colspan="6">
                            <div class="drawer-panel">
                                <div class="drawer-grid">
                                    <div class="drawer-card">
                                        <div class="drawer-card-title">Quick Actions & Shortcuts</div>
                                        <div class="drawer-action-group">
                                            <button type="button" class="action-btn copy-btn" onclick="copyText('${ip}', this)">📋 Copy IP (${ip})</button>
                                            <button type="button" class="action-btn copy-btn" onclick="copyText('${info.mac}', this)">📋 Copy MAC</button>
                                            ${hasHttp ? `<a href="http://${ip}" target="_blank" rel="noopener noreferrer" class="action-btn web-btn">🌐 Open Web Admin (http://${ip}) ↗</a>` : ''}
                                            ${hasHttps ? `<a href="https://${ip}" target="_blank" rel="noopener noreferrer" class="action-btn web-btn">🔒 Open HTTPS Admin (https://${ip}) ↗</a>` : ''}
                                            ${hasSsh ? `<button type="button" class="action-btn" onclick="copyText('ssh ${ip}', this)">💻 Copy SSH: ssh ${ip}</button>` : ''}
                                        </div>
                                    </div>
                                    <div class="drawer-card">
                                        <div class="drawer-card-title" style="display: flex; justify-content: space-between; align-items: center;">
                                            <span>Verified Services & Ports</span>
                                            <button type="button" class="btn-rescan-ports" id="rescan-${ip}" onclick="scanPorts('${ip}', this)">⚡ Re-scan</button>
                                        </div>
                                        <div class="services-container" id="services-${ip}">
                                            ${servicesHtml}
                                        </div>
                                    </div>
                                    <div class="drawer-card">
                                        <div class="drawer-card-title">Discovery Timeline</div>
                                        <div class="timeline-details">
                                            <div><strong>First Seen:</strong> <span>${info.first_seen || 'Current Session'}</span></div>
                                            <div><strong>Last Seen:</strong> <span>${info.last_seen || 'Unknown'}</span></div>
                                            <div><strong>Protocol Source:</strong> <span>${badgeLabel || 'Standard Discovery'}</span></div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </td>
                    </tr>`;
                }
                tbody.innerHTML = html;
            } catch (err) {
                console.error("Refresh error:", err);
            }
        }

        setInterval(refreshData, 5000);
    </script>
</body>
</html>
"""

