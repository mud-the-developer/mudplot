"""Real populated C05 forms: weights/bands/raw hue/roles, atomic errors and reopen."""

from __future__ import annotations

import hashlib
import io
import json
import xml.etree.ElementTree as ET

import matplotlib.pyplot as plt
import mudplot as mp
import numpy as np
import pytest
from matplotlib.colors import to_rgba
from matplotlib.patches import Polygon
from PIL import Image

pytest.importorskip("playwright.sync_api")
from playwright.sync_api import expect

pytest_plugins = ["test_editor_browser", "test_rust_specialized_controls"]


def settle(page):
    page.wait_for_function(
        "() => !document.querySelector('.htmx-request,.htmx-swapping,.htmx-settling')"
    )
    page.locator(".preview-wrap img").evaluate("image => image.decode()")


def disclose(form):
    ancestors = form.locator("xpath=ancestor::details")
    for index in range(ancestors.count() - 1, -1, -1):
        details = ancestors.nth(index)
        if not details.evaluate("element => element.open"):
            details.locator("summary").first.click()


def open_document(page, raw):
    form = page.locator('form[hx-post="/open"]')
    disclose(form)
    form.locator('textarea[name="json"]').fill(json.dumps(raw))
    form.locator('button[type="submit"]').click()
    settle(page)


def displayed_surface(page, url):
    actual = page.locator(".preview-wrap img").evaluate("""async image => {
      await image.decode();
      const canvas = document.createElement('canvas');
      canvas.width=image.naturalWidth;canvas.height=image.naturalHeight;
      const context=canvas.getContext('2d');context.drawImage(image,0,0);
      const pixels=context.getImageData(0,0,canvas.width,canvas.height).data;
      const hash=await crypto.subtle.digest('SHA-256',pixels.buffer);
      const hex=Array.from(new Uint8Array(hash),
          v=>v.toString(16).padStart(2,'0')).join('');
      return {size:[canvas.width,canvas.height],hash:hex};
    }""")
    response = page.request.get(url + "/fig.png")
    assert response.ok
    with Image.open(io.BytesIO(response.body())) as raster:
        assert actual["size"] == list(raster.size)
        assert (
            actual["hash"]
            == hashlib.sha256(raster.convert("RGBA").tobytes()).hexdigest()
        )
    return actual["hash"]


def replacement_form(page):
    details = page.locator('[data-key="replace-layer-0-0"]')
    expect(details).to_be_visible()
    if not details.evaluate("element => element.open"):
        details.locator("summary").click()
    return details.locator('form[hx-post="/action/raw"]')


def replace_from_populated_form(page, change):
    form = replacement_form(page)
    field = form.locator('textarea[name="json"]')
    payload = json.loads(field.input_value())
    assert (
        payload["type"] == "ReplaceLayer"
        and payload["panel"] == payload["layer_index"] == 0
    )
    change(payload["layer"])
    field.fill(json.dumps(payload))
    form.get_by_role("button", name="Replace layer", exact=True).click()
    settle(page)


def actual_native_proof(raw, *, median, tails, edited):
    figure = mp.Plot.from_json(json.dumps(raw)).render()
    try:
        axis = figure.axes[0]
        np.testing.assert_array_equal(axis.lines[0].get_ydata(), [median, median])
        np.testing.assert_array_equal(axis.lines[1].get_ydata(), tails)
        real = [patch for patch in axis.patches if isinstance(patch, Polygon)]
        assert len(real) == 6  # two requested raw hues, three retained bands each
        if edited:
            np.testing.assert_allclose(
                np.asarray(real[1].get_facecolor()), to_rgba("#aa0000", 0.8)
            )
            np.testing.assert_allclose(
                np.asarray(real[5].get_facecolor()), to_rgba("#008800", 0.9)
            )
            assert real[1].get_linewidth() == 0.5 and real[4].get_linewidth() == 2
            assert [axis.lines[i].get_marker() for i in (1, 3)] == ["P", "X"]
    finally:
        plt.close(figure)


@pytest.mark.parametrize("frontend", ["python", "rust"])
@pytest.mark.parametrize("width", [1400, 540])
def test_real_populated_boxen_replacement_lifecycle(request, tmp_path, frontend, width):
    if frontend == "python":
        page, url = request.getfixturevalue("editor")
        page.set_viewport_size({"width": width, "height": 1000})
        owned = False
    else:
        browser = request.getfixturevalue("browser")
        url, _ = request.getfixturevalue("rust_editor_server")
        page = browser.new_page(viewport={"width": width, "height": 1000})
        page.goto(url)
        owned = True
    try:
        data = {
            "c": ["A"] * 10,
            "v": [0, 1, 2, 8, 30, 10, 11, 12, 18, 40],
            "w": [1, 2, 2, 1, 0.1] * 2,
            "w_alt": [0.1, 2, 2, 1, 0.1] * 2,
            "h": ["left"] * 5 + ["right"] * 5,
            "protocol": ["A"] * 5 + ["B"] * 5,
            "stroke": [1] * 5 + [2] * 5,
        }
        start = mp.plot(data).size(7, 4).mosaic([["data", "spare"]])
        open_document(page, json.loads(start.to_json()))
        fields = {
            "x": "c",
            "y": "v",
            "group": "h",
            "weights": "w",
            "k_depth": 2,
            "alpha": 0.8,
            "boxen": {
                "band_components": [
                    {"rank": 0, "side": "central", "body": {"color": "#112233"}}
                ],
                "hue_components": [
                    {"level": "right", "components": {"body": {"alpha": 0.9}}}
                ],
            },
        }
        if frontend == "rust":
            form = page.locator('form[hx-post="/layers"]')
            disclose(form)
            form.locator('select[name="layer_type"]').select_option("boxenplot")
            form.locator('textarea[name="fields"]').fill(json.dumps(fields))
        else:
            form = page.locator('form[hx-post="/action"]').filter(
                has=page.locator('input[name="type"][value="add_layer_json"]')
            )
            disclose(form)
            form.locator('select[name="layer_type"]').select_option("boxenplot")
            form.locator('textarea[name="layer_json"]').fill(json.dumps(fields))
        form.get_by_role("button", name="Add layer", exact=True).click()
        settle(page)
        before = page.request.get(url + "/spec.json").json()
        before_surface = displayed_surface(page, url)
        actual_native_proof(before, median=2, tails=[30], edited=False)

        def edit(layer):
            layer["weights"] = "w_alt"
            layer["semantics"] = {
                "size": "stroke",
                "sizes": [0.5, 2],
                "style": "protocol",
                "markers": ["P", "X"],
            }
            layer["boxen"]["band_components"][0]["body"]["color"] = "#aa0000"
            layer["boxen"]["hue_components"][0]["band_components"] = [
                {"rank": 1, "side": "upper", "body": {"color": "#008800"}}
            ]

        replace_from_populated_form(page, edit)
        after = page.request.get(url + "/spec.json").json()
        after_surface = displayed_surface(page, url)
        assert after_surface != before_surface
        actual_native_proof(after, median=2, tails=[0, 30], edited=True)
        assert after["data"]["columns"] == data
        assert [panel["panel_id"] for panel in after["panels"]] == ["data", "spare"]

        def invalid(layer):
            layer["boxen"]["band_components"][0]["body"]["line_width"] = 7

        replace_from_populated_form(page, invalid)
        expect(page.locator(".error")).to_be_visible()
        assert page.request.get(url + "/spec.json").json() == after
        assert displayed_surface(page, url) == after_surface
        page.get_by_role("button", name="Undo", exact=True).click()
        settle(page)
        assert page.request.get(url + "/spec.json").json() == before
        assert displayed_surface(page, url) == before_surface
        page.get_by_role("button", name="Redo", exact=True).click()
        settle(page)
        assert page.request.get(url + "/spec.json").json() == after
        assert displayed_surface(page, url) == after_surface
        files = {}
        for suffix, endpoint in (
            ("json", "spec.json"),
            ("png", "fig.png"),
            ("svg", "fig.svg"),
            ("pdf", "fig.pdf"),
        ):
            with page.expect_download() as download:
                page.locator(f'a[href="/{endpoint}"]').click()
            destination = tmp_path / f"{frontend}-{width}.{suffix}"
            download.value.save_as(destination)
            files[suffix] = destination
        assert json.loads(files["json"].read_text()) == after
        with Image.open(files["png"]) as image:
            assert max(image.size) <= 2000  # documented cached preview, not exactsize
        vector = ET.parse(files["svg"]).getroot()
        width_pt, height_pt = vector.get("width"), vector.get("height")
        assert width_pt is not None and height_pt is not None
        assert float(width_pt.removesuffix("pt")) == 7 * 72
        assert float(height_pt.removesuffix("pt")) == 4 * 72
        assert b"/MediaBox" in files["pdf"].read_bytes()
        open_document(page, json.loads(files["json"].read_text()))
        assert displayed_surface(page, url) == after_surface
        replace_from_populated_form(page, lambda layer: layer.update(weights="w"))
        reopened = page.request.get(url + "/spec.json").json()
        actual_native_proof(reopened, median=2, tails=[30], edited=True)
        assert displayed_surface(page, url) != after_surface
    finally:
        if owned:
            page.close()
