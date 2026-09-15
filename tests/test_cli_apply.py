"""The pure-core ``mudplot apply`` bridge used by non-Python editors."""

import json

import mudplot as mp
import pytest
from mudplot.__main__ import main


def _write_spec(path):
    spec = mp.plot({"x": [1, 2], "y": [3, 4]}).line("x", "y").spec
    path.write_text(mp.to_json(spec), encoding="utf-8")


def test_apply_cli_writes_valid_reduced_spec(tmp_path):
    src, action, out = (tmp_path / name for name in ("in.json", "a.json", "out.json"))
    _write_spec(src)
    action.write_text(json.dumps({"type": "SetTitle", "text": "Rust"}))

    assert main(["apply", str(src), str(action), "-o", str(out)]) == 0
    assert mp.load_spec(out).panels[0].title == "Rust"


@pytest.mark.parametrize(
    "action",
    [
        ["not", "an", "object"],
        {"type": "SetSize", "width": -1, "height": 2},
    ],
)
def test_apply_cli_rejects_invalid_action_or_result(tmp_path, action, capsys):
    src, action_path, out = (
        tmp_path / name for name in ("in.json", "a.json", "out.json")
    )
    _write_spec(src)
    action_path.write_text(json.dumps(action), encoding="utf-8")

    assert main(["apply", str(src), str(action_path), "-o", str(out)]) == 1
    assert "error:" in capsys.readouterr().err
    assert not out.exists()
