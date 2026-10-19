"""Keyboard-only local editor journey; semantics, not screen-reader certification."""

import json
import threading

import mudplot as mp
from dashboard.editor_server import EditorSession, make_server

from test_editor_browser import _settle, _wait_until
from test_review_coordinate_frames import document

pytest_plugins = ["test_editor_browser"]


def test_keyboard_panel_forms_error_recovery_handle_and_navigation(browser, tmp_path):
    spec, active = document((6, 3), 150, 2)
    session = EditorSession()
    session.load_spec(mp.to_json(spec))
    server = make_server(port=0, session=session)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    page = browser.new_page(viewport={"width": 1400, "height": 1100})
    tab_steps = []
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))

    def tab_to(target, label):
        for steps in range(220):
            if target.evaluate("element => element === document.activeElement"):
                tab_steps.append({"target": label, "tabs": steps})
                return
            page.keyboard.press("Tab")
        raise AssertionError(f"Keyboard target unreachable: {label}")

    def wait_state(read, predicate):
        return _wait_until(lambda: (page.wait_for_timeout(25), read())[1], predicate)

    try:
        url = f"http://127.0.0.1:{server.server_address[1]}"
        page.goto(url)
        _settle(page)
        page.evaluate("""() => {
          window.pointerDowns=0;
          document.addEventListener('pointerdown',()=>window.pointerDowns++);
        }""")
        assert (
            page.get_by_role("link", name="Editor", exact=True).get_attribute(
                "aria-current"
            )
            == "page"
        )
        second = page.get_by_role("group", name="Active panel").get_by_role(
            "button", name="2", exact=True
        )
        tab_to(second, "panel 2")
        page.keyboard.press("Enter")
        wait_state(lambda: session.active_panel, lambda panel: panel == active)
        _settle(page)
        assert (
            page.get_by_role("group", name="Active panel")
            .get_by_role("button", name="2", exact=True)
            .get_attribute("aria-pressed")
            == "true"
        )
        title = page.get_by_label("Panel title", exact=True)
        tab_to(title, "panel title")
        page.keyboard.press("Control+A")
        page.keyboard.type("keyboard only")
        page.keyboard.press("Enter")
        wait_state(
            lambda: session.store.state.panels[active].title,
            lambda title: title == "keyboard only",
        )
        _settle(page)
        advanced = page.locator('details[data-key="advanced"] > summary')
        tab_to(advanced, "advanced disclosure")
        page.keyboard.press("Enter")
        raw = page.get_by_label("Raw JSON action", exact=False)
        tab_to(raw, "raw action")
        page.keyboard.press("Control+A")
        page.keyboard.type("{")
        submit = page.get_by_role("button", name="Dispatch JSON action", exact=True)
        tab_to(submit, "dispatch invalid JSON")
        page.keyboard.press("Enter")
        wait_state(lambda: session.error, bool)
        _settle(page)
        alert = page.get_by_role("alert")
        assert alert.is_visible() and "JSON" in alert.inner_text()
        error_text = alert.inner_text()
        raw = page.get_by_label("Raw JSON action", exact=False)
        tab_to(raw, "correct raw action")
        page.keyboard.press("Control+A")
        page.keyboard.type(
            json.dumps(
                {"type": "SetTitle", "text": "keyboard recovered", "panel": active}
            )
        )
        tab_to(
            page.get_by_role("button", name="Dispatch JSON action", exact=True),
            "dispatch corrected JSON",
        )
        page.keyboard.press("Enter")
        wait_state(
            lambda: session.store.state.panels[active].title,
            lambda title: title == "keyboard recovered",
        )
        _settle(page)
        assert page.get_by_role("alert").count() == 0 and session.error is None
        handle = page.get_by_role(
            "button", name="Move panel title; drag or use arrow keys", exact=True
        )
        tab_to(handle, "panel title movement handle")
        assert handle.evaluate("el=>getComputedStyle(el).outlineWidth") == "2px"
        before = session.store.state.panels[active].title_position
        assert before is not None
        page.keyboard.press("ArrowRight")
        right = wait_state(
            lambda: session.store.state.panels[active].title_position,
            lambda value: value != before,
        )
        assert right is not None and right[0] > before[0]
        _settle(page)
        assert (
            page.evaluate("document.activeElement.dataset.handleId")
            == f"title::{active}"
        )
        page.keyboard.press("Shift+ArrowLeft")
        left = wait_state(
            lambda: session.store.state.panels[active].title_position,
            lambda value: value != right,
        )
        assert left is not None and left[0] < before[0]
        _settle(page)
        pointer_downs = page.evaluate("window.pointerDowns")
        assert pointer_downs == 0
        tab_to(page.get_by_role("link", name="Docs", exact=True), "Docs navigation")
        page.keyboard.press("Enter")
        page.wait_for_url(url + "/docs")
        assert (
            page.get_by_role("link", name="Docs", exact=True).get_attribute(
                "aria-current"
            )
            == "page"
        )
        tab_to(page.get_by_role("link", name="Editor", exact=True), "Editor navigation")
        page.keyboard.press("Enter")
        page.wait_for_url(url + "/")
        _settle(page)
        assert (
            page.get_by_label("Panel title", exact=True).input_value()
            == "keyboard recovered"
        )
        assert session.store.state.panels[0].title == "" and errors == []
        (tmp_path / "keyboard_trace.json").write_text(
            json.dumps(
                {
                    "tab_steps": tab_steps,
                    "pointerdowns_before_navigation": pointer_downs,
                    "selected_panel": active,
                    "error_text": error_text,
                    "recovered_title": "keyboard recovered",
                    "title_position_before": before,
                    "after_right": right,
                    "after_shift_left": left,
                    "page_errors": errors,
                    "scope": "Keyboard-only path; not full AT certification.",
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
