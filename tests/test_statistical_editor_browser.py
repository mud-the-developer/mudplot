"""Actual C07 typed roles, exact inference, live transactions and displayed pixels."""

from __future__ import annotations

import copy
import json
import re
import xml.etree.ElementTree as ET
from fractions import Fraction

import matplotlib.pyplot as plt
import mudplot as mp
import numpy as np
import pytest
from matplotlib.collections import LineCollection

from test_boxen_editor_browser import (
    disclose,
    displayed_surface,
    open_document,
    replace_from_populated_form,
    settle,
)

pytest_plugins = ["test_editor_browser", "test_rust_specialized_controls"]


def data_table():
    rows = []
    for cell, factor in [("left", 1), ("right", 1.5)]:
        for date in ["2026-01-01", "2026-07-01"]:
            for hue, size, style in [(True, 1, "First"), (1, 3, "Second")]:
                for index, (value, weight) in enumerate(
                    zip([0, 10, 20], [1, 38, 1], strict=True)
                ):
                    rows.append(
                        {
                            "date": date,
                            "v": factor * value,
                            "w": weight,
                            "h": hue,
                            "size": size,
                            "style": style,
                            "cell": cell,
                            "id": f"{cell}-{date}-{type(hue).__name__}-{index}",
                        }
                    )
    return {name: [row[name] for row in rows] for name in rows[0]}


def native_proof(document, kind, estimator, *, mapped_size):
    plot = mp.Plot.from_json(json.dumps(document))
    figure = plot.render()
    data = document["data"]["columns"]
    try:
        targets = [
            axis
            for axis in figure.axes
            if axis.get_ylabel() == "Observed response (μm)"
        ]
        assert len(targets) == len(document["panels"])
        for panel, axis in zip(document["panels"], targets, strict=True):
            wanted = panel.get("filters", {}).get("cell")
            rows = [
                i
                for i in range(len(data["v"]))
                if wanted is None or data["cell"][i] == wanted
            ]
            expected = []
            expected_intervals = []
            inference = panel["layers"][0]["stat"]
            random = np.random.default_rng(inference["seed"])
            for hue in [True, 1]:
                for date in ["2026-01-01", "2026-07-01"]:
                    selected = [
                        i
                        for i in rows
                        if type(data["h"][i]) is type(hue)
                        and data["h"][i] == hue
                        and data["date"][i] == date
                    ]
                    if not selected:
                        continue
                    pairs = sorted(
                        (data["v"][i], Fraction(data["w"][i])) for i in selected
                    )
                    if estimator == "mean":
                        value = float(
                            sum((Fraction(v) * w for v, w in pairs), Fraction())
                            / sum((w for _, w in pairs), Fraction())
                        )
                    else:
                        total = sum((w for _, w in pairs), Fraction())
                        mass = Fraction()
                        for observed, weight in pairs:
                            mass += weight
                            if mass >= total / 2:
                                value = observed
                                break
                    expected.append(value)
                    if inference["errorbar"] == "pi":
                        tail = (100 - Fraction(inference["level"])) / 200
                        total = sum((weight for _, weight in pairs), Fraction())
                        endpoints = []
                        for probability in (tail, 1 - tail):
                            mass = Fraction()
                            for observed, weight in pairs:
                                mass += weight
                                if mass >= total * probability:
                                    endpoints.append(observed)
                                    break
                        expected_intervals.append(endpoints)
                    else:
                        indices = random.integers(
                            0,
                            len(selected),
                            size=(inference["n_boot"], len(selected)),
                        )
                        replicates = []
                        for chosen in indices:
                            cohort = [selected[int(index)] for index in chosen]
                            total = sum(
                                (Fraction(data["w"][i]) for i in cohort), Fraction()
                            )
                            replicates.append(
                                float(
                                    sum(
                                        (
                                            Fraction(data["v"][i])
                                            * Fraction(data["w"][i])
                                            for i in cohort
                                        ),
                                        Fraction(),
                                    )
                                    / total
                                )
                            )
                        tail = (1 - inference["level"] / 100) / 2
                        expected_intervals.append(
                            np.quantile(replicates, [tail, 1 - tail]).tolist()
                        )
            if kind == "barplot":
                marks = [
                    patch
                    for patch in axis.patches
                    if patch.get_data_transform().contains_branch(axis.transData)
                ]
                np.testing.assert_allclose(
                    [patch.get_height() for patch in marks],
                    expected,
                    rtol=2e-15,
                    atol=0,
                )
                if mapped_size and marks:
                    assert sorted(patch.get_linewidth() for patch in marks) == [
                        1,
                        1,
                        2.5,
                        2.5,
                    ]
            else:
                marks = [
                    line
                    for line in axis.lines
                    if len(line.get_ydata()) and line.get_marker() in ["D", "^"]
                ]
                actual = [value for line in marks for value in line.get_ydata()]
                np.testing.assert_allclose(actual, expected, rtol=2e-15, atol=0)
                if mapped_size and marks:
                    assert sorted(line.get_markersize() for line in marks) == [2, 4]
                    assert all(line.get_linewidth() == 1.25 for line in marks)
            intervals = [
                segment
                for item in axis.collections
                if isinstance(item, LineCollection)
                for segment in item.get_segments()
            ]
            np.testing.assert_allclose(
                [segment[:, 1] for segment in intervals],
                expected_intervals,
                rtol=2e-15,
                atol=0,
            )
        assert plot.spec.data.columns == data_table()
    finally:
        plt.close(figure)


def raw_action(page, frontend, action):
    name = "Apply action" if frontend == "rust" else "Dispatch JSON action"
    form = page.locator('form[hx-post="/action/raw"]').filter(
        has=page.locator("button", has_text=name)
    )
    disclose(form)
    form.locator("textarea[name=json]").fill(json.dumps(action))
    form.get_by_role("button", name=name, exact=True).click()
    settle(page)


@pytest.mark.parametrize("frontend", ["python", "rust"])
@pytest.mark.parametrize("width", [1400, 540])
def test_human_statistical_roles_inference_live_rejection_history_exports(
    request, tmp_path, frontend, width
):
    if frontend == "python":
        page, url = request.getfixturevalue("editor")
        page.set_viewport_size({"width": width, "height": 1100})
        owned = False
    else:
        browser = request.getfixturevalue("browser")
        url, _ = request.getfixturevalue("rust_editor_server")
        page = browser.new_page(viewport={"width": width, "height": 1100})
        page.goto(url)
        owned = True
    try:
        data = data_table()
        base = (
            mp.plot(data)
            .secondary_yaxis("Observed response (μm)")
            .date_axis("x", timezone="UTC")
            .size(12, 7)
        )
        open_document(page, json.loads(base.to_json()))
        displayed_surface(page, url)
        fields = {
            "x": "date",
            "y": "v",
            "axis": "y2",
            "stat": {
                "estimator": "median",
                "errorbar": "pi",
                "level": 95,
                "weights": "w",
                "n_boot": 31,
                "seed": 7,
            },
            "semantics": {"hue": "h", "hue_order": [True, 1]},
        }
        if frontend == "rust":
            form = page.locator('form[hx-post="/layers"]')
            disclose(form)
            form.locator("select[name=layer_type]").select_option("barplot")
            form.locator("textarea[name=fields]").fill(json.dumps(fields))
        else:
            form = page.locator('form[hx-post="/action"]').filter(
                has=page.locator("input[name=type][value=add_layer_json]")
            )
            disclose(form)
            form.locator("select[name=layer_type]").select_option("barplot")
            form.locator("textarea[name=layer_json]").fill(json.dumps(fields))
        form.get_by_role("button", name="Add layer", exact=True).click()
        settle(page)
        built = page.request.get(url + "/spec.json").json()
        displayed_surface(page, url)
        native_proof(built, "barplot", "median", mapped_size=False)

        def point(layer):
            layer["type"] = "pointplot"
            layer["baseline"] = None
            layer["line_width"] = 1.25
            layer["stat"].update(
                estimator="mean", errorbar="ci", level=80, n_boot=31, seed=7
            )
            layer["semantics"].update(
                size="size",
                size_norm=[1, 3],
                sizes=[2, 4],
                style="style",
                markers=["D", "^"],
            )

        replace_from_populated_form(page, point)
        edited = page.request.get(url + "/spec.json").json()
        displayed_surface(page, url)
        native_proof(edited, "pointplot", "mean", mapped_size=True)
        raw_action(
            page,
            frontend,
            {
                "type": "SetLiveFacets",
                "col": "cell",
                "col_order": ["left", "empty", "right"],
                "col_wrap": 2,
            },
        )
        live = page.request.get(url + "/spec.json").json()
        live_surface = displayed_surface(page, url)
        native_proof(live, "pointplot", "mean", mapped_size=True)
        recipe = copy.deepcopy(live["facet_template"]["template"])
        layer = recipe["layers"][0]
        layer["type"] = "barplot"
        layer["line_width"] = None
        layer["baseline"] = 0
        layer["stat"].update(estimator="median", errorbar="pi", level=95)
        layer["semantics"]["sizes"] = [1, 2.5]
        raw_action(page, frontend, {"type": "SetFacetTemplate", "template": recipe})
        after = page.request.get(url + "/spec.json").json()
        after_surface = displayed_surface(page, url)
        native_proof(after, "barplot", "median", mapped_size=True)
        assert after["data"]["columns"] == data
        replace_from_populated_form(page, lambda layer: layer.update(line_width=3))
        assert page.locator(".error").is_visible()
        assert (
            page.request.get(url + "/spec.json").json() == after
            and displayed_surface(page, url) == after_surface
        )

        def invalid_inference(layer):
            layer["line_width"] = None
            layer["stat"]["errorbar"] = "se"

        replace_from_populated_form(page, invalid_inference)
        assert page.locator(".error").is_visible()
        assert (
            page.request.get(url + "/spec.json").json() == after
            and displayed_surface(page, url) == after_surface
        )
        page.get_by_role("button", name="Undo", exact=True).click()
        settle(page)
        assert (
            page.request.get(url + "/spec.json").json() == live
            and displayed_surface(page, url) == live_surface
        )
        page.get_by_role("button", name="Redo", exact=True).click()
        settle(page)
        assert (
            page.request.get(url + "/spec.json").json() == after
            and displayed_surface(page, url) == after_surface
        )
        files = {}
        for extension, endpoint in [
            ("json", "spec.json"),
            ("png", "fig.png"),
            ("svg", "fig.svg"),
            ("pdf", "fig.pdf"),
        ]:
            with page.expect_download() as request_download:
                page.locator(f'a[href="/{endpoint}"]').click()
            destination = tmp_path / f"{frontend}-{width}.{extension}"
            request_download.value.save_as(destination)
            files[extension] = destination
        assert json.loads(files["json"].read_text()) == after
        vector = ET.parse(files["svg"]).getroot()
        assert (
            float(vector.attrib["width"].removesuffix("pt")) == 12 * 72
            and float(vector.attrib["height"].removesuffix("pt")) == 7 * 72
        )
        bounds = re.search(rb"/MediaBox\s*\[([\d.\s-]+)\]", files["pdf"].read_bytes())
        assert bounds is not None
        assert [float(value) for value in bounds[1].split()] == [0, 0, 12 * 72, 7 * 72]
        open_document(page, json.loads(files["json"].read_text()))
        assert (
            page.request.get(url + "/spec.json").json() == after
            and displayed_surface(page, url) == after_surface
        )
        replace_from_populated_form(page, lambda layer: layer.update(alpha=0.6))
        final = page.request.get(url + "/spec.json").json()
        displayed_surface(page, url)
        native_proof(final, "barplot", "median", mapped_size=True)
        assert final["data"]["columns"] == data
    finally:
        if owned:
            page.close()
