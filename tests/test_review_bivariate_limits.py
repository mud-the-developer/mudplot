"""Bivariate resolution bounds reject before native quadratic allocation."""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mudplot as mp
import pytest
from matplotlib.axes import Axes

DATA = {"x": [1, 2, 3, 4], "y": [1, 4, 2, 3]}


def build(kind, options):
    plot = mp.plot(DATA)
    return getattr(plot, kind)("x", "y", **options).spec


@pytest.mark.parametrize(
    "kind,options,field",
    [
        ("hist2d", {"bins": 513}, "bins"),
        ("hist2d", {"bins": [1, 513]}, "bins"),
        ("hist2d", {"bins": list(range(514))}, "bins"),
        ("hist2d", {"bins": 1000000}, "bins"),
        ("hexbin", {"gridsize": 513}, "gridsize"),
        ("hexbin", {"gridsize": 1000000}, "gridsize"),
    ],
)
def test_excessive_bivariate_resolution_is_rejected_before_native_draw(
    kind, options, field, monkeypatch
):
    spec = build(kind, options)
    before = mp.to_json(spec)
    figures = plt.get_fignums()
    issues = mp.validate(spec)
    assert any(field in issue and "512" in issue for issue in issues)

    def unexpected(*args, **kwargs):
        raise AssertionError("native allocation must not be reached")

    monkeypatch.setattr(Axes, kind, unexpected)
    with pytest.raises(ValueError, match="512"):
        mp.render(spec)
    assert mp.to_json(spec) == before and plt.get_fignums() == figures


@pytest.mark.parametrize(
    "kind,options",
    [
        ("hist2d", {"bins": 512}),
        ("hist2d", {"bins": [1, 512]}),
        ("hist2d", {"bins": list(range(513))}),
        ("hexbin", {"gridsize": 512}),
    ],
)
def test_supported_bivariate_boundary_preserves_raw_bin_values(kind, options):
    spec = build(kind, options)
    before = mp.to_json(spec)
    assert mp.validate(spec) == []
    assert mp.to_json(spec) == before


def test_capabilities_expose_the_bivariate_resolution_boundary():
    limit = mp.capabilities()["bivariate_density"]
    assert limit["max_bins_per_axis"] == 512
    assert limit["max_hexbin_gridsize"] == 512
