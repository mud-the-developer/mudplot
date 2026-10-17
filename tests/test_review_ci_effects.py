"""Keep the Rust smoke environment aligned with its optional-effect fixtures."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_rust_smoke_job_installs_optional_effects_used_by_its_fixtures():
    smoke = (ROOT / "scripts/rust_editor_smoke_test.py").read_text(encoding="utf-8")
    assert "from examples.regression_modes" in smoke
    assert "from examples.clustered_profiles" in smoke
    workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    job = workflow.split("\n  rust-editor:\n", 1)[1]
    assert "uv sync --locked --extra all" in job
