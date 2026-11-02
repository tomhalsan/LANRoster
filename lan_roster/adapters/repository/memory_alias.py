import threading
from typing import Dict
from lan_roster.domain.models import DeviceAlias
from lan_roster.ports.alias_repository import DeviceAliasRepositoryPort


class InMemoryAliasRepository(DeviceAliasRepositoryPort):
    """Thread-safe in-memory adapter for device aliases."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._aliases: Dict[str, DeviceAlias] = {}

    def get_alias(self, mac: str) -> DeviceAlias | None:
        norm = mac.strip().upper()
        with self._lock:
            return self._aliases.get(norm)

    def get_all_aliases(self) -> Dict[str, DeviceAlias]:
        with self._lock:
            return dict(self._aliases)

    def save_alias(self, mac: str, nickname: str, notes: str) -> DeviceAlias:
        norm = mac.strip().upper()
        alias = DeviceAlias(mac=norm, nickname=nickname.strip(), notes=notes.strip())
        with self._lock:
            self._aliases[norm] = alias
        return alias

    def delete_alias(self, mac: str) -> None:
        norm = mac.strip().upper()
        with self._lock:
            self._aliases.pop(norm, None)
