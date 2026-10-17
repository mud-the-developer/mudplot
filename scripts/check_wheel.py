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
    "tests/fixtures/review_json_boundaries.json",
    "tests/fixtures/review_state_paths.json",
    "tests/fixtures/review_http_boundaries.json",
    "tests/fixtures/review_full_spec_fields.json",
    "scripts/check_python_bridge_paths.py",
    "scripts/check_request_body_limits.py",
    "docs/PLOT_GALLERY.md",
    "docs/COMPATIBILITY.md",
    "docs/COMPATIBILITY.ko.md",
    "docs/VISUAL_QUALITY.md",
    "docs/VISUAL_QUALITY.ko.md",
    "docs/VISUAL_REVIEW.html",
    "docs/FACETS.md",
    "docs/FACETS.ko.md",
    "docs/JOINT_GRID.md",
    "docs/JOINT_GRID.ko.md",
    "docs/PAIR_GRID.md",
    "docs/PAIR_GRID.ko.md",
    "docs/HEATMAP.md",
    "docs/HEATMAP.ko.md",
    "docs/REGRESSION.md",
    "docs/REGRESSION.ko.md",
    "docs/CLUSTERMAP.md",
    "docs/CLUSTERMAP.ko.md",
    "examples/clustered_profiles.py",
    "docs/images/clustered_profiles.png",
    "docs/images/clustered_profiles.pdf",
    "docs/images/clustered_profiles.svg",
    "docs/images/clustered_profiles.mplot.json",
    "examples/regression_modes.py",
    *(
        f"docs/images/{name}.{extension}"
        for name in (
            "regression_residual",
            "regression_logx",
            "regression_robust",
            "regression_logistic",
            "regression_lowess",
        )
        for extension in ("png", "pdf", "svg", "mplot.json")
    ),
    "examples/heatmap_controls.py",
    "docs/images/heatmap_controls.png",
    "docs/images/heatmap_controls.pdf",
    "docs/images/heatmap_controls.svg",
    "docs/images/heatmap_controls.mplot.json",
    "examples/pair_observations.py",
    "examples/kde_grids.py",
    "docs/images/kde_joint.png",
    "docs/images/kde_joint.pdf",
    "docs/images/kde_joint.svg",
    "docs/images/kde_joint.mplot.json",
    "docs/images/kde_pair.png",
    "docs/images/kde_pair.pdf",
    "docs/images/kde_pair.svg",
    "docs/images/kde_pair.mplot.json",
    "docs/images/pair_observations.png",
    "docs/images/pair_observations.pdf",
    "docs/images/pair_observations.svg",
    "docs/images/pair_observations.mplot.json",
    "examples/joint_observations.py",
    "docs/images/joint_observations.png",
    "docs/images/joint_observations.pdf",
    "docs/images/joint_observations.svg",
    "docs/images/joint_observations.mplot.json",
    "examples/faceted_responses.py",
    "docs/images/faceted_responses.png",
    "docs/images/faceted_responses.pdf",
    "docs/images/faceted_responses.svg",
    "docs/images/faceted_responses.mplot.json",
    "docs/images/visual_before.png",
    "docs/images/visual_before.pdf",
    "docs/images/visual_before.svg",
    "docs/images/visual_before.mplot.json",
    "docs/images/visual_after.png",
    "docs/images/visual_after.pdf",
    "docs/images/visual_after.svg",
    "docs/images/visual_after.mplot.json",
    "docs/images/visual_after_gray.png",
    "docs/images/visual_after_protan.png",
    "docs/images/visual_after_deutan.png",
    "docs/images/visual_quality.json",
    "docs/images/visual_response.png",
    "docs/images/visual_response.pdf",
    "docs/images/visual_response.svg",
    "docs/images/visual_response.mplot.json",
    "docs/images/visual_endpoint.png",
    "docs/images/visual_endpoint.pdf",
    "docs/images/visual_endpoint.svg",
    "docs/images/visual_endpoint.mplot.json",
    "docs/images/visual_response_mobile.png",
    "docs/images/visual_response_mobile.mplot.json",
    "docs/images/visual_endpoint_mobile.png",
    "docs/images/visual_endpoint_mobile.mplot.json",
    "docs/images/visual_response_gray.png",
    "docs/images/visual_response_protan.png",
    "docs/images/visual_response_deutan.png",
    "examples/publication_showcase.py",
    "scripts/render_docs_demo.py",
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
    "dashboard/plot_gallery.py",
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
        from dashboard.plot_gallery import GALLERY_EXAMPLES

        expected_examples = {f"{example.name}.py" for example in GALLERY_EXAMPLES}
        packaged_examples = {
            Path(name).name
            for name in sdist_names
            if "/examples/plots/" in name and name.endswith(".py")
        }
        if packaged_examples != expected_examples:
            missing.append(
                "sdist plot examples differ: "
                f"expected {sorted(expected_examples)}, got {sorted(packaged_examples)}"
            )

        expected_gallery_assets = {
            filename
            for example in GALLERY_EXAMPLES
            for filename in (
                f"{example.name}.png",
                f"{example.name}.mplot.json",
            )
        }
        packaged_gallery_assets = {
            Path(name).name for name in sdist_names if "/docs/images/plots/" in name
        }
        if packaged_gallery_assets != expected_gallery_assets:
            missing.append(
                "sdist plot gallery assets differ: "
                f"expected {sorted(expected_gallery_assets)}, "
                f"got {sorted(packaged_gallery_assets)}"
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
            "assert mudplot.from_json(mudplot.to_json(mudplot.FigureSpec())).version; "
            "p=mudplot.plot({'x':[1,2],'y':[3,4]}).scatter('x','y'); "
            "p.joint(marginal_kind='kde',kde={'cut':0}); "
            "assert len(p.spec.panels)==3 and mudplot.validate(p.spec)==[]; "
            "assert mudplot.apply(p.action_log)==p.spec; "
            "q=mudplot.plot({'a':[1,2],'b':[3,4]}).pair(['a','b'],diag_kind='kde'); "
            "assert len(q.spec.panels)==4 and mudplot.validate(q.spec)==[]; "
            "assert mudplot.apply(q.action_log)==q.spec; "
            "h=mudplot.plot().matrix('m',[[1,2],[3,4]]); "
            "h.heatmap('m',heatmap={'annot':True}); "
            "assert mudplot.validate(h.spec)==[]; "
            "assert mudplot.apply(h.action_log)==h.spec; "
            "r=mudplot.plot({'x':[1,2,3],'y':[2,3,4]}).residplot('x','y'); "
            "assert mudplot.validate(r.spec)==[]; "
            "u=mudplot.Plot.from_json(r.to_json()).spec; "
            "assert mudplot.apply(r.action_log)==u; "
            "c=mudplot.plot().matrix('m',[[1,2],[3,4]]).clustermap('m'); "
            "assert mudplot.validate(c.spec)==[]; "
            "assert mudplot.apply(c.action_log)==c.spec"
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
