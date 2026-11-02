from lan_roster.domain.exceptions import LANRosterException
from lan_roster.domain.models import DeviceAlias
from lan_roster.ports.alias_repository import DeviceAliasRepositoryPort
from lan_roster.ports.repository import DeviceRepositoryPort


class UpdateDeviceAliasUseCase:
    """
    Use case for setting or clearing user-defined nicknames and notes for a device by MAC address.
    Propagates the customization to durable alias storage and active device records.
    """

    def __init__(
        self,
        alias_repo: DeviceAliasRepositoryPort,
        device_repo: DeviceRepositoryPort,
    ) -> None:
        self.alias_repo = alias_repo
        self.device_repo = device_repo

    def execute(self, mac: str, nickname: str = "", notes: str = "") -> DeviceAlias:
        if not mac or not mac.strip():
            raise LANRosterException("MAC address cannot be empty.")

        norm_mac = mac.strip().upper()
        clean_nickname = nickname.strip()
        clean_notes = notes.strip()

        alias = self.alias_repo.save_alias(
            mac=norm_mac,
            nickname=clean_nickname,
            notes=clean_notes,
        )

        # Update matching devices currently in device repository
        devices = self.device_repo.get_devices()
        updated = []
        for dev in devices.values():
            if dev.mac.upper() == norm_mac:
                dev.nickname = clean_nickname
                dev.notes = clean_notes
                updated.append(dev)

        if updated:
            self.device_repo.save_devices(updated)

        return alias
