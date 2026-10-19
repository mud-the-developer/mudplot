"""Reject missing/skipped required CI paths; local optional tests may still skip."""

from __future__ import annotations

import argparse
import json
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path

MAX_JUNIT_BYTES = 64 * 1024 * 1024
PGF = ("test_references", "test_pgf_export_emits_figcite_and_href_macros")
BROWSER = ("test_editor_browser", "test_dragging_the_legend_moves_it_and_persists")
PAPER = "test_exported_pgf_compiles_into_a_real_paper"
TECTONIC = ("test_references", f"{PAPER}[tectonic]")
TEX_MATRIX = tuple(
    ("test_references", f"{PAPER}[{engine}]")
    for engine in ("pdflatex+bibtex", "lualatex+bibtex", "lualatex+biblatex")
)
REQUIRED = {
    "ci": (BROWSER, PGF, TECTONIC),
    "minimum": (PGF, TECTONIC),
    "tex": TEX_MATRIX,
    "release": (BROWSER, PGF, TECTONIC, *TEX_MATRIX),
}


def audit_report(path: Path, profile: str) -> dict:
    outcomes = defaultdict(list)
    counts: Counter[str] = Counter()
    with path.open("rb") as report:
        raw = report.read(MAX_JUNIT_BYTES + 1)
    if len(raw) > MAX_JUNIT_BYTES:
        raise ValueError("JUnit report exceeds 64 MiB")
    text = raw.decode("utf-8-sig")
    if "\x00" in text or any(tag in text.lower() for tag in ("<!doctype", "<!entity")):
        raise ValueError("JUnit must be UTF-8 without NUL, DTD or entity declarations")
    for case in ET.fromstring(text).iter("testcase"):
        skipped = case.find("skipped")
        if case.find("failure") is not None or case.find("error") is not None:
            status = "failed"
        elif skipped is not None:
            status = "xfailed" if "xfail" in skipped.get("type", "") else "skipped"
        else:
            status = "passed"
        counts[status] += 1
        identity = (case.get("classname", "").rsplit(".", 1)[-1], case.get("name", ""))
        outcomes[identity].append(status)
    required = [
        {"module": module, "name": name, "outcomes": outcomes[(module, name)]}
        for module, name in REQUIRED[profile]
    ]
    return {
        "profile": profile,
        "total": sum(counts.values()),
        "counts": dict(counts),
        "required": required,
        "ok": counts["failed"] == 0
        and all(row["outcomes"] == ["passed"] for row in required),
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("profile", choices=REQUIRED)
    parser.add_argument("report", type=Path)
    args = parser.parse_args(argv)
    try:
        result = audit_report(args.report, args.profile)
    except (OSError, ET.ParseError, ValueError) as error:
        result = {"profile": args.profile, "ok": False, "error": type(error).__name__}
    print(json.dumps(result, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
