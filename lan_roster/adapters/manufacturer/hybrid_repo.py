import urllib.request
from typing import Dict
from lan_roster.ports.manufacturer import ManufacturerRepositoryPort


class HybridManufacturerRepository(ManufacturerRepositoryPort):
    """
    Adapter implementing hardware manufacturer lookup using:
    1. Local privacy/randomized bit detection.
    2. Curated high-performance offline OUI database.
    3. In-memory dynamic cache.
    4. Online OUI API fallback.
    """

    OUI_MAP: Dict[str, str] = {
        # Arris / CommScope / Comcast Xfinity Gateways
        "E8CD15": "Arris / Comcast Gateway",
        "001DD0": "Arris / Comcast",
        "001E46": "Arris / Comcast",
        "24767D": "Arris / Comcast",
        "44AA50": "Arris / Comcast",
        "5CE30E": "Arris / Comcast",
        "903EAB": "Arris / Comcast",
        "A41588": "Arris / Comcast",
        "B81619": "Arris / Comcast",
        "CC65AD": "Arris / Comcast",

        # Apple
        "5C9BA6": "Apple", "000393": "Apple", "000502": "Apple", "000A27": "Apple",
        "000A95": "Apple", "000D93": "Apple", "0010FA": "Apple", "001124": "Apple",
        "001451": "Apple", "0016CB": "Apple", "0017F2": "Apple", "0019E3": "Apple",
        "001B63": "Apple", "001CB3": "Apple", "001D4F": "Apple", "001E52": "Apple",
        "001EC2": "Apple", "001F5B": "Apple", "001FF3": "Apple", "0021E9": "Apple",
        "002241": "Apple", "002312": "Apple", "002332": "Apple", "00236C": "Apple",
        "002436": "Apple", "002500": "Apple", "00254B": "Apple", "0025BC": "Apple",
        "002608": "Apple", "00264A": "Apple", "0026B0": "Apple", "0026BB": "Apple",
        "109397": "Apple", "109ADD": "Apple", "14109F": "Apple", "147DDA": "Apple",
        "1499E2": "Apple", "14C213": "Apple", "18AF61": "Apple", "18EE69": "Apple",
        "20768F": "Apple", "28CFDA": "Apple", "3408BC": "Apple", "34159E": "Apple",
        "34363B": "Apple", "38CA84": "Apple", "3C0754": "Apple", "3C15C2": "Apple",
        "3C22FB": "Apple", "406C8F": "Apple", "4098AD": "Apple", "40A6D9": "Apple",
        "442A60": "Apple", "48437C": "Apple", "48605F": "Apple", "48D705": "Apple",
        "4C3275": "Apple", "50BC96": "Apple", "542696": "Apple", "54724F": "Apple",
        "5855CA": "Apple", "600308": "Apple", "6030D4": "Apple", "60334B": "Apple",
        "606720": "Apple", "64200C": "Apple", "6476BA": "Apple", "685B35": "Apple",
        "6C4008": "Apple", "701124": "Apple", "703EAC": "Apple", "70708B": "Apple",
        "70EF00": "Apple", "741BB2": "Apple", "748114": "Apple", "7831C1": "Apple",
        "784F43": "Apple", "787B8A": "Apple", "78CA39": "Apple", "7C04D0": "Apple",
        "7C6D62": "Apple", "804971": "Apple", "80929F": "Apple", "80E650": "Apple",
        "842E27": "Apple", "88665A": "Apple", "8C8590": "Apple", "9027E4": "Apple",
        "907240": "Apple", "9801A7": "Apple", "9810E8": "Apple", "98B8E3": "Apple",
        "9C04EB": "Apple", "A45E60": "Apple", "A4C361": "Apple", "A85B78": "Apple",
        "AC1F74": "Apple", "B418D1": "Apple", "B8098A": "Apple", "B87826": "Apple",
        "BC52B7": "Apple", "C81EE7": "Apple", "C82A14": "Apple", "C8334B": "Apple",
        "CC088D": "Apple", "DC2B61": "Apple", "DC3714": "Apple", "DC5285": "Apple",
        "E06678": "Apple", "E425E7": "Apple", "E4CE8F": "Apple", "E8802E": "Apple",
        "EC3586": "Apple", "F01898": "Apple", "F07960": "Apple", "F40F24": "Apple",
        "F437B7": "Apple", "F82793": "Apple", "F8E903": "Apple", "C8D083": "Apple",

        # Google
        "14C67D": "Google", "001A11": "Google", "1C56FE": "Google", "3C5A37": "Google",
        "546009": "Google", "703ACB": "Google", "D86C63": "Google", "F40304": "Google",
        "F4F5E8": "Google", "D4351D": "Google Nest",

        # Amazon
        "20BEB8": "Amazon", "CCAFE3": "Amazon", "50BBB5": "Amazon", "381F26": "Amazon",
        "00FC8B": "Amazon", "44650D": "Amazon", "6837E9": "Amazon", "747548": "Amazon",
        "84D6D0": "Amazon", "AC63BE": "Amazon", "40B4CD": "Amazon", "FC65DE": "Amazon",

        # Sony / PlayStation
        "605BB4": "Sony Interactive (PlayStation)", "00041F": "Sony", "001315": "Sony",
        "0015C1": "Sony", "0019C5": "Sony", "001D0D": "Sony", "0024BE": "Sony",
        "F8461C": "Sony", "904748": "Sony Interactive (PlayStation 5)",

        # Microsoft
        "000D3A": "Microsoft", "00125A": "Microsoft", "00155D": "Microsoft", "0017FA": "Microsoft",
        "001DD8": "Microsoft", "002248": "Microsoft", "0025AE": "Microsoft", "281878": "Microsoft",
        "7C1E52": "Microsoft", "DC9840": "Microsoft", "28C63F": "Microsoft Surface",

        # Samsung
        "0007AB": "Samsung", "0012FB": "Samsung", "001599": "Samsung", "001632": "Samsung",
        "08373D": "Samsung", "14BB6E": "Samsung", "28987B": "Samsung", "34C9F0": "Samsung",
        "508569": "Samsung", "64B5C6": "Samsung", "8C71F8": "Samsung", "94652D": "Samsung",
        "B857D8": "Samsung", "C819F7": "Samsung", "CC07AB": "Samsung", "D059E4": "Samsung",

        # Networking & IoT
        "D80D17": "TP-Link", "002719": "TP-Link", "50C7BF": "TP-Link", "60A44C": "TP-Link",
        "704F57": "TP-Link", "98DAC4": "TP-Link", "C006C3": "TP-Link", "E848B8": "TP-Link",
        "080581": "Roku", "20F543": "Roku", "2CAA8E": "Roku", "84EAED": "Roku",
        "AC3A7A": "Roku", "B0EE45": "Roku", "D83134": "Roku",
        "B827EB": "Raspberry Pi", "DCA632": "Raspberry Pi", "E45F01": "Raspberry Pi",
        "28CDC1": "Raspberry Pi",

        # Intel (Windows PC / Laptops)
        "CC1531": "Intel (Windows PC)", "801316": "Intel (Windows PC)",
        "0002B3": "Intel", "000347": "Intel", "000423": "Intel", "000E0C": "Intel",
        "001302": "Intel", "001500": "Intel", "8086F2": "Intel", "843497": "Intel",
        "001B21": "Intel", "001E67": "Intel", "00215C": "Intel", "0022FB": "Intel",
        "002314": "Intel", "0024D7": "Intel", "0026C7": "Intel", "3413E8": "Intel",
        "4851C5": "Intel", "5891CF": "Intel", "6805CA": "Intel", "A44CC8": "Intel",
        "C85B76": "Intel",

        # PC Manufacturers (Dell, HP, Lenovo)
        "001422": "Dell PC", "001A6B": "Dell PC", "180373": "Dell PC", "24B6FD": "Dell PC",
        "44A842": "Dell PC", "B8AC6F": "Dell PC", "D4BEB9": "Dell PC", "F8BC12": "Dell PC",
        "001B9A": "Lenovo PC", "002186": "Lenovo PC", "00238C": "Lenovo PC", "002655": "Lenovo PC",
        "047D7B": "Lenovo PC", "207693": "Lenovo PC", "3C970E": "Lenovo PC", "54EE75": "Lenovo PC",
        "68F728": "Lenovo PC", "8CE9B4": "Lenovo PC",
        "001635": "HP PC", "001708": "HP PC", "0018FE": "HP PC", "0019BB": "HP PC",
        "10604B": "HP PC", "1458D0": "HP PC", "186024": "HP PC", "28924A": "HP PC",
        "308D99": "HP PC", "3863BB": "HP PC", "3C5282": "HP PC", "40A8F0": "HP PC",

        # Other Local Devices & Peripherals
        "E42686": "DWnet (IP Camera)",
        "3C62F0": "Sercomm (Comcast Pod)",
        "2C641F": "Vizio Smart TV",
        "D4808B": "Seiko Epson Printer",
    }

    def __init__(self) -> None:
        self._cache: Dict[str, str] = {}

    def get_manufacturer(self, mac_address: str) -> str:
        clean = mac_address.replace(":", "").replace("-", "").upper()
        if len(clean) >= 6:
            first_byte = int(clean[:2], 16)
            # Evaluate locally administered / randomized MAC bit
            if first_byte & 0x02:
                return "Private/Randomized MAC"

            prefix = clean[:6]
            if prefix in self.OUI_MAP:
                return self.OUI_MAP[prefix]

            if prefix in self._cache:
                return self._cache[prefix]

            # Online lookup fallback
            try:
                req = urllib.request.Request(
                    f"https://api.macvendors.com/{prefix}",
                    headers={"User-Agent": "LANRoster/1.0"},
                )
                with urllib.request.urlopen(req, timeout=0.8) as resp:
                    vendor_name = resp.read().decode("utf-8").strip()
                    self._cache[prefix] = vendor_name
                    return vendor_name
            except Exception:
                self._cache[prefix] = "Generic Device"

        return "Generic Device"

