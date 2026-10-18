"""Real Chromium coverage, kept separate from no-browser minimum dependencies."""

import threading

import mudplot as mp
import pytest
from dashboard.editor_server import EditorSession, make_server

from test_editor_browser import _settle, _wait_until
from test_review_coordinate_frames import document

pytest_plugins = ["test_editor_browser"]


def test_secondary_data_drag_matches_log_inverted_transform_and_history(browser):
    spec, active = document()
    session = EditorSession()
    session.load_spec(mp.to_json(spec))
    session.select_panel(active)
    server = make_server(port=0, session=session)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    page = browser.new_page(viewport={"width": 1400, "height": 1000})
    try:
        page.goto(f"http://127.0.0.1:{server.server_address[1]}")
        _settle(page)
        handle = page.locator(f'[data-handle-id="layer-at:3:{active}"]')
        handle.wait_for()
        rect = handle.bounding_box()
        wrap = page.locator(".preview-wrap").bounding_box()
        assert rect is not None and wrap is not None and 0 <= rect["y"] < 1000
        x0, y0, x1, y1 = session.layout["panel_bbox"]
        fx, fy = x0 + 0.4 * (x1 - x0), y0 + 0.65 * (y1 - y0)
        page.mouse.move(rect["x"] + rect["width"] / 2, rect["y"] + rect["height"] / 2)
        page.mouse.down()
        page.mouse.move(
            wrap["x"] + fx * wrap["width"],
            wrap["y"] + (1 - fy) * wrap["height"],
            steps=10,
        )
        page.mouse.up()
        _wait_until(
            lambda: session.store.state.panels[active].layers[3].at,
            lambda at: at != [10, 100],
        )
        actual = session.store.state.panels[active].layers[3].at
        assert actual is not None
        assert actual == pytest.approx([10**1.2, 10**2.3], rel=0.02)
        assert session.store.state.panels[active].layers[2].at == [10, 1]
        assert session.store.state.panels[0].layers == []
        session.undo()
        assert session.store.state.panels[active].layers[3].at == [10, 100]
        session.redo()
        assert session.store.state.panels[active].layers[3].at == actual
        assert mp.from_json(mp.to_json(session.store.state)) == session.store.state
    finally:
        page.close()
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
