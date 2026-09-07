"""The ``mudplot migrate`` CLI subcommand."""

import json

import mudplot as mp
from mudplot.__main__ import main


def _write_spec(path, **overrides):
    d = mp.plot({"x": [1, 2], "y": [3, 4]}).line("x", "y").spec.to_dict()
    d.update(overrides)
    path.write_text(json.dumps(d), encoding="utf-8")


def test_migrate_writes_the_current_version(tmp_path, capsys):
    src, out = tmp_path / "in.json", tmp_path / "out.json"
    _write_spec(src)
    assert main(["migrate", str(src), "-o", str(out)]) == 0
    assert json.loads(out.read_text())["version"] == mp.capabilities()["spec_version"]
    assert "wrote" in capsys.readouterr().err


def test_migrate_is_idempotent(tmp_path):
    src, out = tmp_path / "in.json", tmp_path / "out.json"
    _write_spec(src)
    main(["migrate", str(src), "-o", str(out)])
    before = out.read_text()
    main(["migrate", str(out), "-o", str(out)])
    assert out.read_text() == before


def test_migrate_rejects_unknown_future_version(tmp_path, capsys):
    src, out = tmp_path / "in.json", tmp_path / "out.json"
    _write_spec(src, version="99.0")
    assert main(["migrate", str(src), "-o", str(out)]) == 1
    assert "99.0" in capsys.readouterr().err
    assert not out.exists()


def test_migrate_requires_out_flag(tmp_path):
    src = tmp_path / "in.json"
    _write_spec(src)
    try:
        main(["migrate", str(src)])
        raised = False
    except SystemExit:
        raised = True
    assert raised
