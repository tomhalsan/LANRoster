class LANRosterException(Exception):
    """Base exception for all domain errors."""
    pass


class InvalidSubnetException(LANRosterException):
    """Raised when an invalid CIDR subnet string is provided."""
    pass


class ScanExecutionException(LANRosterException):
    """Raised when an underlying network scan fails."""
    pass

