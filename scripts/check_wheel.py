"""CI helper: build a wheel and verify it packages py.typed + LICENSE.

Kept as a real script file (not an inline YAML heredoc) so it's normal,
readable, testable Python -- and so it can't trip up YAML's block-scalar
indentation rules the way an inline heredoc can.
"""

from __future__ import annotations

import glob
import subprocess
import sys
import tempfile
import zipfile


def main() -> int:
    with tempfile.TemporaryDirectory() as out_dir:
        subprocess.run(
            [sys.executable, "-m", "build", "--wheel", "--outdir", out_dir, "."],
            check=True,
        )
        wheels = glob.glob(f"{out_dir}/*.whl")
        if not wheels:
            print("error: no wheel was built", file=sys.stderr)
            return 1
        wheel = wheels[0]
        names = zipfile.ZipFile(wheel).namelist()

        missing = []
        if "mudplot/py.typed" not in names:
            missing.append("mudplot/py.typed")
        if not any(n.endswith("licenses/LICENSE") for n in names):
            missing.append("*licenses/LICENSE")
        if missing:
            print(f"error: wheel is missing {missing}", file=sys.stderr)
            print("wheel contents:", names, file=sys.stderr)
            return 1

        print(f"wheel packaging OK: {wheel}")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
