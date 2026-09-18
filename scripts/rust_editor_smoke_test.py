"""Boot the Rust editor and exercise its Python/HTTP/htmx boundary."""

from __future__ import annotations

import argparse
import json
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST = REPO_ROOT / "mudplot-editor" / "Cargo.toml"


def _request(
    url: str,
    data: bytes | None = None,
    content_type: str | None = None,
    headers: dict[str, str] | None = None,
):
    request_headers = dict(headers or {})
    if content_type:
        request_headers["Content-Type"] = content_type
    return urllib.request.urlopen(
        urllib.request.Request(url, data=data, headers=request_headers), timeout=30
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
        page.on("pageerror", lambda error: errors.append(str(error)))
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

        with _request(f"{base}/") as response:
            page = response.read()
            assert response.headers["X-Content-Type-Options"] == "nosniff"
            assert response.headers["Cache-Control"] == "no-store"
            assert response.headers["Cross-Origin-Resource-Policy"] == "same-origin"
            assert "object-src 'none'" in response.headers["Content-Security-Policy"]
            assert b"mudplot Rust editor" in page
            assert b"Visual controls" in page
            assert b'"allowScriptTags":false' in page
            assert b"Required/optional fields for all 28 layers" in page
        with _request(f"{base}/fig.png") as response:
            assert response.read(8) == b"\x89PNG\r\n\x1a\n"
        with _request(f"{base}/static/htmx.min.js") as response:
            assert len(response.read()) > 10_000

        try:
            _request(f"{base}/spec.json", headers={"Host": "attacker.example"})
            raise AssertionError("non-loopback Host unexpectedly succeeded")
        except urllib.error.HTTPError as error:
            assert error.code == 403

        cross_origin = json.dumps(
            {"type": "SetTitle", "text": "CSRF", "panel": 0}
        ).encode()
        try:
            _request(
                f"{base}/action",
                cross_origin,
                "application/json",
                {"Origin": "https://attacker.example"},
            )
            raise AssertionError("cross-origin action unexpectedly succeeded")
        except urllib.error.HTTPError as error:
            assert error.code == 403

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

        action = json.dumps(
            {"type": "SetTitle", "text": "Agent JSON", "panel": 0}
        ).encode()
        with _request(f"{base}/action", action, "application/json") as response:
            assert json.load(response)["panels"][0]["title"] == "Agent JSON"

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
        for invalid, status in invalid_actions:
            try:
                _request(f"{base}/action", invalid, "application/json")
                raise AssertionError("invalid action unexpectedly succeeded")
            except urllib.error.HTTPError as error:
                assert error.code == status

        with _form(
            base,
            "/action/raw",
            {"json": '{"type":"SetTitle","text":"htmx form","panel":0}'},
        ) as response:
            assert b'<main id="app">' in response.read()
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
        if browser:
            _browser_check(base)
    finally:
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
