"""Load/save a FigureSpec as JSON (the ``.mplot.json`` format).

The on-disk schema is intentionally plain JSON so the Rust (serde) frontend
can read and write the exact same files.
"""

from __future__ import annotations

import contextlib
import json
import math
import os
import secrets
import stat
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from .spec import FigureSpec

__all__ = ["from_json", "load_spec", "save_spec", "to_json"]

_RESERVED_JSON_KEY = "$serde_json::private::Number"


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"non-standard JSON constant {value!r}")


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result = {}
    for key, value in pairs:
        if key == _RESERVED_JSON_KEY:
            raise ValueError(f"JSON object key {key!r} is reserved")
        if key in result:
            raise ValueError(f"duplicate JSON object key {key!r}")
        result[key] = value
    return result


def _validate_json_value(value: Any) -> None:
    if value is None or type(value) in (bool, int):
        return
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("JSON numbers must be finite")
        return
    if isinstance(value, str):
        if any("\ud800" <= char <= "\udfff" for char in value):
            raise ValueError("JSON strings must not contain lone surrogates")
        return
    if isinstance(value, list):
        for item in value:
            _validate_json_value(item)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise ValueError("JSON object keys must be strings")
            if key == _RESERVED_JSON_KEY:
                # ponytail: use a custom Rust JSON AST if this key is ever needed.
                raise ValueError(f"JSON object key {key!r} is reserved")
            _validate_json_value(key)
            _validate_json_value(item)
        return
    raise ValueError(f"{type(value).__name__} is not a JSON value")


def _loads_json(text: str) -> Any:
    try:
        value = json.loads(
            text,
            parse_constant=_reject_json_constant,
            object_pairs_hook=_reject_duplicate_keys,
        )
        _validate_json_value(value)
        return value
    except (json.JSONDecodeError, ValueError, RecursionError) as error:
        raise ValueError(f"invalid JSON: {error}") from error


def to_json(
    spec: FigureSpec, *, indent: int | None = 2, sort_keys: bool = False
) -> str:
    value = spec.to_dict()
    _validate_json_value(value)
    return json.dumps(
        value,
        indent=indent,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=sort_keys,
    )


def from_json(text: str) -> FigureSpec:
    try:
        return FigureSpec.from_dict(_loads_json(text))
    except (json.JSONDecodeError, TypeError, ValueError, RecursionError) as e:
        raise ValueError(f"invalid FigureSpec JSON: {e}") from e


@contextlib.contextmanager
def _atomic_destination(path: str | Path) -> Iterator[Path]:
    destination = Path(path)
    if destination.is_symlink():
        destination = destination.resolve()
    temporary = destination.with_name(
        f".{destination.name}.{secrets.token_hex(16)}.tmp"
    )
    mode = stat.S_IMODE(destination.stat().st_mode) if destination.exists() else None
    try:
        yield temporary
        with temporary.open("rb+") as handle:
            if mode is not None:
                temporary.chmod(mode)
            os.fsync(handle.fileno())
        os.replace(temporary, destination)
    except BaseException:
        with contextlib.suppress(OSError):
            temporary.unlink()
        raise


def _atomic_write_text(path: str | Path, text: str) -> None:
    with (
        _atomic_destination(path) as temporary,
        temporary.open("x", encoding="utf-8", newline="\n") as handle,
    ):
        handle.write(text)


def save_spec(spec: FigureSpec, path: str | Path) -> None:
    _atomic_write_text(path, to_json(spec))


def load_spec(path: str | Path) -> FigureSpec:
    return from_json(Path(path).read_text(encoding="utf-8"))
