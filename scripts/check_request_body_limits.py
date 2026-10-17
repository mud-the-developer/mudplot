"""Sequential local 16 MiB boundary probes; no load test or project dependency change.

Run: uv run python scripts/check_request_body_limits.py
RSS/peak observations cover the server PID only (lifetime peak), not native
renderer descendants, and are not a hard memory/CPU or whole-application bound.
"""

from __future__ import annotations

import contextlib
import ctypes
import hashlib
import http.client
import json
import os
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import urlencode

ROOT = Path(__file__).resolve().parents[1]
LIMIT = 16 * 1024 * 1024
SPEC = {
    "version": "0.1",
    "size": [4, 3],
    "data": {"columns": {"x": [1, 2], "y": [2, 3]}},
    "panels": [
        {"title": "body baseline", "layers": [{"type": "line", "x": "x", "y": "y"}]}
    ],
}


def _memory(pid):
    if os.name == "nt":
        from ctypes import wintypes

        class Counters(ctypes.Structure):
            _fields_ = [
                ("cb", wintypes.DWORD),
                ("faults", wintypes.DWORD),
                *(
                    (name, ctypes.c_size_t)
                    for name in (
                        "peak_rss",
                        "rss",
                        "peak_paged",
                        "paged",
                        "peak_nonpaged",
                        "nonpaged",
                        "pagefile",
                        "peak_pagefile",
                    )
                ),
            ]

        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        kernel.OpenProcess.restype = wintypes.HANDLE
        kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        api = ctypes.WinDLL("psapi", use_last_error=True)
        api.GetProcessMemoryInfo.argtypes = [
            wintypes.HANDLE,
            ctypes.POINTER(Counters),
            wintypes.DWORD,
        ]
        api.GetProcessMemoryInfo.restype = wintypes.BOOL
        handle = kernel.OpenProcess(0x1000 | 0x10, False, pid)
        if not handle:
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            counters = Counters()
            counters.cb = ctypes.sizeof(counters)
            if not api.GetProcessMemoryInfo(
                handle, ctypes.byref(counters), counters.cb
            ):
                raise ctypes.WinError(ctypes.get_last_error())
            return {
                "rss_bytes": counters.rss,
                "lifetime_peak_rss_bytes": counters.peak_rss,
            }
        finally:
            kernel.CloseHandle(handle)
    if sys.platform.startswith("linux"):
        values = {}
        for line in (
            Path(f"/proc/{pid}/status").read_text(encoding="ascii").splitlines()
        ):
            key, _, value = line.partition(":")
            if key in ("VmRSS", "VmHWM"):
                values[key] = int(value.split()[0]) * 1024
        return {
            "rss_bytes": values["VmRSS"],
            "lifetime_peak_rss_bytes": values["VmHWM"],
        }
    raise RuntimeError("RSS probe supports Windows/Linux server PIDs only")


def _get(port, path):
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=15)
    try:
        connection.request("GET", path)
        response = connection.getresponse()
        assert response.status == 200
        return response.read()
    finally:
        connection.close()


def _snapshot(port):
    try:
        spec = json.loads(_get(port, "/spec.json"))
    except (UnicodeError, json.JSONDecodeError) as error:
        raise RuntimeError("body-probe server returned invalid spec JSON") from error
    return spec, hashlib.sha256(_get(port, "/fig.png")).hexdigest()


class Payload:
    def __init__(self, prefix, padding, size):
        assert size >= len(prefix)
        self.prefix, self.padding, self.size = prefix, padding, size
        self.yielded = 0

    def __iter__(self):
        self.yielded += len(self.prefix)
        yield self.prefix
        remaining = self.size - len(self.prefix)
        block = self.padding * 65536
        while remaining:
            part = block[: min(remaining, len(block))]
            self.yielded += len(part)
            remaining -= len(part)
            yield part


def _send(
    port, path, content_type, payload, *, chunked=False, declared=None, transfer=None
):
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=45)
    headers = {"Content-Type": content_type, "HX-Request": "true"}
    if transfer is not None:
        headers["Transfer-Encoding"] = transfer
    if declared is not None:
        headers["Content-Length"] = str(declared)
    elif not chunked:
        headers["Content-Length"] = str(payload.size if payload is not None else 0)
    write_error = None
    try:
        try:
            connection.request("POST", path, payload, headers, encode_chunked=chunked)
        except OSError as error:
            write_error = type(error).__name__
        response = connection.getresponse()
        body = response.read()
        assert response.headers["Cache-Control"] == "no-store"
        assert "frame-ancestors 'none'" in response.headers["Content-Security-Policy"]
        return response.status, body, write_error
    finally:
        connection.close()


def _payload(kind, path, size, marker):
    action = json.dumps({"type": "SetTitle", "text": marker})
    if kind == "rust" and path == "/action":
        return "application/json", Payload(action.encode(), b" ", size)
    if path == "/open":
        spec = {**SPEC, "panels": [{**SPEC["panels"][0], "title": marker}]}
        fields = {"json": json.dumps(spec)}
    elif path == "/action/raw":
        fields = {"json": action}
    else:
        fields = {"text": marker, "panel": "0"}
        if kind == "python":
            fields["type"] = "set_title"
    prefix = urlencode(fields).encode() + b"&padding="
    return "application/x-www-form-urlencoded", Payload(prefix, b"x", size)


@contextlib.contextmanager
def _server(kind, binary):
    with socket.socket() as reservation:
        reservation.bind(("127.0.0.1", 0))
        port = reservation.getsockname()[1]
    worker = (
        "import os; from dashboard.editor_server import make_server; "
        f"server=make_server(port={port}); "
        "print('BODY_PROBE_PID:'+str(os.getpid()),flush=True); server.serve_forever()"
    )
    args = (
        [sys.executable, "-u", "-c", worker]
        if kind == "python"
        else [str(binary), "--bind", f"127.0.0.1:{port}", "--python", sys.executable]
    )
    process = subprocess.Popen(
        args,
        cwd=ROOT,
        env={
            **os.environ,
            "MPLBACKEND": "Agg",
            "PYTHONUTF8": "1",
            "PYTHONIOENCODING": "utf-8",
        },
        stdout=subprocess.PIPE if kind == "python" else subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        start_new_session=os.name != "nt",
    )
    try:
        deadline = time.monotonic() + 40
        while True:
            if process.poll() is not None:
                raise RuntimeError(f"{kind} server exited before readiness")
            try:
                _get(port, "/spec.json")
                break
            except OSError:
                if time.monotonic() >= deadline:
                    raise
                time.sleep(0.1)
        server_pid = process.pid
        if kind == "python":
            assert process.stdout is not None
            identity = process.stdout.readline().decode("ascii").strip()
            assert identity.startswith("BODY_PROBE_PID:")
            server_pid = int(identity.split(":", 1)[1])
        encoded = urlencode({"json": json.dumps(SPEC)}).encode()
        status, _, _ = _send(
            port,
            "/open",
            "application/x-www-form-urlencoded",
            Payload(encoded, b"x", len(encoded)),
        )
        assert status == 200
        yield process, port, server_pid
    finally:
        if process.poll() is None:
            if os.name == "nt":
                subprocess.run(
                    ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                    capture_output=True,
                    timeout=10,
                    check=True,
                )
            else:
                os.killpg(process.pid, signal.SIGTERM)
        process.communicate(timeout=10)
        try:
            leftover = socket.create_connection(("127.0.0.1", port), timeout=0.5)
        except OSError:
            pass
        else:
            leftover.close()
            raise RuntimeError("owned body-probe listener did not close")


def _probe(kind, binary):
    with _server(kind, binary) as (process, port, server_pid):
        baseline = _memory(server_pid)
        results = []
        paths = ["/action", "/action/raw", "/open"]
        if kind == "rust":
            paths.append("/control/title")
        for path in paths:
            for size in (LIMIT - 1, LIMIT, LIMIT + 1):
                marker = f"{kind}:{path}:{size}"
                content_type, payload = _payload(kind, path, size, marker)
                before = _snapshot(port)
                if size > LIMIT:
                    status, _, error = _send(
                        port, path, content_type, None, declared=size
                    )
                    assert status == (400 if kind == "python" else 413)
                    assert _snapshot(port) == before
                    yielded = 0
                else:
                    status, _, error = _send(port, path, content_type, payload)
                    assert status == 200 and error is None
                    assert _snapshot(port)[0]["panels"][0]["title"] == marker
                    yielded = payload.yielded
                    assert yielded == size
                results.append(
                    {
                        "path": path,
                        "encoding": "content-length",
                        "decoded_size": size,
                        "payload_yielded": yielded,
                        "status": status,
                        "send_error": error,
                        "memory": _memory(server_pid),
                    }
                )
        for path in paths + (["/undo", "/reset"] if kind == "rust" else ["/reset"]):
            sizes = (
                (LIMIT - 1, LIMIT, LIMIT + 1)
                if kind == "rust" and path in paths
                else (LIMIT + 1,)
            )
            for size in sizes:
                marker = f"chunk:{path}:{size}"
                content_type, payload = _payload(kind, path, size, marker)
                before = _snapshot(port)
                if kind == "python":
                    status, _, error = _send(
                        port, path, content_type, None, chunked=True, transfer="chunked"
                    )
                    assert status == 400 and _snapshot(port) == before
                    yielded = 0
                else:
                    status, _, error = _send(
                        port, path, content_type, payload, chunked=True
                    )
                    yielded = payload.yielded
                    if size > LIMIT:
                        assert status == 413 and _snapshot(port) == before
                    else:
                        assert status == 200 and error is None
                        assert _snapshot(port)[0]["panels"][0]["title"] == marker
                        assert yielded == size
                results.append(
                    {
                        "path": path,
                        "encoding": "chunked",
                        "decoded_size": size,
                        "payload_yielded": yielded,
                        "status": status,
                        "send_error": error,
                        "memory": _memory(server_pid),
                    }
                )
        content_type, recovery = _payload(kind, paths[0], 256, "body-probe-recovered")
        assert _send(port, paths[0], content_type, recovery)[0] == 200
        assert _snapshot(port)[0]["panels"][0]["title"] == "body-probe-recovered"
        return {
            "server": kind,
            "baseline_memory": baseline,
            "server_pid_matches_popen": server_pid == process.pid,
            "cases": results,
            "recovery": True,
        }


def main():
    manifest = ROOT / "mudplot-editor/Cargo.toml"
    subprocess.run(
        ["cargo", "build", "--locked", "--manifest-path", str(manifest)],
        cwd=ROOT,
        check=True,
    )
    try:
        metadata = json.loads(
            subprocess.check_output(
                [
                    "cargo",
                    "metadata",
                    "--no-deps",
                    "--format-version=1",
                    "--manifest-path",
                    str(manifest),
                ],
                cwd=ROOT,
                text=True,
                encoding="utf-8",
            )
        )
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise RuntimeError("cannot read Cargo body-probe target metadata") from error
    binary = (
        Path(metadata["target_directory"])
        / "debug"
        / ("mudplot-editor.exe" if os.name == "nt" else "mudplot-editor")
    )
    results = [_probe(kind, binary) for kind in ("python", "rust")]
    print(
        json.dumps(
            {
                "limit_bytes": LIMIT,
                "memory_scope": (
                    "server PID RSS and lifetime peak only; excludes native renderer "
                    "descendants; no hard CPU/memory or concurrent-load claim"
                ),
                "results": results,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
