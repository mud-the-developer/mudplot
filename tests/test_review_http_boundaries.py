"""SEC-01/02/03/05: bounded loopback requests, not external service/load tests."""

from __future__ import annotations

import http.client
import json
import threading
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlencode, urlparse

import matplotlib

matplotlib.use("Agg")
import mudplot as mp
import pytest
from dashboard.editor_server import EditorSession, make_server

CASES = json.loads(
    (Path(__file__).parent / "fixtures/review_http_boundaries.json").read_text(
        encoding="utf-8"
    )
)


def _headers(headers):
    assert headers["Cache-Control"] == "no-store"
    assert headers["X-Content-Type-Options"] == "nosniff"
    assert headers["X-Frame-Options"] == "DENY"
    assert "frame-ancestors 'none'" in headers["Content-Security-Policy"]
    assert "script-src 'self';" in headers["Content-Security-Policy"]


def _snapshot(base):
    with urllib.request.urlopen(base + "/spec.json", timeout=10) as response:
        spec = json.load(response)
    with urllib.request.urlopen(base + "/fig.png", timeout=10) as response:
        return spec, response.read()


@pytest.fixture(scope="module")
def local_editor():
    session = EditorSession()
    session.load_spec(
        mp.plot({"x": [1, 2], "y": [2, 3]}).line("x", "y").size(4, 3).to_json()
    )
    server = make_server(port=0, session=session)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
        assert not thread.is_alive()


@pytest.mark.parametrize("host", CASES["rejected_hosts"])
def test_untrusted_host_is_rejected_with_headers_and_no_state_change(
    host, local_editor
):
    before = _snapshot(local_editor)
    request = urllib.request.Request(
        local_editor + "/spec.json",
        headers={"Host": host, "X-Forwarded-Host": urlparse(local_editor).netloc},
    )
    with pytest.raises(urllib.error.HTTPError) as caught:
        urllib.request.urlopen(request, timeout=10)
    with caught.value as response:
        assert response.code == 403
        _headers(response.headers)
    assert _snapshot(local_editor) == before


@pytest.mark.parametrize("host", CASES["accepted_hosts"])
def test_loopback_host_authorities_are_accepted(host, local_editor):
    request = urllib.request.Request(
        local_editor + "/spec.json", headers={"Host": host}
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        assert response.status == 200
        _headers(response.headers)


@pytest.mark.parametrize("template", CASES["rejected_origins"])
def test_origin_mismatch_is_rejected_without_changing_state_or_preview(
    template, local_editor
):
    port = urlparse(local_editor).port
    assert port is not None
    headers = {
        name: value.format(base=local_editor, port=port, other_port=port + 1)
        for name, value in template.items()
    }
    before = _snapshot(local_editor)
    request = urllib.request.Request(
        local_editor + "/action",
        b"",  # Require rejection before form parsing or a body upload.
        headers=headers,
    )
    with pytest.raises(urllib.error.HTTPError) as caught:
        urllib.request.urlopen(request, timeout=10)
    with caught.value as response:
        assert response.code == 403
        _headers(response.headers)
    assert _snapshot(local_editor) == before


@pytest.mark.parametrize("template", CASES["accepted_origins"])
def test_native_agent_and_same_origin_mutations_remain_supported(
    template, local_editor
):
    headers = {
        name: value.format(base=local_editor) for name, value in template.items()
    }
    text = "accepted:" + json.dumps(template, sort_keys=True)
    request = urllib.request.Request(
        local_editor + "/action",
        urlencode({"type": "set_suptitle", "text": text}).encode(),
        headers=headers,
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        assert response.status == 200
    assert _snapshot(local_editor)[0]["suptitle"] == text


@pytest.mark.parametrize(
    "path",
    [
        "/",
        "/fig.png",
        "/fig.pdf",
        "/fig.svg",
        "/static/htmx.min.js",
        "/static/editor.js",
    ],
)
def test_normal_static_preview_and_export_headers_are_consistent(path, local_editor):
    with urllib.request.urlopen(local_editor + path, timeout=30) as response:
        assert response.status == 200
        _headers(response.headers)
        assert response.read()


def test_oversized_declared_body_is_rejected_before_body_upload(local_editor):
    before = _snapshot(local_editor)
    parsed = urlparse(local_editor)
    connection = http.client.HTTPConnection(parsed.hostname, parsed.port, timeout=5)
    try:
        connection.putrequest("POST", "/action")
        connection.putheader("Content-Length", str(16 * 1024 * 1024 + 1))
        connection.endheaders()
        response = connection.getresponse()
        assert response.status == 400
        _headers(response.headers)
        assert b"16 MiB" in response.read()
    finally:
        connection.close()
    assert _snapshot(local_editor) == before


def test_missing_host_and_unknown_route_are_rejected_and_keep_state(local_editor):
    before = _snapshot(local_editor)
    parsed = urlparse(local_editor)
    connection = http.client.HTTPConnection(parsed.hostname, parsed.port, timeout=5)
    try:
        connection.putrequest("GET", "/spec.json", skip_host=True)
        connection.endheaders()
        response = connection.getresponse()
        assert response.status == 403
        _headers(response.headers)
        response.read()
    finally:
        connection.close()
    with pytest.raises(urllib.error.HTTPError) as caught:
        urllib.request.urlopen(local_editor + "/does-not-exist", timeout=10)
    with caught.value as response:
        assert response.code == 404
        _headers(response.headers)
    assert _snapshot(local_editor) == before
