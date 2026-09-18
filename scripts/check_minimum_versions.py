# /// script
# requires-python = ">=3.10,<3.11"
# dependencies = [
#   "matplotlib==3.8.0",
#   "numpy==1.23.0",
#   "pytest==9.0.3",
# ]
# ///
"""Run the render/layout contract against the declared minimum dependencies."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
TESTS = (
    "tests/test_layers.py",
    "tests/test_layout.py",
    "tests/test_new_layers.py",
    "tests/test_stabilization.py",
    "tests/test_references.py",
)


def main() -> int:
    os.chdir(ROOT)
    sys.path.insert(0, str(ROOT))
    return pytest.main(["-q", "--disable-warnings", "-m", "not browser", *TESTS])


if __name__ == "__main__":
    raise SystemExit(main())
