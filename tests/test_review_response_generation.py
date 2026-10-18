"""HTML delivery ordering is UI state, independent of reducer/history revisions."""

import json
import urllib.request
from urllib.parse import urlencode

import mudplot as mp

pytest_plugins = ["test_dashboard_editor"]


def test_view_generations_increase_across_undo_reset_open_and_errors(running_server):
    generations = []
    requests = [
        ("/action", {"type": "set_title", "text": "first"}),
        ("/undo", {}),
        ("/redo", {}),
        ("/reset", {}),
        ("/open", {"json": mp.plot().labels(title="opened").to_json()}),
        ("/open", {"json": "{"}),
        ("/select-panel", {"panel": "0"}),
    ]
    for path, fields in requests:
        request = urllib.request.Request(
            running_server + path,
            data=urlencode(fields).encode(),
            headers={"HX-Request": "true"},
        )
        with urllib.request.urlopen(request) as response:
            assert response.status == 200
            assert response.headers.get_content_type() == "text/html"
            generation = response.headers.get("X-Mudplot-View-Generation")
            assert generation is not None and generation.isdecimal()
            generations.append(int(generation))
            assert b'id="app-body"' not in response.read()
    assert generations == list(range(1, len(requests) + 1))
    with urllib.request.urlopen(running_server + "/spec.json") as response:
        spec = json.load(response)
    assert spec["panels"][0]["title"] == "opened"
    assert "_view_generation" not in spec and "view_generation" not in spec


def test_readonly_responses_do_not_change_view_generation_or_content_types(
    running_server,
):
    for path, content_type in (
        ("/", "text/html"),
        ("/docs", "text/html"),
        ("/spec.json", "application/json"),
        ("/fig.png", "image/png"),
    ):
        with urllib.request.urlopen(running_server + path) as response:
            assert response.status == 200
            assert response.headers.get_content_type() == content_type
            assert response.headers.get("X-Mudplot-View-Generation") is None
            assert response.read()
    request = urllib.request.Request(
        running_server + "/action",
        data=urlencode({"type": "set_title", "text": "first"}).encode(),
        headers={"HX-Request": "true"},
    )
    with urllib.request.urlopen(request) as response:
        assert response.headers.get("X-Mudplot-View-Generation") == "1"
