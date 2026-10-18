"""Two local pages and a raw-action client share the documented session lock."""

import hashlib
import json
import threading
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlencode

import mudplot as mp
from dashboard import editor_server as editor
from mudplot import actions as A

from test_editor_browser import _settle, _wait_until

pytest_plugins = ["test_editor_browser"]


def test_two_tabs_and_raw_action_have_serial_commits_without_lost_fields(
    browser, monkeypatch, tmp_path
):
    initial = mp.plot({"x": [0, 1, 2], "y": [1, 3, 2]}).line("x", "y").size(4, 3).spec
    initial.dpi = 100
    session = editor.EditorSession()
    session.load_spec(mp.to_json(initial))
    original_png = session.png
    entered = threading.Event()
    release = threading.Event()
    arrivals = []
    commits = []
    observed = {name: threading.Event() for name in ("tab-a", "tab-b", "raw")}
    original_read = editor._Handler._read_body
    original_render = session._render_preview
    original_commit = session._commit_store

    def read_body(handler):
        body = original_read(handler)
        actor = handler.headers.get("X-Test-Actor")
        if actor in observed:
            arrivals.append(actor)
            observed[actor].set()
        return body

    def render(spec, active_panel):
        if not entered.is_set():
            entered.set()
            assert release.wait(12)
        return original_render(spec, active_panel)

    def commit(store, active_panel):
        original_commit(store, active_panel)
        action = session.store.history[-1]
        actor = (
            "tab-a"
            if isinstance(action, A.SetTitle)
            else "tab-b"
            if isinstance(action, A.SetSuptitle)
            else "raw"
        )
        commits.append(
            {
                "actor": actor,
                "action": A.action_to_dict(action),
                "spec_sha256": hashlib.sha256(
                    mp.to_json(session.store.state, sort_keys=True).encode()
                ).hexdigest(),
                "png_sha256": hashlib.sha256(session.png).hexdigest(),
            }
        )

    monkeypatch.setattr(editor._Handler, "_read_body", read_body)
    monkeypatch.setattr(session, "_render_preview", render)
    monkeypatch.setattr(session, "_commit_store", commit)
    server = editor.make_server(port=0, session=session)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    url = f"http://127.0.0.1:{server.server_address[1]}"
    pages = [
        browser.new_page(viewport={"width": 1400, "height": 1000}) for _ in range(2)
    ]

    def raw_action():
        data = urlencode(
            {"json": json.dumps(A.action_to_dict(A.SetSize(5, 3)))}
        ).encode()
        request = urllib.request.Request(
            url + "/action/raw",
            data=data,
            headers={"HX-Request": "true", "X-Test-Actor": "raw"},
        )
        with urllib.request.urlopen(request, timeout=20) as response:
            return {
                "status": response.status,
                "content_type": response.headers.get_content_type(),
                "generation": response.headers.get("X-Mudplot-View-Generation"),
                "body_length": len(response.read()),
            }

    try:
        for page in pages:
            page.goto(url)
            _settle(page)
        pages[0].evaluate("""() => {
          htmx.ajax('POST','/action', {target:'#app-body',swap:'innerHTML',
            headers:{'X-Test-Actor':'tab-a'},
            values:{type:'set_title',panel:0,text:'tab-a'}});
        }""")
        _wait_until(lambda: (pages[0].wait_for_timeout(25), entered.is_set())[1], bool)
        pages[1].evaluate("""() => {
          htmx.ajax('POST','/action', {target:'#app-body',swap:'innerHTML',
            headers:{'X-Test-Actor':'tab-b'},
            values:{type:'set_suptitle',text:'tab-b'}});
        }""")
        _wait_until(
            lambda: (pages[1].wait_for_timeout(25), observed["tab-b"].is_set())[1], bool
        )
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(raw_action)
            assert observed["raw"].wait(5)
            assert arrivals == ["tab-a", "tab-b", "raw"]
            assert (
                commits == []
                and session.store.state == initial
                and session.png == original_png
            )
            release.set()
            raw_response = future.result(timeout=20)
        _wait_until(
            lambda: (pages[0].wait_for_timeout(25), len(commits))[1], lambda n: n == 3
        )
        orders = [c["actor"] for c in commits]
        assert orders in (["tab-a", "tab-b", "raw"], ["tab-a", "raw", "tab-b"])
        allowed = mp.apply(
            [A.SetTitle("tab-a"), A.SetSuptitle("tab-b"), A.SetSize(5, 3)], initial
        )
        assert session.store.state == allowed and len(session.store.history) == 3
        assert (
            raw_response["status"] == 200
            and raw_response["content_type"] == "text/html"
        )
        assert raw_response["generation"] in ("2", "3")
        reference = editor.EditorSession()
        reference.load_spec(mp.to_json(allowed))
        assert session.png == reference.png
        for page in pages:
            page.reload()
            _settle(page)
            assert page.get_by_label("Panel title").input_value() == "tab-a"
            assert float(page.locator('input[name="width"]').input_value()) == 5
        (tmp_path / "shared_timeline.json").write_text(
            json.dumps(
                {
                    "arrivals": arrivals,
                    "commits": commits,
                    "raw_response": raw_response,
                    "final_spec": allowed.to_dict(),
                    "final_png_sha256": hashlib.sha256(session.png).hexdigest(),
                    "tabs_refreshed": 2,
                    "policy": "Session-serialized; no live collaboration/FIFO claim.",
                },
                indent=2,
            ),
            encoding="utf-8",
        )
    finally:
        release.set()
        for page in pages:
            page.close()
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
