"""The dependency-free ``mudplot apply`` bridge for non-Python editors."""

import json

import mudplot as mp
import pytest
from mudplot import io
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
        [["type", "SetTitle"], ["text", "not an object"]],
        {"type": "AddLayer", "layer": []},
        {"type": "SetSize", "width": -1, "height": 2},
        {"type": "SetSize", "width": float("nan"), "height": 2},
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


def test_apply_cli_preserves_output_on_io_failure(tmp_path, capsys, monkeypatch):
    src, action, out = (tmp_path / name for name in ("in.json", "a.json", "out.json"))
    _write_spec(src)
    action.write_text(json.dumps({"type": "SetTitle", "text": "new"}))
    out.write_text("keep", encoding="utf-8")

    def fail_replace(source, target):
        raise OSError("simulated replace failure")

    monkeypatch.setattr(io.os, "replace", fail_replace)
    assert main(["apply", str(src), str(action), "-o", str(out)]) == 1
    assert "error: simulated replace failure" in capsys.readouterr().err
    assert out.read_text(encoding="utf-8") == "keep"


def test_apply_cli_rejects_excessively_nested_action_json(tmp_path, capsys):
    src, action, out = (tmp_path / name for name in ("in.json", "a.json", "out.json"))
    _write_spec(src)
    action.write_text("[" * 2_000 + "]" * 2_000, encoding="utf-8")

    assert main(["apply", str(src), str(action), "-o", str(out)]) == 1
    assert "error:" in capsys.readouterr().err
    assert not out.exists()


def test_apply_cli_rejects_non_object_spec_without_traceback(tmp_path, capsys):
    src, action, out = (tmp_path / name for name in ("in.json", "a.json", "out.json"))
    src.write_text("[]", encoding="utf-8")
    action.write_text(json.dumps({"type": "SetTitle", "text": "nope"}))

    assert main(["apply", str(src), str(action), "-o", str(out)]) == 1
    assert "FigureSpec must be a JSON object" in capsys.readouterr().err
    assert not out.exists()
