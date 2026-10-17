"""SEC-03: reject unsupported/ambiguous framing before a mutation or body read."""

from __future__ import annotations

import http.client
import io
import socket
import threading
from http.client import HTTPMessage

import mudplot as mp
import pytest
from dashboard import editor_server
from dashboard.editor_server import _Handler


class BodyReader(io.BytesIO):
    def __init__(self, body):
        super().__init__(body)
        self.reads = []

    def read(self, size=-1):
        self.reads.append(size)
        return super().read(size)


def _handler(headers, body=b""):
    handler = _Handler.__new__(_Handler)
    handler.headers = HTTPMessage()
    for name, value in headers:
        handler.headers.add_header(name, value)
    reader = BodyReader(body)
    handler.rfile = reader
    return handler, reader


@pytest.mark.parametrize(
    "headers",
    [
        [("Transfer-Encoding", "chunked")],
        [("Transfer-Encoding", "identity")],
        [("Transfer-Encoding", "chunked"), ("Content-Length", "0")],
    ],
)
def test_python_rejects_transfer_encoding_without_reading_or_ignoring_it(headers):
    handler, reader = _handler(headers, b"4\r\ntest\r\n0\r\n\r\n")
    with pytest.raises(ValueError, match="Transfer-Encoding"):
        handler._read_body()
    assert reader.reads == []


@pytest.mark.parametrize("lengths", [("0", "20"), ("20", "20")])
def test_python_rejects_duplicate_content_lengths_before_body_read(lengths):
    handler, reader = _handler(
        [("Content-Length", value) for value in lengths], b"x" * 20
    )
    with pytest.raises(ValueError, match="Content-Length"):
        handler._read_body()
    assert reader.reads == []


def test_python_rejects_truncated_body_instead_of_returning_a_valid_action_prefix():
    handler, reader = _handler([("Content-Length", "100")], b"type=reset")
    with pytest.raises(ValueError, match=r"incomplete|truncated"):
        handler._read_body()
    assert reader.reads == [100]


@pytest.mark.parametrize("size", [31, 32, 33])
def test_python_body_limit_is_checked_before_allocation(size, monkeypatch):
    monkeypatch.setattr(editor_server, "_MAX_BODY_BYTES", 32)
    body = b"x" * size
    handler, reader = _handler([("Content-Length", str(size))], body)
    if size > 32:
        with pytest.raises(ValueError, match="16 MiB"):
            handler._read_body()
        assert reader.reads == []
    else:
        assert handler._read_body() == body
        assert reader.reads == [size]


@pytest.fixture(scope="module")
def framing_server():
    session = editor_server.EditorSession()
    session.load_spec(
        mp.plot({"x": [1], "y": [2]}).line("x", "y").labels(title="keep").to_json()
    )
    server = editor_server.make_server(port=0, session=session)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield session, server.server_address[1]
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
        assert not thread.is_alive()


@pytest.mark.parametrize("framing", ["chunked", "duplicate", "truncated"])
def test_bad_http_framing_cannot_reset_or_apply_a_partial_action(
    framing, framing_server
):
    session, port = framing_server
    state, history, preview = session.store.state, session.store.history, session.png
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    try:
        connection.putrequest("POST", "/action" if framing == "truncated" else "/reset")
        if framing == "chunked":
            connection.putheader("Transfer-Encoding", "chunked")
            connection.endheaders()
        elif framing == "duplicate":
            connection.putheader("Content-Length", "0")
            connection.putheader("Content-Length", "10")
            connection.endheaders()
        else:
            body = b"type=set_title&text=must-not-commit"
            connection.putheader("Content-Length", str(len(body) + 7))
            connection.endheaders(body)
            assert connection.sock is not None
            connection.sock.shutdown(socket.SHUT_WR)
        response = connection.getresponse()
        assert response.status == 400
        assert response.headers["Cache-Control"] == "no-store"
        response.read()
    finally:
        connection.close()
    assert session.store.state == state and session.store.history == history
    assert session.png == preview


def test_empty_unframed_body_remains_valid_for_bodyless_local_actions():
    handler, reader = _handler([])
    assert handler._read_body() == b"" and reader.reads == []
