import concurrent.futures
import ipaddress
import re
import socket
import struct
import subprocess
import threading
import time
from flask import Flask, jsonify, render_template_string, request, redirect, url_for
from scapy.all import ARP, Ether, srp

app = Flask(__name__)

# Lock for thread-safe state management
data_lock = threading.Lock()

# Scanner control event
scan_trigger = threading.Event()

# Discovered devices dictionary:
# {ip: {"mac": mac, "hostname": name, "source": source, "vendor": vendor, "last_seen": timestamp}}
devices = {}

# Common hardware vendor OUI mappings (first 6 hex chars of MAC address)
OUI_MAP = {
    # Arris / CommScope / Comcast Xfinity Gateways
    'E8CD15': 'Arris / Comcast Gateway',
    '001DD0': 'Arris / Comcast',
    '001E46': 'Arris / Comcast',
    '24767D': 'Arris / Comcast',
    '44AA50': 'Arris / Comcast',
    '5CE30E': 'Arris / Comcast',
    '903EAB': 'Arris / Comcast',
    'A41588': 'Arris / Comcast',
    'B81619': 'Arris / Comcast',
    'CC65AD': 'Arris / Comcast',

    # Apple
    '5C9BA6': 'Apple', '000393': 'Apple', '000502': 'Apple', '000A27': 'Apple',
    '000A95': 'Apple', '000D93': 'Apple', '0010FA': 'Apple', '001124': 'Apple',
    '001451': 'Apple', '0016CB': 'Apple', '0017F2': 'Apple', '0019E3': 'Apple',
    '001B63': 'Apple', '001CB3': 'Apple', '001D4F': 'Apple', '001E52': 'Apple',
    '001EC2': 'Apple', '001F5B': 'Apple', '001FF3': 'Apple', '0021E9': 'Apple',
    '002241': 'Apple', '002312': 'Apple', '002332': 'Apple', '00236C': 'Apple',
    '002436': 'Apple', '002500': 'Apple', '00254B': 'Apple', '0025BC': 'Apple',
    '002608': 'Apple', '00264A': 'Apple', '0026B0': 'Apple', '0026BB': 'Apple',
    '109397': 'Apple', '109ADD': 'Apple', '14109F': 'Apple', '147DDA': 'Apple',
    '1499E2': 'Apple', '14C213': 'Apple', '18AF61': 'Apple', '18EE69': 'Apple',
    '20768F': 'Apple', '28CFDA': 'Apple', '3408BC': 'Apple', '34159E': 'Apple',
    '34363B': 'Apple', '38CA84': 'Apple', '3C0754': 'Apple', '3C15C2': 'Apple',
    '3C22FB': 'Apple', '406C8F': 'Apple', '4098AD': 'Apple', '40A6D9': 'Apple',
    '442A60': 'Apple', '48437C': 'Apple', '48605F': 'Apple', '48D705': 'Apple',
    '4C3275': 'Apple', '50BC96': 'Apple', '542696': 'Apple', '54724F': 'Apple',
    '5855CA': 'Apple', '600308': 'Apple', '6030D4': 'Apple', '60334B': 'Apple',
    '606720': 'Apple', '64200C': 'Apple', '6476BA': 'Apple', '685B35': 'Apple',
    '6C4008': 'Apple', '701124': 'Apple', '703EAC': 'Apple', '70708B': 'Apple',
    '70EF00': 'Apple', '741BB2': 'Apple', '748114': 'Apple', '7831C1': 'Apple',
    '784F43': 'Apple', '787B8A': 'Apple', '78CA39': 'Apple', '7C04D0': 'Apple',
    '7C6D62': 'Apple', '804971': 'Apple', '80929F': 'Apple', '80E650': 'Apple',
    '842E27': 'Apple', '88665A': 'Apple', '8C8590': 'Apple', '9027E4': 'Apple',
    '907240': 'Apple', '9801A7': 'Apple', '9810E8': 'Apple', '98B8E3': 'Apple',
    '9C04EB': 'Apple', 'A45E60': 'Apple', 'A4C361': 'Apple', 'A85B78': 'Apple',
    'AC1F74': 'Apple', 'B418D1': 'Apple', 'B8098A': 'Apple', 'B87826': 'Apple',
    'BC52B7': 'Apple', 'C81EE7': 'Apple', 'C82A14': 'Apple', 'C8334B': 'Apple',
    'CC088D': 'Apple', 'DC2B61': 'Apple', 'DC3714': 'Apple', 'DC5285': 'Apple',
    'E06678': 'Apple', 'E425E7': 'Apple', 'E4CE8F': 'Apple', 'E8802E': 'Apple',
    'EC3586': 'Apple', 'F01898': 'Apple', 'F07960': 'Apple', 'F40F24': 'Apple',
    'F437B7': 'Apple', 'F82793': 'Apple', 'F8E903': 'Apple', 'C8D083': 'Apple',

    # Google
    '14C67D': 'Google', '001A11': 'Google', '1C56FE': 'Google', '3C5A37': 'Google',
    '546009': 'Google', '703ACB': 'Google', 'D86C63': 'Google', 'F40304': 'Google',
    'F4F5E8': 'Google', 'D4351D': 'Google Nest',

    # Amazon
    '20BEB8': 'Amazon', 'CCAFE3': 'Amazon', '50BBB5': 'Amazon', '381F26': 'Amazon',
    '00FC8B': 'Amazon', '44650D': 'Amazon', '6837E9': 'Amazon', '747548': 'Amazon',
    '84D6D0': 'Amazon', 'AC63BE': 'Amazon', '40B4CD': 'Amazon', 'FC65DE': 'Amazon',

    # Sony / PlayStation
    '605BB4': 'Sony Interactive (PlayStation)', '00041F': 'Sony', '001315': 'Sony',
    '0015C1': 'Sony', '0019C5': 'Sony', '001D0D': 'Sony', '0024BE': 'Sony',
    'F8461C': 'Sony', '904748': 'Sony Interactive (PlayStation 5)',

    # Microsoft
    '000D3A': 'Microsoft', '00125A': 'Microsoft', '00155D': 'Microsoft', '0017FA': 'Microsoft',
    '001DD8': 'Microsoft', '002248': 'Microsoft', '0025AE': 'Microsoft', '281878': 'Microsoft',
    '7C1E52': 'Microsoft', 'DC9840': 'Microsoft', '28C63F': 'Microsoft Surface',

    # Samsung
    '0007AB': 'Samsung', '0012FB': 'Samsung', '001599': 'Samsung', '001632': 'Samsung',
    '08373D': 'Samsung', '14BB6E': 'Samsung', '28987B': 'Samsung', '34C9F0': 'Samsung',
    '508569': 'Samsung', '64B5C6': 'Samsung', '8C71F8': 'Samsung', '94652D': 'Samsung',
    'B857D8': 'Samsung', 'C819F7': 'Samsung', 'CC07AB': 'Samsung', 'D059E4': 'Samsung',

    # Networking & IoT
    'D80D17': 'TP-Link', '002719': 'TP-Link', '50C7BF': 'TP-Link', '60A44C': 'TP-Link',
    '704F57': 'TP-Link', '98DAC4': 'TP-Link', 'C006C3': 'TP-Link', 'E848B8': 'TP-Link',
    '080581': 'Roku', '20F543': 'Roku', '2CAA8E': 'Roku', '84EAED': 'Roku',
    'AC3A7A': 'Roku', 'B0EE45': 'Roku', 'D83134': 'Roku',
    'B827EB': 'Raspberry Pi', 'DCA632': 'Raspberry Pi', 'E45F01': 'Raspberry Pi',
    '28CDC1': 'Raspberry Pi',

    # Intel (Windows PC / Laptops)
    'CC1531': 'Intel (Windows PC)', '801316': 'Intel (Windows PC)',
    '0002B3': 'Intel', '000347': 'Intel', '000423': 'Intel', '000E0C': 'Intel',
    '001302': 'Intel', '001500': 'Intel', '8086F2': 'Intel', '843497': 'Intel',
    '001B21': 'Intel', '001E67': 'Intel', '00215C': 'Intel', '0022FB': 'Intel',
    '002314': 'Intel', '0024D7': 'Intel', '0026C7': 'Intel', '3413E8': 'Intel',
    '4851C5': 'Intel', '5891CF': 'Intel', '6805CA': 'Intel', 'A44CC8': 'Intel',
    'C85B76': 'Intel',

    # PC Manufacturers (Dell, HP, Lenovo)
    '001422': 'Dell PC', '001A6B': 'Dell PC', '180373': 'Dell PC', '24B6FD': 'Dell PC',
    '44A842': 'Dell PC', 'B8AC6F': 'Dell PC', 'D4BEB9': 'Dell PC', 'F8BC12': 'Dell PC',
    '001B9A': 'Lenovo PC', '002186': 'Lenovo PC', '00238C': 'Lenovo PC', '002655': 'Lenovo PC',
    '047D7B': 'Lenovo PC', '207693': 'Lenovo PC', '3C970E': 'Lenovo PC', '54EE75': 'Lenovo PC',
    '68F728': 'Lenovo PC', '8CE9B4': 'Lenovo PC',
    '001635': 'HP PC', '001708': 'HP PC', '0018FE': 'HP PC', '0019BB': 'HP PC',
    '10604B': 'HP PC', '1458D0': 'HP PC', '186024': 'HP PC', '28924A': 'HP PC',
    '308D99': 'HP PC', '3863BB': 'HP PC', '3C5282': 'HP PC', '40A8F0': 'HP PC',

    # Other Local Devices & Peripherals
    'E42686': 'DWnet (IP Camera)',
    '3C62F0': 'Sercomm (Comcast Pod)',
    '2C641F': 'Vizio Smart TV',
    'D4808B': 'Seiko Epson Printer',
}

ONLINE_OUI_CACHE = {}

def detect_default_subnet():
    """Detects active default interface and returns its CIDR subnet (e.g., 10.0.0.0/24)."""
    try:
        out = subprocess.check_output(['route', '-n', 'get', 'default'], timeout=2).decode()
        iface = None
        for line in out.splitlines():
            if 'interface:' in line:
                iface = line.split(':')[1].strip()
                break
        if iface:
            if_out = subprocess.check_output(['ifconfig', iface], timeout=2).decode()
            for line in if_out.splitlines():
                line = line.strip()
                if line.startswith('inet '):
                    parts = line.split()
                    ip = parts[1]
                    netmask_hex = parts[3]
                    netmask_int = int(netmask_hex, 16)
                    cidr = bin(netmask_int).count('1')
                    net = ipaddress.IPv4Network(f"{ip}/{cidr}", strict=False)
                    return str(net)
    except Exception:
        pass
    return "10.0.0.0/24"

# Global scan status state
scan_state = {
    "subnet": detect_default_subnet(),
    "scanning": False,
    "last_scan_time": "Never",
    "error_message": None,
    "total_found": 0
}

def get_vendor(mac):
    """Identifies manufacturer from MAC address OUI, local privacy bit, or cached lookup."""
    clean = mac.replace(':', '').replace('-', '').upper()
    if len(clean) >= 6:
        first_byte = int(clean[:2], 16)
        # Check randomized / locally administered bit
        if first_byte & 0x02:
            return "Private/Randomized MAC"
        prefix = clean[:6]
        if prefix in OUI_MAP:
            return OUI_MAP[prefix]
        if prefix in ONLINE_OUI_CACHE:
            return ONLINE_OUI_CACHE[prefix]
        # Quick fallback for unknown OUI prefixes
        try:
            import urllib.request
            req = urllib.request.Request(f"https://api.macvendors.com/{prefix}", headers={"User-Agent": "NetScanner/1.0"})
            with urllib.request.urlopen(req, timeout=0.8) as resp:
                v = resp.read().decode('utf-8').strip()
                ONLINE_OUI_CACHE[prefix] = v
                return v
        except Exception:
            ONLINE_OUI_CACHE[prefix] = "Generic Device"
    return "Generic Device"

def resolve_netbios(ip, timeout=0.4):
    """Queries target IP for Windows NetBIOS node status on UDP 137."""
    name = ('*' + ' ' * 14 + '\x00')
    encoded = []
    for c in name:
        b = ord(c)
        encoded.append(chr(((b >> 4) & 0xF) + ord('A')))
        encoded.append(chr((b & 0xF) + ord('A')))
    encoded_name = ''.join(encoded).encode('ascii')

    header = struct.pack('>HHHHHH', 0x1337, 0x0000, 1, 0, 0, 0)
    question = b'\x20' + encoded_name + b'\x00' + struct.pack('>HH', 0x0021, 0x0001)
    packet = header + question

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(timeout)
    try:
        sock.sendto(packet, (ip, 137))
        data, _ = sock.recvfrom(1024)
        if len(data) > 56:
            num_names = data[56]
            offset = 57
            for _ in range(num_names):
                if offset + 18 <= len(data):
                    raw_name = data[offset:offset+15].decode('latin1', errors='ignore').strip()
                    name_type = data[offset+15]
                    flags = struct.unpack('>H', data[offset+16:offset+18])[0]
                    is_group = bool(flags & 0x8000)
                    if not is_group and name_type in (0x00, 0x20) and raw_name:
                        return raw_name
                    offset += 18
    except Exception:
        pass
    finally:
        sock.close()
    return None

def resolve_mdns_batch(ips, timeout=1.5):
    """
    Sends mDNS reverse PTR queries for all target IPs in parallel
    to multicast 224.0.0.251:5353 and gathers responses.
    """
    def make_mdns_ptr(ip):
        parts = ip.split('.')
        rev = f"{parts[3]}.{parts[2]}.{parts[1]}.{parts[0]}.in-addr.arpa"
        header = struct.pack('>HHHHHH', 0, 0, 1, 0, 0, 0)
        q = b''
        for p in rev.split('.'):
            q += bytes([len(p)]) + p.encode('ascii')
        q += b'\x00'
        q += struct.pack('>HH', 12, 1)  # PTR, IN
        return header + q

    def parse_dns_name(data, offset):
        parts = []
        visited = set()
        orig = None
        while offset < len(data):
            length = data[offset]
            if length == 0:
                if orig is None: orig = offset + 1
                break
            elif (length & 0xC0) == 0xC0:
                if orig is None: orig = offset + 2
                ptr = struct.unpack('>H', data[offset:offset+2])[0] & 0x3FFF
                if ptr in visited: break
                visited.add(ptr)
                offset = ptr
            else:
                offset += 1
                parts.append(data[offset:offset+length].decode('utf-8', errors='ignore'))
                offset += length
        return '.'.join(parts), (orig if orig else offset)

    results = {}
    if not ips:
        return results

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        s.bind(('', 5353))
        mreq = struct.pack('4sL', socket.inet_aton('224.0.0.251'), socket.INADDR_ANY)
        s.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        s.settimeout(0.3)

        for ip in ips:
            pkt = make_mdns_ptr(ip)
            s.sendto(pkt, ('224.0.0.251', 5353))
            try:
                s.sendto(pkt, (ip, 5353))
            except Exception:
                pass

        end = time.time() + timeout
        while time.time() < end:
            try:
                data, _ = s.recvfrom(4096)
                if len(data) > 12:
                    num_ans = struct.unpack('>H', data[6:8])[0]
                    num_q = struct.unpack('>H', data[4:6])[0]
                    curr = 12
                    for _ in range(num_q):
                        _, curr = parse_dns_name(data, curr)
                        curr += 4
                    for _ in range(num_ans):
                        if curr >= len(data): break
                        qname, curr = parse_dns_name(data, curr)
                        if curr + 10 > len(data): break
                        rtype, rclass, ttl, rdlen = struct.unpack('>HHIH', data[curr:curr+10])
                        curr += 10
                        if rtype == 12:
                            target, _ = parse_dns_name(data, curr)
                            if 'in-addr.arpa' in qname:
                                p = qname.replace('.in-addr.arpa', '').split('.')
                                orig_ip = f"{p[3]}.{p[2]}.{p[1]}.{p[0]}"
                                results[orig_ip] = target.rstrip('.')
                        curr += rdlen
            except socket.timeout:
                pass
            except Exception:
                pass
        s.close()
    except Exception:
        pass
    return results

def resolve_ssdp_batch(timeout=1.0):
    """Sends UPnP SSDP M-SEARCH to discover smart devices and computer names."""
    results = {}
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(0.3)
    msg = (
        'M-SEARCH * HTTP/1.1\r\n'
        'HOST: 239.255.255.250:1900\r\n'
        'MAN: "ssdp:discover"\r\n'
        'MX: 1\r\n'
        'ST: ssdp:all\r\n\r\n'
    ).encode()
    try:
        sock.sendto(msg, ('239.255.255.250', 1900))
        end = time.time() + timeout
        locations = {}
        while time.time() < end:
            try:
                data, addr = sock.recvfrom(2048)
                ip = addr[0]
                text = data.decode('latin1', errors='ignore')
                for line in text.splitlines():
                    if line.upper().startswith('LOCATION:'):
                        loc = line.split(':', 1)[1].strip()
                        if ip not in locations:
                            locations[ip] = loc
            except socket.timeout:
                pass
            except Exception:
                pass

        import urllib.request
        for ip, url in list(locations.items())[:8]:
            try:
                req = urllib.request.Request(url, headers={'User-Agent': 'NetScanner/1.0'})
                with urllib.request.urlopen(req, timeout=0.5) as resp:
                    xml = resp.read().decode('utf-8', errors='ignore')
                    m = re.search(r'<friendlyName>(.*?)</friendlyName>', xml, re.IGNORECASE)
                    if m:
                        results[ip] = m.group(1).strip()
            except Exception:
                pass
    except Exception:
        pass
    finally:
        sock.close()
    return results

def resolve_reverse_dns(ip):
    """Standard unicast reverse DNS fallback."""
    try:
        host, _, _ = socket.gethostbyaddr(ip)
        return host
    except Exception:
        return None

def arp_scan(target_subnet):
    """Executes Layer 2 ARP discovery and multi-protocol hostname resolution."""
    broadcast = Ether(dst="ff:ff:ff:ff:ff:ff")
    arp_request = ARP(pdst=target_subnet)
    packet = broadcast / arp_request

    answered, _ = srp(packet, timeout=2, verbose=False)

    discovered = {}
    current_time = time.strftime("%H:%M:%S")

    for _, received_packet in answered:
        ip = received_packet.psrc
        mac = received_packet.hwsrc
        discovered[ip] = mac

    all_ips = list(discovered.keys())

    # 1. Batch mDNS lookup (Macs, TVs, Android, IoT, Windows 10/11)
    mdns_names = resolve_mdns_batch(all_ips, timeout=1.5)

    # 2. SSDP / UPnP lookup (Smart TVs, media devices, Windows network discovery)
    ssdp_names = resolve_ssdp_batch(timeout=0.8)

    # 3. Concurrent NetBIOS NBNS queries (Windows computers and Samba servers)
    netbios_names = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        future_to_ip = {executor.submit(resolve_netbios, ip): ip for ip in all_ips}
        for future in concurrent.futures.as_completed(future_to_ip):
            ip = future_to_ip[future]
            try:
                nb = future.result()
                if nb:
                    netbios_names[ip] = nb
            except Exception:
                pass

    # 4. Synthesize final results
    scan_results = {}
    for ip, mac in discovered.items():
        hostname = "Unknown"
        source = ""
        vendor = get_vendor(mac)

        if ip in mdns_names and mdns_names[ip]:
            hostname = mdns_names[ip]
            source = "mDNS"
        elif ip in netbios_names and netbios_names[ip]:
            hostname = netbios_names[ip]
            source = "NetBIOS"
        elif ip in ssdp_names and ssdp_names[ip]:
            hostname = ssdp_names[ip]
            source = "SSDP"
        else:
            # Fallback to unicast reverse DNS
            dns_name = resolve_reverse_dns(ip)
            if dns_name:
                hostname = dns_name
                source = "DNS"
            elif any(w in vendor for w in ["Intel", "Microsoft", "Dell", "Lenovo", "HP"]):
                source = "Firewalled"

        scan_results[ip] = {
            "mac": mac,
            "hostname": hostname,
            "source": source,
            "vendor": vendor,
            "last_seen": current_time
        }

    return scan_results

def scan_worker():
    """Background thread that executes the ARP sweep periodically or on trigger."""
    while True:
        with data_lock:
            active_subnet = scan_state["subnet"]
            scan_state["scanning"] = True
            scan_state["error_message"] = None

        try:
            results = arp_scan(active_subnet)
            with data_lock:
                devices.clear()
                devices.update(results)
                scan_state["last_scan_time"] = time.strftime("%H:%M:%S")
                scan_state["total_found"] = len(results)
                scan_state["scanning"] = False
        except Exception as e:
            with data_lock:
                scan_state["error_message"] = str(e)
                scan_state["scanning"] = False
            print(f"[!] Scan error: {e}")

        # Wait 30 seconds for next scheduled sweep, or wake up immediately if user triggered rescan
        scan_trigger.wait(timeout=30)
        scan_trigger.clear()

HTML_TEMPLATE = """
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
                    <span class="dot {% if state.scanning %}scanning{% endif %}" id="statusDot"></span>
                    <span id="statusText">
                        {% if state.scanning %}
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
                    {% for ip, info in devices.items() %}
                    <tr>
                        <td class="ip">{{ ip }}</td>
                        <td>
                            <div class="hostname-cell">
                                <span class="hostname">{{ info.hostname }}</span>
                                {% if info.source %}
                                <span class="badge badge-{{ info.source.lower() }}">
                                    {% if info.source == 'Firewalled' %}Windows (Firewalled){% else %}{{ info.source }}{% endif %}
                                </span>
                                {% endif %}
                            </div>
                        </td>
                        <td class="vendor {% if 'Private' in info.vendor %}vendor-private{% endif %}">{{ info.vendor }}</td>
                        <td class="mac">{{ info.mac }}</td>
                        <td class="time">{{ info.last_seen }}</td>
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
        // Smooth polling to update device list in place without wiping user input
        async function refreshData() {
            try {
                const res = await fetch('/api/devices');
                if (!res.ok) return;
                const data = await res.json();
                
                // Update status indicator
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

                // Update table rows
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

        // Poll every 5 seconds
        setInterval(refreshData, 5000);
    </script>
</body>
</html>
"""

def sort_devices(dev_dict):
    """Sorts dictionary of devices numerically by IP address."""
    return dict(
        sorted(dev_dict.items(), key=lambda x: [int(p) for p in x[0].split('.')])
    )

@app.route("/", methods=["GET"])
def index():
    with data_lock:
        sorted_devs = sort_devices(devices)
        current_state = dict(scan_state)
    return render_template_string(
        HTML_TEMPLATE,
        devices=sorted_devs,
        state=current_state,
        error=current_state.get("error_message")
    )

@app.route("/scan", methods=["POST"])
def trigger_scan():
    raw_subnet = request.form.get("subnet", "").strip()
    if not raw_subnet:
        raw_subnet = "10.0.0.0/24"

    # Automatically add /24 if user just typed an IP without mask
    if "/" not in raw_subnet:
        raw_subnet = f"{raw_subnet}/24"

    try:
        network = ipaddress.ip_network(raw_subnet, strict=False)
        formatted_subnet = str(network)
        with data_lock:
            scan_state["subnet"] = formatted_subnet
            scan_state["error_message"] = None
        # Wake up background scanner thread immediately
        scan_trigger.set()
    except ValueError as e:
        with data_lock:
            scan_state["error_message"] = f"Invalid subnet CIDR format: '{raw_subnet}'. Please use format like 10.0.0.0/24 or 10.0.0.0/25."

    return redirect(url_for("index"))

@app.route("/api/devices", methods=["GET"])
def api_devices():
    with data_lock:
        return jsonify({
            "devices": sort_devices(devices),
            "state": scan_state
        })

@app.route("/api/set-subnet", methods=["POST"])
def api_set_subnet():
    data = request.get_json(silent=True) or {}
    raw_subnet = data.get("subnet", "").strip()
    if not raw_subnet:
        return jsonify({"error": "Missing subnet"}), 400

    if "/" not in raw_subnet:
        raw_subnet = f"{raw_subnet}/24"

    try:
        network = ipaddress.ip_network(raw_subnet, strict=False)
        formatted_subnet = str(network)
        with data_lock:
            scan_state["subnet"] = formatted_subnet
            scan_state["error_message"] = None
        scan_trigger.set()
        return jsonify({"success": True, "subnet": formatted_subnet})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

if __name__ == "__main__":
    # Start the background ARP + multi-protocol scanner thread
    scanner = threading.Thread(target=scan_worker, daemon=True)
    scanner.start()

    # Bind to 0.0.0.0 so all devices on LAN can view the registry
    app.run(host="0.0.0.0", port=8000)
