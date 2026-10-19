"""Total layer expansion is checked before bulk decode/copy/effects."""

import copy
from types import SimpleNamespace

import mudplot as mp
import pytest
from mudplot import _facet, _joint
from mudplot import actions as A
from mudplot import reducer as reducer_module
from mudplot import spec as spec_module
from mudplot.spec import DataSpec, FigureSpec, LayerSpec, PanelSpec

DATA = {"x": [1, 2, 3, 4], "y": [1, 4, 2, 3], "g": ["a", "a", "b", "b"]}


def scatter():
    return LayerSpec(type="scatter", x="x", y="y", color="#222222")


def figure(counts):
    return FigureSpec(
        data=DataSpec(columns=copy.deepcopy(DATA)),
        panels=[
            PanelSpec(layers=[scatter() for _ in range(count)]) for count in counts
        ],
    )


def test_addlayer_rejects_before_copying_the_new_layer(monkeypatch):
    spec = figure([1024])
    incoming = scatter()
    before = mp.to_json(spec)
    original = copy.deepcopy

    def copying(value):
        if value is incoming:
            raise AssertionError("new layer copy must not be reached")
        return original(value)

    monkeypatch.setattr(reducer_module, "copy", SimpleNamespace(deepcopy=copying))
    with pytest.raises(ValueError, match="1024"):
        mp.reduce(spec, A.AddLayer(incoming))
    assert mp.to_json(spec) == before


@pytest.mark.parametrize(
    "counts,panel_only", [([1025], False), ([512, 513], False), ([1025], True)]
)
def test_raw_arrays_reject_before_individual_layer_decode(
    counts, panel_only, monkeypatch
):
    raw = {
        "panels": [
            {"layers": [{"type": "scatter"} for _ in range(count)]} for count in counts
        ]
    }
    original = spec_module._from_dict

    def decode(cls, value):
        if cls is LayerSpec:
            raise AssertionError("layer decode must not be reached")
        return original(cls, value)

    before = copy.deepcopy(raw)
    monkeypatch.setattr(spec_module, "_from_dict", decode)
    with pytest.raises(ValueError, match="1024"):
        if panel_only:
            PanelSpec.from_dict(raw["panels"][0])
        else:
            FigureSpec.from_dict(raw)
    assert raw == before


def test_direct_oversized_figure_is_rejected_before_layer_validation():
    assert any("1024" in issue for issue in mp.validate(figure([512, 513])))


def test_facet_expansion_rejects_before_template_copy(monkeypatch):
    spec = figure([513])
    before = mp.to_json(spec)

    def unexpected(value):
        raise AssertionError("facet bulk copy must not be reached")

    monkeypatch.setattr(_facet, "copy", SimpleNamespace(deepcopy=unexpected))
    with pytest.raises(ValueError, match="1024"):
        _facet.materialize_facets(
            spec,
            row=None,
            col="g",
            row_order=None,
            col_order=None,
            col_wrap=None,
            share_x="all",
            share_y="all",
        )
    assert mp.to_json(spec) == before


def joint_figure(count):
    spec = figure([1])
    spec.panels[0].layers += [
        LayerSpec(type="text", text="synthetic", at=[1, 1], color="#222222")
        for _ in range(count - 1)
    ]
    return spec


def test_joint_expansion_rejects_before_source_copy(monkeypatch):
    spec = joint_figure(1023)
    before = mp.to_json(spec)

    def unexpected(value):
        raise AssertionError("joint bulk copy must not be reached")

    monkeypatch.setattr(_joint, "copy", SimpleNamespace(deepcopy=unexpected))
    with pytest.raises(ValueError, match="1024"):
        _joint.materialize_joint(spec, bins=20, ratio=3.0, marginal_stat="density")
    assert mp.to_json(spec) == before


@pytest.mark.parametrize("counts", [[1024], [512, 512]])
def test_supported_raw_boundary_is_not_truncated(counts):
    initial = figure(counts)
    restored = FigureSpec.from_dict(initial.to_dict())
    assert sum(len(panel.layers) for panel in restored.panels) == 1024
    assert restored == initial and mp.validate(restored) == []


def test_last_addlayer_retains_existing_layers_and_inputs():
    initial = figure([1023])
    result = mp.reduce(initial, A.AddLayer(scatter()))
    assert (
        len(result.panels[0].layers) == 1024 and len(initial.panels[0].layers) == 1023
    )


def test_facet_and_joint_boundaries_remain_supported():
    faceted = mp.reduce(figure([512]), A.SetFacets(col="g"))
    joint = mp.reduce(joint_figure(1022), A.SetJointGrid())
    for spec in (faceted, joint):
        assert sum(len(panel.layers) for panel in spec.panels) == 1024
        assert mp.validate(spec) == []


def test_capabilities_expose_total_not_per_panel_budget():
    assert mp.capabilities()["figure_structure"]["max_layers"] == 1024
