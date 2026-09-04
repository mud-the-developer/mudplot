"""Command-line interface for mudplot.

Subcommands:
    mudplot capabilities              print the engine's capabilities (JSON)
    mudplot schema [--out FILE]        print/write the FigureSpec JSON Schema
    mudplot docs [--out FILE]          print/write the Markdown reference docs
    mudplot validate SPEC.json         validate a saved spec, print issues
    mudplot render SPEC.json OUT.png   render a saved spec to an image/PDF

``capabilities``, ``schema``, ``docs`` and ``validate`` need only the pure
core. ``render`` needs the ``[render]`` extra (numpy + matplotlib).
"""

from __future__ import annotations

import argparse
import json
import sys


def _cmd_capabilities(args: argparse.Namespace) -> int:
    from .capabilities import capabilities

    print(json.dumps(capabilities(), indent=2, ensure_ascii=False))
    return 0


def _cmd_schema(args: argparse.Namespace) -> int:
    from .schema import json_schema

    text = json.dumps(json_schema(), indent=2, ensure_ascii=False)
    if args.out:
        from pathlib import Path

        Path(args.out).write_text(text, encoding="utf-8")
        print(f"wrote {args.out}", file=sys.stderr)
    else:
        print(text)
    return 0


def _cmd_docs(args: argparse.Namespace) -> int:
    from .docs import reference_markdown

    text = reference_markdown()
    if args.out:
        from pathlib import Path

        Path(args.out).write_text(text, encoding="utf-8")
        print(f"wrote {args.out}", file=sys.stderr)
    else:
        print(text)
    return 0


def _cmd_validate(args: argparse.Namespace) -> int:
    from .io import load_spec
    from .validate import validate

    spec = load_spec(args.spec)
    issues = validate(spec)
    if not issues:
        print("OK: no issues found")
        return 0
    for issue in issues:
        print(f"- {issue}")
    return 1


def _cmd_render(args: argparse.Namespace) -> int:
    from ._render import save
    from .io import load_spec

    spec = load_spec(args.spec)
    save(spec, args.out)
    print(f"wrote {args.out}", file=sys.stderr)
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="mudplot", description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)

    sp = sub.add_parser("capabilities", help="print engine capabilities as JSON")
    sp.set_defaults(func=_cmd_capabilities)

    sp = sub.add_parser("schema", help="print/write the FigureSpec JSON Schema")
    sp.add_argument("--out", help="write schema to this file instead of stdout")
    sp.set_defaults(func=_cmd_schema)

    sp = sub.add_parser("docs", help="print/write the Markdown reference docs")
    sp.add_argument("--out", help="write docs to this file instead of stdout")
    sp.set_defaults(func=_cmd_docs)

    sp = sub.add_parser("validate", help="validate a saved .mplot.json spec")
    sp.add_argument("spec", help="path to a .mplot.json file")
    sp.set_defaults(func=_cmd_validate)

    sp = sub.add_parser("render", help="render a saved spec to an image/PDF")
    sp.add_argument("spec", help="path to a .mplot.json file")
    sp.add_argument("out", help="output path (.png/.pdf/.svg)")
    sp.set_defaults(func=_cmd_render)

    return p


# Exceptions expected from ordinary user mistakes (bad path, malformed JSON,
# invalid spec/action content) get a clean one-line stderr message + exit
# code 1 instead of a raw Python traceback -- much friendlier for shell
# scripts and agents parsing the output. Anything else still raises normally
# (through --debug or when not caught), since that indicates a real bug
# worth a full traceback rather than a swallowed one-liner.
_USER_ERRORS = (
    FileNotFoundError,
    IsADirectoryError,
    PermissionError,
    json.JSONDecodeError,
    ValueError,
    TypeError,
)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except _USER_ERRORS as e:
        print(f"error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
