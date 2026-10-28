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
            max-width: 1050px;
        }
        header {
            margin-bottom: 24px;
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
            padding: 14px 18px;
            border-bottom: 1px solid var(--border);
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
        }
        .hostname {
            font-weight: 600;
            color: #1e293b;
        }
        .badge {
            font-size: 0.72rem;
            font-weight: 600;
            padding: 2px 6px;
            border-radius: 4px;
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }
        .badge-mdns { background: #ede9fe; color: var(--purple); }
        .badge-netbios { background: #e0f2fe; color: var(--blue); }
        .badge-ssdp { background: #ffedd5; color: var(--orange); }
        .badge-dns { background: #dcfce7; color: var(--success); }
        .badge-http { background: #e0e7ff; color: #4338ca; }
        .badge-firewalled { background: #fef3c7; color: #b45309; }
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
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>LANRoster</h1>
            <p class="subtitle">Real-time local device discovery with mDNS, NetBIOS, SSDP, and hardware fingerprinting</p>
        </header>

        {% if error %}
        <div class="error-banner">
            ⚠️ {{ error }}
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
                    Discovered: <strong id="deviceCount">{{ devices|length }}</strong> active devices | Last updated: <span id="lastSeen">{{ state.last_scan_time }}</span>
                </div>
            </div>
        </div>

        <div class="card">
            <table>
                <thead>
                    <tr>
                        <th>IP Address</th>
                        <th>Hostname</th>
                        <th>Device / Manufacturer</th>
                        <th>MAC Address</th>
                        <th>Last Seen</th>
                    </tr>
                </thead>
                <tbody id="devicesTable">
                    {% for ip, device in devices.items() %}
                    <tr>
                        <td class="ip">{{ ip }}</td>
                        <td>
                            <div class="hostname-cell">
                                <span class="hostname">{{ device.hostname }}</span>
                                {% if device.source.value %}
                                <span class="badge badge-{{ device.source.value.lower() }}">
                                    {% if device.source.value == 'Firewalled' %}Windows (Firewalled){% else %}{{ device.source.value }}{% endif %}
                                </span>
                                {% endif %}
                            </div>
                        </td>
                        <td class="vendor {% if 'Private' in device.vendor %}vendor-private{% endif %}">{{ device.vendor }}</td>
                        <td class="mac">{{ device.mac }}</td>
                        <td class="time">{{ device.last_seen }}</td>
                    </tr>
                    {% else %}
                    <tr>
                        <td colspan="5" class="empty-state">
                            Scanning subnet range... devices will populate automatically.
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
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
                    tbody.innerHTML = `<tr><td colspan="5" class="empty-state">No devices discovered yet.</td></tr>`;
                    return;
                }

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

                    html += `<tr>
                        <td class="ip">${ip}</td>
                        <td>
                            <div class="hostname-cell">
                                <span class="hostname">${info.hostname}</span>
                                ${badgeHtml}
                            </div>
                        </td>
                        <td class="vendor ${isPrivate}">${info.vendor}</td>
                        <td class="mac">${info.mac}</td>
                        <td class="time">${info.last_seen}</td>
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

