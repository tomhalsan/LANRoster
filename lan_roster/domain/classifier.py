from lan_roster.domain.models import DeviceCategory, HostnameSource


class DeviceClassifier:
    """Domain service classifying devices based on network heuristics and signals."""

    ROUTER_GATEWAY_VENDORS = (
        "arris",
        "cisco",
        "netgear",
        "ubiquiti",
        "linksys",
        "technicolor",
        "actiontec",
        "mikrotik",
        "tp-link",
        "d-link",
        "synology",
        "eero",
        "huawei",
        "zyxel",
        "sagemcom",
    )

    ROUTER_KEYWORDS = (
        "router",
        "gateway",
        "modem",
        "accesspoint",
        "access-point",
        "unifi",
        "ubnt",
        "wifi",
        "wlan",
        "extender",
        "mesh",
    )

    MOBILE_KEYWORDS = (
        "iphone",
        "ipad",
        "ipod",
        "galaxy",
        "pixel",
        "android",
        "mobile",
        "phone",
        "oneplus",
        "xiaomi",
        "redmi",
    )

    COMPUTER_KEYWORDS = (
        "pc",
        "desktop",
        "laptop",
        "macbook",
        "mbp",
        "imac",
        "mac-mini",
        "macmini",
        "macpro",
        "workstation",
        "thinkpad",
        "latitude",
        "precision",
        "surface",
        "optiplex",
        "xps",
    )

    COMPUTER_VENDORS = (
        "microsoft",
        "dell",
        "lenovo",
        "intel",
        "asus",
        "acer",
    )

    SMART_TV_KEYWORDS = (
        "tv",
        "appletv",
        "apple-tv",
        "roku",
        "chromecast",
        "firetv",
        "firestick",
        "bravia",
        "vizio",
        "tizen",
        "webos",
        "shield",
    )

    SMART_TV_VENDORS = (
        "roku",
        "vizio",
        "tcl",
        "hisense",
    )

    PRINTER_KEYWORDS = (
        "printer",
        "print",
        "laserjet",
        "deskjet",
        "officejet",
        "photosmart",
        "copier",
        "mfp",
    )

    PRINTER_VENDORS = (
        "brother",
        "epson",
        "canon",
        "xerox",
        "lexmark",
        "ricoh",
        "konica",
    )

    GAMING_KEYWORDS = (
        "playstation",
        "ps4",
        "ps5",
        "xbox",
        "nintendo",
        "switch",
    )

    GAMING_VENDORS = (
        "sony interactive",
        "nintendo",
    )

    SMART_HOME_KEYWORDS = (
        "sonos",
        "homepod",
        "echo",
        "alexa",
        "nest",
        "hue",
        "ring",
        "smartplug",
        "camera",
        "cam",
        "thermostat",
        "roomba",
        "bulb",
    )

    SMART_HOME_VENDORS = (
        "sonos",
        "amazon technologies",
        "philips lighting",
        "signify",
        "nest labs",
        "tuya",
        "espressif",
        "wemo",
        "lutron",
        "irobot",
    )

    @classmethod
    def classify(
        cls,
        ip: str,
        hostname: str = "",
        vendor: str = "",
        source: HostnameSource = HostnameSource.UNKNOWN,
    ) -> DeviceCategory:
        host = (hostname or "").lower()
        v = (vendor or "").lower()

        # 1. Printers (check before computer/HP)
        if any(k in host for k in cls.PRINTER_KEYWORDS) or any(k in v for k in cls.PRINTER_VENDORS):
            return DeviceCategory.PRINTER

        # 2. Gaming Consoles
        if any(k in host for k in cls.GAMING_KEYWORDS) or any(k in v for k in cls.GAMING_VENDORS):
            return DeviceCategory.GAMING

        # 3. Smart TVs and Streaming
        if any(k in host for k in cls.SMART_TV_KEYWORDS) or any(k in v for k in cls.SMART_TV_VENDORS):
            return DeviceCategory.SMART_TV
        if "google cast" in v or "google cast" in host:
            return DeviceCategory.SMART_TV
        if ("lg electronics" in v or "samsung electronics" in v) and any(
            k in host for k in ("tv", "display", "media", "smart")
        ):
            return DeviceCategory.SMART_TV

        # 4. Smart Home / Audio / IoT
        if any(k in host for k in cls.SMART_HOME_KEYWORDS) or any(k in v for k in cls.SMART_HOME_VENDORS):
            return DeviceCategory.SMART_HOME

        # 5. Mobile Devices
        # Apple iOS probe specifically tags "Apple, Inc. (iOS)"
        if "ios" in v:
            return DeviceCategory.MOBILE
        if any(k in host for k in cls.MOBILE_KEYWORDS):
            return DeviceCategory.MOBILE
        if "samsung" in v and not any(k in host for k in ("tv", "display")):
            return DeviceCategory.MOBILE

        # 6. Network Infrastructure / Gateway
        is_gateway_ip = ip.endswith(".1") or ip.endswith(".254")
        if any(k in host for k in cls.ROUTER_KEYWORDS):
            return DeviceCategory.NETWORK
        if is_gateway_ip and any(k in v for k in cls.ROUTER_GATEWAY_VENDORS):
            return DeviceCategory.NETWORK

        # 7. Computers & Workstations
        if source == HostnameSource.NETBIOS or source == HostnameSource.FIREWALLED:
            return DeviceCategory.COMPUTER
        if any(k in host for k in cls.COMPUTER_KEYWORDS):
            return DeviceCategory.COMPUTER
        if any(k in v for k in cls.COMPUTER_VENDORS):
            return DeviceCategory.COMPUTER
        if "hp" in v and not any(k in host for k in cls.PRINTER_KEYWORDS):
            return DeviceCategory.COMPUTER

        # 8. Apple heuristic fallback
        if "apple" in v:
            if any(k in host for k in ("mac", "book", "mini", "imac")):
                return DeviceCategory.COMPUTER
            elif "tv" in host:
                return DeviceCategory.SMART_TV
            else:
                return DeviceCategory.MOBILE

        # 9. Generic / Unknown
        return DeviceCategory.GENERIC
