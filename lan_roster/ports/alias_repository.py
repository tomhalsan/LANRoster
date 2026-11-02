from abc import ABC, abstractmethod
from typing import Dict
from lan_roster.domain.models import DeviceAlias


class DeviceAliasRepositoryPort(ABC):
    """
    Port interface for persisting user-defined nicknames and notes by MAC address.
    Abstracts durable storage of device customizations.
    """

    @abstractmethod
    def get_alias(self, mac: str) -> DeviceAlias | None:
        """Fetches alias record for a given MAC address (case-insensitive)."""
        pass

    @abstractmethod
    def get_all_aliases(self) -> Dict[str, DeviceAlias]:
        """Fetches all stored aliases keyed by normalized uppercase MAC address."""
        pass

    @abstractmethod
    def save_alias(self, mac: str, nickname: str, notes: str) -> DeviceAlias:
        """Stores or updates an alias record for a MAC address."""
        pass

    @abstractmethod
    def delete_alias(self, mac: str) -> None:
        """Deletes an alias record for a MAC address."""
        pass
