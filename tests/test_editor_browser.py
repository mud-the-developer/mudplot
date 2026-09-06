"""Real-browser tests for the editor's direct-manipulation features.

Everything else exercises the editor over HTTP and asserts on HTML strings,
which cannot see whether a drag actually works: the handles are positioned
by CSS, moved by mouse events, and committed by htmx. This file drives a
real browser instead, so a broken swap/handle/coordinate mapping fails here
rather than in someone's hands.

Skipped unless Playwright and a Chrome install are both present; CI runs the
rest of the suite regardless.
"""

import json
import threading
import time
import urllib.request
from urllib.parse import urlencode

import pytest

pytest.importorskip("playwright", reason="playwright not installed")
from dashboard.editor_server import make_server
from playwright.sync_api import sync_playwright


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


def _enable(page, label: str):
    """Turn on an explicit position for "Legend"/"Title" via its button."""
    group = page.get_by_role("group", name=f"{label} position")
    group.get_by_role("button", name="Enable").click()


def test_dragging_the_legend_moves_it_and_persists(editor):
    page, url = editor
    _enable(page, "Legend")
    handle = page.locator(".drag-handle.legend")
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
    _enable(page, "Title")
    handle = page.locator(".drag-handle.title")
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
    _enable(page, "Legend")
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

    # panel 1 (the second) is empty until selected and given a layer
    page.get_by_role("group", name="Active panel").get_by_role(
        "button", name="2"
    ).click()
    # wait for the swap to actually land: the forms rendered for the previous
    # selection still carry the old panel number, so typing too early edits it
    page.get_by_text("Editing panel 2").wait_for()
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

    # a dragged legend must land on the selected panel too
    _enable(page, "Legend")
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

    layers = _wait_until(
        lambda: _spec(url)["panels"][0]["layers"],
        lambda ls: any(ly["citation"] == "fischler1981" for ly in ls),
    )
    added = next(ly for ly in layers if ly["citation"] == "fischler1981")
    assert added["label"] == "RANSAC"
    assert added["href"] == "https://doi.org/10.1145/358669"
