import ipaddress
from lan_roster.domain.exceptions import InvalidSubnetException
from lan_roster.ports.repository import DeviceRepositoryPort


class UpdateSubnetUseCase:
    """Use case for validating and updating the target scanning subnet."""

    def __init__(self, device_repo: DeviceRepositoryPort) -> None:
        self.device_repo = device_repo

    def execute(self, raw_subnet: str) -> str:
        clean_subnet = raw_subnet.strip() if raw_subnet else "10.0.0.0/24"

        # If user typed an IP without CIDR mask (e.g. 10.0.0.1 or 10.0.0.0), default to /24
        if "/" not in clean_subnet:
            clean_subnet = f"{clean_subnet}/24"

        try:
            network = ipaddress.ip_network(clean_subnet, strict=False)
            normalized = str(network)
            self.device_repo.update_scan_state(
                subnet=normalized,
                error_message=None,
            )
            return normalized
        except ValueError as e:
            err = f"Invalid subnet CIDR format: '{raw_subnet}'. Please use format like 10.0.0.0/24 or 10.0.0.0/25."
            self.device_repo.update_scan_state(error_message=err)
            raise InvalidSubnetException(err) from e

