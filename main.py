from __future__ import annotations

import argparse
import logging

from tcp_server import TcpLuServer


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="TCP-сервер LU-разложения",
        add_help=False,
    )
    parser._optionals.title = "параметры"
    parser.add_argument("-h", "--help", action="help", help="показать эту справку и выйти")
    parser.add_argument("--host", default="0.0.0.0", help="Адрес для прослушивания")
    parser.add_argument("--port", type=int, default=6767, help="TCP-порт для прослушивания")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    server = TcpLuServer(args.host, args.port)
    server.serve_forever()


if __name__ == "__main__":
    main()
