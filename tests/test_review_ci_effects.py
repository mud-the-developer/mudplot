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
    job = workflow.split("\n  lint-and-test:\n", 1)[1].split(
        "\n  minimum-render:\n", 1
    )[0]
    # Baseline063 exceeded45minutes; measure the full suite instead of dropping tests.
    assert "timeout-minutes: 60" in job
    assert "run: uv run pytest -q --durations=25" in job


def test_minimum_suite_has_its_own_finite_job_with_the_same_tex_prerequisites():
    workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    assert "\n  minimum-render:\n" in workflow
    regular, minimum = workflow.split("\n  minimum-render:\n", 1)
    minimum = minimum.split("\n  rust-editor:\n", 1)[0]
    assert "Minimum render dependency contract" not in regular
    assert "timeout-minutes: 60" in minimum and 'python-version: "3.10"' in minimum
    assert "persist-credentials: false" in minimum
    assert "scripts/check_minimum_versions.py.lock" in minimum
    assert "uv sync --locked --extra dev --extra browser" in minimum
    assert "uv run --no-sync playwright install-deps chromium" in minimum
    assert "playwright install --with-deps chromium" in regular
    assert "uv run --python 3.10 --locked --script" in " ".join(minimum.split())
    assert "scripts/check_minimum_versions.py" in minimum
    for prerequisite in (
        "texlive-latex-base",
        "texlive-latex-recommended",
        "texlive-pictures",
        "ghostscript",
        'TECTONIC_VERSION: "0.15.0"',
        "875fbbc9ab48560d7776088c608e0beee49197b57ab4a2f6c5385b2c661c842f",
        "sha256sum --check --strict",
    ):
        assert prerequisite in regular and prerequisite in minimum
    runner = (ROOT / "scripts/check_minimum_versions.py").read_text(encoding="utf-8")
    assert '"--durations=25"' in runner and "*TESTS" in runner
    assert '"-m", "not browser"' in runner


def test_minimum_runner_keeps_all_files_and_propagates_pytest_result(monkeypatch):
    import sys

    from scripts import check_minimum_versions as runner

    captured = []
    monkeypatch.setattr(sys, "path", sys.path.copy())
    monkeypatch.chdir(ROOT)
    monkeypatch.setattr(runner.importlib.metadata, "version", lambda _name: "probe")
    monkeypatch.setattr(runner.pytest, "main", lambda args: captured.extend(args) or 17)
    assert runner.main() == 17
    assert captured == [
        "-q",
        "--disable-warnings",
        "--durations=25",
        "-m",
        "not browser",
        *runner.TESTS,
    ]
