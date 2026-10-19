"""Owned render work is bounded without rewriting the declarative source."""

import io

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mudplot as mp
import pytest
from dashboard.editor_server import EditorSession
from matplotlib.transforms import Bbox
from mudplot import _render as renderer
from mudplot._render import _check_render_budget


def huge():
    spec = mp.plot({"x": [0, 1], "y": [1, 2]}).line("x", "y").size(4, 3).spec
    spec.dpi = 10000
    return spec


@pytest.mark.parametrize("fmt", ["", "png", "svg", "pdf", "pgf"])
def test_exact_render_rejects_before_native_canvas_creation(fmt, monkeypatch):
    spec = huge()
    before = mp.to_json(spec)
    figures = plt.get_fignums()
    assert mp.validate(spec) == []

    def unexpected(*args, **kwargs):
        raise AssertionError("native canvas allocation must not be reached")

    monkeypatch.setattr(plt, "figure", unexpected)
    with pytest.raises(ValueError, match="40000000"):
        mp.render(spec, fmt=fmt)
    assert mp.to_json(spec) == before and plt.get_fignums() == figures


@pytest.mark.parametrize("fmt", ["png", "svg", "pdf"])
def test_save_budget_checks_output_dpi_before_native_save(fmt, monkeypatch):
    spec = huge()
    small = mp.from_json(mp.to_json(spec))
    small.dpi = 100
    fig = mp.render(small)
    try:

        def unexpected(*args, **kwargs):
            raise AssertionError("native save must not be reached")

        monkeypatch.setattr(fig, "savefig", unexpected)
        with pytest.raises(ValueError, match="40000000"):
            renderer._save_figure(fig, spec, io.BytesIO(), fmt)
        assert plt.fignum_exists(fig.number)
    finally:
        plt.close(fig)


def test_tight_output_checks_expanded_bbox_before_native_save(monkeypatch):
    spec = mp.plot().size(4, 3).spec
    spec.dpi = 100
    fig = mp.render(spec)
    try:
        monkeypatch.setattr(
            fig, "get_tightbbox", lambda: Bbox.from_bounds(0, 0, 10000, 10000)
        )

        def unexpected(*args, **kwargs):
            raise AssertionError("tight native save must not be reached")

        monkeypatch.setattr(fig, "savefig", unexpected)
        with pytest.raises(ValueError, match="40000000"):
            renderer._save_figure(fig, spec, io.BytesIO(), "png", tight=True)
    finally:
        plt.close(fig)


@pytest.mark.parametrize("fmt", ["png", "svg", "pdf"])
def test_rejected_owned_save_retains_previous_target_and_no_staging(tmp_path, fmt):
    target = tmp_path / f"previous.{fmt}"
    target.write_bytes(b"previous complete output")
    figures = plt.get_fignums()
    with pytest.raises(ValueError, match="40000000"):
        mp.save(huge(), target)
    assert target.read_bytes() == b"previous complete output"
    assert list(tmp_path.iterdir()) == [target] and plt.get_fignums() == figures


@pytest.mark.parametrize("size,dpi", [([4000, 10000], 1), ([1e308, 1e308], 2e-305)])
def test_budget_boundary_and_safe_capped_float_geometry(size, dpi):
    _check_render_budget(size, dpi)


@pytest.mark.parametrize("size,dpi", [([4001, 10000], 1), ([1e308, 1e308], 1e308)])
def test_budget_overflow_is_explicit_valueerror(size, dpi):
    with pytest.raises(ValueError, match="40000000"):
        _check_render_budget(size, dpi)


def test_large_source_dpi_remains_valid_and_capped_preview_works():
    spec = huge()
    before = mp.to_json(spec)
    session = EditorSession()
    session.load_spec(before)
    assert (
        mp.to_json(session.store.state) == before and session.store.state.dpi == 10000
    )
    assert session.png.startswith(b"\x89PNG")
    with pytest.raises(ValueError, match="40000000"):
        session.export("svg")
    assert mp.to_json(session.store.state) == before and session.error is None


def test_capabilities_expose_effect_budget_not_spec_dpi_cap():
    assert mp.capabilities()["render_budget"]["max_canvas_pixels"] == 40000000
