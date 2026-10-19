"""Actual Chromium DPI/CSS/visual-viewport scale checks for data editing."""

import json
import threading

import mudplot as mp
import pytest
from dashboard.editor_server import EditorSession, make_server

from test_editor_browser import _settle, _wait_until
from test_review_coordinate_frames import document

pytest_plugins = ["test_editor_browser"]


@pytest.mark.parametrize(
    "dpr,css_zoom,page_scale", [(1, 1.0, 1.0), (2, 1.25, 1.0), (2, 1.0, 1.25)]
)
def test_scaled_preview_drag_keyboard_undo_redo_keep_data_frame(
    browser, tmp_path, dpr, css_zoom, page_scale
):
    spec, active = document((6, 3), 600, 2)
    session = EditorSession()
    session.load_spec(mp.to_json(spec))
    session.select_panel(active)
    server = make_server(port=0, session=session)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    context = browser.new_context(
        viewport={"width": 1400, "height": 1100}, device_scale_factor=dpr
    )
    page = context.new_page()
    try:
        url = f"http://127.0.0.1:{server.server_address[1]}"
        page.goto(url)
        _settle(page)
        page.evaluate("value => document.body.style.zoom = String(value)", css_zoom)
        cdp = context.new_cdp_session(page)
        cdp.send("Emulation.setPageScaleFactor", {"pageScaleFactor": page_scale})
        assert page.evaluate("window.devicePixelRatio") == dpr
        assert page.evaluate("window.visualViewport.scale") == pytest.approx(page_scale)
        page.evaluate("""() => document.addEventListener('mouseup', ev => {
          window.lastPointer = {x:ev.clientX,y:ev.clientY};
        })""")
        handle = page.locator(f'[data-handle-id="layer-at:3:{active}"]')
        handle.wait_for()
        rect = handle.bounding_box()
        wrap = page.locator(".preview-wrap").bounding_box()
        assert rect is not None and wrap is not None
        x0, y0, x1, y1 = session.layout["panel_bbox"]
        fx, fy = x0 + 0.4 * (x1 - x0), y0 + 0.65 * (y1 - y0)
        destination = [
            wrap["x"] + fx * wrap["width"],
            wrap["y"] + (1 - fy) * wrap["height"],
        ]
        page.mouse.move(rect["x"] + rect["width"] / 2, rect["y"] + rect["height"] / 2)
        page.mouse.down()
        page.mouse.move(*destination, steps=10)
        page.mouse.up()
        _wait_until(
            lambda: (
                page.wait_for_timeout(25),
                session.store.state.panels[active].layers[3].at,
            )[1],
            lambda at: at != [10, 100],
        )
        dragged = session.store.state.panels[active].layers[3].at
        assert dragged is not None
        assert dragged == pytest.approx([10**1.2, 10**2.3], rel=0.025)
        pointer = page.evaluate("window.lastPointer")
        _settle(page)
        handle = page.locator(f'[data-handle-id="layer-at:3:{active}"]')
        image_x = float(handle.get_attribute("data-imgx"))
        image_y = float(handle.get_attribute("data-imgy"))
        x0, y0, x1, y1 = session.layout["panel_bbox"]
        next_x = min(1, max(0, (min(1, image_x + 0.02) - x0) / (x1 - x0)))
        next_y = min(1, max(0, (image_y - y0) / (y1 - y0)))
        expected_key = [10 ** (2 - 2 * next_x), 10 ** (1 + 2 * next_y)]
        handle.focus()
        page.keyboard.press("ArrowRight")
        _wait_until(
            lambda: (
                page.wait_for_timeout(25),
                session.store.state.panels[active].layers[3].at,
            )[1],
            lambda at: at != dragged,
        )
        moved = session.store.state.panels[active].layers[3].at
        assert moved is not None and moved == pytest.approx(expected_key, rel=3e-5)
        assert moved[0] < dragged[0]  # rightward pixels on an inverted log x axis
        _settle(page)
        # HTMX restores focus on the next animation frame, not the state commit.
        page.wait_for_function(
            "id => document.activeElement.dataset.handleId === id",
            arg=f"layer-at:3:{active}",
            timeout=5000,
        )
        page.get_by_role("button", name="Undo", exact=True).click()
        _wait_until(
            lambda: session.store.state.panels[active].layers[3].at,
            lambda at: at == dragged,
        )
        _settle(page)
        page.get_by_role("button", name="Redo", exact=True).click()
        _wait_until(
            lambda: session.store.state.panels[active].layers[3].at,
            lambda at: at == moved,
        )
        _settle(page)
        preview_shape = page.locator(".preview-wrap img").evaluate(
            """async image => {
              await image.decode();
              return [image.naturalWidth, image.naturalHeight];
            }"""
        )
        assert session.store.state.dpi == 600 and session.store.state.size == [6, 3]
        assert session.store.state.panels[active].layers[2].at == [10, 1]
        assert session.store.state.panels[0].layers == []
        response = page.request.get(url + "/spec.json")
        assert (
            response.status == 200
            and mp.from_json(response.text()) == session.store.state
        )
        (tmp_path / "scale_trace.json").write_text(
            json.dumps(
                {
                    "dpr": dpr,
                    "css_zoom": css_zoom,
                    "visual_page_scale": page_scale,
                    "spec_dpi": 600,
                    "spec_size": [6, 3],
                    "preview_pixel_shape": preview_shape,
                    "desired_client_xy": destination,
                    "actual_pointer": pointer,
                    "drag_data": dragged,
                    "expected_drag": [10**1.2, 10**2.3],
                    "keyboard_data": moved,
                    "expected_keyboard": expected_key,
                    "layout": session.layout,
                },
                indent=2,
            ),
            encoding="utf-8",
        )
    finally:
        context.close()
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
