"""``python -m dashboard`` — build the static site, or run the live editor."""

from __future__ import annotations

import argparse
import sys


def _cmd_build(args: argparse.Namespace) -> int:
    from .site import build_site

    out = build_site(args.out)
    print(f"built site at {out}/index.html", file=sys.stderr)
    return 0


def _cmd_serve(args: argparse.Namespace) -> int:
    from .editor_server import serve

    serve(host=args.host, port=args.port)
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="dashboard")
    sub = parser.add_subparsers(dest="command")

    sp = sub.add_parser("build", help="build the static docs+gallery site")
    sp.add_argument("--out", default="dashboard/site_build", help="output directory")
    sp.set_defaults(func=_cmd_build)

    sp = sub.add_parser("serve", help="run the local interactive editor")
    sp.add_argument("--host", default="127.0.0.1")
    sp.add_argument("--port", type=int, default=8765)
    sp.set_defaults(func=_cmd_serve)

    # `python -m dashboard --out DIR` (no subcommand) keeps working as a
    # shorthand for `build`, so the pre-existing CLI/CI usage is unaffected.
    parser.add_argument("--out", default="dashboard/site_build", help=argparse.SUPPRESS)

    args = parser.parse_args(argv)
    if args.command is None:
        return _cmd_build(args)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
