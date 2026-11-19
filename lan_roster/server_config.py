import argparse
import sys
from dataclasses import dataclass
from typing import Sequence, TextIO


@dataclass(frozen=True)
class ServerConfig:
    """Server network binding configuration."""

    host: str = "127.0.0.1"
    port: int = 8000

    @property
    def is_loopback(self) -> bool:
        """Returns True if the bind host is a local loopback address."""
        return self.host in ("127.0.0.1", "localhost", "::1")


def parse_server_config(argv: Sequence[str] | None = None) -> ServerConfig:
    """
    Parses command-line arguments for server binding policy.

    Defaults to localhost (127.0.0.1:8000) for safe local-only access.
    The --lan flag explicitly opt-in binds to all interfaces (0.0.0.0:8000).
    """
    parser = argparse.ArgumentParser(
        prog="lan-roster",
        description="LANRoster — Real-time local network device directory and scanner.",
    )
    parser.add_argument(
        "--lan",
        action="store_true",
        help=(
            "Expose the web server to the local network (binds to 0.0.0.0). "
            "WARNING: Provides no authentication or CSRF protection."
        ),
    )

    args = parser.parse_args(argv)

    host = "0.0.0.0" if args.lan else "127.0.0.1"
    return ServerConfig(host=host, port=8000)


def format_startup_banner(config: ServerConfig) -> str:
    """Formats the startup banner and any security warnings for the selected configuration."""
    if config.is_loopback:
        return (
            f"[*] Starting LANRoster on {config.host}:{config.port} (localhost only)\n"
            f"[*] Dashboard URL: http://{config.host}:{config.port}\n"
        )

    return (
        "\n"
        "[!] ========================================================================\n"
        "[!] WARNING: LAN exposure active!\n"
        f"[!] LANRoster is listening on {config.host}:{config.port} (all network interfaces).\n"
        "[!] This application provides NO authentication or CSRF protection.\n"
        "[!] Any device that can reach this service may view and modify device roster state.\n"
        "[!] Run only on a trusted, private local network. Never expose to the public internet.\n"
        "[!] ========================================================================\n"
        f"[*] Starting LANRoster on {config.host}:{config.port}\n"
    )


def print_startup_banner(config: ServerConfig, out: TextIO | None = None) -> None:
    """Outputs the startup banner to the specified text stream (defaults to sys.stdout)."""
    target = out if out is not None else sys.stdout
    target.write(format_startup_banner(config))
    target.flush()
