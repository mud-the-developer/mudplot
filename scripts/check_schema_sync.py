"""CI helper: verify schemas/*.json and docs/REFERENCE.md are up to date.

Regenerates each artifact into a temp dir and diffs it against the checked-in
copy, so a spec/capabilities change without a matching regeneration fails CI
instead of silently drifting (Rust consumers rely on ``schemas/`` being the
single source of truth).
"""

from __future__ import annotations

import filecmp
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# (subcommand, checked-in path, supports --out).
# ``capabilities`` has no --out flag, so it's regenerated via stdout
# redirection instead -- matching exactly how schemas/capabilities.json was
# produced (`python -m mudplot capabilities > schemas/capabilities.json`),
# since piping through ``print()`` adds a trailing newline that ``--out``
# does not, and comparing the two inconsistently would give false positives.
_TARGETS = [
    ("schema", "schemas/figure_spec.schema.json", True),
    ("capabilities", "schemas/capabilities.json", False),
    ("docs", "docs/REFERENCE.md", True),
]


def _regenerate(subcommand: str, out_path: Path, use_out_flag: bool) -> None:
    base_cmd = [sys.executable, "-m", "mudplot", subcommand]
    if use_out_flag:
        subprocess.run([*base_cmd, "--out", str(out_path)], cwd=REPO_ROOT, check=True)
    else:
        with out_path.open("w", encoding="utf-8") as f:
            subprocess.run(base_cmd, cwd=REPO_ROOT, stdout=f, check=True)


def main() -> int:
    ok = True
    with tempfile.TemporaryDirectory() as tmp:
        for subcommand, checked_in, use_out_flag in _TARGETS:
            out_path = Path(tmp) / Path(checked_in).name
            _regenerate(subcommand, out_path, use_out_flag)
            checked_in_path = REPO_ROOT / checked_in
            if not filecmp.cmp(out_path, checked_in_path, shallow=False):
                flag = " --out <path>" if use_out_flag else " > <path>"
                print(
                    f"error: {checked_in} is out of date; regenerate with:\n"
                    f"  python -m mudplot {subcommand}{flag}",
                    file=sys.stderr,
                )
                ok = False
            else:
                print(f"OK: {checked_in} is in sync")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
