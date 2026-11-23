"""JSON-01: every modeled field, separate from semantic/renderability validation.

Regenerate the structural fixture: uv run python tests/test_review_full_spec_fields.py
The deliberately incompatible options stress codecs, not plotting support.
"""

from __future__ import annotations

import argparse
import json
import types
import typing
from dataclasses import MISSING, fields, is_dataclass
from pathlib import Path
from typing import Any, get_args, get_origin

import jsonschema
import mudplot as mp
import pytest
from mudplot import spec as models

FIXTURE = Path(__file__).parent / "fixtures/review_full_spec_fields.json"
MODELS = {
    name: cls
    for name, cls in vars(models).items()
    if isinstance(cls, type) and is_dataclass(cls) and issubclass(cls, models.SpecBase)
}


def _field_value(field):
    if field.default is not MISSING:
        return field.default
    if field.default_factory is not MISSING:
        return field.default_factory()
    return None  # Required fixture values are generated from their declared type.


def _model(cls):
    hints = typing.get_type_hints(cls)
    return cls(
        **{
            field.name: _sample(
                hints[field.name], None, f"{cls.__name__}.{field.name}", 0
            )
            for field in fields(cls)
            if field.default is MISSING and field.default_factory is MISSING
        }
    )


def _sample(tp, current, tag, variant):
    origin, args = get_origin(tp), get_args(tp)
    if origin is typing.Literal:
        return args[variant % len(args)]
    if origin in (types.UnionType, typing.Union):
        choices = [choice for choice in args if choice is not type(None)]
        if (
            variant == 2
            and type(None) in args
            and not any(is_dataclass(choice) for choice in choices)
        ):
            return None
        return _sample(choices[variant % len(choices)], current, tag, variant)
    if isinstance(tp, type) and is_dataclass(tp):
        hints = typing.get_type_hints(tp)
        return tp(
            **{
                field.name: models.SPEC_VERSION
                if tp is models.FigureSpec and field.name == "version"
                else _sample(
                    hints[field.name],
                    _field_value(field),
                    f"{tag}.{field.name}",
                    variant,
                )
                for field in fields(tp)
            }
        )
    if tp is Any:
        return {
            "tag": tag,
            "values": [None, True, 2**80 + 1, -(2**80 + 1), 0.5, "한글 Ω 😀 <&>"],
        }
    if tp is bool:
        return not current if type(current) is bool else tag.endswith("[0]")
    if tp is int:
        return (
            (current if type(current) is int else 0)
            + variant
            + 1
            + sum(map(ord, tag)) % 31
        )
    if tp is float:
        return (
            (current if type(current) in (int, float) else 0)
            + 0.125
            + variant / 4
            + (sum(map(ord, tag)) % 31 + 1) / 1024
        )
    if tp is str:
        return f"probe:{tag}:한글 Ω 😀 <&>"
    if origin in (list, tuple) or tp is list:
        item_type = args[0] if args else Any
        values = [
            _sample(item_type, None, f"{tag}[{index}]", variant)
            for index in range(1 if is_dataclass(item_type) else 2)
        ]
        return tuple(values) if origin is tuple else values
    if origin is dict or tp is dict:
        value_type = args[1] if args else Any
        return {"probe κ": _sample(value_type, None, tag + ".probe κ", variant)}
    raise AssertionError(f"unhandled modeled type: {tp}")


def _walk(value):
    if is_dataclass(value) and not isinstance(value, type):
        yield value
        for field in fields(value):
            yield from _walk(getattr(value, field.name))
    elif isinstance(value, dict):
        for item in value.values():
            yield from _walk(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from _walk(item)


def _figures() -> list[models.FigureSpec]:
    figures = []
    for variant in range(3):
        figure = _sample(models.FigureSpec, None, "FigureSpec", variant)
        assert isinstance(figure, models.FigureSpec)
        figures.append(figure)
    return figures


def _payload():
    return {
        "scope": (
            "Structural/schema-valid codec stress only; mutually incompatible "
            "options are intentionally populated. Not renderable plot claims."
        ),
        "model_fields": {
            name: [field.name for field in fields(cls)]
            for name, cls in sorted(MODELS.items())
        },
        "figures": [figure.to_dict() for figure in _figures()],
    }


def _assert_json_types(expected, actual):
    assert type(actual) is type(expected)
    if isinstance(expected, dict):
        assert set(actual) == set(expected)
        for key in expected:
            _assert_json_types(expected[key], actual[key])
    elif isinstance(expected, list):
        assert len(actual) == len(expected)
        for left, right in zip(expected, actual, strict=True):
            _assert_json_types(left, right)
    else:
        assert actual == expected


@pytest.mark.parametrize(
    "cls,field_name",
    [
        pytest.param(cls, field.name, id=f"{name}.{field.name}")
        for name, cls in sorted(MODELS.items())
        for field in fields(cls)
        if type(None) in get_args(typing.get_type_hints(cls)[field.name])
    ],
)
def test_every_nullable_field_distinguishes_omitted_null_and_explicit_default(
    cls, field_name
):
    baseline = _model(cls).to_dict()
    validator = jsonschema.Draft202012Validator(mp.json_schema(cls))
    omitted = _model(cls).to_dict()
    omitted.pop(field_name, None)
    validator.validate(omitted)
    _assert_json_types(baseline, cls.from_dict(omitted).to_dict())
    field = next(field for field in fields(cls) if field.name == field_name)
    for value in (None, getattr(_model(cls), field_name)):
        payload = _model(cls).to_dict()
        payload[field_name] = value
        validator.validate(payload)
        decoded = cls.from_dict(payload)
        assert getattr(decoded, field_name) == value
        expected = dict(payload)
        if value is None and field.metadata.get("omit_none"):
            del expected[field_name]
        _assert_json_types(expected, decoded.to_dict())
    types_ = get_args(typing.get_type_hints(cls)[field_name])
    if int in types_ or float in types_ or bool in types_:
        value = False if bool in types_ else 0
        payload = _model(cls).to_dict()
        payload[field_name] = value
        validator.validate(payload)
        assert cls.from_dict(payload).to_dict()[field_name] == value


@pytest.mark.parametrize(
    "figure", _figures(), ids=["filled", "alternate-unions", "nullable"]
)
@pytest.mark.parametrize("ascii_escapes", [False, True])
def test_every_structurally_supported_field_survives_python_json(figure, ascii_escapes):
    before = figure.to_dict()
    jsonschema.Draft202012Validator(mp.json_schema()).validate(before)
    encoded = json.dumps(before, ensure_ascii=ascii_escapes, allow_nan=False)
    for restored in (mp.from_json(encoded), mp.Plot.from_json(encoded).spec):
        _assert_json_types(before, restored.to_dict())
        assert [type(node) for node in _walk(restored)] == [
            type(node) for node in _walk(figure)
        ]
    _assert_json_types(before, mp.from_json(mp.to_json(figure)).to_dict())


if __name__ == "__main__":
    payload = _payload()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    arguments = parser.parse_args()
    for figure in payload["figures"]:
        jsonschema.Draft202012Validator(mp.json_schema()).validate(figure)
    encoded = json.dumps(payload, ensure_ascii=False, allow_nan=False, indent=2) + "\n"
    if arguments.check:
        if FIXTURE.read_text(encoding="utf-8") != encoded:
            raise SystemExit("full-field fixture is stale; run this generator")
    else:
        FIXTURE.write_text(encoded, encoding="utf-8")
    print(
        f"{'Checked' if arguments.check else 'Wrote'} {FIXTURE.name}: "
        f"{len(MODELS)} model types, "
        f"{sum(len(fields(cls)) for cls in MODELS.values())} fields, "
        "3 structural figures"
    )
