"""Build release distributions and verify their required packaged files."""

from __future__ import annotations

import argparse
import glob
import hashlib
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import zipfile
from pathlib import Path

HTMX_SHA256 = "449317ade7881e949510db614991e195c3a099c4c791c24dacec55f9f4a2a452"

SDIST_FILES = (
    "LICENSE",
    "README.md",
    "SECURITY.md",
    "SECURITY.ko.md",
    "pyproject.toml",
    "uv.lock",
    "schemas/capabilities.json",
    "schemas/figure_spec.schema.json",
    "scripts/audit_dependencies.py",
    "scripts/audit_dependencies.py.lock",
    "scripts/check_minimum_versions.py",
    "scripts/check_minimum_versions.py.lock",
    "dashboard/README.md",
    "dashboard/README.ko.md",
    "dashboard/__init__.py",
    "dashboard/__main__.py",
    "dashboard/editor_server.py",
    "dashboard/editor_view.py",
    "dashboard/markdown_lite.py",
    "dashboard/samples.py",
    "dashboard/site.py",
    "dashboard/static/htmx.min.js",
    "dashboard/static/htmx.LICENSE",
    "mudplot-editor/Cargo.toml",
    "mudplot-editor/Cargo.lock",
    "mudplot-editor/README.md",
    "mudplot-editor/README.ko.md",
    "mudplot-editor/default_spec.json",
    "mudplot-editor/src/lib.rs",
    "mudplot-editor/src/main.rs",
    "mudplot-editor/src/model.rs",
    "mudplot-editor/src/python.rs",
    "mudplot-editor/templates/page.html",
    "mudplot-editor/templates/fragment.html",
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--out-dir", help="copy the verified wheel and sdist to this empty directory"
    )
    args = parser.parse_args()

    with tempfile.TemporaryDirectory() as out_dir:
        # With no --wheel/--sdist selector, build creates an sdist and builds
        # the wheel from it. --no-isolation keeps the backend in uv.lock.
        subprocess.run(
            [
                sys.executable,
                "-m",
                "build",
                "--no-isolation",
                "--outdir",
                out_dir,
                ".",
            ],
            check=True,
        )
        wheels = glob.glob(f"{out_dir}/*.whl")
        sdists = glob.glob(f"{out_dir}/*.tar.gz")
        if len(wheels) != 1 or len(sdists) != 1:
            print(
                f"error: expected one wheel and one sdist, got {wheels} and {sdists}",
                file=sys.stderr,
            )
            return 1

        with zipfile.ZipFile(wheels[0]) as archive:
            wheel_names = archive.namelist()
        missing = []
        if "mudplot/py.typed" not in wheel_names:
            missing.append("wheel:mudplot/py.typed")
        if not any(name.endswith("licenses/LICENSE") for name in wheel_names):
            missing.append("wheel:*licenses/LICENSE")
        wheel_roots = {name.partition("/")[0] for name in wheel_names}
        unexpected_roots = sorted(
            root
            for root in wheel_roots
            if root != "mudplot"
            and not (root.startswith("mudplot-") and root.endswith(".dist-info"))
        )
        if unexpected_roots:
            missing.append(f"wheel unexpected top-level paths: {unexpected_roots}")

        with tarfile.open(sdists[0]) as archive:
            sdist_names = archive.getnames()
            htmx_name = next(
                (
                    name
                    for name in sdist_names
                    if name.endswith("/dashboard/static/htmx.min.js")
                ),
                None,
            )
            htmx_file = archive.extractfile(htmx_name) if htmx_name else None
            if htmx_file is not None:
                digest = hashlib.sha256(htmx_file.read()).hexdigest()
                if digest != HTMX_SHA256:
                    missing.append(f"sdist htmx SHA-256 is {digest}")
        missing.extend(
            f"sdist:{required}"
            for required in SDIST_FILES
            if not any(name.endswith(f"/{required}") for name in sdist_names)
        )
        for forbidden in (
            ".hypothesis",
            "mudplot-editor/target",
            "src/pretext",
            "src/SciencePlots",
        ):
            if any(f"/{forbidden}/" in name for name in sdist_names):
                missing.append(f"sdist must not contain {forbidden}")

        if missing:
            print(
                f"error: distributions are missing or contain {missing}",
                file=sys.stderr,
            )
            return 1

        smoke = (
            "import mudplot; "
            "assert '.whl' in mudplot.__file__; "
            "assert mudplot.from_json(mudplot.to_json(mudplot.FigureSpec())).version"
        )
        subprocess.run(
            [sys.executable, "-S", "-c", smoke],
            cwd=out_dir,
            env={**os.environ, "PYTHONPATH": wheels[0]},
            check=True,
        )

        if args.out_dir:
            destination = Path(args.out_dir)
            destination.mkdir(parents=True, exist_ok=True)
            if any(destination.iterdir()):
                print(
                    f"error: output directory is not empty: {destination}",
                    file=sys.stderr,
                )
                return 1
            for artifact in (*sdists, *wheels):
                shutil.copy2(artifact, destination)

        print(f"distribution packaging OK: {sdists[0]}, {wheels[0]}")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
