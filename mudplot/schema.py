"""JSON Schema generation for the spec dataclasses.

Lets an AI agent (or a form generator, or a Rust serde consumer) know the exact
shape of a ``FigureSpec`` and every nested type. Pure and dependency-free —
implemented by introspecting dataclass type hints.
"""

from __future__ import annotations

import types
import typing
from dataclasses import MISSING, fields, is_dataclass
from typing import Union, get_args, get_origin

from .spec import DataSpec, FigureSpec

__all__ = ["json_schema"]

_UNION_ORIGINS = (Union, types.UnionType)

_PRIMITIVES = {
    str: {"type": "string"},
    bool: {"type": "boolean"},
    int: {"type": "integer"},
    float: {"type": "number"},
    type(None): {"type": "null"},
}


def _schema_for(tp, defs: dict) -> dict[str, object]:
    origin = get_origin(tp)

    if tp in _PRIMITIVES:
        return dict(_PRIMITIVES[tp])

    if origin is typing.Literal:
        return {"enum": list(get_args(tp))}

    if origin in _UNION_ORIGINS:
        args = get_args(tp)
        non_none = [a for a in args if a is not type(None)]
        sub = [_schema_for(a, defs) for a in non_none]
        if type(None) in args:
            sub.append({"type": "null"})
        return sub[0] if len(sub) == 1 else {"anyOf": sub}

    if origin in (list, tuple):
        args = get_args(tp)
        item = _schema_for(args[0], defs) if args else {}
        return {"type": "array", "items": item}

    if origin is dict:
        return {"type": "object"}

    if isinstance(tp, type) and is_dataclass(tp):
        name = tp.__name__
        if name not in defs:
            defs[name] = {}  # placeholder to break recursion
            defs[name] = _dataclass_schema(tp, defs)
        return {"$ref": f"#/$defs/{name}"}

    return {}  # unknown -> permissive


def _dataclass_schema(cls, defs: dict) -> dict:
    hints = typing.get_type_hints(cls)
    props = {}
    required = []
    for f in fields(cls):
        prop = _schema_for(hints[f.name], defs)
        if f.default is not MISSING:
            prop = {**prop, "default": f.default}
        elif f.default_factory is MISSING:  # no default at all -> required
            required.append(f.name)
        if cls is DataSpec and f.name == "matrices":
            item = get_args(hints[f.name])[1]
            prop["additionalProperties"] = _schema_for(item, defs)
        bounds = {
            key: f.metadata[key]
            for key in ("minItems", "maxItems")
            if key in f.metadata
        }
        if bounds:
            array = (
                prop
                if prop.get("type") == "array"
                else next(
                    item
                    for item in typing.cast("list[dict[str, object]]", prop["anyOf"])
                    if item.get("type") == "array"
                )
            )
            array.update(bounds)
        props[f.name] = prop
    schema = {"type": "object", "properties": props}
    if getattr(cls, "_reject_unknown_fields", False):
        schema["additionalProperties"] = False
    if required:
        schema["required"] = required
    return schema


def json_schema(cls=FigureSpec) -> dict:
    """Return a JSON Schema (draft 2020-12) dict for ``cls`` (default FigureSpec)."""
    defs: dict = {}
    root = _dataclass_schema(cls, defs)
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": cls.__name__,
        **root,
        "$defs": defs,
    }
