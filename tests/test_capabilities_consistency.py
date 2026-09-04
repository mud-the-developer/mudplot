"""Cross-module consistency ("drift guard") tests.

These exist because a real bug slipped through once: ``capabilities()``
under-reported that bar/errorbar/band/hline/vline/text/annotate all support
``axis="y2"`` routing (only line/scatter listed it), even though
``validate.py`` and ``render.py`` already handled it correctly for all of
them. An agent trusting ``capabilities()`` would never have discovered this
worked. These tests pin the three sources of truth (LAYER_TYPES, LayerSpec's
real fields, and validate's routable-type set) together so they can't drift
apart silently again.
"""

from dataclasses import fields as dc_fields

from mudplot.capabilities import LAYER_TYPES
from mudplot.render import _DIST_TYPES, _MATRIX_TYPES, _SERIES_TYPES
from mudplot.spec import LayerSpec
from mudplot.validate import _AXIS_ROUTABLE_TYPES

_LAYERSPEC_FIELDS = {f.name for f in dc_fields(LayerSpec)} - {"type"}
_RENDER_KNOWN_TYPES = (
    _SERIES_TYPES
    | _DIST_TYPES
    | _MATRIX_TYPES
    | {
        "hline",
        "vline",
        "text",
        "annotate",
    }
)


def test_every_layer_type_field_is_a_real_layerspec_field():
    for layer_type, spec in LAYER_TYPES.items():
        for field_name in spec["required"] + spec["optional"]:
            assert field_name in _LAYERSPEC_FIELDS, (
                f"{layer_type}: {field_name!r} is not a real LayerSpec field"
            )


def test_every_layer_type_is_handled_by_the_renderer():
    for layer_type in LAYER_TYPES:
        assert layer_type in _RENDER_KNOWN_TYPES, (
            f"{layer_type!r} is advertised in capabilities() but render.py "
            "doesn't know how to draw it"
        )


def test_every_renderer_type_is_advertised_in_capabilities():
    for layer_type in _RENDER_KNOWN_TYPES:
        assert layer_type in LAYER_TYPES, (
            f"render.py handles {layer_type!r} but it's missing from "
            "capabilities.LAYER_TYPES"
        )


def test_axis_field_advertised_exactly_for_routable_types():
    """Every type that actually supports axis="y2" routing (per
    validate._AXIS_ROUTABLE_TYPES) must say so in capabilities(), and no
    type that *doesn't* support it should falsely claim to."""
    for layer_type, spec in LAYER_TYPES.items():
        advertises_axis = "axis" in spec["optional"]
        actually_routable = layer_type in _AXIS_ROUTABLE_TYPES
        assert advertises_axis == actually_routable, (
            f"{layer_type}: capabilities() advertises axis={advertises_axis} "
            f"but validate._AXIS_ROUTABLE_TYPES says {actually_routable}"
        )
