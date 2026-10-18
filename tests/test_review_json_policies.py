"""JSON-08/09/10/12: explicit structural policies and bounded corrupt-input checks."""

from __future__ import annotations

import copy
import hashlib
import json
import os
import subprocess
import sys

import jsonschema
import mudplot as mp
import pytest
from mudplot.spec import LayerSpec


def test_known_version_ignores_unknown_dataclass_fields_but_keeps_data_metadata():
    original = (
        mp.plot({"x": [1, 2], "y": [2, 3], "metadata": [{"future": True}, None]})
        .line("x", "y")
        .spec
    )
    value = original.to_dict()
    value["future_figure"] = {"literal": 1}
    value["theme"]["future_theme"] = 2
    value["panels"][0]["future_panel"] = 3
    value["panels"][0]["layers"][0]["future_layer"] = 4
    assert mp.from_json(json.dumps(value)) == original
    invalid = copy.deepcopy(value)
    invalid["version"] = "999.future"
    with pytest.raises(ValueError, match="version"):
        mp.from_json(json.dumps(invalid))
    assert original.data.columns["metadata"] == [{"future": True}, None]


@pytest.mark.parametrize(
    "value", [{}, {"marker_size": None}, {"marker_size": 0}, {"marker_size": 7.5}]
)
def test_optional_marker_omission_null_zero_and_explicit_value(value):
    plot = mp.plot({"x": [1], "y": [2]}).scatter("x", "y", **value)
    expected = value.get("marker_size")
    assert plot.spec.panels[0].layers[0].marker_size == expected
    jsonschema.Draft202012Validator(mp.json_schema()).validate(plot.spec.to_dict())
    restored = mp.Plot.from_json(plot.to_json())
    assert restored.spec.panels[0].layers[0].marker_size == expected
    assert restored.spec == plot.spec
    layer = LayerSpec.from_dict({"type": "scatter", "x": "x", "y": "y", **value})
    assert isinstance(layer, LayerSpec)
    assert layer.marker_size == expected


def test_canonical_keys_whitespace_and_unicode_do_not_reorder_or_coerce_data():
    plot = mp.plot({"x": [2, 1], "y": [4, 3], "label": ["한글 Ω 😀", "<&>"]}).line(
        "x", "y"
    )
    expected = mp.to_json(plot.spec, indent=None, sort_keys=True)
    value = plot.spec.to_dict()
    variants = [
        json.dumps(value, ensure_ascii=False),
        json.dumps(value, ensure_ascii=True, indent=4),
        json.dumps(dict(reversed(list(value.items()))), ensure_ascii=False),
    ]
    hashes = [
        hashlib.sha256(
            mp.to_json(mp.from_json(text), indent=None, sort_keys=True).encode()
        ).hexdigest()
        for text in variants
    ]
    assert hashes == [hashlib.sha256(expected.encode()).hexdigest()] * len(variants)
    changed = copy.deepcopy(value)
    changed["data"]["columns"]["x"].reverse()
    assert (
        mp.to_json(mp.FigureSpec.from_dict(changed), indent=None, sort_keys=True)
        != expected
    )
    changed = copy.deepcopy(value)
    changed["data"]["columns"]["x"] = [2.0, 1.0]
    assert (
        mp.to_json(mp.FigureSpec.from_dict(changed), indent=None, sort_keys=True)
        != expected
    )


@pytest.mark.parametrize("kind", ["truncated", "bad_utf8", "deep", "large_valid"])
def test_bounded_child_json_checks_are_errors_or_lossless_and_can_recover(kind):
    code = """import sys
import mudplot as m
kind=sys.argv[1]
if kind=='truncated': payload='{"data":{"columns":{"x":[1,2]}'
elif kind=='bad_utf8': payload=b'{"suptitle":"'+bytes([255])+b'"}'
elif kind=='deep': payload='{"data":{"columns":{"x":'+ '['*3000+'0'+']'*3000+'}}}'
else: payload='{"data":{"columns":{"unused":['+','.join(map(str,range(20000)))+']}}}'
try:
    spec=m.from_json(payload)
except ValueError:
    assert kind!='large_valid'
else:
    assert kind=='large_valid'
    assert m.from_json(m.to_json(spec)).data.columns['unused']==list(range(20000))
assert m.from_json('{"suptitle":"recovered"}').suptitle=='recovered'
"""
    subprocess.run(
        [sys.executable, "-c", code, kind],
        env={**os.environ, "PYTHONUTF8": "1"},
        check=True,
        timeout=20,
    )
