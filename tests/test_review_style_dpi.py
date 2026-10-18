"""LAY-08/09: style ownership and physical rather than pixel comparisons."""

import copy
import os
import struct
import subprocess
import sys
from dataclasses import replace
from pathlib import Path
from xml.etree import ElementTree as ET

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mudplot as mp
import pytest
from dashboard.editor_server import EditorSession

from test_review_mixed_guides import mixed


def variants():
    p = (
        mp.plot({"x": [1, 2, 3], "y": [1, 3, 2]})
        .line("x", "y", label="trace")
        .size(5, 3)
        .labels(title="Signal")
    )
    return [
        p.theme("publication").spec,
        p.theme("minimal").font(size=13).spec,
        p.theme("paper-grid").journal("nature").spec,
    ]


@pytest.mark.parametrize("extension", ["png", "pdf", "svg"])
def test_alternating_theme_journal_and_caller_rc_match_fresh_process(
    extension, tmp_path
):
    specs = variants()
    expected = []
    with plt.rc_context(
        {"font.size": 17, "axes.linewidth": 2.75, "svg.hashsalt": "caller"}
    ):
        before = copy.deepcopy(dict(matplotlib.rcParams))
        for index, spec in enumerate(specs):
            source, output = (
                tmp_path / f"spec{index}.json",
                tmp_path / f"alone{index}.{extension}",
            )
            mp.save_spec(spec, source)
            plt.close(mp.save(spec, str(output)))
            expected.append(output.read_bytes())
            assert dict(matplotlib.rcParams) == before
        for index in (2, 0, 1, 0, 2):
            output = tmp_path / f"repeat{index}.{extension}"
            plt.close(mp.save(specs[index], str(output)))
            assert output.read_bytes() == expected[index]
            assert dict(matplotlib.rcParams) == before
        script = (
            "import matplotlib;matplotlib.use('Agg');"
            "import matplotlib.pyplot as p;import mudplot as m,sys;"
            "matplotlib.rcParams.update({'font.size':17,'axes.linewidth':2.75,"
            "'svg.hashsalt':'caller'});"
            "from pathlib import Path;root=Path(sys.argv[1]);ext=sys.argv[2];"
            "[(p.close(m.save(m.load_spec(root/f'spec{i}.json'),"
            "str(root/f'fresh{i}.{ext}')))) for i in range(3)]"
        )
        subprocess.run(
            [sys.executable, "-c", script, str(tmp_path), extension],
            cwd=tmp_path,
            env={**os.environ, "PYTHONPATH": str(Path.cwd()), "MPLBACKEND": "Agg"},
            capture_output=True,
            check=True,
            timeout=45,
        )
        assert all(
            (tmp_path / f"fresh{i}.{extension}").read_bytes() == expected[i]
            for i in range(3)
        )
        assert dict(matplotlib.rcParams) == before


def test_failed_render_restores_complete_caller_rc():
    spec = variants()[0]
    spec.panels[0].layers[0].color = "not-a-colour"
    before = copy.deepcopy(dict(matplotlib.rcParams))
    figures = set(plt.get_fignums())
    with pytest.raises(ValueError):
        mp.render(spec)
    assert dict(matplotlib.rcParams) == before
    assert set(plt.get_fignums()) == figures


def test_editor_preview_cap_preserves_original_geometry_state_and_final_export():
    p = (
        mp.plot({"x": [1, 2, 3], "y": [1, 3, 2]})
        .line("x", "y")
        .labels(title="Signal", x="Time", y="Value")
        .size(10, 5)
    )
    p.dispatch(mp.actions.SetDpi(600))
    spec = p.spec
    session = EditorSession()
    session.load_spec(mp.to_json(spec))
    assert session.error is None and session.store.state == spec
    assert struct.unpack(">II", session.png[16:24]) == (2000, 1000)
    fig = mp.render(spec)
    try:
        box = fig.axes[0].get_position()
        assert (
            max(
                abs(a - b) * scale
                for a, b, scale in zip(
                    session.layout["panel_bbox"],
                    box.extents,
                    [10, 5, 10, 5],
                    strict=True,
                )
            )
            <= 0.02
        )
    finally:
        plt.close(fig)
    root = ET.fromstring(session.export("svg"))
    assert [
        float(root.attrib[k].removesuffix("pt")) for k in ("width", "height")
    ] == pytest.approx([720, 360])
    assert session.store.state == spec and p.spec == spec


def test_dense_guide_positions_keep_physical_padding_across_dpi():
    p = mixed()
    spec = p.spec
    geometry, line_widths = [], []
    for dpi in (150, 300):
        fig = mp.render(replace(spec, dpi=dpi))
        try:
            geometry.append(
                [[float(v) for v in ax.get_position().extents] for ax in fig.axes[:2]]
            )
            line_widths.append(
                [line.get_linewidth() for ax in fig.axes for line in ax.lines]
            )
            assert fig.get_size_inches() == pytest.approx([6, 3])
        finally:
            plt.close(fig)
    assert p.spec == spec
    assert line_widths[0] == line_widths[1]
    assert (
        max(
            abs(a - b) * scale
            for x, y in zip(geometry[0], geometry[1], strict=True)
            for a, b, scale in zip(x, y, [6, 3, 6, 3], strict=True)
        )
        <= 0.02
    )
