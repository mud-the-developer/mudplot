"""JSON Schema *compatibility* tests: does ``mp.json_schema()`` actually work
as a real JSON Schema, not just "shaped like one" (see the existing
``test_schema_export.py::test_schema_is_valid_json_schema_shape`` for that
weaker check)?

This matters once a Rust/serde consumer, a form generator, or an external
tool starts validating ``.mplot.json`` files against the exported schema
directly rather than trusting mudplot's own (separate) ``validate()`` --
the two must actually agree on what's a valid spec.
"""

import jsonschema
import mudplot as mp
import pytest
from mudplot.spec import FigureSpec


def _schema():
    return mp.json_schema()


def test_schema_is_a_well_formed_json_schema():
    """The schema document itself must obey the Draft 2020-12 meta-schema
    (catches e.g. a malformed $ref, a "required" naming a property that
    doesn't exist, ...) -- not just "has a $schema key".
    """
    jsonschema.Draft202012Validator.check_schema(_schema())


def _validator():
    return jsonschema.Draft202012Validator(_schema())


# A range of real specs exercising most of the schema's shape: nested
# dataclasses ($ref/$defs), lists of dataclasses (panels/layers), a dict of
# dataclasses (LayerSpec.references), optional/None fields, enums-as-str
# fields, and every top-level section (theme/data/panels).
def _demo_specs():
    data = {
        "x": [1, 2, 3, 1, 2, 3],
        "y": [1, 4, 9, 2, 3, 5],
        "g": ["a", "a", "a", "b", "b", "b"],
    }
    plain = mp.plot(data).line("x", "y", group="g").spec
    with_refs = (
        mp.plot(data)
        .line(
            "x",
            "y",
            group="g",
            references={
                "a": mp.Reference(citation="fischler_1981", href="https://doi.org/x"),
                "b": mp.Reference(citation="toldo_2008"),
            },
        )
        .title_reference(citation="hartley2003")
        .reference_style(measure_text="(Author, Year)")
        .legend(bbox_to_anchor=[0.8, 0.5])
        .title_position([0.5, 0.9])
        .spec
    )
    multi_panel = (
        mp.plot(data)
        .layout(1, 2)
        .line("x", "y", group="g", panel=0)
        .box("x", panel=1)
        .secondary_yaxis("Y2", panel=0)
        .spec
    )
    matrix = mp.plot({}).matrix("field", [[1, 2], [3, 4]]).heatmap("field").spec
    threed = mp.plot(data).projection3d().scatter3d("x", "y", "x", c="y").spec
    default = FigureSpec()
    return {
        "plain grouped line": plain,
        "grouped references + reference_style + explicit positions": with_refs,
        "multi-panel + secondary axis": multi_panel,
        "matrix/heatmap": matrix,
        "3-D scatter": threed,
        "bare default": default,
    }


@pytest.mark.parametrize("name", list(_demo_specs()))
def test_real_specs_validate_against_the_exported_schema(name):
    spec = _demo_specs()[name]
    _validator().validate(spec.to_dict())


def test_wrong_type_is_actually_rejected():
    """The schema must be a real constraint, not silently permissive: a
    spec.json with the wrong type for a well-known field should fail.
    """
    d = FigureSpec().to_dict()
    d["size"] = "not-a-list"
    with pytest.raises(jsonschema.ValidationError):
        _validator().validate(d)


def test_unknown_top_level_field_type_mismatch_is_rejected():
    d = FigureSpec().to_dict()
    d["dpi"] = "not-a-number"
    with pytest.raises(jsonschema.ValidationError):
        _validator().validate(d)


def test_a_minimal_layer_dict_is_schema_valid_despite_missing_xy():
    """LayerSpec's every field has a default (x: str = "", ...), so the
    schema has no "required" list for it at all -- "line needs x and y" is
    mudplot's own semantic ``validate()`` concern (see test_validate*.py),
    not something the JSON Schema enforces. Documented here explicitly so a
    future schema-tightening change doesn't silently break this assumption
    for external (non-mudplot) consumers of the exported schema.
    """
    d = FigureSpec().to_dict()
    d["panels"][0]["layers"] = [{"type": "line"}]
    _validator().validate(d)
