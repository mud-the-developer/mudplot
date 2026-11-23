"""Real Rust human forms for C02 roles/scopes and explicit live transactions."""

import copy
import json
import xml.etree.ElementTree as ET

import mudplot as mp
import numpy as np
import pytest
from PIL import Image
from playwright.sync_api import expect

from test_rust_specialized_controls import opened, settle, spec
from test_swarm_workflow import assert_clear, assert_paths

pytest_plugins = ["test_rust_specialized_controls"]


def raw_action(page, action):
    form = page.locator('form[hx-post="/action/raw"]').filter(
        has=page.locator("button").filter(has_text="Apply action")
    )
    details = page.locator("details").filter(has=form)
    if not details.evaluate("node => node.open"):
        details.locator("summary").click()
    form.locator("textarea").fill(json.dumps(action))
    form.locator("button").click()
    settle(page)


def add_layer(page, kind, fields):
    form = page.locator('form[hx-post="/layers"]')
    form.locator('select[name="layer_type"]').select_option(kind)
    form.locator('textarea[name="fields"]').fill(json.dumps(fields))
    form.locator('input[name="panel"]').fill("0")
    form.locator("button").click()
    settle(page)


def history(page, name):
    page.get_by_role("button", name=name, exact=True).click()
    settle(page)


def preview(page, url):
    response = page.request.get(url + "/fig.png")
    assert response.ok
    return response.body()


def native_swarm_proof(raw, *, scalar, styles, expected_counts):
    plot = mp.Plot.from_json(json.dumps(raw))
    figure = plot.render()
    try:
        axes = [ax for ax in figure.axes if ax.get_ylabel() == "Response"]
        assert [len(ax.collections) for ax in axes] == [
            2 if n else 0 for n in expected_counts
        ]
        for ax, n in zip(axes, expected_counts, strict=True):
            if not n:
                continue
            first, second = ax.collections
            names = [styles[0] if i % 2 == 0 else styles[1] for i in range(n)]
            assert_paths(first, [scalar] * n)
            assert_paths(second, names)
            assert_clear(ax, [first, second], [[scalar] * n, names])
            # Native temporal category jitter never rewrites measurement values.
            np.testing.assert_allclose(
                np.asarray(first.get_offsets())[:, 1], [1, 1.01, 2][:n], rtol=0, atol=0
            )
    finally:
        import matplotlib.pyplot as plt

        plt.close(figure)


@pytest.mark.parametrize("width", [1400, 540])
def test_real_swarm_forms_roles_scope_template_reopen_history_and_exports(
    rust_browser, width
):
    browser, url, directory = rust_browser
    output = directory / f"swarm-{width}"
    output.mkdir(exist_ok=True)
    context = browser.new_context(
        viewport={"width": width, "height": 1100}, reduced_motion="reduce"
    )
    page = context.new_page()
    page.goto(url)
    data = {
        "c": ["2026-01-01"] * 6,
        "v": [1, 1.01, 2] * 2,
        "h": [-10, 0, 10] * 2,
        "m": [1, 2, 3] * 2,
        "shape": ["A", "B", "A"] * 2,
        "cohort": ["left"] * 3 + ["right"] * 3,
        "id": ["l3", "l1", "l2", "r3", "r1", "r2"],
    }
    base = mp.plot(data).size(12, 7).secondary_yaxis("Response", scale="log")
    base.date_axis("x", timezone="UTC").labels(title="C02 observations")
    opened(page, json.loads(base.to_json()))
    scalar = {
        "x": "c",
        "y": "v",
        "axis": "y2",
        "marker": "s",
        "marker_size": 6,
        "pack_scope": "members",
    }
    add_layer(page, "swarmplot", scalar)
    one = spec(page, url)
    roles = {
        "x": "c",
        "y": "v",
        "axis": "y2",
        "pack_scope": "members",
        "semantics": {
            "scale_id": "roles",
            "hue": "h",
            "hue_kind": "numeric",
            "hue_norm": [-10, 10],
            "size": "m",
            "size_norm": [1, 3],
            "sizes": [3, 7],
            "style": "shape",
            "markers": ["s", "^"],
        },
    }
    add_layer(page, "swarmplot", roles)
    accepted = spec(page, url)
    png = preview(page, url)
    assert accepted["data"]["columns"] == data
    assert len(accepted["panels"][0]["layers"]) == 2
    add_layer(page, "swarmplot", {**scalar, "orient": "h"})
    expect(page.locator(".error")).to_be_visible()
    assert spec(page, url) == accepted and preview(page, url) == png
    # A rejected edit must not consume a history entry.
    history(page, "Undo")
    assert spec(page, url) == one
    history(page, "Redo")
    assert spec(page, url) == accepted
    add_layer(page, "swarmplot", {**roles, "marker": "o"})
    expect(page.locator(".error")).to_be_visible()
    assert spec(page, url) == accepted and preview(page, url) == png
    raw_action(
        page,
        {
            "type": "SetLiveFacets",
            "col": "cohort",
            "col_order": ["left", "empty", "right"],
            "col_wrap": 2,
        },
    )
    live = spec(page, url)
    assert len(live["panels"]) == 3 and live["facet_template"]["selectors"] == [
        {"cohort": "left"},
        {"cohort": "empty"},
        {"cohort": "right"},
    ]
    raw_action(page, {"type": "SetTitle", "text": "Local view only", "panel": 0})
    local = spec(page, url)
    with page.expect_download() as download:
        page.locator('.exports a[href="/spec.json"]').click()
    downloaded = output / "local.mplot.json"
    download.value.save_as(downloaded)
    opened(page, json.loads(downloaded.read_text()))
    assert (
        spec(page, url) == local
        and spec(page, url)["panels"][0]["title"] == "Local view only"
    )
    native_swarm_proof(local, scalar="s", styles=["s", "^"], expected_counts=[3, 0, 3])
    template = copy.deepcopy(local["facet_template"]["template"])
    for layer in template["layers"]:
        layer["pack_scope"] = "changed-membership"
    template["layers"][0]["marker"] = "v"
    template["layers"][1]["semantics"]["markers"] = ["D", "^"]
    template["layers"][1]["semantics"]["sizes"] = [4, 8]
    raw_action(page, {"type": "SetFacetTemplate", "template": template})
    edited = spec(page, url)
    assert edited["panels"][0]["title"] != "Local view only"
    assert all(
        layer["pack_scope"] == "changed-membership"
        for panel in edited["panels"]
        for layer in panel["layers"]
    )
    native_swarm_proof(edited, scalar="v", styles=["D", "^"], expected_counts=[3, 0, 3])
    edited_png = preview(page, url)
    invalid = copy.deepcopy(template)
    invalid["layers"][1]["width"] = 0.3
    raw_action(page, {"type": "SetFacetTemplate", "template": invalid})
    expect(page.locator(".error")).to_be_visible()
    assert spec(page, url) == edited and preview(page, url) == edited_png
    history(page, "Undo")
    assert spec(page, url) == local
    history(page, "Redo")
    assert spec(page, url) == edited
    assert preview(page, url) == edited_png
    for extension in ["png", "svg", "pdf", "json"]:
        endpoint = "/spec.json" if extension == "json" else "/fig." + extension
        async_name = (
            "edited.mplot.json" if extension == "json" else "edited." + extension
        )
        with page.expect_download() as download:
            page.locator(f'.exports a[href="{endpoint}"]').click()
        target = output / async_name
        download.value.save_as(target)
        if extension == "png":
            assert Image.open(target).size == (2000, 1166)
        elif extension == "svg":
            tree = ET.fromstring(target.read_bytes())
            assert (
                tree.tag.endswith("svg")
                and float(tree.attrib["width"].removesuffix("pt")) == 864
            )
        elif extension == "pdf":
            import subprocess

            info = subprocess.run(
                ["pdfinfo", str(target)], capture_output=True, text=True, check=True
            ).stdout
            assert "864 x 504 pts" in info
    opened(page, json.loads((output / "edited.mplot.json").read_text()))
    assert spec(page, url) == edited
    assert spec(page, url)["data"]["columns"] == data
    page.screenshot(path=str(output / "surface.png"), full_page=True)
    context.close()


def test_real_registered_spectrum_form_preserves_weak_coherence_and_rejected_state(
    rust_browser,
):
    browser, url, directory = rust_browser
    context = browser.new_context(viewport={"width": 1400, "height": 1100})
    page = context.new_page()
    page.goto(url)
    signal = [1, 1e-200, -1, 1e-200] * 4
    base = mp.plot({"signal": signal, "id": list(range(16))}).size(8, 4)
    opened(page, json.loads(base.to_json()))
    fields = {
        "x": "signal",
        "y": "signal",
        "spectrum": {
            "fs": 4,
            "kind": "coherence",
            "nfft": 4,
            "window": "boxcar",
            "pad_to": None,
            "overlap": 0,
            "detrend": "none",
            "sides": "onesided",
            "scaling": "density",
            "scale": "linear",
        },
        "label": "Same-channel coherence",
    }
    add_layer(page, "spectrum", fields)
    accepted = spec(page, url)
    png = preview(page, url)
    assert accepted["data"]["columns"]["signal"] == signal
    native = mp.Plot.from_json(json.dumps(accepted)).render()
    try:
        values = np.ma.asarray(native.axes[0].lines[0].get_ydata())
        assert not np.ma.getmaskarray(values).any()
        np.testing.assert_allclose(values, [1, 1, 1])
        np.testing.assert_array_equal(native.axes[0].lines[0].get_xdata(), [0, 1, 2])
    finally:
        import matplotlib.pyplot as plt

        plt.close(native)
    bad = copy.deepcopy(fields)
    bad["spectrum"]["fs"] = False
    add_layer(page, "spectrum", bad)
    expect(page.locator(".error")).to_be_visible()
    assert spec(page, url) == accepted and preview(page, url) == png
    history(page, "Undo")
    assert spec(page, url)["panels"][0]["layers"] == []
    history(page, "Redo")
    assert spec(page, url) == accepted
    output = directory / "integrated-spectrum"
    output.mkdir(exist_ok=True)
    (output / "weak-native.png").write_bytes(png)
    with page.expect_download() as download:
        page.locator('.exports a[href="/spec.json"]').click()
    download.value.save_as(output / "weak-source.mplot.json")
    page.screenshot(path=str(output / "weak-surface.png"), full_page=True)
    # Separate, well-conditioned odd-padding edit through the actual JSON form.
    # Weak-bin normalization is not an exact-arithmetic FFT promise.
    conditioned = copy.deepcopy(accepted)
    conditioned["data"]["columns"]["signal"] = [1, 1e-3, -1, 1e-3] * 4
    conditioned["panels"][0]["layers"][0]["spectrum"]["pad_to"] = 5
    opened(page, conditioned)
    accepted = spec(page, url)
    native = mp.Plot.from_json(json.dumps(accepted)).render()
    try:
        samples = np.array([1, 1e-3, -1, 1e-3])
        coefficient = (
            np.exp(-2j * np.pi * np.outer(np.arange(3), np.arange(4)) / 5) @ samples
        )
        assert np.all(np.abs(coefficient) > 1e-4)
        power = np.abs(coefficient) ** 2
        expected = np.abs(np.conj(coefficient) * coefficient) ** 2 / (power * power)
        values = np.ma.asarray(native.axes[0].lines[0].get_ydata())
        assert not np.ma.getmaskarray(values).any()
        np.testing.assert_allclose(values, expected, rtol=1e-12)
        np.testing.assert_array_equal(
            native.axes[0].lines[0].get_xdata(), [0, 0.8, 1.6]
        )
    finally:
        plt.close(native)
    for extension in ["png", "svg", "pdf", "json"]:
        endpoint = "/spec.json" if extension == "json" else "/fig." + extension
        with page.expect_download() as download:
            page.locator(f'.exports a[href="{endpoint}"]').click()
        download.value.save_as(output / ("spectrum." + extension))
    opened(page, json.loads((output / "spectrum.json").read_text()))
    assert spec(page, url) == accepted
    page.screenshot(path=str(output / "surface.png"), full_page=True)
    context.close()
