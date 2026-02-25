import argparse
from typing import List, Optional


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="typhonbreaker")
    sub = parser.add_subparsers(dest="command", required=True)

    p_webui = sub.add_parser("webui", help="Start the Typhon WebUI")
    p_webui.add_argument("--host", default="0.0.0.0")
    p_webui.add_argument("--port", default=6240, type=int)
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = _build_parser().parse_args(argv)

    if args.command == "webui":
        from Typhon.webui.app import run

        run(host=args.host, port=args.port)
        return 0

    raise SystemExit(f"unknown command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
