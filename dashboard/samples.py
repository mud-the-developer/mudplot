"""Small built-in sample datasets for quickly trying out the editor.

Pure data, zero dependencies — used by the "load sample" buttons in the
interactive editor (see ``editor_server.py``).
"""

from __future__ import annotations

import math

__all__ = ["SAMPLES", "sample_columns"]


def _sine_groups() -> dict:
    n = 60
    xs = [i * 10.0 / (n - 1) for i in range(n)]
    return {
        "x": xs * 3,
        "y": (
            [math.sin(x) for x in xs]
            + [math.sin(x) * 0.6 for x in xs]
            + [math.sin(x) * 0.3 for x in xs]
        ),
        "series": ["A"] * n + ["B"] * n + ["C"] * n,
    }


def _scatter_continuous() -> dict:
    n = 50
    xs = [i / (n - 1) for i in range(n)]
    ys = [math.cos(6 * x) for x in xs]
    zs = [math.sin(6 * x) for x in xs]
    return {"x": xs, "y": ys, "z": zs}


def _bar_groups() -> dict:
    cats = [1, 2, 3, 4]
    return {
        "x": cats * 2,
        "y": [10, 20, 15, 18, 5, 8, 25, 12],
        "group": ["A"] * 4 + ["B"] * 4,
    }


SAMPLES: dict[str, dict] = {
    "sine": _sine_groups(),
    "scatter": _scatter_continuous(),
    "bars": _bar_groups(),
}


def sample_columns(name: str) -> dict:
    if name not in SAMPLES:
        raise ValueError(f"unknown sample {name!r}; choose from {list(SAMPLES)}")
    return SAMPLES[name]
