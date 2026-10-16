"""Built-in data and complete figure drafts for the source-tree editor.

Import and dataset construction need no optional dependencies. Complete figure
builders use the render extras lazily; selecting a draft does not open it.
"""

from __future__ import annotations

import math

from mudplot.spec import FigureSpec

__all__ = ["FIGURE_SAMPLES", "SAMPLES", "sample_columns", "sample_figure"]

FIGURE_SAMPLES = {
    "response": ("Response · 700px", "response", 700),
    "response-mobile": ("Response · 320px", "response", 320),
    "endpoint": ("Endpoint · 700px", "endpoint", 700),
    "endpoint-mobile": ("Endpoint · 320px", "endpoint", 320),
}


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


def sample_figure(name: str) -> FigureSpec:
    """Build a fresh, checked spec from a fixed allowlist, never a user path."""
    if not isinstance(name, str) or name not in FIGURE_SAMPLES:
        raise ValueError("unknown figure example")
    from examples.publication_showcase import build_plot
    from mudplot.validate import assert_valid

    _, kind, width = FIGURE_SAMPLES[name]
    spec = build_plot(kind, width_px=width).spec
    assert_valid(spec)
    return spec
