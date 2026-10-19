"""JSON-11: real checker catches intentional drift in isolated artifact copies."""

import json
import shutil
from dataclasses import fields
from pathlib import Path

import mudplot as mp
import pytest
from mudplot import actions as A
from mudplot.capabilities import LAYER_TYPES
from mudplot.spec import LayerSpec
from scripts import check_schema_sync as sync

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("target", [p for _, p, _ in sync._TARGETS])
def test_checker_rejects_drift_then_accepts_restored_copy(
    target, tmp_path, monkeypatch, capsys
):
    for _, relative, _ in sync._TARGETS:
        destination = tmp_path / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, destination)
    monkeypatch.setattr(sync, "REPO_ROOT", tmp_path)
    monkeypatch.setenv("PYTHONPATH", str(ROOT))
    assert sync.main() == 0
    original = (tmp_path / target).read_bytes()
    if target.endswith(".json"):
        contents = json.loads(original)
        contents["review_intentional_drift"] = True
        (tmp_path / target).write_text(json.dumps(contents), encoding="utf-8")
    else:
        (tmp_path / target).write_bytes(original + b"\nintentional drift\n")
    assert sync.main() == 1
    error = capsys.readouterr().err
    assert target in error and "regenerate with:" in error
    command = (
        "python -m scripts.render_docs_demo"
        if target == "docs/PLOT_GALLERY.md"
        else "python -m mudplot"
    )
    assert command in error
    (tmp_path / target).write_bytes(original)
    assert sync.main() == 0


def test_layer_action_registry_schema_capabilities_and_reference_agree():
    caps = mp.capabilities()
    schema = mp.json_schema()
    reference = mp.reference_markdown()
    assert set(caps["actions"]) == set(A.ACTION_REGISTRY)
    for name, cls in A.ACTION_REGISTRY.items():
        assert [entry["name"] for entry in caps["actions"][name]] == [
            f.name for f in fields(cls)
        ]
        assert f"`{name}`" in reference
    layer_schema = schema["$defs"]["LayerSpec"]["properties"]["type"]
    assert layer_schema["type"] == "string"
    assert layer_schema["default"] in LAYER_TYPES
    assert set(schema["$defs"]["LayerSpec"]["properties"]) == {
        f.name for f in fields(LayerSpec)
    }
    assert set(LAYER_TYPES) == set(caps["layers"])
    assert all(f"`{kind}`" in reference for kind in LAYER_TYPES)
