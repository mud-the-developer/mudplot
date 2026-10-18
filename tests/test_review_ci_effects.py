"""Keep CI fixtures and finite execution budgets aligned with observed checks."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_rust_smoke_job_installs_optional_effects_used_by_its_fixtures():
    smoke = (ROOT / "scripts/rust_editor_smoke_test.py").read_text(encoding="utf-8")
    assert "from examples.regression_modes" in smoke
    assert "from examples.clustered_profiles" in smoke
    workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    job = workflow.split("\n  rust-editor:\n", 1)[1]
    assert "uv sync --locked --extra all" in job


def test_python_matrix_retains_full_suite_with_timeout_headroom_and_timings():
    workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    job = workflow.split("\n  lint-and-test:\n", 1)[1].split("\n  rust-editor:\n", 1)[0]
    # Baseline063 exceeded45minutes; measure the full suite instead of dropping tests.
    assert "timeout-minutes: 60" in job
    assert "run: uv run pytest -q --durations=25" in job
