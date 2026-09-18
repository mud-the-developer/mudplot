# /// script
# requires-python = ">=3.10"
# dependencies = ["pip-audit==2.10.1"]
# ///
"""Audit every committed Python dependency lock for known vulnerabilities."""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MINIMUM_SCRIPT = ROOT / "scripts" / "check_minimum_versions.py"
AUDIT_SCRIPT = Path(__file__).resolve()


def main() -> int:
    exports = (
        ("root", "--all-extras", "--no-emit-project"),
        ("minimum", "--script", str(MINIMUM_SCRIPT)),
        ("audit", "--script", str(AUDIT_SCRIPT)),
    )
    with tempfile.TemporaryDirectory() as directory:
        for name, *selection in exports:
            requirements = Path(directory) / f"{name}.txt"
            subprocess.run(
                [
                    "uv",
                    "export",
                    "--locked",
                    *selection,
                    "--output-file",
                    str(requirements),
                ],
                cwd=ROOT,
                stdout=subprocess.DEVNULL,
                check=True,
            )
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pip_audit",
                    "--require-hashes",
                    "--disable-pip",
                    "--requirement",
                    str(requirements),
                ],
                cwd=ROOT,
                check=True,
            )
    print("Python dependency audits OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
