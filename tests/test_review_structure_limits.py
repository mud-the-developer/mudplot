"""Bound figure expansion before object/native geometry allocation."""

import mudplot as mp
import pytest
from mudplot import actions as A
from mudplot import reducer as reducer_module
from mudplot import spec as spec_module
from mudplot.spec import FigureSpec, PanelSpec


@pytest.mark.parametrize(
    "action,count",
    [
        (A.SetTitle("not applied", panel=256), 1),
        (A.SetLayout(17, 16), 1),
        (A.SetLayout(100000, 100000), 1),
        (A.AddPanel(), 256),
    ],
)
def test_oversized_actions_reject_before_new_panel_construction(
    action, count, monkeypatch
):
    spec = FigureSpec(panels=[PanelSpec() for _ in range(count)])
    before = mp.to_json(spec)

    def unexpected():
        raise AssertionError("panel allocation must not be reached")

    monkeypatch.setattr(reducer_module, "PanelSpec", unexpected)
    with pytest.raises(ValueError, match="256"):
        mp.reduce(spec, action)
    assert mp.to_json(spec) == before


def test_overlong_raw_panel_array_rejects_before_panel_decode(monkeypatch):
    original = spec_module._from_dict
    raw = {"panels": [{} for _ in range(257)]}

    def decode(cls, data):
        if cls is PanelSpec:
            raise AssertionError("individual panel decode must not be reached")
        return original(cls, data)

    monkeypatch.setattr(spec_module, "_from_dict", decode)
    with pytest.raises(ValueError, match="256"):
        FigureSpec.from_dict(raw)
    assert raw == {"panels": [{} for _ in range(257)]}


@pytest.mark.parametrize("index", [99, 255])
def test_positive_panel_creation_still_extends_inside_supported_limit(index):
    initial = FigureSpec()
    result = mp.reduce(initial, A.SetTitle("created", panel=index))
    assert len(result.panels) == index + 1 and result.panels[index].title == "created"
    assert len(initial.panels) == 1 and initial.panels[0].title == ""
    assert mp.validate(result) == []


def test_last_add_panel_and_layout_boundary_are_supported():
    initial = FigureSpec(panels=[PanelSpec() for _ in range(255)])
    assert len(mp.reduce(initial, A.AddPanel()).panels) == 256
    result = mp.reduce(FigureSpec(), A.SetLayout(16, 16))
    assert result.layout == [16, 16] and len(result.panels) == 256
    assert mp.validate(result) == []


@pytest.mark.parametrize(
    "spec",
    [FigureSpec(panels=[PanelSpec() for _ in range(257)]), FigureSpec(layout=[17, 16])],
)
def test_direct_spec_overflow_is_rejected_by_validation(spec):
    assert any("256" in issue for issue in mp.validate(spec))


def test_capabilities_explain_structure_bounds():
    assert mp.capabilities()["figure_structure"] == {
        "max_panels": 256,
        "max_layout_cells": 256,
        "max_layers": 1024,
    }
