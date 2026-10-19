"""Observe existing gesture submission, not a new core history coalescer."""

import json
import threading
import time
from urllib.parse import parse_qs, urlparse

import mudplot as mp
from dashboard.editor_server import EditorSession, make_server

from test_editor_browser import _settle, _wait_until
from test_review_coordinate_frames import document

pytest_plugins = ["test_editor_browser"]


def test_mouse_gestures_commit_once_and_keep_independent_edits_and_undo(
    browser, tmp_path
):
    spec, active = document((6, 3), 150, 2)
    session = EditorSession()
    session.load_spec(mp.to_json(spec))
    session.select_panel(active)
    server = make_server(port=0, session=session)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    page = browser.new_page(viewport={"width": 1400, "height": 1100})
    requests = []
    samples = []

    def record(request):
        if urlparse(request.url).path == "/action":
            requests.append(parse_qs(request.post_data or ""))

    def wait(read, predicate):
        return _wait_until(lambda: (page.wait_for_timeout(25), read())[1], predicate)

    def gesture(xfrac, yfrac):
        handle = page.locator(f'[data-handle-id="layer-at:3:{active}"]')
        rect = handle.bounding_box()
        wrap = page.locator(".preview-wrap").bounding_box()
        assert rect is not None and wrap is not None
        x0, y0, x1, y1 = session.layout["panel_bbox"]
        target = [
            wrap["x"] + (x0 + xfrac * (x1 - x0)) * wrap["width"],
            wrap["y"] + (1 - y0 - yfrac * (y1 - y0)) * wrap["height"],
        ]
        before = len(session.action_log())
        sent = len(requests)
        point = session.store.state.panels[active].layers[3].at
        page.mouse.move(rect["x"] + rect["width"] / 2, rect["y"] + rect["height"] / 2)
        page.mouse.down()
        page.mouse.move(*target, steps=100)
        assert len(requests) == sent and len(session.action_log()) == before
        start = time.perf_counter()
        page.mouse.up()
        wait(lambda: len(session.action_log()), lambda count: count == before + 1)
        _settle(page)
        assert len(requests) == sent + 1
        changed = session.store.state.panels[active].layers[3].at
        samples.append(
            {
                "move_steps": 100,
                "requests_while_moving": 0,
                "requests_on_release": 1,
                "commit_roundtrip_ms": (time.perf_counter() - start) * 1000,
            }
        )
        return point, changed

    try:
        url = f"http://127.0.0.1:{server.server_address[1]}"
        page.goto(url)
        _settle(page)
        page.on("request", record)
        handle = page.locator(f'[data-handle-id="layer-at:3:{active}"]')
        handle.click()
        _settle(page)
        assert (
            requests == [] and session.action_log() == []
        )  # focus-only click is not an edit
        original, first = gesture(0.4, 0.65)
        page.get_by_role("button", name="Undo", exact=True).press("Enter")
        wait(
            lambda: session.store.state.panels[active].layers[3].at,
            lambda value: value == original,
        )
        _settle(page)
        page.get_by_role("button", name="Redo", exact=True).press("Enter")
        wait(
            lambda: session.store.state.panels[active].layers[3].at,
            lambda value: value == first,
        )
        _settle(page)
        page.get_by_label("Panel title", exact=True).fill("independent edit")
        page.get_by_label("Panel title", exact=True).press("Enter")
        wait(
            lambda: session.store.state.panels[active].title,
            lambda value: value == "independent edit",
        )
        _settle(page)
        before_second, second = gesture(0.55, 0.45)
        assert before_second == first and second != first
        history = session.action_log()
        assert [action["type"] for action in history] == [
            "SetLayerAt",
            "SetTitle",
            "SetLayerAt",
        ]
        page.get_by_role("button", name="Undo", exact=True).press("Enter")
        wait(
            lambda: session.store.state.panels[active].layers[3].at,
            lambda value: value == first,
        )
        _settle(page)
        assert session.store.state.panels[active].title == "independent edit"
        page.get_by_role("button", name="Undo", exact=True).press("Enter")
        wait(
            lambda: session.store.state.panels[active].title,
            lambda value: value == "selected",
        )
        assert session.store.state.panels[active].layers[3].at == first
        assert len(requests) == 3 and samples[0]["requests_on_release"] == 1
        (tmp_path / "gesture_trace.json").write_text(
            json.dumps(
                {
                    "gestures": samples,
                    "requests": requests,
                    "committed_history": history,
                    "original_at": original,
                    "first_at": first,
                    "second_at": second,
                    "undo_boundary_verified": True,
                    "policy": "Mouse-up submits once; no new core coalescer.",
                },
                indent=2,
            ),
            encoding="utf-8",
        )
    finally:
        page.close()
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
