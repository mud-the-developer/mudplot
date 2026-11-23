"""Actual Rust JSON layer/action forms for the complete C03 scientific workflow."""

from __future__ import annotations

import copy
import datetime as dt
import json
import re
import struct
import subprocess
import xml.etree.ElementTree as ET
from typing import Any

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import mudplot as mp
import numpy as np
import pytest
from matplotlib.cbook import boxplot_stats
from matplotlib.markers import MarkerStyle
from playwright.sync_api import expect

from test_box_workflow import bodies
from test_rust_specialized_controls import opened, spec
from test_swarm_editor_browser import add_layer, history, preview, raw_action

pytest_plugins = ["test_rust_specialized_controls"]


def source_table():
    result: dict[str, list[Any]] = {}
    for date, hue, method, magnitude, value_scale, cell in (
        ("2026-01-01", True, "A", 1, 1, "left"),
        ("2026-07-01", 1, "B", 3, 2, "right"),
    ):
        values = np.asarray([1, 2, 3, 4, 5, 30]) * value_scale
        summary = boxplot_stats(values, bootstrap=None)[0]
        indices = np.random.default_rng(17).integers(
            0, len(values), size=(257, len(values))
        )
        low, high = np.quantile(
            np.median(values[indices], axis=1), [0.1, 0.9], method="linear"
        )
        summary["cilo"], summary["cihi"] = low, high
        for index, value in enumerate(values):
            row = {
                "c": date,
                "v": float(value),
                "h": hue,
                "m": magnitude,
                "method": method,
                "cell": cell,
                "id": f"original-{cell}-{index}",
                "med": float(summary["med"]) if index == 0 else None,
            }
            for role in (
                "q1",
                "q3",
                "whislo",
                "whishi",
                "mean",
                "cilo",
                "cihi",
                "fliers",
            ):
                row[role] = (
                    (
                        summary[role].tolist()
                        if role == "fliers"
                        else float(summary[role])
                    )
                    if index == 0
                    else None
                )
            for name, value in row.items():
                result.setdefault(name, []).append(value)
    return result


def native_proof(raw, *, live=False, fraction=0.3):
    plot = mp.Plot.from_json(json.dumps(raw))
    native = plot.render()
    try:
        targets = [ax for ax in native.axes if ax.get_ylabel() == "Response (mm)"]
        assert [len(bodies(ax)) for ax in targets] == ([1, 0, 1] if live else [2])
        spacing = float(
            mdates.date2num(dt.datetime(2026, 7, 1))
            - mdates.date2num(dt.datetime(2026, 1, 1))
        )
        width = 0.8 * spacing / 2
        selected = [targets[0], targets[2]] if live else [targets[0], targets[0]]
        for index, ax in enumerate(selected):
            body = bodies(ax)[0 if live else index]
            assert body.get_linewidth() == [1, 2][index]
            reference_marker = MarkerStyle(
                raw["panels"][0]["layers"][0]["semantics"]["markers"][index]
            )
            reference_path = reference_marker.get_path().transformed(
                reference_marker.get_transform()
            )
            lines = ax.lines[0:7] if live else ax.lines[index * 7 : (index + 1) * 7]
            assert float(np.ptp(np.asarray(lines[2].get_xdata()))) == pytest.approx(
                width * fraction
            )
            assert lines[2].get_color() == ["red", "blue"][index]
            np.testing.assert_array_equal(lines[6].get_ydata(), [30 * (index + 1)])
            actual_marker = MarkerStyle(lines[6].get_marker())
            np.testing.assert_array_equal(
                actual_marker.get_path()
                .transformed(actual_marker.get_transform())
                .vertices,
                reference_path.vertices,
            )
            expected_median = 3.5 * (index + 1)
            np.testing.assert_array_equal(lines[4].get_ydata(), [expected_median] * 2)
        return [
            patch.get_path().vertices.copy() for ax in targets for patch in bodies(ax)
        ]
    finally:
        plt.close(native)


def visible_svg_caps(source):
    result = []

    def visit(node):
        if node.tag.rsplit("}", 1)[-1] == "defs" or node.attrib.get(
            "id", ""
        ).startswith("legend"):
            return
        if node.tag.rsplit("}", 1)[-1] == "path":
            style = dict(
                item.strip().split(":", 1)
                for item in node.attrib.get("style", "").split(";")
                if ":" in item
            )
            if style.get("stroke", "").strip() in ("#ff0000", "#0000ff"):
                values = re.findall(
                    r"[-+]?(?:\d*\.)?\d+(?:[eE][-+]?\d+)?", node.attrib.get("d", "")
                )
                xy = np.asarray([float(value) for value in values]).reshape(-1, 2)
                result.append(xy)
        for child in node:
            visit(child)

    visit(ET.fromstring(source))
    return result


@pytest.mark.parametrize("width", [1400, 540])
def test_real_box_forms_raw_to_supplied_mode_live_reopen_history_rejection_and_exports(
    rust_browser, width
):
    browser, url, directory = rust_browser
    output = directory / f"box-{width}"
    output.mkdir(exist_ok=True)
    context = browser.new_context(
        viewport={"width": width, "height": 1150}, reduced_motion="reduce"
    )
    page = context.new_page()
    page.goto(url)
    data = source_table()
    base = mp.plot(data).size(12, 7).secondary_yaxis("Response (mm)")
    base.date_axis("x", timezone="UTC").labels(
        title="C03 supplied/raw workflow", y="Unused primary frame"
    )
    opened(page, json.loads(base.to_json()))
    entries = [
        {"level": True, "components": {"cap": {"color": "red"}}},
        {"level": 1, "components": {"cap": {"color": "blue"}}},
    ]
    fields = {
        "x": "c",
        "y": "v",
        "axis": "y2",
        "showmeans": True,
        "box": {
            "median_ci": {"level": 80, "n_boot": 257, "seed": 17},
            "cap_fraction": 0.3,
            "hue_components": entries,
        },
        "semantics": {
            "scale_id": "box-ui",
            "hue": "h",
            "size": "m",
            "sizes": [1, 2],
            "style": "method",
        },
    }
    add_layer(page, "box", fields)
    raw = spec(page, url)
    raw_png = preview(page, url)
    raw_geometry = native_proof(raw)
    assert raw["data"]["columns"] == data
    raw_action(page, {"type": "RemoveLayer", "layer_index": 0})
    summary_fields = {
        **fields,
        "y": "med",
        "notch": True,
        "box": {
            "summary": {
                role: role
                for role in (
                    "q1",
                    "q3",
                    "whislo",
                    "whishi",
                    "mean",
                    "cilo",
                    "cihi",
                    "fliers",
                )
            },
            "cap_fraction": 0.3,
            "hue_components": entries,
        },
    }
    add_layer(page, "box", summary_fields)
    supplied = spec(page, url)
    supplied_png = preview(page, url)
    supplied_geometry = native_proof(supplied)
    for actual, expected in zip(supplied_geometry, raw_geometry, strict=True):
        np.testing.assert_allclose(actual, expected, rtol=1e-12, atol=1e-10)
    invalid = copy.deepcopy(summary_fields)
    invalid["box"]["summary"]["q1"] = "whishi"
    add_layer(page, "box", invalid)
    expect(page.locator(".error")).to_be_visible()
    assert spec(page, url) == supplied and preview(page, url) == supplied_png
    history(page, "Undo")
    history(page, "Undo")
    assert spec(page, url) == raw and preview(page, url) == raw_png
    history(page, "Redo")
    history(page, "Redo")
    assert spec(page, url) == supplied and preview(page, url) == supplied_png
    with page.expect_download() as download:
        page.locator('.exports a[href="/spec.json"]').click()
    target = output / "supplied.mplot.json"
    download.value.save_as(target)
    opened(page, json.loads(target.read_text()))
    assert spec(page, url) == supplied
    raw_action(
        page,
        {
            "type": "SetLiveFacets",
            "col": "cell",
            "col_order": ["left", "empty", "right"],
            "col_wrap": 2,
        },
    )
    raw_action(
        page, {"type": "SetLayout", "rows": 2, "cols": 2, "width_ratios": [3, 2]}
    )
    raw_action(page, {"type": "SetTitle", "text": "Local title", "panel": 0})
    local = spec(page, url)
    opened(page, local)
    template = copy.deepcopy(local["facet_template"]["template"])
    template["layers"][0]["box"]["cap_fraction"] = 1
    raw_action(page, {"type": "SetFacetTemplate", "template": template})
    edited = spec(page, url)
    assert edited["panels"][0]["title"] != "Local title"
    assert edited["width_ratios"] == [3, 2] and len(edited["panels"]) == 3
    native_proof(edited, live=True, fraction=1)
    edited_png = preview(page, url)
    invalid_template = copy.deepcopy(template)
    invalid_template["layers"][0]["box"]["median_ci"] = {"seed": 17}
    raw_action(page, {"type": "SetFacetTemplate", "template": invalid_template})
    expect(page.locator(".error")).to_be_visible()
    assert spec(page, url) == edited and preview(page, url) == edited_png
    history(page, "Undo")
    assert spec(page, url) == local
    history(page, "Redo")
    assert spec(page, url) == edited and preview(page, url) == edited_png
    for extension in ("png", "svg", "pdf", "json"):
        endpoint = "/spec.json" if extension == "json" else "/fig." + extension
        with page.expect_download() as download:
            page.locator('.exports a[href="' + endpoint + '"]').click()
        target = output / (
            "edited.mplot.json" if extension == "json" else "edited." + extension
        )
        download.value.save_as(target)
        if extension == "png":
            assert target.read_bytes() == edited_png
            assert struct.unpack("!II", edited_png[16:24]) == (2000, 1166)
        elif extension == "svg":
            caps = visible_svg_caps(target.read_bytes())
            assert len(caps) == 4
            for xy in caps:
                assert np.ptp(xy[:, 0]) > 0
                assert np.ptp(xy[:, 1]) == pytest.approx(0, abs=1e-8)
        elif extension == "pdf":
            info = subprocess.run(
                ["pdfinfo", str(target)], check=True, capture_output=True, text=True
            ).stdout
            assert "864 x 504 pts" in info
        else:
            assert json.loads(target.read_text()) == edited
    opened(page, json.loads((output / "edited.mplot.json").read_text()))
    assert spec(page, url) == edited
    assert edited["data"]["columns"] == data
    page.screenshot(path=str(output / "surface.png"), full_page=True)
    context.close()
