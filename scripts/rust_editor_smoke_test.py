"""Boot the Rust editor and exercise its Python/HTTP/htmx boundary."""

from __future__ import annotations

import argparse
import hashlib
import http.client
import json
import os
import socket
import struct
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import mudplot as mp
from mudplot.capabilities import LAYER_TYPES

REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST = REPO_ROOT / "mudplot-editor" / "Cargo.toml"


def _assert_security_headers(headers) -> None:
    assert headers["Cache-Control"] == "no-store"
    assert headers["X-Content-Type-Options"] == "nosniff"
    assert headers["X-Frame-Options"] == "DENY"
    assert "frame-ancestors 'none'" in headers["Content-Security-Policy"]
    assert "script-src 'self';" in headers["Content-Security-Policy"]


def _request(
    url: str,
    data: bytes | None = None,
    content_type: str | None = None,
    headers: dict[str, str] | None = None,
):
    request_headers = dict(headers or {})
    if content_type:
        request_headers["Content-Type"] = content_type
    try:
        response = urllib.request.urlopen(
            urllib.request.Request(url, data=data, headers=request_headers), timeout=30
        )
    except urllib.error.HTTPError as error:
        _assert_security_headers(error.headers)
        raise
    _assert_security_headers(response.headers)
    return response


def _review_recent_layer_contracts(base: str) -> None:
    def capture():
        with _request(f"{base}/spec.json") as response:
            spec = json.load(response)
        with _request(f"{base}/fig.png") as response:
            preview = response.read()
        assert preview.startswith(b"\x89PNG\r\n\x1a\n")
        return spec, preview

    original = capture()
    source = {"x": [2, 1, 2], "y": [3, -1, 4], "w": [1, 1, 2]}
    examples = [
        mp.plot(source).stem("x", "y", baseline=0.5).size(4, 3),
        mp.plot(source).regplot("x", "y", weights="w").size(4, 3),
        mp.plot(source).stairs("y", [0, 1, 3, 4], baseline=0.5).size(4, 3),
        mp.plot(source).eventplot("x", offset=1, length=0.4).size(4, 3),
        mp.plot(source).broken_barh("x", "w", bottom=1, height=0.5).size(4, 3),
        mp.plot(source).swarmplot("x", "y", semantics={"size": "w"}).size(4, 3),
        mp.plot(source)
        .swarmplot(
            "x",
            "y",
            semantics={
                "size": "w",
                "size_kind": "categorical",
                "size_order": [2, 3, 1],
            },
        )
        .size(4, 3),
    ]
    for plot in examples:
        expected = json.loads(plot.to_json())
        html = _submit(base, "/open", {"json": plot.to_json()})
        assert b'class="error"' not in html
        before = capture()
        assert before[0] == expected
        action = {"type": "SetTitle", "text": "Native layer round trip", "panel": 0}
        with _request(
            f"{base}/action", json.dumps(action).encode(), "application/json"
        ) as response:
            changed = json.load(response)
        plot.dispatch(mp.actions.SetTitle(action["text"]))
        after = capture()
        assert after[0] == changed == json.loads(plot.to_json())
        with _request(f"{base}/undo", b"") as response:
            assert response.status == 200
        assert capture() == before
        with _request(f"{base}/redo", b"") as response:
            assert response.status == 200
        assert capture() == after
    _submit(base, "/open", {"json": json.dumps(original[0])})
    assert capture() == original
    print(
        "Native layer boundary OK: stem/WLS/stairs/event/interval/numeric+class swarm"
    )


def _review_history_contracts(base: str) -> None:
    def capture():
        with _request(f"{base}/spec.json") as response:
            spec = json.load(response)
        with _request(f"{base}/fig.png") as response:
            return spec, response.read()

    states = [capture()]
    original, initial_preview = states[0]
    for title in ("A", "B", "C"):
        with _request(
            f"{base}/action",
            json.dumps({"type": "SetTitle", "text": title}).encode(),
            "application/json",
        ) as response:
            assert json.load(response)["panels"][0]["title"] == title
        states.append(capture())
    for state in reversed(states[:-1]):
        with _request(f"{base}/undo", b"") as response:
            assert response.status == 200
        assert capture() == state
    with _request(f"{base}/undo", b"") as response:
        assert response.status == 200
    assert capture() == states[0]
    for state in states[1:]:
        with _request(f"{base}/redo", b"") as response:
            assert response.status == 200
        assert capture() == state
    with _request(f"{base}/redo", b"") as response:
        assert response.status == 200
    assert capture() == states[-1]
    with _request(f"{base}/undo", b"") as response:
        assert response.status == 200
    with _request(
        f"{base}/action", b'{"type":"SetTitle","text":"D"}', "application/json"
    ) as response:
        assert json.load(response)["panels"][0]["title"] == "D"
    branch = capture()
    with _request(f"{base}/redo", b"") as response:
        assert response.status == 200
    assert capture() == branch
    assert mp.from_json(json.dumps(branch[0])).panels[0].title == "D"
    _submit(base, "/open", {"json": json.dumps(original)})
    assert capture() == (original, initial_preview)
    with _request(f"{base}/undo", b"") as response:
        assert response.status == 200
    assert capture() == branch  # Rust open is undoable; Python opens fresh history.
    with _request(f"{base}/redo", b"") as response:
        assert response.status == 200
    assert capture() == (original, initial_preview)
    print("History boundary/branch OK: spec and PNG agree at every undo/redo step")


def _review_document_policies(base: str) -> None:
    def capture():
        with _request(f"{base}/spec.json") as response:
            spec = json.load(response)
        with _request(f"{base}/fig.png") as response:
            return spec, response.read()

    def post(path):
        with _request(base + path, b"") as response:
            assert response.status == 200

    def title(text):
        with _request(
            f"{base}/action",
            json.dumps({"type": "SetTitle", "text": text}).encode(),
            "application/json",
        ) as response:
            assert json.load(response)["panels"][0]["title"] == text

    original = capture()
    first = (
        mp.plot({"x": [1, 2], "y": [2, 3]})
        .line("x", "y")
        .labels(title="document A")
        .size(4, 3)
    )
    second = (
        mp.plot({"u": [1, 2], "v": [3, 4]})
        .line("u", "v")
        .labels(title="document B")
        .size(4, 3)
    )
    _submit(base, "/open", {"json": first.to_json()})
    title("A-edited")
    edited_a = capture()
    title("A-future")
    post("/undo")
    assert capture() == edited_a
    _submit(base, "/open", {"json": second.to_json()})
    opened_b = capture()
    assert mp.FigureSpec.from_dict(opened_b[0]) == second.spec
    post("/redo")
    assert capture() == opened_b
    post("/undo")
    assert capture() == edited_a
    post("/redo")
    assert capture() == opened_b
    title("B-edited")
    edited_b = capture()
    post("/reset")
    assert capture() == original
    post("/undo")
    assert capture() == edited_b
    post("/redo")
    assert capture() == original
    title("no-op")
    unchanged = capture()
    title("discarded-future")
    post("/undo")
    assert capture() == unchanged
    title("no-op")
    post("/redo")
    assert capture() == unchanged
    post("/undo")
    assert capture() == unchanged
    post("/undo")
    assert capture() == original
    post("/redo")
    post("/redo")
    assert capture() == unchanged
    _submit(base, "/open", {"json": json.dumps(original[0])})
    assert capture() == original
    print(
        "Document/no-op policies OK: open/reset snapshots, "
        "redo invalidation and current JSON/PNG"
    )


def _review_preview_contracts(base: str) -> None:
    with _request(f"{base}/spec.json") as response:
        original = json.load(response)
    rows = []
    for size in ([4, 3], [3, 4]):
        for dpi in (499, 500, 501):
            plot = mp.plot({"x": [1, 2], "y": [2, 3]}).line("x", "y").size(*size)
            plot.dispatch(mp.actions.SetDpi(dpi))
            _submit(base, "/open", {"json": plot.to_json()})
            with _request(f"{base}/spec.json") as response:
                actual = json.load(response)
            assert actual == plot.spec.to_dict()
            with _request(f"{base}/fig.png") as response:
                pixels = struct.unpack(">II", response.read()[16:24])
            effective = min(dpi, 2000 / max(size))
            assert pixels == tuple(int(value * effective) for value in size)
            assert max(pixels) <= 2000
            with _request(f"{base}/fig.svg") as response:
                svg = response.read().decode("utf-8")
            assert f'width="{size[0] * 72}pt" height="{size[1] * 72}pt"' in svg
            with _request(f"{base}/fig.pdf") as response:
                assert (
                    f"/MediaBox [ 0 0 {size[0] * 72} {size[1] * 72} ]".encode()
                    in response.read()
                )
            with _request(f"{base}/spec.json") as response:
                assert json.load(response) == actual
            rows.append({"size": size, "dpi": dpi, "preview_pixels": pixels})
    _submit(base, "/open", {"json": json.dumps(original)})
    print("Preview boundary contract OK: " + json.dumps(rows, sort_keys=True))


def _review_state_paths(base: str) -> None:
    case = json.loads(
        (REPO_ROOT / "tests/fixtures/review_state_paths.json").read_text(
            encoding="utf-8"
        )
    )
    with _request(f"{base}/spec.json") as response:
        original = json.load(response)
    final_json = []
    for route in ("agent", "form"):
        state = mp.FigureSpec.from_dict(case["initial"])
        actual = state
        _submit(base, "/open", {"json": mp.to_json(state)})
        for step in case["steps"]:
            action = step["action"]
            if route == "form" and "rust_form" in step:
                form = step["rust_form"]
                assert b'class="error"' not in _submit(
                    base, form["path"], form["fields"]
                )
            elif route == "form" and action["type"] == "AddLayer":
                layer = dict(action["layer"])
                kind = layer.pop("type")
                assert b'class="error"' not in _submit(
                    base,
                    "/layers",
                    {
                        "layer_type": kind,
                        "fields": json.dumps(layer),
                        "panel": str(action["panel"]),
                    },
                )
            else:
                with _request(
                    f"{base}/action", json.dumps(action).encode(), "application/json"
                ) as response:
                    assert response.status == 200
            state = mp.apply([action], state)
            with _request(f"{base}/spec.json") as response:
                actual = mp.FigureSpec.from_dict(json.load(response))
                assert actual == state, action["type"]
        final_json.append(mp.to_json(actual, sort_keys=True))
    assert final_json[0] == final_json[1]
    _submit(base, "/open", {"json": json.dumps(original)})
    print(
        "Cross-path state OK (supported forms/agent):",
        hashlib.sha256(final_json[0].encode()).hexdigest(),
    )


def _review_failure_contracts(base: str) -> None:
    def capture():
        with _request(f"{base}/spec.json") as response:
            spec = json.load(response)
        with _request(f"{base}/fig.png") as response:
            return spec, response.read()

    original, _ = capture()
    valid = mp.plot({"x": [1, 2], "y": [2, 3]}).line("x", "y").size(4, 3)
    _submit(base, "/open", {"json": valid.to_json()})
    for title in ("A", "B"):
        with _request(
            f"{base}/action",
            json.dumps({"type": "SetTitle", "text": title}).encode(),
            "application/json",
        ) as response:
            assert response.status == 200
    future = capture()
    with _request(f"{base}/undo", b"") as response:
        assert response.status == 200
    before = capture()
    invalid = (
        mp.plot({"x": [1, 2], "y": [2, 3]}).line("x", "y", color="not-a-color").spec
    )
    assert mp.validate(invalid) == []
    for failure in ("invalid_action", "damaged_json", "render_action", "render_import"):
        if failure in ("invalid_action", "render_action"):
            action = (
                {"type": "SetSize", "width": -1, "height": 3}
                if failure == "invalid_action"
                else {
                    "type": "AddLayer",
                    "layer": invalid.panels[0].layers[0].to_dict(),
                }
            )
            try:
                _request(
                    f"{base}/action", json.dumps(action).encode(), "application/json"
                )
                raise AssertionError(f"unexpected successful {failure}")
            except urllib.error.HTTPError as error:
                assert error.code == 400
        else:
            text = "{damaged JSON" if failure == "damaged_json" else mp.to_json(invalid)
            assert b'class="error"' in _submit(base, "/open", {"json": text})
        assert capture() == before, failure
        with _request(f"{base}/redo", b"") as response:
            assert response.status == 200
        assert capture() == future, failure
        with _request(f"{base}/undo", b"") as response:
            assert response.status == 200
        assert capture() == before
    with _request(
        f"{base}/action", b'{"type":"SetTitle","text":"recovered"}', "application/json"
    ) as response:
        assert json.load(response)["panels"][0]["title"] == "recovered"
    _submit(base, "/open", {"json": json.dumps(original)})
    print("Failure atomicity OK: validation/JSON/render failures retain spec/PNG/redo")


def _review_http_boundaries(base: str) -> None:
    def headers(response_headers):
        assert response_headers["Cache-Control"] == "no-store"
        assert response_headers["X-Content-Type-Options"] == "nosniff"
        assert response_headers["X-Frame-Options"] == "DENY"
        assert "frame-ancestors 'none'" in response_headers["Content-Security-Policy"]

    def capture():
        with _request(f"{base}/spec.json") as response:
            spec = json.load(response)
        with _request(f"{base}/fig.png") as response:
            return spec, response.read()

    cases = json.loads(
        (REPO_ROOT / "tests/fixtures/review_http_boundaries.json").read_text(
            encoding="utf-8"
        )
    )
    before = capture()
    parsed = urllib.parse.urlparse(base)
    assert parsed.hostname is not None and parsed.port is not None
    for path in cases["rejected_file_paths"]:
        connection = http.client.HTTPConnection(parsed.hostname, parsed.port, timeout=5)
        try:
            connection.request("GET", path)
            response = connection.getresponse()
            assert response.status in (400, 404), path
            headers(response.headers)
            assert b"private route probe" not in response.read()
        finally:
            connection.close()
        assert capture() == before
    with tempfile.TemporaryDirectory(prefix="mudplot-http-export-") as directory:
        protected = Path(directory) / "private.txt"
        protected.write_bytes(b"private export probe")
        query = urllib.parse.urlencode({"out": str(protected), "path": str(protected)})
        with _request(f"{base}/fig.svg?{query}") as response:
            assert response.status == 200 and b"<svg" in response.read()
        assert protected.read_bytes() == b"private export probe"
        assert capture() == before
    for host in cases["rejected_hosts"]:
        try:
            _request(
                f"{base}/spec.json",
                headers={"Host": host, "X-Forwarded-Host": parsed.netloc},
            )
            raise AssertionError(f"accepted Host {host}")
        except urllib.error.HTTPError as error:
            assert error.code == 403
            headers(error.headers)
        assert capture() == before
    for host in cases["accepted_hosts"]:
        with _request(f"{base}/spec.json", headers={"Host": host}) as response:
            assert response.status == 200
            headers(response.headers)
    for template in cases["rejected_origins"]:
        request_headers = {
            name: value.format(base=base, port=parsed.port, other_port=parsed.port + 1)
            for name, value in template.items()
        }
        try:
            _request(
                f"{base}/action",
                b"",  # Require header rejection before body decoding/upload.
                "application/json",
                request_headers,
            )
            raise AssertionError(f"accepted Origin {template}")
        except urllib.error.HTTPError as error:
            assert error.code == 403
            headers(error.headers)
        assert capture() == before
    for template in cases["accepted_origins"]:
        request_headers = {
            name: value.format(base=base) for name, value in template.items()
        }
        with _request(
            f"{base}/action",
            b'{"type":"SetSuptitle","text":"accepted origin"}',
            "application/json",
            request_headers,
        ) as response:
            assert json.load(response)["suptitle"] == "accepted origin"
    accepted_state = capture()
    connection = http.client.HTTPConnection(parsed.hostname, parsed.port, timeout=5)
    try:
        connection.putrequest("POST", "/action")
        connection.putheader("Content-Type", "application/json")
        connection.putheader("Content-Length", str(16 * 1024 * 1024 + 1))
        connection.endheaders()
        response = connection.getresponse()
        assert response.status == 413
        headers(response.headers)
        response.read()
    finally:
        connection.close()
    assert capture() == accepted_state
    try:
        _request(f"{base}/does-not-exist")
        raise AssertionError("unknown route succeeded")
    except urllib.error.HTTPError as error:
        assert error.code == 404
        headers(error.headers)
    _submit(base, "/open", {"json": json.dumps(before[0])})
    print("HTTP boundary OK: Host/Origin/16MiB/path policies and security headers")


def _review_json_boundaries(base: str) -> None:
    corpus = json.loads(
        (REPO_ROOT / "tests/fixtures/review_json_boundaries.json").read_text(
            encoding="utf-8"
        )
    )
    with _request(f"{base}/spec.json") as response:
        before = json.load(response)
    with _request(f"{base}/fig.png") as response:
        preview = response.read()
    for case in corpus["invalid_specs"]:
        with _form(base, "/open", {"json": case["text"]}) as response:
            assert b"error" in response.read().lower(), case["id"]
        with _request(f"{base}/spec.json") as response:
            assert json.load(response) == before, case["id"]
        with _request(f"{base}/fig.png") as response:
            assert response.read() == preview, case["id"]
    for case in corpus["invalid_actions"]:
        try:
            _request(f"{base}/action", case["text"].encode(), "application/json")
            raise AssertionError(f"accepted action {case['id']}")
        except urllib.error.HTTPError as error:
            assert error.code in (400, 422), case["id"]
        with _form(base, "/action/raw", {"json": case["text"]}) as response:
            assert b"error" in response.read().lower(), case["id"]
        with _request(f"{base}/spec.json") as response:
            assert json.load(response) == before, case["id"]
        with _request(f"{base}/fig.png") as response:
            assert response.read() == preview, case["id"]
    for case in corpus["valid_specs"]:
        _submit(base, "/open", {"json": case["text"]})
        with _request(f"{base}/spec.json") as response:
            actual = mp.FigureSpec.from_dict(json.load(response))
        assert actual == mp.from_json(case["text"]), case["id"]
    _submit(base, "/open", {"json": json.dumps(before)})
    print(
        "JSON boundary corpus OK: 19 specs/11 actions rejected, "
        "2 accepted; spec/preview retained"
    )


def _form(base: str, path: str, fields: dict[str, str]):
    return _request(
        f"{base}{path}",
        urllib.parse.urlencode(fields).encode(),
        "application/x-www-form-urlencoded",
    )


def _submit(base: str, path: str, fields: dict[str, str]) -> bytes:
    with _form(base, path, fields) as response:
        assert response.status == 200
        return response.read()


def _browser_check(base: str) -> None:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as error:
        raise RuntimeError("--browser requires the browser extra") from error

    with sync_playwright() as playwright:
        try:
            browser = playwright.chromium.launch()
        except Exception:
            browser = playwright.chromium.launch(channel="chrome")
        page = browser.new_page()
        errors: list[str] = []

        def check_console(message):
            if "content security policy" in message.text.lower():
                errors.append(message.text)

        page.on("pageerror", lambda error: errors.append(error.stack or str(error)))
        page.on("console", check_console)
        page.goto(base)
        assert page.evaluate("typeof window.htmx") == "object"
        assert page.locator(".canvas img").evaluate("image => image.naturalWidth") > 0

        title = page.locator('form[hx-post="/control/title"] input[name="text"]')
        title.fill("Browser verified")
        page.locator('form[hx-post="/control/title"] button').click()
        page.wait_for_function(
            "document.querySelector('input[name=text]').value === 'Browser verified'"
        )
        assert page.url.rstrip("/") == base
        assert page.locator("header").is_visible()

        theme = page.locator('form[hx-post="/control/theme"] select')
        theme.select_option("paper")
        page.locator('form[hx-post="/control/theme"] button').click()
        page.wait_for_function(
            "document.querySelector('select[name=name]').value === 'paper'"
        )
        page.wait_for_load_state("networkidle")
        with _request(f"{base}/spec.json") as response:
            edited = mp.FigureSpec.from_dict(json.load(response))
        default = mp.Plot.from_json(
            (REPO_ROOT / "mudplot-editor/default_spec.json").read_text(encoding="utf-8")
        ).spec
        for operation, expected in (
            ("reset", default),
            ("undo", edited),
            ("redo", default),
        ):
            page.locator(f'button[hx-post="/{operation}"]').click()
            page.wait_for_load_state("networkidle")
            with _request(f"{base}/spec.json") as response:
                assert mp.FigureSpec.from_dict(json.load(response)) == expected
        assert not errors, errors
        browser.close()


def main(*, browser: bool = False) -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]

    env = {**os.environ, "MUDPLOT_PYTHON": sys.executable}
    process = subprocess.Popen(
        [
            "cargo",
            "run",
            "--quiet",
            "--locked",
            "--manifest-path",
            str(MANIFEST),
            "--",
            "--bind",
            f"127.0.0.1:{port}",
        ],
        cwd=REPO_ROOT,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    base = f"http://127.0.0.1:{port}"
    try:
        deadline = time.monotonic() + 60
        while True:
            if process.poll() is not None:
                raise RuntimeError(process.stdout.read() if process.stdout else "")
            try:
                with _request(f"{base}/spec.json") as response:
                    initial = json.load(response)
                break
            except urllib.error.URLError as error:
                if time.monotonic() >= deadline:
                    raise TimeoutError(
                        "Rust editor did not start within 60 seconds"
                    ) from error
                time.sleep(0.1)

        # History boundaries require fresh startup state before scenario edits.
        _review_history_contracts(base)
        _review_recent_layer_contracts(base)
        _review_document_policies(base)
        _review_preview_contracts(base)
        with _request(f"{base}/") as response:
            page = response.read()
            assert response.headers["X-Content-Type-Options"] == "nosniff"
            assert response.headers["Cache-Control"] == "no-store"
            assert response.headers["Cross-Origin-Resource-Policy"] == "same-origin"
            assert "object-src 'none'" in response.headers["Content-Security-Policy"]
            assert b"mudplot Rust editor" in page
            assert b"Visual controls" in page
            assert b'"allowScriptTags":false' in page
            expected = f"Required/optional fields for all {len(LAYER_TYPES)} layers"
            assert expected.encode() in page
        with _request(f"{base}/fig.png") as response:
            assert response.read(8) == b"\x89PNG\r\n\x1a\n"
        with _request(f"{base}/static/htmx.min.js") as response:
            assert len(response.read()) > 10_000

        try:
            _request(f"{base}/spec.json", headers={"Host": "attacker.example"})
            raise AssertionError("non-loopback Host unexpectedly succeeded")
        except urllib.error.HTTPError as error:
            assert error.code == 403
            assert error.headers["Cache-Control"] == "no-store"
            assert error.headers["X-Content-Type-Options"] == "nosniff"
            assert "frame-ancestors 'none'" in error.headers["Content-Security-Policy"]

        try:
            _request(
                f"{base}/action",
                b"",  # Probe the pre-body Origin boundary, not JSON validation.
                "application/json",
                {"Origin": "https://attacker.example"},
            )
            raise AssertionError("cross-origin action unexpectedly succeeded")
        except urllib.error.HTTPError as error:
            assert error.code == 403
            assert error.headers["Cache-Control"] == "no-store"
            assert error.headers["X-Content-Type-Options"] == "nosniff"
            assert "frame-ancestors 'none'" in error.headers["Content-Security-Policy"]

        html = _submit(base, "/control/title", {"text": "Visual form", "panel": "0"})
        assert b'value="Visual form"' in html
        html = _submit(base, "/control/theme", {"name": "paper-grid"})
        assert b'value="paper-grid" selected' in html
        html = _submit(base, "/control/size", {"width": "4", "height": "3"})
        assert b'name="width" type="number" min="0.01" step="any" value="4.0"' in html
        assert b'name="height" type="number" min="0.01" step="any" value="3.0"' in html
        html = _submit(
            base, "/control/projection", {"projection": "polar", "panel": "0"}
        )
        assert b'value="polar" selected' in html
        _submit(base, "/control/projection", {"projection": "2d", "panel": "0"})
        _submit(
            base,
            "/layers",
            {
                "layer_type": "scatter",
                "fields": '{"x":"x","y":"y","label":"points"}',
                "panel": "0",
            },
        )
        with _request(f"{base}/spec.json") as response:
            edited = json.load(response)
        assert edited["panels"][0]["title"] == "Visual form"
        assert edited["theme"]["name"] == "paper-grid"
        assert edited["size"] == [4.0, 3.0]
        assert edited["panels"][0]["projection"] == "2d"
        assert len(edited["panels"][0]["layers"]) == 2

        with _form(
            base,
            "/layers",
            {"layer_type": "scatter", "fields": "[]", "panel": "0"},
        ) as response:
            assert b"layer fields must be a JSON object" in response.read()
        with _request(f"{base}/spec.json") as response:
            assert len(json.load(response)["panels"][0]["layers"]) == 2

        edited["panels"][0]["title"] = "Opened spec"
        huge_integer = 10**80 + 1
        row_count = len(next(iter(edited["data"]["columns"].values())))
        huge_values = [huge_integer] * row_count
        edited["data"]["columns"]["unused_huge_integer"] = huge_values
        boundaries = [
            2**53 - 1,
            2**53,
            2**53 + 1,
            2**63 - 1,
            2**63,
            2**64 - 1,
            2**64,
            huge_integer,
        ]
        signed_boundaries = [
            value for number in boundaries for value in (number, -number)
        ]
        edited["data"]["columns"]["unused_integer_boundaries"] = [
            signed_boundaries
        ] * row_count
        edited["data"]["columns"]["unused_unicode"] = ["한글 Ω 😀"] * row_count
        edited["data"]["columns"]["sample_weight"] = [1.0] * row_count
        edited["data"]["columns"]["line_x"] = [i // 2 + 1 for i in range(row_count)]
        edited["data"]["columns"]["semantic_hue"] = [
            "A" if i % 2 else "B" for i in range(row_count)
        ]
        edited["data"]["columns"]["semantic_style"] = [
            "X" if i % 2 else "Y" for i in range(row_count)
        ]
        edited["data"]["columns"]["semantic_size"] = list(range(row_count))
        _submit(base, "/open", {"json": json.dumps(edited)})
        with _form(
            base,
            "/open",
            {"json": json.dumps({"version": "0.1", "panels": []})},
        ) as response:
            assert b"figure has no panels" in response.read()
        with _request(f"{base}/spec.json") as response:
            opened = json.load(response)
        assert opened["panels"][0]["title"] == "Opened spec"
        assert opened["data"]["columns"]["unused_huge_integer"] == huge_values
        assert (
            opened["data"]["columns"]["unused_integer_boundaries"]
            == [signed_boundaries] * row_count
        )
        assert opened["data"]["columns"]["unused_unicode"] == ["한글 Ω 😀"] * row_count
        with _request(f"{base}/fig.png") as response:
            previous_png = response.read()
        for payload in (
            '{"dpi":100,"dpi":100}',
            '{"dpi":100,"dpi":200}',
            '{"theme":{"font":{"size":11,"size":11}}}',
            '{"theme":{"font":{"size":11,"size":12}}}',
            '{"data":{"columns":{"unused":[{"key":1,"key":1}]}}}',
            '{"data":{"columns":{"unused":[{"key":1,"key":2}]}}}',
        ):
            with _form(base, "/open", {"json": payload}) as response:
                assert b"duplicate JSON object key" in response.read()
            with _request(f"{base}/spec.json") as response:
                assert json.load(response) == opened
            with _request(f"{base}/fig.png") as response:
                assert response.read() == previous_png

        action = json.dumps(
            {"type": "SetTitle", "text": "Agent JSON", "panel": 0}
        ).encode()
        with _request(f"{base}/action", action, "application/json") as response:
            agent_state = json.load(response)
            assert agent_state["panels"][0]["title"] == "Agent JSON"
        with _request(f"{base}/fig.png") as response:
            agent_preview = response.read()

        invalid_actions = (
            (
                json.dumps({"type": "SetSize", "width": -1, "height": 2}).encode(),
                400,
            ),
            (b'{"type":"SetSize","width":1e400,"height":2}', 400),
            (
                b'{"type":"SetTitle","type":"SetSize","width":1,"height":2}',
                422,
            ),
        )
        invalid_actions += tuple(
            (text.encode(), 422)
            for text in (
                '{"type":"SetTitle","text":"A","text":"A"}',
                '{"type":"SetTitle","text":"A","text":"B"}',
                '{"type":"SetFont","params":{"size":11,"size":11}}',
                '{"type":"SetFont","params":{"size":11,"size":12}}',
                '{"type":"SetData","columns":{"unused":[{"key":1,"key":1}]}}',
                '{"type":"SetData","columns":{"unused":[{"key":1,"key":2}]}}',
            )
        )
        for invalid, status in invalid_actions:
            try:
                _request(f"{base}/action", invalid, "application/json")
                raise AssertionError("invalid action unexpectedly succeeded")
            except urllib.error.HTTPError as error:
                assert error.code == status
            with _request(f"{base}/spec.json") as response:
                assert json.load(response) == agent_state
            with _request(f"{base}/fig.png") as response:
                assert response.read() == agent_preview
        for invalid, status in invalid_actions[3:]:
            assert status == 422
            with _form(base, "/action/raw", {"json": invalid.decode()}) as response:
                assert b"duplicate JSON object key" in response.read()
            with _request(f"{base}/spec.json") as response:
                assert json.load(response) == agent_state

        with _form(
            base,
            "/action/raw",
            {"json": '{"type":"SetTitle","text":"htmx form","panel":0}'},
        ) as response:
            assert b'<main id="app"' in response.read()
        with _request(f"{base}/undo", b"") as response:
            assert response.status == 200

        _submit(
            base,
            "/layers",
            {
                "layer_type": "violin",
                "fields": '{"x":"y","weights":"sample_weight","inner":"quart"}',
                "panel": "0",
            },
        )
        with _request(f"{base}/spec.json") as response:
            weighted = json.load(response)["panels"][0]["layers"][-1]
        assert weighted["type"] == "violin"
        assert weighted["weights"] == "sample_weight"

        with _request(
            f"{base}/action",
            json.dumps({"type": "SetLayout", "rows": 1, "cols": 2}).encode(),
            "application/json",
        ) as response:
            assert len(json.load(response)["panels"]) == 2
        _submit(
            base,
            "/layers",
            {
                "layer_type": "lineplot",
                "panel": "1",
                "fields": json.dumps(
                    {
                        "x": "line_x",
                        "y": "y",
                        "error_style": "band",
                        "stat": {"errorbar": "sd"},
                    }
                ),
            },
        )
        with _request(f"{base}/spec.json") as response:
            estimated = json.load(response)["panels"][1]["layers"][-1]
        assert estimated["type"] == "lineplot" and estimated["error_style"] == "band"
        _submit(
            base,
            "/layers",
            {
                "layer_type": "scatter",
                "panel": "1",
                "fields": json.dumps(
                    {
                        "x": "line_x",
                        "y": "y",
                        "semantics": {
                            "hue": "semantic_hue",
                            "size": "semantic_size",
                            "style": "semantic_style",
                            "legend": False,
                            "scale_id": "study",
                        },
                    }
                ),
            },
        )
        with _request(f"{base}/spec.json") as response:
            semantic = json.load(response)["panels"][1]["layers"][-1]
        assert semantic["semantics"]["hue"] == "semantic_hue"
        assert semantic["semantics"]["size"] == "semantic_size"
        assert semantic["semantics"]["style"] == "semantic_style"
        assert semantic["semantics"]["scale_id"] == "study"
        _submit(
            base,
            "/layers",
            {
                "layer_type": "scatter",
                "panel": "1",
                "fields": json.dumps(
                    {
                        "x": "x",
                        "y": "y",
                        "semantics": {
                            "hue": "semantic_hue",
                            "size": "semantic_size",
                            "style": "semantic_style",
                            "legend": True,
                            "scale_id": "study",
                        },
                    }
                ),
            },
        )
        with _request(f"{base}/spec.json") as response:
            shared = json.load(response)["panels"][1]["layers"][-2:]
        assert all(layer["semantics"]["scale_id"] == "study" for layer in shared)

        _submit(
            base,
            "/layers",
            {
                "layer_type": "lineplot",
                "panel": "1",
                "fields": json.dumps(
                    {
                        "x": "line_x",
                        "y": "y",
                        "stat": {"errorbar": None},
                        "semantics": {
                            "scale_id": "study",
                            "hue": "semantic_hue",
                            "size": "semantic_size",
                            "style": "semantic_style",
                        },
                    }
                ),
            },
        )
        with _request(f"{base}/spec.json") as response:
            mapped_line = json.load(response)["panels"][1]["layers"][-1]
        assert (
            mapped_line["type"] == "lineplot"
            and mapped_line["semantics"]["scale_id"] == "study"
        )

        for element, multiple in (
            ("bars", "stack"),
            ("bars", "dodge"),
            ("step", "layer"),
            ("step", "stack"),
        ):
            _submit(
                base,
                "/layers",
                {
                    "layer_type": "hist",
                    "panel": "1",
                    "fields": json.dumps(
                        {
                            "x": "line_x",
                            "group": "semantic_hue",
                            "bins": [0.5, 1.5, 2.5, 4.5],
                            "hue_order": ["empty", "B", "A"],
                            "histogram": {
                                "stat": "density",
                                "weights": "sample_weight",
                                "multiple": multiple,
                                "element": element,
                            },
                        }
                    ),
                },
            )
            with _request(f"{base}/spec.json") as response:
                histogram = json.load(response)["panels"][1]["layers"][-1]
            assert histogram["type"] == "hist"
            assert histogram["histogram"]["multiple"] == multiple
            assert histogram["histogram"]["element"] == element
            with _request(f"{base}/fig.png") as response:
                assert response.read(8) == b"\x89PNG\r\n\x1a\n"
            with _request(f"{base}/undo", b"") as response:
                assert response.status == 200

        exports = {}
        for fmt, prefix in (("pdf", b"%PDF"), ("svg", b"<?xml")):
            with _request(f"{base}/fig.{fmt}") as response:
                assert response.headers["Content-Disposition"].endswith(f"figure.{fmt}")
                exports[fmt] = response.read()
            assert exports[fmt].startswith(prefix)
            with _request(f"{base}/fig.{fmt}") as response:
                assert response.read() == exports[fmt]
        with _request(f"{base}/spec.json") as response:
            final = json.load(response)
        assert initial["panels"][0]["title"] == "mudplot Rust editor"
        assert final["panels"][0]["title"] == "Agent JSON"
        assert final["data"]["columns"]["unused_huge_integer"] == huge_values

        template = mp.plot(
            {
                "x": [2, 1, 1, 1, 2, 1, 2],
                "y": [8, 4, 5, 2, 3, 4, 6],
                "group": ["B", "B", "B", "A", "A", "A", "A"],
                "site": ["North"] * 5 + ["South"] * 2,
            }
        ).line("x", "y", group="group")
        _submit(base, "/open", {"json": template.to_json()})
        with _request(
            f"{base}/action",
            json.dumps({"type": "SetFacets", "col": "site"}).encode(),
            "application/json",
        ) as response:
            faceted = json.load(response)
        assert [panel["filters"] for panel in faceted["panels"]] == [
            {"site": "North"},
            {"site": "South"},
        ]
        assert faceted["data"] == template.spec.data.to_dict()
        assert all(
            panel["layers"][0]["hue_order"] == ["B", "A"] for panel in faceted["panels"]
        )
        assert all(panel["layers"][0]["stat"] is None for panel in faceted["panels"])
        with _request(f"{base}/fig.png") as response:
            assert response.read(8) == b"\x89PNG\r\n\x1a\n"
        with _request(f"{base}/fig.svg") as response:
            assert b"<svg" in response.read()
        joint_template = (
            mp.plot(
                {
                    "x": [1, 2, None, 4, 5],
                    "y": [2, 4, 5, None, 7],
                    "group": ["A", "A", "B", "B", "B"],
                }
            )
            .scatter("x", "y", group="group")
            .size(6, 6)
        )
        _submit(base, "/open", {"json": joint_template.to_json()})
        with _request(
            f"{base}/action",
            json.dumps({"type": "SetJointGrid", "bins": 3}).encode(),
            "application/json",
        ) as response:
            joint = json.load(response)
        assert len(joint["panels"]) == 3 and joint["layout"] == [2, 2]
        assert joint["data"] == joint_template.spec.data.to_dict()
        assert all(panel["dropna"] == ["x", "y", "group"] for panel in joint["panels"])
        assert joint["share_x"] == "col" and joint["share_y"] == "row"
        for extension, prefix in (("png", b"\x89PNG"), ("svg", b"<?xml")):
            with _request(f"{base}/fig.{extension}") as response:
                assert response.read().startswith(prefix)
        pair_template = mp.plot(
            {
                "a": [1, 2, None, 4],
                "b": [2, None, 4, 5],
                "c": [4, 3, 2, 1],
                "group": ["A", "A", "B", "B"],
            }
        ).size(8, 8)
        _submit(base, "/open", {"json": pair_template.to_json()})
        with _request(
            f"{base}/action",
            json.dumps(
                {
                    "type": "SetPairGrid",
                    "columns": ["a", "b", "c"],
                    "group": "group",
                    "bins": 3,
                }
            ).encode(),
            "application/json",
        ) as response:
            pair = json.load(response)
        assert len(pair["panels"]) == 9 and pair["layout"] == [3, 3]
        assert pair["data"] == pair_template.spec.data.to_dict()
        assert pair["panels"][1]["y"]["share_id"] == pair["panels"][2]["y"]["share_id"]
        assert pair["panels"][0]["y"]["share_id"] is None
        for extension, prefix in (("png", b"\x89PNG"), ("svg", b"<?xml")):
            with _request(f"{base}/fig.{extension}") as response:
                assert response.read().startswith(prefix)
        kde_data = {
            "x": [1, 2, 3, 4, 5, 6],
            "y": [2, 4, 3, 5, 7, 6],
            "z": [6, 4, 5, 3, 1, 2],
            "group": ["A"] * 3 + ["B"] * 3,
        }
        kde_template = mp.plot(kde_data).scatter("x", "y", group="group").size(6, 6)
        _submit(base, "/open", {"json": kde_template.to_json()})
        with _request(
            f"{base}/action",
            json.dumps(
                {
                    "type": "SetJointGrid",
                    "marginal_kind": "kde",
                    "kde": {"cut": 0, "gridsize": 31, "bw_adjust": 0.75},
                }
            ).encode(),
            "application/json",
        ) as response:
            kde_joint = json.load(response)
        assert kde_joint["data"] == kde_template.spec.data.to_dict()
        assert all(kde_joint["panels"][i]["layers"][0]["type"] == "kde" for i in (1, 2))
        kde_pair_template = mp.plot(kde_data).size(8, 8)
        _submit(base, "/open", {"json": kde_pair_template.to_json()})
        with _request(
            f"{base}/action",
            json.dumps(
                {
                    "type": "SetPairGrid",
                    "columns": ["x", "y", "z"],
                    "group": "group",
                    "diag_kind": "kde",
                    "kde": {"cut": 0, "gridsize": 31},
                }
            ).encode(),
            "application/json",
        ) as response:
            kde_pair = json.load(response)
        assert kde_pair["data"] == kde_pair_template.spec.data.to_dict()
        assert all(
            kde_pair["panels"][i]["layers"][0]["type"] == "kde" for i in (0, 4, 8)
        )
        for extension, prefix in (("png", b"\x89PNG"), ("svg", b"<?xml")):
            with _request(f"{base}/fig.{extension}") as response:
                assert response.read().startswith(prefix)
        heatmap_template = mp.plot().matrix("m", [[-2, 0, 3], [1, 4, 8]]).size(6, 4)
        _submit(base, "/open", {"json": heatmap_template.to_json()})
        with _request(
            f"{base}/action",
            json.dumps(
                {
                    "type": "AddLayer",
                    "layer": {
                        "type": "heatmap",
                        "matrix": "m",
                        "cmap_kind": "diverging",
                        "colorbar": True,
                        "line_width": 0.5,
                        "edge_color": "#ffffff",
                        "heatmap": {
                            "annot": True,
                            "center": 0,
                            "fmt": ".1f",
                            "mask": [[False, True, False], [False, False, False]],
                            "xlabels": ["A", "B", "C"],
                            "ylabels": ["N", "S"],
                        },
                    },
                }
            ).encode(),
            "application/json",
        ) as response:
            heatmap = json.load(response)
        assert heatmap["data"] == heatmap_template.spec.data.to_dict()
        assert heatmap["panels"][0]["layers"][0]["heatmap"]["annot"] is True
        for extension, prefix in (("png", b"\x89PNG"), ("svg", b"<?xml")):
            with _request(f"{base}/fig.{extension}") as response:
                assert response.read().startswith(prefix)
        from examples.regression_modes import build_plots as regression_examples

        for name, source in regression_examples().items():
            template = mp.plot(source.spec.data.columns).size(7, 4.5)
            _submit(base, "/open", {"json": template.to_json()})
            layer = source.spec.panels[0].layers[0]
            with _request(
                f"{base}/action",
                json.dumps({"type": "AddLayer", "layer": layer.to_dict()}).encode(),
                "application/json",
            ) as response:
                regression = json.load(response)
            assert regression["data"] == template.spec.data.to_dict(), name
            assert (
                regression["panels"][0]["layers"][0]["regression"]
                == layer.to_dict()["regression"]
            )
            for extension, prefix in (("png", b"\x89PNG"), ("svg", b"<?xml")):
                with _request(f"{base}/fig.{extension}") as response:
                    assert response.read().startswith(prefix), name
        from examples.clustered_profiles import build_plot as cluster_example

        source = cluster_example()
        template = (
            mp.plot()
            .matrix("profiles", source.spec.data.matrices["profiles"])
            .size(7, 6.5)
        )
        _submit(base, "/open", {"json": template.to_json()})
        with _request(
            f"{base}/action",
            json.dumps(
                {
                    "type": "AddLayer",
                    "layer": source.spec.panels[0].layers[0].to_dict(),
                }
            ).encode(),
            "application/json",
        ) as response:
            clustered = json.load(response)
        assert clustered["data"] == template.spec.data.to_dict()
        assert clustered["panels"][0]["layers"][0]["cluster"]["z_score"] == "row"
        for extension, prefix in (("png", b"\x89PNG"), ("svg", b"<?xml")):
            with _request(f"{base}/fig.{extension}") as response:
                assert response.read().startswith(prefix)
        _review_state_paths(base)
        _review_failure_contracts(base)
        _review_http_boundaries(base)
        _review_json_boundaries(base)
        if browser:
            _browser_check(base)
    finally:
        if os.name == "nt" and process.poll() is None:
            # Terminate this owned cargo/server tree, not just its cargo parent.
            subprocess.run(
                ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                capture_output=True,
                timeout=10,
            )
        else:
            process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()

    print("Rust editor smoke test OK")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--browser", action="store_true")
    raise SystemExit(main(browser=parser.parse_args().browser))
