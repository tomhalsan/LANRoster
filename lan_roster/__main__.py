from typing import Sequence

from lan_roster.bootstrap import bootstrap
from lan_roster.server_config import parse_server_config, print_startup_banner


def main(argv: Sequence[str] | None = None) -> None:
    """
    Console script and module entry point for LANRoster.

    Parses command-line configuration, prints startup status,
    bootstraps application dependencies, and starts the web server.
    """
    config = parse_server_config(argv)
    print_startup_banner(config)
    app = bootstrap()
    app.run(host=config.host, port=config.port)


if __name__ == "__main__":
    main()
