"""Controlled response delivery order with real htmx and server rendering."""

import hashlib
import io
import json
import threading
from urllib.parse import parse_qs, urlparse

import mudplot as mp
from dashboard.editor_server import EditorSession, make_server
from PIL import Image

from test_editor_browser import _settle, _wait_until

pytest_plugins = ["test_editor_browser"]


def test_late_old_fragment_cannot_overwrite_latest_successful_state(browser, tmp_path):
    spec = (
        mp.plot({"x": [0, 1, 2], "y": [1, 3, 2]})
        .line("x", "y")
        .size(4, 3)
        .labels(title="initial")
        .spec
    )
    spec.dpi = 100
    session = EditorSession()
    session.load_spec(mp.to_json(spec))
    server = make_server(port=0, session=session)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    page = browser.new_page(viewport={"width": 1400, "height": 1000})
    held = []
    timeline = []
    errors = []
    console_errors = []
    failed_requests = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.on(
        "console",
        lambda message: (
            console_errors.append(
                {
                    "text": message.text,
                    "path": urlparse(message.location.get("url", "")).path,
                }
            )
            if message.type == "error"
            else None
        ),
    )
    page.on("requestfailed", lambda request: failed_requests.append(request.failure))

    def route_action(route):
        text = parse_qs(route.request.post_data or "").get("text", [""])[0]
        response = route.fetch()
        timeline.append(
            {
                "event": "server_response",
                "request": text,
                "generation": response.headers.get("x-mudplot-view-generation"),
                "status": response.status,
                "committed_title": session.store.state.panels[0].title,
                "png_sha256": hashlib.sha256(session.png).hexdigest(),
            }
        )
        if text == "older-first":
            held.append((route, response))
            return
        route.fulfill(response=response)

    try:
        page.goto(f"http://127.0.0.1:{server.server_address[1]}")
        _settle(page)
        page.route("**/action", route_action)
        page.evaluate("""() => {
          window.finishedTitles = [];
          window.issueTitle = (text, index) => {
            const source = document.querySelectorAll('form[hx-post="/action"]')[index];
            htmx.ajax('POST', '/action', {
              source:source, target:'#app-body', swap:'innerHTML',
              values:{type:'set_title',panel:0,text:text}
            }).then(() => window.finishedTitles.push(text));
          };
        }""")
        page.evaluate("() => { window.issueTitle('older-first', 0); }")
        _wait_until(lambda: (page.wait_for_timeout(25), len(held))[1], lambda n: n == 1)
        assert session.store.state.panels[0].title == "older-first"
        page.evaluate("() => { window.issueTitle('newer-second', 1); }")
        _wait_until(
            lambda: page.get_by_label("Panel title").input_value(),
            lambda value: value == "newer-second",
        )
        assert session.store.state.panels[0].title == "newer-second"
        timeline.append(
            {
                "event": "new_visible",
                "dom_title": page.get_by_label("Panel title").input_value(),
                "spec_title": session.store.state.panels[0].title,
            }
        )
        held[0][0].fulfill(response=held[0][1])
        held.clear()
        _settle(page)
        page.wait_for_function("() => window.finishedTitles.length === 2")
        actual_pixel_hash = page.evaluate("""async () => {
          const image=document.querySelector('.preview-wrap img'); await image.decode();
          const canvas=document.createElement('canvas');
          canvas.width=image.naturalWidth; canvas.height=image.naturalHeight;
          const ctx=canvas.getContext('2d'); ctx.drawImage(image,0,0);
          const bytes=ctx.getImageData(0,0,canvas.width,canvas.height).data;
          const digest=await crypto.subtle.digest('SHA-256',bytes);
          return Array.from(new Uint8Array(digest))
            .map(v=>v.toString(16).padStart(2,'0')).join('');
        }""")
        with Image.open(io.BytesIO(session.png)) as image:
            expected_pixel_hash = hashlib.sha256(
                image.convert("RGBA").tobytes()
            ).hexdigest()
        timeline.append(
            {
                "event": "old_released",
                "dom_title": page.get_by_label("Panel title").input_value(),
                "spec_title": session.store.state.panels[0].title,
                "actual_pixels": actual_pixel_hash,
                "expected_pixels": expected_pixel_hash,
                "page_errors": errors,
                "console_errors": console_errors,
                "failed_requests": failed_requests,
            }
        )
        (tmp_path / "timeline.json").write_text(
            json.dumps(timeline, indent=2), encoding="utf-8"
        )
        assert timeline[-1]["dom_title"] == timeline[-1]["spec_title"] == "newer-second"
        assert actual_pixel_hash == expected_pixel_hash
        assert [
            row["generation"] for row in timeline if row["event"] == "server_response"
        ] == ["1", "2"]
        assert len(session.action_log()) == 2
        assert errors == [] and failed_requests == []
        assert not [
            error for error in console_errors if error["path"] != "/favicon.ico"
        ]
        assert page.locator("#app-body").count() == 1
    finally:
        for route, response in held:
            route.fulfill(response=response)
        page.close()
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
