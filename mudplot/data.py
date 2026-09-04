"""Data ingestion: turn many input formats into ``dict[str, list]`` columns.

Dependency-free by design (part of the pure engine): everything is done with
duck typing and the standard library, so importing this never pulls numpy,
pandas, polars, etc. Supported inputs:

* ``None``                         -> ``{}``
* mapping / dict of columns        -> ``{name: [values...]}``
* list/tuple of dict records       -> pivoted to columns
* list/tuple of rows (2-D)         -> columns ``c0, c1, ...``
* pandas / polars DataFrame        -> via ``.columns`` + column access
* numpy structured array           -> via ``dtype.names``
* numpy / array 2-D                 -> columns ``c0, c1, ...``
* pyarrow Table (``.to_pydict``)   -> its dict
* any object with ``.to_dict()``   -> its dict
* DB-API connection + ``query=``   -> executes and reads the result set
* executed DB-API cursor           -> via ``.description`` + rows
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

__all__ = ["to_columns"]


def _to_list(v) -> list:
    """Coerce a column-ish value to a plain list."""
    if isinstance(v, (list, tuple)):
        return list(v)
    if hasattr(v, "tolist"):  # numpy array / pandas Series / polars Series
        out = v.tolist()
        return out if isinstance(out, list) else list(v)
    if isinstance(v, (str, bytes)):
        return [v]
    try:
        return list(v)
    except TypeError:
        return [v]


def _looks_like_dataframe(data: Any) -> bool:
    # pandas / polars: have a ``columns`` attribute and support df[col]
    return (
        hasattr(data, "columns")
        and hasattr(data, "__getitem__")
        and not isinstance(data, Mapping)
        and not hasattr(data, "dtype")  # exclude structured ndarrays
    )


def _is_structured_ndarray(data: Any) -> bool:
    dtype = getattr(data, "dtype", None)
    return dtype is not None and getattr(dtype, "names", None) is not None


def _is_ndarray_2d(data: Any) -> bool:
    return getattr(data, "ndim", None) == 2 and hasattr(data, "tolist")


def _is_dbapi_cursor(data: Any) -> bool:
    # executed DB-API cursor: has ``description`` and is iterable / fetchable
    return hasattr(data, "description") and (
        hasattr(data, "fetchall") or hasattr(data, "__iter__")
    )


def _records_to_columns(records: list[Mapping]) -> dict[str, list]:
    # union of keys, preserving first-seen order
    keys: list[str] = []
    for r in records:
        for k in r:
            if k not in keys:
                keys.append(str(k))
    return {k: [rec.get(k) for rec in records] for k in keys}


def _rows_to_columns(rows) -> dict[str, list]:
    # rows: iterable of equal-length sequences -> c0, c1, ...
    as_lists = [list(r) for r in rows]
    if not as_lists:
        return {}
    ncols = len(as_lists[0])
    return {f"c{j}": [row[j] for row in as_lists] for j in range(ncols)}


def _cursor_to_columns(cur) -> dict[str, list]:
    names = [d[0] for d in cur.description]
    rows = cur.fetchall() if hasattr(cur, "fetchall") else list(cur)
    cols: dict[str, list] = {name: [] for name in names}
    for row in rows:
        for name, val in zip(names, row, strict=False):
            cols[name].append(val)
    return cols


def to_columns(data: Any, *, query: str | None = None) -> dict[str, list]:
    """Convert ``data`` into an ordered ``dict`` of ``{column: [values]}``.

    If ``query`` is given, ``data`` is treated as a DB-API connection and the
    query is executed to produce the result set.
    """
    if query is not None:
        cur = data.cursor()
        cur.execute(query)
        return _cursor_to_columns(cur)

    if data is None:
        return {}

    if _is_dbapi_cursor(data):
        return _cursor_to_columns(data)

    if isinstance(data, Mapping):
        return {str(k): _to_list(v) for k, v in data.items()}

    if _is_structured_ndarray(data):
        return {str(name): _to_list(data[name]) for name in data.dtype.names}

    if _looks_like_dataframe(data):
        return {str(c): _to_list(data[c]) for c in data.columns}

    if hasattr(data, "to_pydict"):  # pyarrow Table
        return {str(k): _to_list(v) for k, v in data.to_pydict().items()}

    if isinstance(data, (list, tuple)):
        if len(data) == 0:
            return {}
        first = data[0]
        if isinstance(first, Mapping):
            return _records_to_columns(list(data))
        # NOTE: strings/bytes have __len__ too but are scalars here, not row
        # sequences -- without this exclusion, a flat list of strings (e.g.
        # category labels) would be silently shredded into one "column" per
        # *character* instead of raising/treating them as a single column.
        if not isinstance(first, (str, bytes)) and (
            isinstance(first, (list, tuple)) or hasattr(first, "__len__")
        ):
            return _rows_to_columns(data)
        raise TypeError(
            "list input must be records (list of dicts) or rows (list of "
            "sequences); a flat list has no column name — pass a dict instead"
        )

    if _is_ndarray_2d(data):
        return _rows_to_columns(data.tolist())

    if hasattr(data, "to_dict"):  # generic, keep last (broad)
        d = data.to_dict()
        if isinstance(d, Mapping):
            return {str(k): _to_list(v) for k, v in d.items()}

    raise TypeError(
        f"unsupported data type {type(data).__name__!r}; pass a dict of columns, "
        "list of records, DataFrame, numpy array, or a DB cursor / (conn, query)"
    )
