"""Fail a release when its tag, Python, Rust, or changelog versions drift."""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

import mudplot

ROOT = Path(__file__).resolve().parent.parent


def _declared_version(path: Path, section: str) -> str:
    text = path.read_text(encoding="utf-8")
    marker = f"[{section}]"
    if marker not in text:
        raise ValueError(f"{path.name} has no [{section}] section")
    block = text.split(marker, 1)[1].split("\n[", 1)[0]
    match = re.search(r'^version = "([^"]+)"', block, re.MULTILINE)
    if not match:
        raise ValueError(f"{path.name} [{section}] has no version")
    return match.group(1)


def _cargo_lock_version() -> str:
    text = (ROOT / "mudplot-editor" / "Cargo.lock").read_text(encoding="utf-8")
    for block in text.split("[[package]]"):
        if re.search(r'^name = "mudplot-editor"$', block, re.MULTILINE):
            match = re.search(r'^version = "([^"]+)"$', block, re.MULTILINE)
            if match:
                return match.group(1)
    raise ValueError("Cargo.lock has no mudplot-editor package")


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    tag = args[0] if args else os.environ.get("GITHUB_REF_NAME", "")
    expected_tag = f"v{mudplot.__version__}"
    issues = []
    if tag != expected_tag:
        issues.append(f"tag is {tag!r}, expected {expected_tag!r}")
    project_version = _declared_version(ROOT / "pyproject.toml", "project")
    rust_version = _declared_version(ROOT / "mudplot-editor" / "Cargo.toml", "package")
    versions = (
        ("pyproject", project_version),
        ("Rust", rust_version),
        ("Cargo.lock", _cargo_lock_version()),
    )
    for source, version in versions:
        if version != mudplot.__version__:
            issues.append(
                f"{source} version is {version!r}, Python is {mudplot.__version__!r}"
            )
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    if f"## [{mudplot.__version__}]" not in changelog:
        issues.append(f"CHANGELOG.md has no [{mudplot.__version__}] release heading")
    wheel_url = (
        f"releases/download/v{mudplot.__version__}/"
        f"mudplot-{mudplot.__version__}-py3-none-any.whl"
    )
    for name in ("README.md", "README.ko.md"):
        readme = (ROOT / name).read_text(encoding="utf-8")
        if f"**v{mudplot.__version__}**" not in readme:
            issues.append(f"{name} has no current version status")
        if wheel_url not in readme:
            issues.append(f"{name} has no current GitHub wheel URL")
    if issues:
        for issue in issues:
            print(f"error: {issue}", file=sys.stderr)
        return 1
    print(f"release versions agree: {expected_tag}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
