"""File/open and real vector-export failure recovery through the browser UI."""

import hashlib
import json
import threading

import matplotlib.pyplot as plt
import mudplot as mp
import pytest
from dashboard.editor_server import EditorSession, make_server
from mudplot import _render as renderer

from test_editor_browser import _settle, _wait_until

pytest_plugins = ["test_editor_browser"]


@pytest.mark.parametrize(
    "swap_delay,settle_delay", [(0, 20), (200, 100)], ids=["normal", "delayed-dom"]
)
def test_file_failures_and_vector_export_failures_preserve_state_then_recover(
    browser, monkeypatch, tmp_path, swap_delay, settle_delay
):
    first = (
        mp.plot({"x": [1, 2], "y": [2, 3]})
        .line("x", "y")
        .labels(title="file A")
        .size(4, 3)
        .spec
    )
    second = (
        mp.plot({"u": [1, 2], "v": [3, 4]})
        .line("u", "v")
        .labels(title="file B")
        .size(4, 3)
        .spec
    )
    first.dpi = second.dpi = 100
    invalid_spec = mp.plot({"u": [1, 2], "v": [3, 4]}).line("missing", "v").spec
    files = {
        "a": tmp_path / "source-a.json",
        "bad_json": tmp_path / "broken.json",
        "bad_spec": tmp_path / "invalid.json",
        "b": tmp_path / "source-b.json",
    }
    files["a"].write_text(mp.to_json(first), encoding="utf-8")
    files["bad_json"].write_text('{"bad":', encoding="utf-8")
    files["bad_spec"].write_text(mp.to_json(invalid_spec), encoding="utf-8")
    files["b"].write_text(mp.to_json(second), encoding="utf-8")
    originals = {name: path.read_bytes() for name, path in files.items()}
    session = EditorSession()
    server = make_server(port=0, session=session)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    page = browser.new_page(viewport={"width": 1400, "height": 1000})
    page.add_init_script(
        "document.addEventListener('DOMContentLoaded', () => {"
        f"window.htmx.config.defaultSwapDelay = {swap_delay};"
        f"window.htmx.config.defaultSettleDelay = {settle_delay};"
        "});"
    )
    timeline = []
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    export_failure = threading.Event()
    original_save = renderer._save_figure

    def save(fig, spec, target, fmt):
        if export_failure.is_set() and fmt == "svg":
            raise OSError("synthetic SVG export failure")
        return original_save(fig, spec, target, fmt)

    def snapshot(stage):
        state = session.store.state
        row = {
            "stage": stage,
            "spec_sha256": hashlib.sha256(
                mp.to_json(state, sort_keys=True).encode()
            ).hexdigest(),
            "png_sha256": hashlib.sha256(session.png).hexdigest(),
            "history": session.action_log(),
            "error": session.error,
        }
        timeline.append(row)
        return state, session.png, session.action_log(), dict(session.layout)

    def open_file(path):
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
        _settle(page)

    def edit_title(text):
        page.get_by_label("Panel title", exact=True).fill(text)
        page.get_by_label("Panel title", exact=True).press("Enter")
        _wait_until(
            lambda: session.store.state.panels[0].title, lambda value: value == text
        )
        _settle(page)

    try:
        url = f"http://127.0.0.1:{server.server_address[1]}"
        page.goto(url)
        _settle(page)
        open_file(files["a"])
        _wait_until(lambda: session.store.state, lambda state: state == first)
        edit_title("A edited")
        saved = snapshot("a_edited")
        assert saved[2]
        for name in ("bad_json", "bad_spec"):
            open_file(files[name])
            page.locator(".error").wait_for()
            assert (
                session.store.state,
                session.png,
                session.action_log(),
                session.layout,
            ) == saved
            assert page.locator("#spec-json").input_value() == files[name].read_text(
                encoding="utf-8"
            )
            text = page.locator(".error").inner_text()
            assert (
                "invalid figure spec" in text
                and "Traceback (most recent call last)" not in text
            )
            assert str(tmp_path) not in text
            snapshot(name + "_rejected")
            assert page.locator(".preview-wrap img").is_visible()
        open_file(files["b"])
        _wait_until(lambda: session.store.state, lambda state: state == second)
        assert session.error is None and session.action_log() == []
        _settle(page)
        assert page.locator(".error").count() == 0
        edit_title("B edited")
        saved = snapshot("b_edited")
        figures = set(plt.get_fignums())
        monkeypatch.setattr(renderer, "_save_figure", save)
        export_failure.set()
        failed = page.request.get(url + "/fig.svg")
        assert failed.status == 400
        assert failed.headers["content-type"].startswith("text/html")
        assert "synthetic SVG export failure" in failed.text()
        assert (
            session.store.state,
            session.png,
            session.action_log(),
            session.layout,
        ) == saved
        assert set(plt.get_fignums()) == figures
        snapshot("svg_export_rejected")
        edit_title("B after export failure")
        assert session.error is None
        export_failure.clear()
        exported = page.request.get(url + "/fig.svg")
        assert exported.status == 200 and exported.headers["content-type"].startswith(
            "image/svg+xml"
        )
        assert "<svg" in exported.text() and "B after export failure" in exported.text()
        snapshot("edited_and_exported")
        with page.expect_download() as download:
            page.get_by_role("link", name="Spec (.json)", exact=True).click()
        target = tmp_path / "download.json"
        download.value.save_as(str(target))
        assert mp.load_spec(target) == session.store.state
        assert {name: path.read_bytes() for name, path in files.items()} == originals
        assert errors == []
        (tmp_path / "recovery_timeline.json").write_text(
            json.dumps(
                {
                    "timeline": timeline,
                    "failed_export_status": failed.status,
                    "recovered_export_status": exported.status,
                    "source_files_unchanged": True,
                    "download_matches_state": True,
                    "page_errors": errors,
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
