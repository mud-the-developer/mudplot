"""Real-browser tests for the editor's direct-manipulation features.

Everything else exercises the editor over HTTP and asserts on HTML strings,
which cannot see whether a drag actually works: the handles are positioned
by CSS, moved by mouse events, and committed by htmx. This file drives a
real browser instead, so a broken swap/handle/coordinate mapping fails here
rather than in someone's hands.

Skipped unless Playwright and a Chrome install are both present; CI runs the
rest of the suite regardless.
"""

import contextlib
import json
import threading
import time
import urllib.request
from pathlib import Path
from urllib.parse import urlencode

import pytest

pytest.importorskip("playwright", reason="playwright not installed")
from dashboard.editor_server import make_server
from playwright.sync_api import expect, sync_playwright


@pytest.fixture(scope="module")
def browser():
    with sync_playwright() as p:
        try:
            # Playwright's own chromium if it was downloaded (CI), otherwise
            # an already-installed Chrome (typical dev machine, no download).
            try:
                b = p.chromium.launch()
            except Exception:
                b = p.chromium.launch(channel="chrome")
        except Exception as e:  # pragma: no cover - environment dependent
            pytest.skip(f"no browser available for Playwright: {e}")
        yield b
        b.close()


@pytest.fixture
def editor(browser):
    """A running editor with a line chart already plotted, plus a page."""
    server = make_server(port=0)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    time.sleep(0.05)
    url = f"http://127.0.0.1:{port}"
    for fields in (
        {"type": "load_sample", "name": "sine"},
        {
            "type": "add_layer",
            "layer_type": "line",
            "x": "x",
            "y": "y",
            "group": "series",
        },
    ):
        urllib.request.urlopen(
            urllib.request.Request(
                url + "/action", data=urlencode(fields).encode(), method="POST"
            )
        ).read()
    page = browser.new_page(viewport={"width": 1400, "height": 1000})
    page.goto(url)
    yield page, url
    page.close()
    server.shutdown()


def _spec(url: str) -> dict:
    with urllib.request.urlopen(url + "/spec.json") as r:
        return json.loads(r.read())


def _settle(page):
    """Wait until no editor request is in flight.

    Every action re-renders the whole app body, so a control clicked while
    an earlier swap is still on the wire belongs to a DOM that is about to
    be replaced. A user doesn't hit that (they wait for the screen), but a
    test driving clicks back to back does.
    """
    page.wait_for_load_state("networkidle")


def _wait_until(read, ok, timeout: float = 10.0):
    """Poll ``read()`` until ``ok(value)``, then return the value."""
    deadline = time.time() + timeout
    value = read()
    while time.time() < deadline:
        value = read()
        if ok(value):
            return value
        time.sleep(0.1)
    raise AssertionError(f"condition never held; last value: {value!r}")


def _enable(page, label: str, url: str, done):
    """Turn on an explicit position for "Legend"/"Title" via its button.

    Retries: a click landing in the moment a swap replaces the button hits a
    detached node, so the request is never sent and nothing happens. Waiting
    for network idle first makes that rare, not impossible, and it is the
    test's problem rather than the app's -- a person clicks a button they
    can see, then waits for the screen.
    """
    deadline = time.time() + 30
    while time.time() < deadline:
        group = page.get_by_role("group", name=f"{label} position")
        # button may vanish mid-swap; re-resolve and try again
        with contextlib.suppress(Exception):
            group.get_by_role("button", name="Enable").click(timeout=5000)
        _settle(page)
        try:
            if done(_spec(url)):
                return
        except (IndexError, KeyError, TypeError):
            pass
    raise AssertionError(f"{label} position never turned on")


def _legend_set(index: int):
    return lambda spec: spec["panels"][index]["legend"]["bbox_to_anchor"] is not None


def _title_pos_set(index: int):
    return lambda spec: spec["panels"][index]["title_position"] is not None


def test_any_layer_form_adds_registered_layer_through_htmx(editor):
    page, url = editor
    page.locator('details[data-key="all-layers"] > summary').click()
    form = page.locator('form:has(input[name="type"][value="add_layer_json"])')
    form.locator('select[name="layer_type"]').select_option("hline")
    form.locator('textarea[name="layer_json"]').fill(
        json.dumps({"value": 0.5, "label": "Threshold"})
    )
    form.get_by_role("button", name="Add layer").click()
    _settle(page)
    spec = _wait_until(
        lambda: _spec(url),
        lambda value: value["panels"][0]["layers"][-1]["type"] == "hline",
    )
    assert spec["panels"][0]["layers"][-1]["value"] == 0.5


def test_polar_projection_switches_through_htmx_and_hides_secondary_axis(editor):
    page, url = editor
    form = page.locator('form:has(input[name="type"][value="set_projection"])')
    form.locator('select[name="projection"]').select_option("polar")
    form.get_by_role("button", name="Set projection").click()
    _settle(page)

    spec = _wait_until(
        lambda: _spec(url),
        lambda value: value["panels"][0]["projection"] == "polar",
    )
    assert spec["panels"][0]["projection"] == "polar"
    assert (
        page.locator('form:has(input[name="type"][value="set_secondary_axis"])').count()
        == 0
    )


def test_dragging_the_legend_moves_it_and_persists(editor):
    page, url = editor
    _enable(page, "Legend", url, _legend_set(0))
    handle = page.get_by_role(
        "button", name="Move legend; drag or use arrow keys", exact=True
    )
    handle.wait_for()
    before = handle.bounding_box()

    page.mouse.move(before["x"] + 10, before["y"] + 10)
    page.mouse.down()
    page.mouse.move(before["x"] + 160, before["y"] + 90, steps=10)
    page.mouse.up()

    page.wait_for_function(
        "() => document.querySelectorAll('.drag-handle.legend').length === 1"
    )
    anchor = _spec(url)["panels"][0]["legend"]["bbox_to_anchor"]
    assert anchor is not None
    # right and down on screen -> +x, -y in figure fractions
    assert anchor[0] > 0.8
    assert anchor[1] < 0.5
    after = page.locator(".drag-handle.legend").bounding_box()
    assert abs(after["x"] - (before["x"] + 150)) < 12
    assert abs(after["y"] - (before["y"] + 80)) < 12


def test_arrow_keys_nudge_the_title(editor):
    page, url = editor
    page.get_by_label("Panel title").fill("Nudge me")
    page.get_by_label("Panel title").press("Enter")
    _settle(page)
    _enable(page, "Title", url, _title_pos_set(0))
    handle = page.get_by_role(
        "button", name="Move panel title; drag or use arrow keys", exact=True
    )
    handle.wait_for()

    start = _spec(url)["panels"][0]["title_position"]
    handle.click()
    for _ in range(3):
        page.keyboard.press("ArrowRight")

    # posts are coalesced, so poll for the committed value rather than
    # assuming one round trip per keypress
    moved = _wait_until(
        lambda: _spec(url)["panels"][0]["title_position"],
        lambda pos: pos[0] > start[0] + 0.01,
    )
    assert moved[0] > start[0]
    assert moved[1] == pytest.approx(start[1], abs=1e-6)


def test_swapping_does_not_nest_the_app_body(editor):
    """Every htmx target is #app-body with innerHTML, so a fragment that
    carries its own wrapper silently nests a copy per edit.
    """
    page, _ = editor
    for text in ("one", "two", "three"):
        page.get_by_label("Suptitle").fill(text)
        page.get_by_role("button", name="Set suptitle").click()
        page.wait_for_timeout(150)
    assert page.locator("#app-body").count() == 1
    assert page.locator(".inspector").count() == 1


def test_edits_keep_scroll_position_and_open_sections(editor):
    page, _ = editor
    page.locator("details[data-key='advanced']").locator("summary").click()
    page.locator(".inspector").evaluate("el => el.scrollTop = 400")
    page.wait_for_timeout(100)
    before = page.locator(".inspector").evaluate("el => el.scrollTop")
    assert before > 0

    # Fire the edit without touching a control: focusing an input scrolls it
    # into view, which would move the sidebar before the swap even happens
    # and make this assert about the browser rather than about the restore.
    page.evaluate(
        """() => htmx.ajax('POST', '/action', {
            target: '#app-body', swap: 'innerHTML',
            values: {type: 'set_suptitle', text: 'keeps position'},
        })"""
    )
    page.wait_for_timeout(600)

    assert page.locator("details[data-key='advanced']").evaluate("el => el.open")
    after = page.locator(".inspector").evaluate("el => el.scrollTop")
    assert abs(after - before) < 40


def test_a_render_error_is_shown_without_losing_the_previous_figure(editor):
    page, _ = editor
    page.locator("details[data-key='advanced']").locator("summary").click()
    page.get_by_label("Raw JSON action", exact=False).fill(
        json.dumps({"type": "SetScale", "axis": "x", "scale": "nonsense"})
    )
    page.get_by_role("button", name="Dispatch JSON action").click()
    page.wait_for_selector(".error")
    assert "nonsense" in page.locator(".error").inner_text()
    # the preview still shows the last good render rather than disappearing
    assert page.locator(".preview-wrap img").is_visible()


def test_a_burst_of_nudges_is_not_dropped(editor):
    """Each committed nudge swaps in a new overlay, so keypresses landing
    mid-swap used to vanish -- exactly what holding an arrow key does.
    """
    page, url = editor
    _enable(page, "Legend", url, _legend_set(0))
    page.locator(".drag-handle.legend").wait_for()
    start = _spec(url)["panels"][0]["legend"]["bbox_to_anchor"]

    page.locator(".drag-handle.legend").click()
    for _ in range(8):
        page.keyboard.press("ArrowLeft")
        page.wait_for_timeout(30)

    moved = _wait_until(
        lambda: _spec(url)["panels"][0]["legend"]["bbox_to_anchor"],
        lambda pos: pos[0] < start[0] - 0.1,
    )
    # 8 x 0.02 = 0.16 of travel; allow for coalescing, not for losing most
    assert moved[0] < start[0] - 0.1


def test_editing_targets_the_selected_panel(editor):
    """With more than one panel, the side controls and the drag handles must
    follow the selection instead of always editing panel 0.
    """
    page, url = editor
    page.get_by_label("Columns").fill("2")
    page.get_by_role("button", name="Set grid").click()
    page.get_by_role("group", name="Active panel").wait_for()
    _settle(page)

    # panel 1 (the second) is empty until selected and given a layer
    page.get_by_role("group", name="Active panel").get_by_role(
        "button", name="2"
    ).click()
    # wait for the swap to actually land: the forms rendered for the previous
    # selection still carry the old panel number, so typing too early edits it
    page.get_by_text("Editing panel 2").wait_for()
    _settle(page)
    page.get_by_label("Panel title").fill("Second panel")
    page.get_by_label("Panel title").press("Enter")

    panels = _wait_until(
        lambda: _spec(url)["panels"],
        lambda ps: len(ps) > 1 and ps[1]["title"] == "Second panel",
    )
    assert panels[0]["title"] == ""  # panel 0 untouched

    # a new layer goes to the selected panel: the add-layer form carries no
    # panel field, so this exercises the server-side default
    page.get_by_label("x column").fill("x")
    page.get_by_label("y column").fill("y")
    page.get_by_role("button", name="Add layer").click()
    panels = _wait_until(
        lambda: _spec(url)["panels"],
        lambda ps: len(ps[1]["layers"]) == 1,
    )
    assert len(panels[0]["layers"]) == 1  # still just the original line
    _settle(page)

    # a dragged legend must land on the selected panel too
    _enable(page, "Legend", url, _legend_set(1))
    page.locator(".drag-handle.legend").wait_for()
    handle = page.locator(".drag-handle.legend").bounding_box()
    page.mouse.move(handle["x"] + 10, handle["y"] + 10)
    page.mouse.down()
    page.mouse.move(handle["x"] + 60, handle["y"] + 40, steps=5)
    page.mouse.up()
    panels = _wait_until(
        lambda: _spec(url)["panels"],
        lambda ps: ps[1]["legend"]["bbox_to_anchor"] is not None,
    )
    assert panels[0]["legend"]["bbox_to_anchor"] is None


def test_citation_metadata_can_be_entered_in_the_ui(editor):
    page, url = editor
    # scoped to the add-layer form: the title fields have the same labels
    form = page.locator("form", has=page.get_by_role("button", name="Add layer"))
    form.get_by_label("x column").fill("x")
    form.get_by_label("y column").fill("y")
    form.get_by_label("Legend label", exact=False).fill("RANSAC")
    form.get_by_label("Citation key", exact=False).fill("fischler1981")
    form.get_by_label("Link", exact=False).fill("https://doi.org/10.1145/358669")
    form.get_by_role("button", name="Add layer").click()
    _settle(page)

    layers = _wait_until(
        lambda: _spec(url)["panels"][0]["layers"],
        lambda ls: any(ly["citation"] == "fischler1981" for ly in ls),
    )
    added = next(ly for ly in layers if ly["citation"] == "fischler1981")
    assert added["label"] == "RANSAC"
    assert added["href"] == "https://doi.org/10.1145/358669"


def test_opening_a_spec_file_from_the_picker(editor, tmp_path):
    """The file input is read client-side into the form's textarea, so this
    path only exists in the browser.
    """
    page, url = editor
    saved = json.loads(urllib.request.urlopen(url + "/spec.json").read())
    saved["suptitle"] = "from a file"
    path = tmp_path / "figure.mplot.json"
    path.write_text(json.dumps(saved), encoding="utf-8")

    page.locator("details[data-key='open'] summary").click()
    page.locator("#spec-file").set_input_files(str(path))
    page.wait_for_function(
        "() => (document.getElementById('spec-json') || {}).value.length > 0"
    )
    page.get_by_role("button", name="Open figure").click()

    _wait_until(lambda: _spec(url)["suptitle"], lambda t: t == "from a file")


@pytest.mark.parametrize(
    "viewport,width,suffix",
    [
        (900, 700, ""),
        (600, 320, "_mobile"),
        (360, 320, "_mobile"),
        (320, 280, "_mobile"),
    ],
)
def test_visual_review_uses_real_desktop_and_mobile_layouts(
    browser, tmp_path, viewport, width, suffix
):
    from examples.publication_showcase import build_plot
    from mudplot._estimate import summarize

    page = browser.new_page(viewport={"width": viewport, "height": 900})
    try:
        review = Path(__file__).resolve().parents[1] / "docs" / "VISUAL_REVIEW.html"
        report = json.loads(
            (review.parent / "images/visual_quality.json").read_text(encoding="utf-8")
        )
        page.goto(review.as_uri())
        page.wait_for_function(
            "() => [...document.images].every("
            "image => image.complete && image.naturalWidth > 0)"
        )
        for kind in ("response", "endpoint"):
            image = page.locator(f"#{kind} img")
            info = image.evaluate(
                "image => ({width: image.clientWidth, natural: image.naturalWidth, "
                "source: image.currentSrc})"
            )
            qa = report["charts"][f"visual_{kind}{suffix}"]
            assert info["width"] == width and info["natural"] == qa["source_pixels"][0]
            assert qa["min_display_font_px"] * width / qa["display_pixels"][0] >= 14
            assert info["source"].endswith(f"visual_{kind}{suffix}.png")
            page.locator(f"#{kind}").screenshot(
                path=str(tmp_path / f"{kind}-{width}.png")
            )
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
        sizes = page.locator("figcaption").evaluate_all(
            "items => items.map(item => parseFloat(getComputedStyle(item).fontSize))"
        )
        assert sizes == [14, 14]
        page.locator("#endpoint-values summary").click()
        rows = page.locator("#endpoint-values tbody tr").evaluate_all(
            "rows => rows.map(row => [...row.cells].map("
            "cell => cell.textContent.trim()))"
        )
        plot = build_plot("endpoint")
        summary = summarize(plot.spec.data.columns, plot.spec.panels[0].layers[0])
        expected = []
        for estimate in reversed(summary.estimates):
            assert estimate.lower is not None and estimate.upper is not None
            expected.append(
                [
                    estimate.group,
                    f"{estimate.value:.3f}",
                    f"{estimate.lower:.3f}\u2013{estimate.upper:.3f}",
                ]
            )
        assert rows == expected
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
        print(f"Visual review screenshots: {tmp_path}")
    finally:
        page.close()


@pytest.mark.parametrize("name", ["response-mobile", "endpoint-mobile"])
def test_complete_example_draft_requires_open_and_can_be_edited(editor, name):
    from dashboard.samples import FIGURE_SAMPLES, sample_figure

    page, url = editor
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    before = _spec(url)
    page.locator('details[data-key="samples"] > summary').click()
    page.get_by_role("link", name=FIGURE_SAMPLES[name][0], exact=True).click()
    _settle(page)
    assert _spec(url) == before
    assert page.locator("#open-figure").evaluate("element => element.open")
    expected = sample_figure(name).to_dict()
    assert json.loads(page.get_by_label("Spec JSON").input_value()) == expected
    page.get_by_role("button", name="Open figure", exact=True).click()
    _settle(page)
    assert _spec(url) == expected
    assert not errors, errors
    # The Store commits before htmx finishes its swap and history update.
    expect(page).to_have_url(url + "/")
    assert page.evaluate("localStorage.getItem('htmx-history-cache')") is None
    title = page.get_by_label("Panel title", exact=True)
    expect(title).to_have_value(expected["panels"][0]["title"])
    title.fill("Edited reading example")
    page.locator("form", has=title).get_by_role(
        "button", name="Apply", exact=True
    ).click()
    _settle(page)
    edited = _wait_until(
        lambda: _spec(url),
        lambda spec: spec["panels"][0]["title"] == "Edited reading example",
    )
    assert edited["data"] == expected["data"]
    response = page.request.get(url + "/fig.svg")
    assert response.ok and b"<svg" in response.body()


@pytest.mark.parametrize("kind", ["hist", "kde"])
def test_joint_grid_import_has_three_editable_panels_and_preserves_source(
    editor, tmp_path, kind
):
    import mudplot as mp

    raw = {
        "x": [1, 2, 3, 4, None],
        "y": [2, 3, 5, 6, 8],
        "h": ["A", "A", "B", "B", "B"],
    }
    plot = (
        mp.plot(raw)
        .scatter("x", "y", group="h")
        .joint(
            bins=3 if kind == "hist" else 20,
            marginal_kind=kind,
            kde={"cut": 0, "gridsize": 31} if kind == "kde" else None,
        )
        .size(6, 6)
    )
    expected = plot.spec.to_dict()
    path = tmp_path / "joint.mplot.json"
    path.write_text(plot.to_json(), encoding="utf-8")
    page, url = editor
    page.locator('details[data-key="open"] > summary').click()
    page.locator("#spec-file").set_input_files(str(path))
    page.wait_for_function(
        "() => document.getElementById('spec-json').value.length > 0"
    )
    page.get_by_role("button", name="Open figure", exact=True).click()
    _wait_until(lambda: _spec(url), lambda spec: len(spec["panels"]) == 3)
    assert _spec(url) == expected
    panels = page.get_by_role("group", name="Active panel")
    expect(panels.get_by_role("button")).to_have_count(3)
    panels.get_by_role("button", name="3", exact=True).click()
    page.get_by_text("Editing panel 3").wait_for()
    page.get_by_label("Panel title", exact=True).fill("X marginal edited")
    page.get_by_label("Panel title", exact=True).press("Enter")
    current = _wait_until(
        lambda: _spec(url),
        lambda spec: spec["panels"][2]["title"] == "X marginal edited",
    )
    assert current["panels"][0]["title"] == expected["panels"][0]["title"]
    assert current["data"] == expected["data"]
    response = page.request.get(url + "/fig.svg")
    assert response.ok and b"<svg" in response.body()


@pytest.mark.parametrize("kind", ["hist", "kde"])
def test_pair_grid_file_opens_nine_named_axis_cells_and_exports(editor, tmp_path, kind):
    import mudplot as mp

    raw = {"a": [1, 2, None, 4], "b": [2, None, 4, 5], "c": [4, 3, 2, 1]}
    plot = (
        mp.plot(raw)
        .pair(
            ["a", "b", "c"],
            bins=3 if kind == "hist" else 20,
            diag_kind=kind,
            kde={"cut": 0, "gridsize": 31} if kind == "kde" else None,
        )
        .size(8, 8)
    )
    path = tmp_path / "pair.mplot.json"
    path.write_text(plot.to_json(), encoding="utf-8")
    page, url = editor
    page.locator('details[data-key="open"] > summary').click()
    page.locator("#spec-file").set_input_files(str(path))
    page.wait_for_function(
        "() => document.getElementById('spec-json').value.length > 0"
    )
    page.get_by_role("button", name="Open figure", exact=True).click()
    _wait_until(lambda: _spec(url), lambda spec: len(spec["panels"]) == 9)
    assert _spec(url) == plot.spec.to_dict()
    panels = page.get_by_role("group", name="Active panel")
    expect(panels.get_by_role("button")).to_have_count(9)
    panels.get_by_role("button", name="9", exact=True).click()
    page.get_by_text("Editing panel 9").wait_for()
    page.get_by_label("Panel title", exact=True).fill("Edited diagonal")
    page.get_by_label("Panel title", exact=True).press("Enter")
    current = _wait_until(
        lambda: _spec(url), lambda spec: spec["panels"][8]["title"] == "Edited diagonal"
    )
    assert current["data"] == plot.spec.data.to_dict()
    assert current["panels"][0]["y"]["share_id"] is None
    response = page.request.get(url + "/fig.svg")
    assert response.ok and b"<svg" in response.body()


def test_typed_heatmap_file_retains_mask_norm_and_annotations_after_edit(
    editor, tmp_path
):
    from examples.heatmap_controls import build_plot

    plot = build_plot()
    path = tmp_path / "heatmap.mplot.json"
    path.write_text(plot.to_json(), encoding="utf-8")
    page, url = editor
    page.locator('details[data-key="open"] > summary').click()
    page.locator("#spec-file").set_input_files(str(path))
    page.wait_for_function(
        "() => document.getElementById('spec-json').value.length > 0"
    )
    page.get_by_role("button", name="Open figure", exact=True).click()
    expected = plot.spec.to_dict()
    _wait_until(lambda: _spec(url), lambda spec: spec == expected)
    expect(page.get_by_label("Panel title", exact=True)).to_have_value(
        expected["panels"][0]["title"]
    )
    page.get_by_label("Panel title", exact=True).fill("Edited heatmap")
    with page.expect_response(
        lambda response: response.url == url + "/action"
    ) as submit:
        page.get_by_label("Panel title", exact=True).press("Enter")
    assert submit.value.status in (200, 303), {
        "status": submit.value.status,
        "origin": submit.value.request.all_headers().get("origin"),
        "fetch_site": submit.value.request.all_headers().get("sec-fetch-site"),
    }
    current = _wait_until(
        lambda: _spec(url), lambda spec: spec["panels"][0]["title"] == "Edited heatmap"
    )
    assert current["data"] == expected["data"]
    assert (
        current["panels"][0]["layers"][0]["heatmap"]
        == expected["panels"][0]["layers"][0]["heatmap"]
    )
    response = page.request.get(url + "/fig.svg")
    assert response.ok and b"<svg" in response.body()


def test_native_editor_forms_post_and_undo_without_query_leaks(browser, editor):
    _, url = editor
    original = _spec(url)["panels"][0]["title"]
    context = browser.new_context(java_script_enabled=False)
    page = context.new_page()
    try:
        page.goto(url)
        page.get_by_label("Panel title", exact=True).fill("Private native title")
        with page.expect_response(
            lambda response: response.url == url + "/action"
        ) as submit:
            page.get_by_label("Panel title", exact=True).press("Enter")
        assert submit.value.status == 303
        expect(page).to_have_url(url + "/")
        assert _spec(url)["panels"][0]["title"] == "Private native title"
        assert "Private" not in page.url
        page.get_by_role("button", name="Undo", exact=True).click()
        expect(page).to_have_url(url + "/")
        assert (
            _wait_until(
                lambda: _spec(url)["panels"][0]["title"],
                lambda value: value == original,
            )
            == original
        )
    finally:
        context.close()


@pytest.mark.parametrize("name", ["residual", "logx", "robust", "logistic", "lowess"])
def test_configured_regression_import_edit_and_svg(editor, tmp_path, name):
    if name in ("robust", "logistic", "lowess"):
        pytest.importorskip("statsmodels")
    from examples.regression_modes import build_plots

    plot = build_plots()["regression_" + name]
    expected = plot.spec.to_dict()
    path = tmp_path / f"regression-{name}.mplot.json"
    path.write_text(plot.to_json(), encoding="utf-8")
    page, url = editor
    page.locator('details[data-key="open"] > summary').click()
    page.locator("#spec-file").set_input_files(str(path))
    page.wait_for_function(
        "() => document.getElementById('spec-json').value.length > 0"
    )
    page.get_by_role("button", name="Open figure", exact=True).click()
    _wait_until(lambda: _spec(url), lambda spec: spec == expected)
    expect(page.get_by_label("Panel title", exact=True)).to_have_value(
        expected["panels"][0]["title"]
    )
    page.get_by_label("Panel title", exact=True).fill("Edited regression")
    page.get_by_label("Panel title", exact=True).press("Enter")
    current = _wait_until(
        lambda: _spec(url),
        lambda spec: spec["panels"][0]["title"] == "Edited regression",
    )
    assert current["data"] == expected["data"]
    assert (
        current["panels"][0]["layers"][0]["regression"]
        == expected["panels"][0]["layers"][0]["regression"]
    )
    response = page.request.get(url + "/fig.svg")
    assert response.ok and b"<svg" in response.body()


def test_open_reset_and_download_keep_python_document_history_and_source_files_separate(
    editor, tmp_path
):
    import mudplot as mp

    page, url = editor
    first = (
        mp.plot({"x": [1, 2], "y": [2, 3]})
        .line("x", "y")
        .labels(title="file A")
        .size(4, 3)
    )
    second = (
        mp.plot({"u": [1, 2], "v": [3, 4]})
        .line("u", "v")
        .labels(title="file B")
        .size(4, 3)
    )
    paths = [tmp_path / "source-a.json", tmp_path / "source-b.json"]
    for path, plot in zip(paths, (first, second), strict=True):
        mp.save_spec(plot.spec, path)
    original = [path.read_bytes() for path in paths]

    def open_file(path, expected):
        section = page.locator('details[data-key="open"]')
        if section.get_attribute("open") is None:
            section.locator("summary").click()
        page.locator("#spec-file").set_input_files(str(path))
        page.wait_for_function(
            "expected => document.getElementById('spec-json').value === expected",
            arg=path.read_text(encoding="utf-8"),
        )
        if section.get_attribute("open") is None:
            section.locator("summary").click()
        page.get_by_role("button", name="Open figure", exact=True).click()
        _wait_until(lambda: _spec(url), lambda spec: spec == expected)
        _settle(page)

    open_file(paths[0], first.spec.to_dict())
    page.get_by_label("Panel title", exact=True).fill("A unsaved edit")
    page.get_by_label("Panel title", exact=True).press("Enter")
    _wait_until(
        lambda: _spec(url), lambda spec: spec["panels"][0]["title"] == "A unsaved edit"
    )
    _settle(page)
    open_file(paths[1], second.spec.to_dict())
    history = page.locator('details[data-key="history"]')
    if history.get_attribute("open") is None:
        history.locator("summary").click()
    for name in ("Undo", "Redo"):
        page.get_by_role("button", name=name, exact=True).click()
        _settle(page)
        assert _spec(url) == second.spec.to_dict()
    with page.expect_download() as download:
        page.get_by_role("link", name="Spec (.json)", exact=True).click()
    saved = tmp_path / "download-b.json"
    download.value.save_as(str(saved))
    assert mp.load_spec(saved) == second.spec
    page.get_by_role("button", name="Reset", exact=True).click()
    _settle(page)
    assert _spec(url) == mp.FigureSpec().to_dict()
    with page.expect_download() as download:
        page.get_by_role("link", name="Spec (.json)", exact=True).click()
    saved = tmp_path / "download-reset.json"
    download.value.save_as(str(saved))
    assert mp.load_spec(saved) == mp.FigureSpec()
    assert [path.read_bytes() for path in paths] == original


def test_csp_headers_and_real_htmx_swap_have_no_policy_violations(editor):
    page, url = editor
    violations = []

    def check_console(message):
        if "content security policy" in message.text.lower():
            violations.append(message.text)

    page.on("console", check_console)
    page.on("pageerror", lambda error: violations.append(str(error)))
    page.add_init_script(
        "window.__reviewCsp=[]; document.addEventListener('securitypolicyviolation',"
        "event=>window.__reviewCsp.push(event.effectiveDirective));"
    )
    response = page.reload()
    assert response is not None
    assert "script-src 'self';" in response.headers["content-security-policy"]
    assert response.headers["cache-control"] == "no-store"
    title = page.get_by_label("Panel title", exact=True)
    title.fill("CSP verified")
    title.press("Enter")
    _settle(page)
    assert _spec(url)["panels"][0]["title"] == "CSP verified"
    rejected = page.request.post(
        url + "/action",
        form={"type": "set_title", "text": "blocked"},
        headers={"Origin": "null"},
    )
    assert rejected.status == 403
    assert rejected.headers["cache-control"] == "no-store"
    assert "frame-ancestors 'none'" in rejected.headers["content-security-policy"]
    assert page.evaluate("window.__reviewCsp") == []
    assert not violations, violations


def test_cluster_file_keeps_orders_metadata_and_matrix_after_title_edit(
    editor, tmp_path
):
    pytest.importorskip("scipy")
    from examples.clustered_profiles import build_plot

    plot = build_plot()
    expected = plot.spec.to_dict()
    path = tmp_path / "cluster.mplot.json"
    path.write_text(plot.to_json(), encoding="utf-8")
    page, url = editor
    page.locator('details[data-key="open"] > summary').click()
    page.locator("#spec-file").set_input_files(str(path))
    page.wait_for_function(
        "() => document.getElementById('spec-json').value.length > 0"
    )
    page.get_by_role("button", name="Open figure", exact=True).click()
    _wait_until(lambda: _spec(url), lambda spec: spec == expected)
    expect(page.get_by_label("Panel title", exact=True)).to_have_value(
        expected["panels"][0]["title"]
    )
    page.get_by_label("Panel title", exact=True).fill("Edited clustered profiles")
    page.get_by_label("Panel title", exact=True).press("Enter")
    current = _wait_until(
        lambda: _spec(url),
        lambda spec: spec["panels"][0]["title"] == "Edited clustered profiles",
    )
    assert current["data"] == expected["data"]
    assert current["panels"][0]["layers"] == expected["panels"][0]["layers"]
    response = page.request.get(url + "/fig.svg")
    assert response.ok and b"<svg" in response.body()


def test_built_reading_gallery_and_downloaded_spec_open_in_editor(
    browser, editor, tmp_path
):
    from dashboard.site import build_site

    site = build_site(str(tmp_path / "site"))
    page = browser.new_page(viewport={"width": 900, "height": 900})
    try:
        for viewport, width, suffix in ((900, 700, ""), (360, 320, "_mobile")):
            page.set_viewport_size({"width": viewport, "height": 900})
            page.goto((site / "index.html").as_uri())
            image = page.locator(".reading-example img")
            page.wait_for_function(
                "() => document.querySelector('.reading-example img').naturalWidth > 0"
            )
            assert image.evaluate("image => image.clientWidth") == width
            assert image.evaluate("image => image.currentSrc").endswith(
                f"visual_response{suffix}.png"
            )
        page.get_by_role(
            "link", name="Open the actual-size desktop/mobile review"
        ).click()
        assert page.url.endswith("reading/VISUAL_REVIEW.html")
        page.get_by_role("link", name="the criteria and limitations").click()
        assert page.url.endswith("VISUAL_QUALITY.html")
        assert page.get_by_role(
            "heading", name="Reading-first chart review", exact=True
        ).is_visible()
    finally:
        page.close()

    page, url = editor
    path = site / "reading/images/visual_response_mobile.mplot.json"
    expected = json.loads(path.read_text(encoding="utf-8"))
    page.locator('details[data-key="open"] > summary').click()
    page.locator("#spec-file").set_input_files(str(path))
    page.wait_for_function(
        "() => document.getElementById('spec-json').value.length > 0"
    )
    page.get_by_role("button", name="Open figure", exact=True).click()
    _settle(page)
    assert _spec(url) == expected
