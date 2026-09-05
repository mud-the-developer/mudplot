"""CI helper: boot the dashboard's local editor server and hit two routes.

A real script file for the same reason as ``check_wheel.py`` -- inline YAML
heredocs are fragile (indentation rules, quoting) compared to a normal
Python file.
"""

from __future__ import annotations

import sys
import threading
import time
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))


def main() -> int:
    from dashboard.editor_server import make_server

    server = make_server(port=0)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    time.sleep(0.2)
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/") as r:
            assert r.status == 200
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/fig.png") as r:
            assert r.status == 200
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/docs") as r:
            assert r.status == 200
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/static/htmx.min.js") as r:
            assert r.status == 200
            assert len(r.read()) > 1000
    finally:
        server.shutdown()
    print("editor smoke test OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
