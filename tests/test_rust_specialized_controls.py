"""Native-coordinate and installed-bridge consumers for CND01.

Set MUDPLOT_EDITOR_BIN and MUDPLOT_BRIDGE_PYTHON for real browser consumers.
CI supplies MUDPLOT_BRIDGE_SOURCE_ROOT for an explicitly labelled source profile;
omit it for independent installed-wheel proof. Required CI forbids missing setup.
"""

import copy
import io
import json
import os
import shutil
import socket
import subprocess
from dataclasses import replace
from pathlib import Path

import mudplot as mp
import pytest
from mudplot._layout_render import panel_legend


def document():
    raw = {
        "version": "0.1",
        "size": [8, 4],
        "dpi": 150,
        "layout": [1, 2],
        "data": {
            "columns": {
                "x": [1, 10, 100],
                "y": [1, 10, 100],
                "z": [1, 2, 3],
            }
        },
        "panels": [
            {
                "title": "Untouched",
                "layers": [
                    {"type": "line", "x": "x", "y": "y", "label": "first"},
                ],
            },
            {
                "title": "Active",
                "title_position": [0.5, 0.9],
                "title_citation": "paper2025",
                "title_href": "https://doi.org/10.1000/example",
                "x": {
                    "label": "Dose",
                    "scale": "log",
                    "limits": [100, 1],
                    "share_id": "dose",
                },
                "y": {"label": "Response", "scale": "log", "limits": [1, 100]},
                "legend": {
                    "frame": True,
                    "title": "Key",
                    "show": True,
                    "location": "upper left",
                    "bbox_to_anchor": [0.8, 0.5],
                },
                "layers": [
                    {"type": "line", "x": "x", "y": "y", "label": "series"},
                    {"type": "text", "text": "Measured", "at": [10, 10]},
                    {
                        "type": "annotate",
                        "text": "Peak",
                        "at": [20, 20],
                        "to": [10, 10],
                    },
                ],
            },
        ],
    }
    return mp.from_json(json.dumps(raw)).to_dict()


@pytest.mark.parametrize(
    "temporal,secondary", [(False, False), (False, True), (True, False), (True, True)]
)
def test_preview_metadata_matches_native_artist_transforms(temporal, secondary):
    import matplotlib.pyplot as plt
    from mudplot._editor import render_preview
    from mudplot._render import _save_figure, render
    from mudplot.spec import AxisSpec, TemporalSpec
    from PIL import Image

    figure = mp.from_json(json.dumps(document()))
    panel = figure.panels[1]
    if temporal:
        panel.x.scale = "linear"
        panel.x.temporal = TemporalSpec(timezone="UTC", unit="day", origin="1970-01-01")
    if secondary:
        panel.y2 = AxisSpec(scale="log", limits=[1000, 1])
        panel.layers[1].axis = "y2"
    before = mp.to_json(figure)
    png, layouts = render_preview(figure)
    native = render(figure)
    try:
        _save_figure(native, figure, io.BytesIO(), "png")
        ax = next(a for a in native.axes if getattr(a, "_mudplot_panel", None) == 1)
        target = getattr(ax, "_mudplot_secondary_axis", None) if secondary else ax
        handle = next(h for h in layouts[1]["handles"] if h["layer_index"] == 1)
        expected = (
            target.transData.transform([10, 10]) / native.canvas.get_width_height()
        )
        assert [handle["imgx"], handle["imgy"]] == pytest.approx(expected, abs=1e-12)
        assert handle["ylim"] == list(target.get_ylim())
        assert Image.open(io.BytesIO(png)).size == (1200, 600)
        assert tuple(layouts[1]["image_size"]) == Image.open(io.BytesIO(png)).size
        assert mp.to_json(figure) == before
    finally:
        plt.close(native)


@pytest.fixture(scope="module")
def rust_browser(request):
    if os.getenv("MUDPLOT_REQUIRE_BROWSER") == "1":
        from playwright import sync_api as playwright
    else:
        playwright = pytest.importorskip("playwright.sync_api")
    url, directory = request.getfixturevalue("rust_editor_server")
    with playwright.sync_playwright() as p:
        browser = p.chromium.launch(
            executable_path=shutil.which("chromium"), headless=True
        )
        try:
            yield browser, url, directory
        finally:
            browser.close()


def settle(page):
    page.locator(".htmx-request, .htmx-swapping, .htmx-settling").wait_for(
        state="hidden", timeout=15000
    )
    page.locator(".preview-wrap img").evaluate("image => image.decode()")


def opened(page, data):
    details = page.locator("details").filter(has=page.locator('form[hx-post="/open"]'))
    if not details.evaluate("d => d.open"):
        details.locator("summary").first.click()
    form = page.locator('form[hx-post="/open"]')
    form.locator("textarea").fill(json.dumps(data))
    form.locator("button").click()
    settle(page)


def selected(page, panel):
    page.locator('form[hx-post="/control/panel"] select').select_option(str(panel))
    page.get_by_role("button", name="Select panel", exact=True).click()
    settle(page)


def edit_axis(page, axis, operation, **values):
    form = page.locator(
        'form[hx-post="/control/axis"]'
        f':has(input[name="axis"][value="{axis}"])'
        f':has(input[name="operation"][value="{operation}"])'
    )
    for name, value in values.items():
        field = form.locator(f'[name="{name}"]')
        if name == "scale":
            field.select_option(value)
        else:
            field.fill(str(value))
    form.locator("button").click()
    settle(page)


def spec(page, url):
    return page.request.get(url + "/spec.json").json()


def point(figure, kind, index):
    panel = figure["panels"][1]
    if kind == "title":
        return panel["title_position"]
    if kind == "legend":
        return panel["legend"]["bbox_to_anchor"]
    return panel["layers"][int(index)]["at"]


def display_point(figure, fraction):
    width, height = figure.canvas.get_width_height()
    return [fraction[0] * width, fraction[1] * height]


def rendered_legend_center(document):
    import matplotlib.pyplot as plt
    from mudplot._render import _save_figure, render

    native = mp.from_json(json.dumps(document))
    native = replace(native, dpi=min(native.dpi, 2000 / max(native.size)))
    figure = render(native)
    try:
        _save_figure(figure, native, io.BytesIO(), "png")
        axis = next(a for a in figure.axes if getattr(a, "_mudplot_panel", None) == 1)
        legend = panel_legend(axis)
        assert legend is not None
        box = legend.get_window_extent(figure.canvas.get_renderer())
        return [(box.x0 + box.x1) / 2, (box.y0 + box.y1) / 2]
    finally:
        plt.close(figure)


def drag(page, handle, dx, dy):
    handle.scroll_into_view_if_needed()
    box = handle.bounding_box()
    image = page.locator(".preview-wrap img").bounding_box()
    x, y = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
    page.mouse.move(x, y)
    page.mouse.down()
    page.mouse.move(x + image["width"] * dx, y + image["height"] * dy, steps=8)
    page.mouse.up()
    settle(page)


def history(page, operation):
    page.get_by_role("button", name=operation, exact=True).press("Enter")
    settle(page)


@pytest.mark.parametrize("dpr,zoom,width", [(1, 1, 1400), (2, 1.25, 1000), (2, 1, 540)])
def test_rust_specialized_lifecycle_and_native_drag(rust_browser, dpr, zoom, width):
    import matplotlib.pyplot as plt
    from mudplot._render import _save_figure, render
    from PIL import Image
    from playwright.sync_api import expect

    browser, url, directory = rust_browser
    context = browser.new_context(
        viewport={"width": width, "height": 1100},
        device_scale_factor=dpr,
        reduced_motion="reduce",
    )
    page = context.new_page()
    initial = document()
    if dpr == 2:
        initial["dpi"] = 600
    page.goto(url)
    opened(page, initial)
    with page.expect_download() as initial_download:
        page.locator('.exports a[href="/spec.json"]').click()
    source_path = directory / f"initial-{dpr}-{width}.json"
    initial_download.value.save_as(source_path)
    source_bytes = source_path.read_bytes()
    opened(page, json.loads(source_bytes))
    selected(page, 1)
    traces = []
    page.evaluate("zoom => document.body.style.zoom = zoom", str(zoom))
    for name in ("width", "height"):
        field = page.locator(f'form[hx-post="/control/size"] input[name="{name}"]')
        assert field.evaluate("""el => {
            const style = getComputedStyle(el);
            const context = document.createElement("canvas").getContext("2d");
            context.font = style.font;
            return el.clientWidth - parseFloat(style.paddingLeft) -
                parseFloat(style.paddingRight) >= context.measureText(el.value).width;
        }""")
    original = spec(page, url)
    source = copy.deepcopy(original["data"])
    first = copy.deepcopy(original["panels"][0])
    title_form = page.locator('form[hx-post="/control/title"]')
    title_form.locator('[name="text"]').fill("Referenced title")
    title_form.locator("button").click()
    settle(page)
    assert spec(page, url)["panels"][1]["title"] == "Referenced title"
    assert spec(page, url)["panels"][1]["title_citation"] == "paper2025"
    assert (
        spec(page, url)["panels"][1]["title_href"] == "https://doi.org/10.1000/example"
    )
    edit_axis(page, "x", "label", text="Second dose")
    assert spec(page, url)["panels"][1]["x"]["share_id"] == "dose"
    assert spec(page, url)["panels"][1]["x"]["label"] == "Second dose"
    edit_axis(page, "y", "label", text="Second response")
    assert spec(page, url)["panels"][1]["y"]["label"] == "Second response"
    edit_axis(page, "x", "scale", scale="linear")
    assert spec(page, url)["panels"][1]["x"]["scale"] == "linear"
    edit_axis(page, "x", "scale", scale="log")
    edit_axis(page, "x", "limits", lo="50", hi="2")
    assert spec(page, url)["panels"][1]["x"]["limits"] == [50, 2]
    edit_axis(page, "x", "limits", lo="", hi="")
    assert spec(page, url)["panels"][1]["x"]["limits"] is None
    edit_axis(page, "y", "scale", scale="linear")
    edit_axis(page, "y", "limits", lo="2", hi="80")
    assert spec(page, url)["panels"][1]["y"]["limits"] == [2, 80]
    edit_axis(page, "y", "limits", lo="", hi="")
    assert spec(page, url)["panels"][1]["y"]["limits"] is None
    page.get_by_role("button", name="Enable secondary y axis", exact=True).click()
    settle(page)
    edit_axis(page, "y2", "label", text="Secondary")
    edit_axis(page, "y2", "limits", lo="1", hi="1000")
    edit_axis(page, "y2", "scale", scale="log")
    assert spec(page, url)["panels"][1]["y2"]["label"] == "Secondary"
    assert spec(page, url)["panels"][1]["y2"]["limits"] == [1, 1000]
    assert spec(page, url)["panels"][1]["y2"]["scale"] == "log"
    page.get_by_role("button", name="Remove secondary y axis", exact=True).click()
    settle(page)
    assert spec(page, url)["panels"][1]["y2"] is None

    data = document()
    data["dpi"] = initial["dpi"]
    data["panels"][1]["y2"] = {"scale": "log", "limits": [1000, 1]}
    data["panels"][1]["layers"][1]["axis"] = "y2"
    opened(page, data)
    selected(page, 1)
    for kind, index in [
        ("title", ""),
        ("legend", ""),
        ("layer-at", "1"),
        ("layer-at", "2"),
    ]:
        before = spec(page, url)
        layout = json.loads(page.locator(".preview-wrap").get_attribute("data-layout"))
        h = next(
            h
            for h in layout["handles"]
            if h["kind"] == kind
            and (kind != "layer-at" or h["layer_index"] == int(index))
        )
        handle = page.locator(f'[data-handle-id="{kind}:{index}:1"]')
        native = mp.from_json(json.dumps(before))
        native = replace(native, dpi=min(native.dpi, 2000 / max(native.size)))
        figure = render(native)
        try:
            _save_figure(figure, native, io.BytesIO(), "png")
            ax = next(a for a in figure.axes if getattr(a, "_mudplot_panel", None) == 1)
            if kind == "legend":
                transform = figure.transFigure
            elif kind == "title":
                transform = ax.transAxes
            else:
                target = (
                    getattr(ax, "_mudplot_secondary_axis", None) if index == "1" else ax
                )
                transform = target.transData
            fraction = [h["imgx"] + 0.025, h["imgy"] - 0.025]
            expected_pixels = display_point(figure, fraction)
            expected_key_pixels = display_point(
                figure, [fraction[0] + 0.02, fraction[1]]
            )
            if kind == "legend":
                legend = panel_legend(ax)
                assert legend is not None
                box = legend.get_window_extent(figure.canvas.get_renderer())
                canvas_width, canvas_height = figure.canvas.get_width_height()
                expected_pixels = [
                    (box.x0 + box.x1) / 2 + 0.025 * canvas_width,
                    (box.y0 + box.y1) / 2 - 0.025 * canvas_height,
                ]
                expected_key_pixels = [
                    expected_pixels[0] + 0.02 * canvas_width,
                    expected_pixels[1],
                ]
            expected = transform.inverted().transform(display_point(figure, fraction))
            expected_keyboard = transform.inverted().transform(
                display_point(figure, [fraction[0] + 0.02, fraction[1]])
            )
        finally:
            plt.close(figure)
        drag(page, handle, 0.025, 0.025)
        changed = spec(page, url)
        actual = point(changed, kind, index)
        assert actual == pytest.approx(expected, rel=0.003, abs=0.003)
        if kind == "legend":
            pointer_box_center = rendered_legend_center(changed)
            assert pointer_box_center == pytest.approx(expected_pixels, abs=1)
        handle.focus()
        page.keyboard.press("ArrowRight")
        page.wait_for_timeout(250)
        settle(page)
        expect(handle).to_be_focused()
        keyboard = spec(page, url)
        keyboard_at = point(keyboard, kind, index)
        assert keyboard_at == pytest.approx(expected_keyboard, rel=0.003, abs=0.003)
        for field in ("title_citation", "title_href"):
            assert keyboard["panels"][1][field] == before["panels"][1][field]
        if kind == "legend":
            for field in ("show", "title", "location", "frame"):
                assert (
                    keyboard["panels"][1]["legend"][field]
                    == before["panels"][1]["legend"][field]
                )
            keyboard_box_center = rendered_legend_center(keyboard)
            assert keyboard_box_center == pytest.approx(expected_key_pixels, abs=1)
            traces.append(
                {
                    "legend_bbox_pointer_pixels": pointer_box_center,
                    "expected_pointer_pixels": expected_pixels,
                    "legend_bbox_keyboard_pixels": keyboard_box_center,
                    "expected_keyboard_pixels": expected_key_pixels,
                    "retained_location": keyboard["panels"][1]["legend"]["location"],
                }
            )
        traces.append(
            {
                "kind": kind,
                "layer": index,
                "pointer": actual,
                "native_pointer": expected.tolist(),
                "keyboard": keyboard_at,
                "native_keyboard": expected_keyboard.tolist(),
                "layout": layout,
            }
        )
        history(page, "Undo")
        assert spec(page, url) == changed
        history(page, "Redo")
        assert spec(page, url) == keyboard
        assert keyboard["panels"][0] == first and keyboard["data"] == source
        assert keyboard["panels"][1]["layers"][2]["to"] == [10, 10]

    good = spec(page, url)
    pixels = page.request.get(url + "/fig.png").body()
    good_json = page.request.get(url + "/spec.json").body()
    stale_revision = (
        int(page.locator(".preview-wrap").get_attribute("data-revision")) - 1
    )
    response = page.request.post(
        url + "/control/move",
        form={
            "kind": "title",
            "panel": "1",
            "revision": str(stale_revision),
            "x": ".4",
            "y": ".4",
        },
    )
    assert "preview changed" in response.text()
    assert int(response.headers["x-mudplot-view-generation"]) == stale_revision + 1
    stale_image = page.request.get(url + f"/fig.png?revision={stale_revision}")
    assert stale_image.status == 409
    edit_axis(page, "x", "limits", lo="-1", hi="20")
    expect(page.get_by_role("alert")).to_be_visible()
    assert spec(page, url) == good
    assert page.request.get(url + "/fig.png").body() == pixels
    history(page, "Undo")
    assert spec(page, url) == changed
    rejected_pixels = page.request.get(url + "/fig.png").body()
    layer_form = page.locator('form[hx-post="/layers"]')
    layer_form.locator('[name="layer_type"]').select_option("line")
    layer_form.locator('[name="fields"]').fill(
        json.dumps(
            {
                "x": "x",
                "y": "y",
                "color": "not-a-colour",
            }
        )
    )
    layer_form.locator("button").click()
    settle(page)
    expect(page.get_by_role("alert")).to_contain_text("not-a-colour")
    assert spec(page, url) == changed
    assert page.request.get(url + "/fig.png").body() == rejected_pixels
    history(page, "Redo")
    assert spec(page, url) == good
    assert page.request.get(url + "/fig.png").body() == pixels
    assert page.request.get(url + "/spec.json").body() == good_json
    saved = page.request.get(url + "/spec.json").body()
    opened(page, json.loads(saved))
    assert spec(page, url) == good
    for ext in ("png", "svg", "pdf"):
        with page.expect_download() as download:
            page.locator(f'.exports a[href="/fig.{ext}"]').click()
        path = directory / f"specialized-{dpr}-{width}.{ext}"
        download.value.save_as(path)
        raw = path.read_bytes()
        if ext == "png":
            expected_size = (1200, 600) if initial["dpi"] == 150 else (2000, 1000)
            assert Image.open(io.BytesIO(raw)).size == expected_size
        elif ext == "svg":
            import xml.etree.ElementTree as ET

            tree = ET.fromstring(raw)
            assert tree.tag.endswith("svg") and "576" in tree.attrib["width"]
        else:
            info = subprocess.run(
                ["pdfinfo", str(path)], capture_output=True, text=True, check=True
            ).stdout
            assert "Pages:           1" in info and "576 x 288 pts" in info
    page.screenshot(
        path=str(directory / f"specialized-{dpr}-{width}-browser.png"), full_page=True
    )

    from datetime import datetime

    from matplotlib.dates import date2num

    temporal = document()
    timestamps = [
        "2025-01-01T00:00:00Z",
        "2025-01-04T12:00:00Z",
        "2025-01-10T00:00:00Z",
    ]
    temporal["data"]["columns"]["dates"] = timestamps
    days = [float(date2num(datetime.fromisoformat(v))) for v in timestamps]
    temporal["panels"][1]["y2"] = {
        "label": "Date",
        "temporal": {
            "timezone": "UTC",
            "unit": "day",
            "origin": "1970-01-01",
        },
    }
    temporal["panels"][1]["x"] = {
        "temporal": {"timezone": "UTC"},
        "limits": [days[-1], days[0]],
    }
    temporal["panels"][1]["layers"][0]["x"] = "dates"
    temporal["panels"][1]["layers"][1].update(axis="y2", at=[days[1], 10])
    temporal["panels"][1]["layers"][2].update(at=[days[1], 20], to=[days[0], 10])
    opened(page, temporal)
    selected(page, 1)
    clock = spec(page, url)["panels"][1]["y2"]["temporal"]
    edit_axis(page, "y2", "label", text="Clock preserved")
    edit_axis(page, "y2", "limits", lo="1", hi="100")
    assert spec(page, url)["panels"][1]["y2"]["temporal"] == clock
    handle = page.locator('[data-handle-id="layer-at:1:1"]')
    layout = json.loads(page.locator(".preview-wrap").get_attribute("data-layout"))
    expected_date = days[1] - 0.02 * (days[-1] - days[0]) / (
        layout["panel_bbox"][2] - layout["panel_bbox"][0]
    )
    drag(page, handle, 0.02, 0)
    moved_date = spec(page, url)["panels"][1]["layers"][1]["at"]
    assert moved_date == pytest.approx([expected_date, 10], abs=0.003)
    handle.focus()
    page.keyboard.press("ArrowRight")
    page.wait_for_timeout(250)
    settle(page)
    assert spec(page, url)["panels"][1]["layers"][1]["at"][0] < moved_date[0]
    assert spec(page, url)["data"] == temporal["data"]
    three = document()
    three["panels"][1] = {"title": "3D", "layers": []}
    opened(page, three)
    selected(page, 1)
    projection = page.locator('form[hx-post="/control/projection"]')
    projection.locator("select").select_option("3d")
    projection.locator("button").click()
    settle(page)
    page.get_by_role("button", name="Set up z axis", exact=True).click()
    settle(page)
    edit_axis(page, "z", "label", text="Height")
    edit_axis(page, "z", "limits", lo="1", hi="100")
    edit_axis(page, "z", "scale", scale="log")
    z_axis = spec(page, url)["panels"][1]["z"]
    assert z_axis["label"] == "Height" and z_axis["scale"] == "log"
    assert z_axis["limits"] == [1, 100]
    assert page.locator(".drag-handle.title, .drag-handle.layer-at").count() == 0
    polar = document()
    polar["data"]["columns"].update(theta=[0, 1, 2], radius=[1, 2, 3])
    polar["panels"][1] = {
        "projection": "polar",
        "title": "Polar title",
        "title_position": [0.5, 0.85],
        "legend": {"bbox_to_anchor": [0.8, 0.7]},
        "layers": [{"type": "line", "x": "theta", "y": "radius", "label": "Polar"}],
    }
    opened(page, polar)
    selected(page, 1)
    for kind in ("title", "legend"):
        before = spec(page, url)
        layout = json.loads(page.locator(".preview-wrap").get_attribute("data-layout"))
        handle_data = next(h for h in layout["handles"] if h["kind"] == kind)
        native = mp.from_json(json.dumps(before))
        figure = render(native)
        try:
            _save_figure(figure, native, io.BytesIO(), "png")
            ax = next(a for a in figure.axes if getattr(a, "_mudplot_panel", None) == 1)
            transform = figure.transFigure if kind == "legend" else ax.transAxes
            fraction = [handle_data["imgx"] + 0.02, handle_data["imgy"] + 0.02]
            expected = transform.inverted().transform(display_point(figure, fraction))
            expected_key = transform.inverted().transform(
                display_point(figure, [fraction[0] - 0.02, fraction[1]])
            )
        finally:
            plt.close(figure)
        handle = page.locator(f'[data-handle-id="{kind}::1"]')
        drag(page, handle, 0.02, -0.02)
        moved = spec(page, url)
        assert point(moved, kind, "") == pytest.approx(expected, abs=0.003)
        handle.focus()
        page.keyboard.press("ArrowLeft")
        page.wait_for_timeout(250)
        settle(page)
        keyed = spec(page, url)
        assert point(keyed, kind, "") == pytest.approx(expected_key, abs=0.003)
        history(page, "Undo")
        assert spec(page, url) == moved
        history(page, "Redo")
        assert spec(page, url) == keyed
        assert keyed["data"] == polar["data"]
        traces.append(
            {
                "projection": "polar",
                "kind": kind,
                "pointer": point(moved, kind, ""),
                "native_pointer": expected.tolist(),
                "keyboard": point(keyed, kind, ""),
                "native_keyboard": expected_key.tolist(),
            }
        )
    polar_json = page.request.get(url + "/spec.json").body()
    polar_png = page.request.get(url + "/fig.png").body()
    layer_form = page.locator('form[hx-post="/layers"]')
    layer_form.locator('[name="layer_type"]').select_option("text")
    layer_form.locator('[name="fields"]').fill(
        json.dumps({"text": "Unsupported polar data anchor", "at": [0.5, 1.5]})
    )
    layer_form.locator("button").click()
    settle(page)
    expect(page.get_by_role("alert")).to_contain_text("not supported on a polar")
    assert page.request.get(url + "/spec.json").body() == polar_json
    assert page.request.get(url + "/fig.png").body() == polar_png
    assert page.locator(".drag-handle.layer-at").count() == 0
    page.screenshot(
        path=str(directory / f"polar-{dpr}-{width}-browser.png"), full_page=True
    )
    assert source_path.read_bytes() == source_bytes
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1")
    traces.append(
        {
            "temporal_pointer": moved_date,
            "native_temporal_x": expected_date,
            "timestamps": timestamps,
            "retained_y2_clock": clock,
            "dpi": initial["dpi"],
            "dpr": dpr,
            "zoom": zoom,
            "width": width,
        }
    )
    (directory / f"trace-{dpr}-{width}.json").write_text(
        json.dumps(traces, indent=2), encoding="utf-8"
    )
    context.close()


def test_bridge_cli_preview_metadata_and_core_boundary(tmp_path):
    python = os.getenv("MUDPLOT_BRIDGE_PYTHON")
    if not python:
        pytest.skip("independently installed wheel required")
    source_path = tmp_path / "source.json"
    source_bytes = json.dumps(document()).encode()
    source_path.write_bytes(source_bytes)
    action_path = tmp_path / "action.json"
    action_path.write_text(
        json.dumps(
            {
                "type": "SetAxisLabel",
                "axis": "x",
                "text": "Installed CLI",
                "panel": 1,
            }
        )
    )
    next_path = tmp_path / "next.json"
    env = os.environ.copy()
    if os.getenv("MUDPLOT_BRIDGE_SOURCE_ROOT"):
        env["PYTHONPATH"] = os.environ["MUDPLOT_BRIDGE_SOURCE_ROOT"]
    else:
        env.pop("PYTHONPATH", None)
    env["MPLBACKEND"] = "Agg"

    def cli(*args, success=True):
        result = subprocess.run(
            [python, "-m", "mudplot", *map(str, args)],
            cwd=tmp_path,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        assert (result.returncode == 0) == success, result.stderr
        return result

    cli("apply", source_path, action_path, "-o", next_path)
    assert (
        json.loads(next_path.read_bytes())["panels"][1]["x"]["label"] == "Installed CLI"
    )
    output = tmp_path / "preview.png"
    metadata = tmp_path / "metadata.json"
    overlap = cli(
        "render",
        source_path,
        output,
        "--preview",
        "--editor-metadata",
        source_path,
        success=False,
    )
    assert "must be distinct" in overlap.stderr
    assert source_path.read_bytes() == source_bytes and not output.exists()
    cli("render", next_path, output, "--preview", "--editor-metadata", metadata)
    from PIL import Image

    assert Image.open(output).size == (1200, 600)
    panels = json.loads(metadata.read_bytes())
    assert len(panels) == 2 and panels[1]["xlim"] == [100, 1]
    assert {h["kind"] for h in panels[1]["handles"]} == {"title", "legend", "layer-at"}
    bad = document()
    bad["panels"][1]["layers"][0]["color"] = "not-a-colour"
    bad_path = tmp_path / "bad.json"
    bad_path.write_text(json.dumps(bad))
    rejected = cli(
        "render",
        bad_path,
        tmp_path / "rejected.png",
        "--preview",
        "--editor-metadata",
        tmp_path / "rejected.json",
        success=False,
    )
    assert "not-a-colour" in rejected.stderr
    assert not (tmp_path / "rejected.png").exists()
    assert not (tmp_path / "rejected.json").exists()
    assert source_path.read_bytes() == source_bytes
    script = (
        "import json,sys,mudplot; mudplot.capabilities(); "
        "assert 'numpy' not in sys.modules and 'matplotlib' not in sys.modules "
        "and 'dashboard' not in sys.modules; "
        "print(json.dumps({'module':mudplot.__file__,'version':mudplot.__version__}))"
    )
    core = subprocess.run(
        [python, "-S", "-c", script],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    runtime = json.loads(core.stdout)
    assert runtime["version"] == mp.__version__
    runtime_module = Path(runtime["module"]).resolve(strict=True)
    assert (
        runtime_module.name == "__init__.py" and runtime_module.parent.name == "mudplot"
    )
    source_root = os.getenv("MUDPLOT_BRIDGE_SOURCE_ROOT")
    if source_root:
        assert runtime_module == Path(source_root).resolve() / "mudplot" / "__init__.py"
    else:
        assert not runtime_module.is_relative_to(
            Path(__file__).resolve().parents[1] / "mudplot"
        )
    runtime["profile"] = (
        "source" if os.getenv("MUDPLOT_BRIDGE_SOURCE_ROOT") else "installed"
    )
    (tmp_path / "bridge-runtime.json").write_text(json.dumps(runtime))


def test_specialized_routes_keep_existing_local_boundary(rust_browser):
    from urllib.parse import urlsplit

    browser, url, _ = rust_browser
    context = browser.new_context()
    client = context.request
    response = client.post(url + "/open", form={"json": json.dumps(document())})
    assert response.status == 200
    original = client.get(url + "/spec.json").body()
    png = client.get(url + "/fig.png").body()
    for route in ("panel", "axis", "secondary", "z", "move"):
        denied = client.post(
            url + "/control/" + route,
            form={"panel": "0"},
            headers={"Origin": "https://attacker.invalid"},
        )
        assert denied.status == 403
        assert "script-src 'self'" in denied.headers["content-security-policy"]
        rebinding = client.post(
            url + "/control/" + route,
            form={"panel": "0"},
            headers={"Host": "attacker.invalid"},
        )
        assert rebinding.status == 403
    address = urlsplit(url)
    with socket.create_connection(
        (address.hostname, address.port), timeout=10
    ) as connection:
        connection.sendall(
            (
                "POST /control/move HTTP/1.1\r\n"
                f"Host: {address.netloc}\r\n"
                "Content-Length: 16777217\r\nConnection: close\r\n\r\n"
            ).encode("ascii")
        )
        status = connection.recv(4096).split(b"\r\n", 1)[0]
        assert b" 413 " in status
    assert client.get(url + "/spec.json").body() == original
    assert client.get(url + "/fig.png").body() == png
    context.close()


@pytest.mark.parametrize("document", [{}, {"version": "0.1"}])
def test_sparse_legacy_open_has_immediately_usable_rendered_axes(
    rust_browser, document
):
    from playwright.sync_api import expect

    browser, url, directory = rust_browser
    context = browser.new_context()
    page = context.new_page()
    page.goto(url)
    for operation in ("label", "limits", "secondary"):
        opened(page, document)
        sparse = page.request.get(url + "/spec.json").body()
        before = json.loads(sparse)
        assert "panels" not in before
        pixels_before = page.request.get(url + "/fig.png").body()
        assert page.locator('form[hx-post="/control/panel"] option').count() == 1
        assert page.locator('form[hx-post="/control/axis"]').count() == 6
        expect(
            page.locator('form[hx-post="/control/size"] [name="width"]')
        ).to_have_value("3.5")
        expect(
            page.locator('form[hx-post="/control/size"] [name="height"]')
        ).to_have_value("2.625")
        selected(page, 0)
        assert page.request.get(url + "/spec.json").body() == sparse
        assert page.request.get(url + "/fig.png").body() == pixels_before
        if operation == "label":
            edit_axis(page, "x", "label", text="Sparse x label")
            assert spec(page, url)["panels"][0]["x"]["label"] == "Sparse x label"
        elif operation == "limits":
            edit_axis(page, "x", "limits", lo="2", hi="8")
            assert spec(page, url)["panels"][0]["x"]["limits"] == [2, 8]
        else:
            page.get_by_role(
                "button", name="Enable secondary y axis", exact=True
            ).click()
            settle(page)
            assert spec(page, url)["panels"][0]["y2"] is not None
        assert page.get_by_role("alert").count() == 0
        edited = page.request.get(url + "/spec.json").body()
        edited_pixels = page.request.get(url + "/fig.png").body()
        assert edited_pixels != pixels_before
        history(page, "Undo")
        assert page.request.get(url + "/spec.json").body() == sparse
        assert page.request.get(url + "/fig.png").body() == pixels_before
        history(page, "Redo")
        assert page.request.get(url + "/spec.json").body() == edited
        assert page.request.get(url + "/fig.png").body() == edited_pixels
        opened(page, json.loads(edited))
        assert page.request.get(url + "/spec.json").body() == edited
        (directory / f"sparse-{len(document)}-{operation}.json").write_bytes(edited)
    page.screenshot(
        path=str(directory / f"sparse-{len(document)}-browser.png"), full_page=True
    )
    context.close()


def test_real_secondary_touch_and_cancel_do_not_own_primary_edit(rust_browser):
    browser, url, directory = rust_browser
    context = browser.new_context(has_touch=True)
    page = context.new_page()
    page.goto(url)
    opened(
        page,
        {
            "version": "0.1",
            "size": [5, 3.5],
            "panels": [
                {
                    "title": "Pointer ownership",
                    "title_position": [0.5, 0.7],
                    "layers": [],
                }
            ],
        },
    )
    before = page.request.get(url + "/spec.json").body()
    pixels_before = page.request.get(url + "/fig.png").body()
    revision = page.locator(".preview-wrap").get_attribute("data-revision")
    handle = page.locator(".drag-handle.title")
    handle.scroll_into_view_if_needed()
    box = handle.bounding_box()
    x, y = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
    page.evaluate("""() => {
        window.pointerTrace = [];
        ["pointerdown", "pointermove", "pointerup", "pointercancel"].forEach(type =>
            document.addEventListener(type, event => window.pointerTrace.push({
                type, id: event.pointerId, primary: event.isPrimary,
                trusted: event.isTrusted, handle: event.target.dataset?.handleId
            }), true));
    }""")
    cdp = context.new_cdp_session(page)
    first = {"x": x, "y": y, "id": 1}
    second = {"x": x + 2, "y": y + 2, "id": 2}
    moved = {"x": x + 42, "y": y + 22, "id": 2}
    for kind, points in [
        ("touchStart", [first]),
        ("touchStart", [first, second]),
        ("touchMove", [first, moved]),
        ("touchEnd", [first]),
        ("touchCancel", []),
    ]:
        cdp.send("Input.dispatchTouchEvent", {"type": kind, "touchPoints": points})
    page.wait_for_load_state("networkidle")
    settle(page)
    trace = page.evaluate("window.pointerTrace")
    assert any(not row["primary"] and row["handle"] == "title::0" for row in trace)
    assert all(row["trusted"] for row in trace)
    assert page.request.get(url + "/spec.json").body() == before
    assert page.request.get(url + "/fig.png").body() == pixels_before
    assert page.locator(".preview-wrap").get_attribute("data-revision") == revision
    (directory / "trusted-pointer-ownership.json").write_text(
        json.dumps(trace, indent=2)
    )
    context.close()


@pytest.mark.parametrize("gesture", ["click", "cancel"])
def test_queued_keyboard_intent_survives_immediate_pointer_gesture(
    rust_browser, gesture
):
    from datetime import UTC, datetime, timedelta

    browser, url, directory = rust_browser
    context = browser.new_context(has_touch=True)
    page = context.new_page()
    try:
        if not hasattr(page, "clock"):
            message = (
                "deterministic queued-key qualification needs the Playwright Clock "
                "test-tool capability (introduced in 1.45); product/browser-extra "
                "dependency floors remain unchanged"
            )
            if os.getenv("MUDPLOT_REQUIRE_BROWSER") == "1":
                pytest.fail(message)
            pytest.skip(message + "; optional skip is not qualification proof")
        page.goto(url)
        opened(
            page,
            {
                "version": "0.1",
                "size": [5, 3.5],
                "panels": [
                    {
                        "title": "Queued keyboard",
                        "title_position": [0.5, 0.7],
                        "layers": [],
                    }
                ],
            },
        )
        before = page.request.get(url + "/spec.json").body()
        handle = page.locator(".drag-handle.title")
        handle.scroll_into_view_if_needed()
        handle.focus()
        now = datetime(2026, 1, 1, tzinfo=UTC)
        page.clock.install(time=now)
        page.clock.pause_at(now + timedelta(seconds=1))
        with page.expect_response(
            lambda response: response.url.endswith("/control/move")
        ):
            page.keyboard.press("ArrowRight")
            box = handle.bounding_box()
            x, y = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
            if gesture == "click":
                page.mouse.move(x, y)
                page.mouse.down()
                page.mouse.up()
            else:
                cdp = context.new_cdp_session(page)
                cdp.send(
                    "Input.dispatchTouchEvent",
                    {
                        "type": "touchStart",
                        "touchPoints": [{"x": x, "y": y, "id": 1}],
                    },
                )
                cdp.send(
                    "Input.dispatchTouchEvent",
                    {"type": "touchCancel", "touchPoints": []},
                )
            page.clock.run_for(250)
            page.clock.resume()
        settle(page)
        edited = page.request.get(url + "/spec.json").body()
        assert edited != before
        assert json.loads(edited)["panels"][0]["title_position"][0] > 0.5
        history(page, "Undo")
        assert page.request.get(url + "/spec.json").body() == before
        history(page, "Redo")
        assert page.request.get(url + "/spec.json").body() == edited
        revision = page.locator(".preview-wrap").get_attribute("data-revision")
        handle.scroll_into_view_if_needed()
        box = handle.bounding_box()
        page.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
        page.wait_for_load_state("networkidle")
        assert page.locator(".preview-wrap").get_attribute("data-revision") == revision
        assert page.request.get(url + "/spec.json").body() == edited
        (directory / f"queued-keyboard-{gesture}.json").write_bytes(edited)
    finally:
        context.close()


@pytest.mark.parametrize("width", [1400, 540])
def test_desktop_inspector_and_mobile_flow_keep_native_controls_reachable(
    rust_browser, width
):
    from playwright.sync_api import expect

    browser, url, directory = rust_browser
    context = browser.new_context(viewport={"width": width, "height": 1000})
    page = context.new_page()
    page.goto(url)
    opened(page, document())
    selected(page, 1)
    open_details = page.locator("details").filter(
        has=page.locator('form[hx-post="/open"]')
    )
    if not open_details.evaluate("element => element.open"):
        open_details.locator("summary").first.click()
    inspector = page.locator(".inspector")
    image = page.locator(".preview-wrap img")
    initial_image = image.bounding_box()
    if width == 1400:
        metrics = inspector.evaluate(
            "el => ({height: el.clientHeight, content: el.scrollHeight})"
        )
        assert metrics["content"] > metrics["height"]
        assert inspector.bounding_box()["height"] < 1000
        page.get_by_role(
            "button", name="Open spec", exact=True
        ).scroll_into_view_if_needed()
        assert inspector.evaluate("el => el.scrollTop") > 0
        assert image.bounding_box()["y"] == pytest.approx(initial_image["y"], abs=1)
        target = page.locator(
            'form[hx-post="/control/axis"]:has(input[name="axis"][value="y"])'
            ':has(input[name="operation"][value="label"]) input[name="text"]'
        )
        target.scroll_into_view_if_needed()
        target.focus()
        scroll = inspector.evaluate("el => el.scrollTop")
        edit_axis(page, "y", "label", text="Independently scrolled response")
        assert inspector.evaluate("el => el.scrollTop") == pytest.approx(scroll, abs=1)
        expect(image).to_be_in_viewport()
    else:
        page.get_by_role(
            "button", name="Open spec", exact=True
        ).scroll_into_view_if_needed()
        expect(
            page.get_by_role("button", name="Open spec", exact=True)
        ).to_be_in_viewport()
        assert page.evaluate("scrollY") > 0
        hidden_image = image.bounding_box()
        assert hidden_image["y"] + hidden_image["height"] < 0
    handle = page.locator('[data-handle-id="title::1"]')
    handle.scroll_into_view_if_needed()
    handle.focus()
    before = spec(page, url)
    with page.expect_response(lambda response: response.url.endswith("/control/move")):
        page.keyboard.press("ArrowRight")
    settle(page)
    expect(handle).to_be_focused()
    assert (
        spec(page, url)["panels"][1]["title_position"][0]
        > before["panels"][1]["title_position"][0]
    )
    page.screenshot(
        path=str(directory / f"bounded-inspector-{width}.png"), full_page=True
    )
    context.close()


@pytest.mark.parametrize("document", [{}, {"version": "0.1"}])
def test_sparse_legacy_can_nest_with_populated_layout_form_and_undo(
    rust_browser, document
):
    import matplotlib.pyplot as plt

    browser, url, _ = rust_browser
    context = browser.new_context()
    try:
        page = context.new_page()
        page.goto(url)
        opened(page, document)
        original = page.request.get(url + "/spec.json").body()
        original_png = page.request.get(url + "/fig.png").body()
        assert "panels" not in json.loads(original)
        details = page.locator("details.layout-controls")
        details.locator("summary").click()
        page.get_by_role("button", name="Nest current grid", exact=True).click()
        settle(page)
        edited = page.request.get(url + "/spec.json").body()
        native_spec = mp.from_json(edited.decode())
        figure = mp.render(native_spec)
        try:
            assert len(figure.axes) == 1
            axis = figure.axes[0]
            assert axis._mudplot_panel_id == "panel1"
            outer = axis.get_subplotspec().get_topmost_subplotspec()
            assert outer.get_gridspec().ncols == 2
            assert outer.colspan.start == 0 and outer.colspan.stop == 1
            assert figure.axes[0].bbox.width > 0
        finally:
            plt.close(figure)
        page.get_by_role("button", name="Undo", exact=True).click()
        settle(page)
        assert page.request.get(url + "/spec.json").body() == original
        assert page.request.get(url + "/fig.png").body() == original_png
        page.get_by_role("button", name="Redo", exact=True).click()
        settle(page)
        assert page.request.get(url + "/spec.json").body() == edited
    finally:
        context.close()
