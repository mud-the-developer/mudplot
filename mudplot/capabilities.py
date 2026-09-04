"""Machine-readable description of what the engine can do.

Designed for AI agents: a single ``capabilities()`` call returns everything an
agent needs to plan a figure — layer types and their fields, available themes /
journals / TeX presets / palette kinds, and the full action vocabulary. Pure
and dependency-free.
"""

from __future__ import annotations

from dataclasses import MISSING, fields

from . import actions as _actions
from .theme import AVAILABLE_JOURNALS, AVAILABLE_THEMES

__all__ = ["LAYER_TYPES", "PALETTE_KINDS", "capabilities"]

# Per-layer field guidance (what an agent should provide for each layer type).
LAYER_TYPES: dict[str, dict[str, list[str]]] = {
    "line": {
        "required": ["x", "y"],
        "optional": [
            "group",
            "label",
            "color",
            "line_width",
            "line_style",
            "marker",
            "marker_size",
            "alpha",
            "axis",
        ],
    },
    "scatter": {
        "required": ["x", "y"],
        "optional": [
            "group",
            "label",
            "color",
            "marker",
            "marker_size",
            "alpha",
            "c",
            "cmap_kind",
            "colorbar",
            "clabel",
            "axis",
        ],
    },
    "bar": {
        "required": ["x", "y"],
        "optional": ["label", "color", "alpha", "axis"],
    },
    "errorbar": {
        "required": ["x", "y"],
        "optional": [
            "yerr",
            "xerr",
            "group",
            "label",
            "color",
            "capsize",
            "marker",
            "marker_size",
            "line_width",
            "alpha",
            "axis",
        ],
    },
    "band": {
        "required": ["x", "y", "y2"],
        "optional": ["group", "label", "color", "alpha", "axis"],
    },
    "hline": {
        "required": ["value"],
        "optional": [
            "label",
            "color",
            "line_style",
            "line_width",
            "alpha",
            "axis",
        ],
    },
    "vline": {
        "required": ["value"],
        "optional": [
            "label",
            "color",
            "line_style",
            "line_width",
            "alpha",
            "axis",
        ],
    },
    "text": {
        "required": ["text", "at"],
        "optional": ["color", "alpha", "axis"],
    },
    "annotate": {
        "required": ["text", "at"],
        "optional": ["to", "color", "alpha", "axis"],
    },
    "hist": {
        "required": ["x"],
        "optional": ["bins", "density", "group", "label", "color", "alpha"],
    },
    "box": {
        "required": ["x"],
        "optional": ["group", "label", "color", "alpha"],
    },
    "heatmap": {
        "required": ["matrix"],
        "optional": ["cmap_kind", "colorbar", "clabel", "alpha"],
    },
    "contour": {
        "required": ["matrix"],
        "optional": ["cmap_kind", "colorbar", "clabel", "alpha", "levels"],
    },
    "contourf": {
        "required": ["matrix"],
        "optional": ["cmap_kind", "colorbar", "clabel", "alpha", "levels"],
    },
    "violin": {
        "required": ["x"],
        "optional": ["group", "label", "color", "alpha"],
    },
    "kde": {
        "required": ["x"],
        "optional": [
            "group",
            "label",
            "color",
            "alpha",
            "line_width",
            "line_style",
        ],
    },
    "pie": {
        "required": ["x", "y"],
        "optional": ["color", "alpha"],
    },
    "scatter3d": {
        "required": ["x", "y", "z"],
        "optional": [
            "group",
            "label",
            "color",
            "marker",
            "marker_size",
            "alpha",
            "c",
            "cmap_kind",
            "colorbar",
            "clabel",
        ],
    },
    "line3d": {
        "required": ["x", "y", "z"],
        "optional": [
            "group",
            "label",
            "color",
            "line_width",
            "line_style",
            "marker",
            "alpha",
        ],
    },
    "surface": {
        "required": ["matrix"],
        "optional": ["cmap_kind", "colorbar", "clabel", "alpha"],
    },
    "wireframe": {
        "required": ["matrix"],
        "optional": ["color", "alpha"],
    },
}

PALETTE_KINDS = ["qualitative", "sequential", "diverging"]


def _default_of(f):
    if f.default is not MISSING:
        return f.default
    if f.default_factory is not MISSING:  # type: ignore[misc]
        return f.default_factory()
    return None


def _action_fields(cls) -> list[dict]:
    return [
        {
            "name": f.name,
            "type": _type_name(f.type),
            "required": f.default is MISSING and f.default_factory is MISSING,
            "default": _default_of(f),
        }
        for f in fields(cls)
    ]


def _type_name(tp) -> str:
    name = getattr(tp, "__name__", str(tp))
    # avoid a bare "|" in union type names (e.g. "str | None") leaking into
    # markdown/pipe-table renderings downstream; "or" reads fine either way.
    return name.replace(" | ", " or ")


def action_vocabulary() -> dict[str, list[dict]]:
    """All dispatchable actions and their fields (name/type/default)."""
    return {
        name: _action_fields(cls)
        for name, cls in sorted(_actions.ACTION_REGISTRY.items())
    }


def capabilities() -> dict:
    """Return a machine-readable summary of the engine's capabilities."""
    from .tex import TEX_PRESETS

    return {
        "spec_version": _spec_version(),
        "layers": LAYER_TYPES,
        "themes": list(AVAILABLE_THEMES),
        "journals": list(AVAILABLE_JOURNALS),
        "palettes": PALETTE_KINDS,
        "tex_presets": {
            name: {
                "columnwidth_pt": ctx.columnwidth_pt,
                "textwidth_pt": ctx.textwidth_pt,
                "fontsize_pt": ctx.fontsize_pt,
                "columns": ctx.columns,
            }
            for name, ctx in TEX_PRESETS.items()
        },
        "actions": action_vocabulary(),
    }


def _spec_version() -> str:
    from .spec import SPEC_VERSION

    return SPEC_VERSION
