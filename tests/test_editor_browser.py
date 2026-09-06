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
        page.wait_for_timeout(250)
    moved = _spec(url)["panels"][0]["title_position"]
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
