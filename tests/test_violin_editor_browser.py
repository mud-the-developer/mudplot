"""Actual C04 human layer/RAW-template forms, matching-profile native references."""

from __future__ import annotations

import copy
import json
import re
import xml.etree.ElementTree as ET
from datetime import UTC, datetime

import matplotlib.pyplot as plt
import mudplot as mp
import numpy as np
import pytest
from matplotlib.collections import PolyCollection

from test_rust_specialized_controls import opened, spec
from test_swarm_editor_browser import add_layer, history, preview, raw_action

pytest_plugins = ["test_rust_specialized_controls"]


def source_table():
    rows = []
    for cell in ["left", "right"]:
        for date in ["2026-01-01", "2026-07-01"]:
            for hue, magnitude, method in [
                (True, 1, "A"),
                (1, 3, "B"),
                ("third", 2, "A"),
            ]:
                for index, (value, weight) in enumerate(
                    zip([1, 4, 9], [1, 3, 2], strict=True)
                ):
                    rows.append(
                        {
                            "date": date,
                            "value": value,
                            "hue": hue,
                            "precision": magnitude,
                            "other_precision": 4 - magnitude,
                            "method": method,
                            "weight": weight,
                            "cell": cell,
                            "id": f"{cell}-{date}-{type(hue).__name__}-{hue}-{index}",
                        }
                    )
    return {name: [row[name] for row in rows] for name in rows[0]}


def layer_fields():
    return {
        "x": "date",
        "y": "value",
        "axis": "y2",
        "weights": "weight",
        "inner": "box",
        "split": True,
        "violin": {
            "hue_components": [
                {"level": True, "components": {"whisker": {"color": "red"}}},
                {"level": 1, "components": {"whisker": {"color": "blue"}}},
            ]
        },
        "semantics": {
            "hue": "hue",
            "hue_order": [True, 1],
            "size": "precision",
            "size_norm": [1, 3],
            "sizes": [1, 2],
            "style": "method",
            "markers": ["D", "^"],
        },
        "marker_size": 5,
        "components": {"body": {"alpha": 0.9}},
    }


def base_document():
    return (
        mp.plot(source_table())
        .secondary_yaxis("Observed response (mm)", scale="log")
        .date_axis("x", timezone="UTC")
        .size(12, 7)
        .to_json()
    )


def assert_native(document, *, mode, rows_per_cell, strokes):
    original = mp.Plot.from_json(json.dumps(document))
    figure = original.render()
    try:
        targets = [
            axis
            for axis in figure.axes
            if axis.get_ylabel() == "Observed response (mm)"
        ]
        expected_cells = 3 if document.get("facet_template") is not None else 1
        assert len(targets) == expected_cells
        populated = []
        for axis in targets:
            body = [
                item for item in axis.collections if isinstance(item, PolyCollection)
            ]
            if not body:
                populated.append(0)
                continue
            populated.append(len(body))
            np.testing.assert_allclose(
                [item.get_linewidths()[0] for item in body], strokes, rtol=0, atol=1e-12
            )
            if mode == "box":
                np.testing.assert_array_equal(
                    [line.get_ydata()[0] for line in axis.lines], [4] * len(body)
                )
                assert [line.get_marker() for line in axis.lines] == [
                    "D",
                    "D",
                    "^",
                    "^",
                ]
                assert all(line.get_markersize() == 5 for line in axis.lines)
            else:
                actual = np.concatenate(
                    [np.asarray(line.get_ydata()) for line in axis.lines]
                )
                np.testing.assert_array_equal(actual, [1, 4, 9] * len(body))
                assert len(actual) == rows_per_cell
                assert all(line.get_markersize() == 6 for line in axis.lines)
            # Independent declared canonical-day slot and pair-lane positions.
            dates = [
                (
                    datetime(2026, month, 1, tzinfo=UTC)
                    - datetime(1970, 1, 1, tzinfo=UTC)
                ).total_seconds()
                / 86400
                for month in [1, 7]
            ]
            for line in axis.lines:
                x = np.asarray(line.get_xdata(), dtype=float)
                assert min(abs(float(x[0]) - date) for date in dates) < 181 * 0.5
        if expected_cells == 3:
            assert populated == ([4, 0, 4] if mode == "box" else [6, 0, 6])
        assert original.spec.data.columns == source_table()
    finally:
        plt.close(figure)


@pytest.mark.parametrize("width", [1400, 540])
def test_violin_forms_keep_native_history_and_exports(rust_browser, width):
    browser, url, directory = rust_browser
    context = browser.new_context(
        viewport={"width": width, "height": 1100}, accept_downloads=True
    )
    page = context.new_page()
    page.goto(url)
    opened(page, json.loads(base_document()))
    add_layer(page, "violin", layer_fields())
    built = spec(page, url)
    assert_native(built, mode="box", rows_per_cell=12, strokes=[1, 1, 2, 2])
    assert built["data"]["columns"] == source_table()
    raw_action(
        page,
        {
            "type": "SetLiveFacets",
            "col": "cell",
            "col_order": ["left", "empty", "right"],
            "col_wrap": 2,
        },
    )
    live = spec(page, url)
    before_png = preview(page, url)
    assert_native(live, mode="box", rows_per_cell=12, strokes=[1, 1, 2, 2])
    template = copy.deepcopy(live["facet_template"]["template"])
    layer = template["layers"][0]
    layer["inner"] = "point"
    layer["violin"] = {
        "split_policy": "paired",
        "hue_components": [{"level": "third", "components": {"body": {"hatch": "//"}}}],
    }
    layer["semantics"]["hue_order"] = [True, 1, "third"]
    layer["semantics"]["size"] = "other_precision"
    layer["components"] = {
        "body": {"alpha": 0.9},
        "point": {"marker_size": 6, "marker_edge_width": 0.75, "face_color": "white"},
    }
    raw_action(page, {"type": "SetFacetTemplate", "template": template})
    edited = spec(page, url)
    edited_png = preview(page, url)
    assert_native(
        edited, mode="point", rows_per_cell=18, strokes=[2, 2, 1, 1, 1.5, 1.5]
    )
    assert edited["data"]["columns"] == source_table()
    invalid = copy.deepcopy(template)
    invalid["layers"][0]["components"]["body"]["line_width"] = 2
    raw_action(page, {"type": "SetFacetTemplate", "template": invalid})
    assert spec(page, url) == edited and preview(page, url) == edited_png
    history(page, "Undo")
    assert spec(page, url) == live and preview(page, url) == before_png
    history(page, "Redo")
    assert spec(page, url) == edited and preview(page, url) == edited_png
    out = directory / f"violin-{width}"
    out.mkdir()
    for details in page.locator("details").all():
        if details.evaluate("node=>node.open"):
            details.locator("summary").first.click()
    page.screenshot(path=str(out / "functional-surface.png"), full_page=True)
    downloads = {}
    for extension, path in [
        ("json", "/spec.json"),
        ("png", "/fig.png"),
        ("svg", "/fig.svg"),
        ("pdf", "/fig.pdf"),
    ]:
        with page.expect_download() as request:
            page.locator(f'a[href="{path}"]').click()
        download = request.value
        target = out / download.suggested_filename
        download.save_as(str(target))
        downloads[extension] = target
    saved = json.loads(downloads["json"].read_text())
    assert saved == edited
    svg = ET.fromstring(downloads["svg"].read_text())
    dimensions = [
        float(svg.attrib[name].removesuffix("pt")) for name in ["width", "height"]
    ]
    np.testing.assert_allclose(dimensions, np.asarray(saved["size"]) * 72, atol=1e-8)
    pdf = downloads["pdf"].read_bytes()
    box = re.search(rb"/MediaBox\s*\[\s*0\s+0\s+([\d.]+)\s+([\d.]+)\s*\]", pdf)
    assert box is not None
    np.testing.assert_allclose(
        [float(value) for value in box.groups()],
        np.asarray(saved["size"]) * 72,
        atol=1e-6,
    )
    opened(page, saved)
    assert spec(page, url) == edited and preview(page, url) == edited_png
    # Reopened recipe storage alone is not an edit: run a real whole transaction.
    further = copy.deepcopy(saved["facet_template"]["template"])
    further["layers"][0]["components"]["point"]["marker_size"] = 7
    raw_action(page, {"type": "SetFacetTemplate", "template": further})
    final = spec(page, url)
    native = mp.Plot.from_json(json.dumps(final)).render()
    try:
        assert all(
            line.get_markersize() == 7 for axis in native.axes for line in axis.lines
        )
        assert sum(len(axis.lines) for axis in native.axes) == 12
    finally:
        plt.close(native)
    history(page, "Undo")
    assert spec(page, url) == edited
    context.close()
