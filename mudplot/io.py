"""Load/save a FigureSpec as JSON (the ``.mplot.json`` format).

The on-disk schema is intentionally plain JSON so a future Rust (serde)
frontend can read and write the exact same files.
"""

from __future__ import annotations

import json
from pathlib import Path

from .spec import FigureSpec

__all__ = ["from_json", "load_spec", "save_spec", "to_json"]


def to_json(spec: FigureSpec, *, indent: int | None = 2) -> str:
    return json.dumps(spec.to_dict(), indent=indent, ensure_ascii=False)


def from_json(text: str) -> FigureSpec:
    return FigureSpec.from_dict(json.loads(text))


def save_spec(spec: FigureSpec, path: str | Path) -> None:
    Path(path).write_text(to_json(spec), encoding="utf-8")


def load_spec(path: str | Path) -> FigureSpec:
    return from_json(Path(path).read_text(encoding="utf-8"))
