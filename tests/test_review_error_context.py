"""Field context stays actionable without changing decoder acceptance/types."""

import copy
import json

import mudplot as mp
import pytest
from mudplot import actions as A
from mudplot.__main__ import main
from mudplot.spec import FigureSpec, LayerSpec


@pytest.mark.parametrize("field", ["width", "height"])
def test_action_numeric_error_identifies_field_without_echoing_value(field):
    action = {"type": "SetSize", "width": 4, "height": 3}
    action[field] = "SYNTHETIC-NUMERIC-CANARY"
    before = copy.deepcopy(action)
    with pytest.raises(TypeError) as error:
        A.action_from_dict(action)
    assert f"SetSize.{field}" in str(error.value)
    assert "expected number, got str" in str(error.value)
    assert "SYNTHETIC-NUMERIC-CANARY" not in str(error.value)
    assert error.value.__cause__ is not None and action == before


def test_nested_spec_error_reports_field_chain_and_keeps_type_and_inputs():
    data = {"theme": {"font": {"size": "SYNTHETIC-NUMERIC-CANARY"}}}
    before = copy.deepcopy(data)
    with pytest.raises(TypeError) as error:
        FigureSpec.from_dict(data)
    message = str(error.value)
    assert "FigureSpec.theme" in message and "ThemeSpec.font" in message
    assert "FontSpec.size" in message and "expected number, got str" in message
    assert "SYNTHETIC-NUMERIC-CANARY" not in message and data == before


@pytest.mark.parametrize("field", ["width", "height"])
def test_cli_numeric_field_context_has_nonzero_exit_and_no_stdout(
    tmp_path, capsys, field
):
    source = tmp_path / "in.json"
    source.write_text(mp.plot().to_json(), encoding="utf-8")
    action = {"type": "SetSize", "width": 4, "height": 3}
    action[field] = "SYNTHETIC-NUMERIC-CANARY"
    payload = tmp_path / "action.json"
    payload.write_text(json.dumps(action), encoding="utf-8")
    output = tmp_path / "previous.json"
    output.write_bytes(b"previous complete output")
    assert main(["apply", str(source), str(payload), "-o", str(output)]) == 1
    captured = capsys.readouterr()
    assert captured.out == "" and f"SetSize.{field}" in captured.err
    assert (
        "Traceback" not in captured.err
        and "SYNTHETIC-NUMERIC-CANARY" not in captured.err
    )
    assert output.read_bytes() == b"previous complete output"


def test_strict_nested_field_error_keeps_valueerror_and_context():
    with pytest.raises(ValueError) as error:
        LayerSpec.from_dict({"type": "heatmap", "heatmap": {"unexpected": True}})
    assert "LayerSpec.heatmap" in str(error.value)
    assert "unknown HeatmapSpec field" in str(error.value)
    assert isinstance(error.value.__cause__, ValueError)


@pytest.mark.parametrize("value", [1.5, [0, 100], None])
def test_union_alternatives_keep_existing_successful_decoding(value):
    raw = {"type": "box", "whis": value}
    before = copy.deepcopy(raw)
    layer = LayerSpec.from_dict(raw)
    assert isinstance(layer, LayerSpec)
    assert layer.whis == value
    assert raw == before
