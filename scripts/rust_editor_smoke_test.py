"""Boot the Rust editor and exercise its Python/HTTP/htmx boundary."""

from __future__ import annotations

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


def _request(url: str, data: bytes | None = None, content_type: str | None = None):
    headers = {"Content-Type": content_type} if content_type else {}
    return urllib.request.urlopen(
        urllib.request.Request(url, data=data, headers=headers), timeout=30
    )


def main() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]

    env = {**os.environ, "MUDPLOT_PYTHON": sys.executable}
    process = subprocess.Popen(
        [
            "cargo",
            "run",
            "--quiet",
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
            assert b"mudplot Rust editor" in response.read()
        with _request(f"{base}/fig.png") as response:
            assert response.read(8) == b"\x89PNG\r\n\x1a\n"
        with _request(f"{base}/static/htmx.min.js") as response:
            assert len(response.read()) > 10_000

        action = json.dumps(
            {"type": "SetTitle", "text": "Agent JSON", "panel": 0}
        ).encode()
        with _request(f"{base}/action", action, "application/json") as response:
            assert json.load(response)["panels"][0]["title"] == "Agent JSON"

        invalid = json.dumps({"type": "SetSize", "width": -1, "height": 2}).encode()
        try:
            _request(f"{base}/action", invalid, "application/json")
            raise AssertionError("invalid action unexpectedly succeeded")
        except urllib.error.HTTPError as error:
            assert error.code == 400

        raw = urllib.parse.urlencode(
            {"json": '{"type":"SetTitle","text":"htmx form","panel":0}'}
        ).encode()
        with _request(
            f"{base}/action/raw", raw, "application/x-www-form-urlencoded"
        ) as response:
            assert b'<main id="app">' in response.read()
        with _request(f"{base}/undo", b"") as response:
            assert response.status == 200
        with _request(f"{base}/spec.json") as response:
            final = json.load(response)
        assert initial["panels"][0]["title"] == "mudplot Rust editor"
        assert final["panels"][0]["title"] == "Agent JSON"
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
    raise SystemExit(main())
