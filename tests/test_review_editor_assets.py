"""Matching-checkout static ownership and the existing metadata release gate."""

from pathlib import Path
from types import SimpleNamespace

import mudplot as mp
from scripts import check_release_version as preflight

ROOT = Path(__file__).resolve().parents[1]


def test_rust_includes_shared_htmx_without_a_second_vendor_copy():
    source = (ROOT / "mudplot-editor/src/lib.rs").read_text(encoding="utf-8")
    assert 'include_bytes!("../../dashboard/static/htmx.min.js")' in source
    assert not (ROOT / "mudplot-editor/static/htmx.min.js").exists()
    license_text = (ROOT / "dashboard/static/htmx.LICENSE").read_text(encoding="utf-8")
    assert "Zero-Clause BSD" in license_text and "Permission to use" in license_text
    script = (ROOT / "dashboard/static/htmx.min.js").read_bytes()
    assert b'version:"1.9.12"' in script
    model = (ROOT / "mudplot-editor/src/model.rs").read_text(encoding="utf-8")
    assert 'include_str!("../../schemas/capabilities.json")' in model


def test_release_gate_explains_python_metadata_mismatch_without_altering_versions(
    monkeypatch, capsys
):
    current = mp.__version__
    monkeypatch.setattr(
        preflight, "mudplot", SimpleNamespace(__version__="9.9.9-probe")
    )
    assert preflight.main(["v9.9.9-probe"]) == 1
    error = capsys.readouterr().err
    assert f"Rust version is '{current}', Python is '9.9.9-probe'" in error
    assert "pyproject version" in error and "Cargo.lock version" in error
    assert mp.__version__ == current
