"""Execute the optional, privacy-limited recipe without altering image bytes."""

import hashlib
import json
from pathlib import Path

import matplotlib.pyplot as plt
import mudplot as mp
import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_documented_manifest_is_separate_deterministic_and_refuses_overwrite(
    tmp_path, monkeypatch
):
    recipe = (
        (ROOT / "docs/OUTPUT_PROVENANCE.md")
        .read_text(encoding="utf-8")
        .split("```python\n", 1)[1]
        .split("```", 1)[0]
    )
    monkeypatch.chdir(tmp_path)
    namespace = {}
    figures = plt.get_fignums()
    exec(compile(recipe, "documented-provenance-recipe", "exec"), namespace)
    assert plt.get_fignums() == figures
    directory = tmp_path / "synthetic-provenance"
    original = {path.name: path.read_bytes() for path in directory.iterdir()}
    manifest = json.loads(original["manifest.json"])
    spec = mp.load_spec(directory / "figure.mplot.json")
    assert spec == namespace["spec"]
    canonical = mp.to_json(spec, indent=None, sort_keys=True).encode("utf-8")
    assert manifest["canonical_spec_sha256"] == hashlib.sha256(canonical).hexdigest()
    assert set(manifest["outputs"]) == {
        "figure.mplot.json",
        "figure.png",
        "figure.pdf",
        "figure.svg",
    }
    assert not set(manifest) & {
        "time",
        "timestamp",
        "hostname",
        "username",
        "argv",
        "paths",
    }
    assert set(manifest["environment"]) == {
        "python",
        "system",
        "machine",
        "mudplot",
        "versions",
        "primary_font_sha256",
    }
    assert (
        "timestamp" not in original["manifest.json"].decode()
        and str(Path.home()) not in original["manifest.json"].decode()
    )
    for name, sha in manifest["outputs"].items():
        assert hashlib.sha256(original[name]).hexdigest() == sha
    repeat = tmp_path / "repeat"
    repeat.mkdir()
    for fmt in ("png", "pdf", "svg"):
        target = repeat / f"figure.{fmt}"
        figure = mp.save(spec, target)
        try:
            assert target.read_bytes() == original[target.name]
        finally:
            plt.close(figure)
    with pytest.raises(FileExistsError):
        exec(compile(recipe, "documented-provenance-recipe", "exec"), {})
    assert {path.name: path.read_bytes() for path in directory.iterdir()} == original
    assert plt.get_fignums() == figures
