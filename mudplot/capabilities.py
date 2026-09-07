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

__all__ = [
    "BACKEND_CAPABILITIES",
    "LAYER_TYPES",
    "PALETTE_KINDS",
    "PALETTE_PRESETS",
    "capabilities",
]

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

# Named, pre-verified qualitative presets (see mudplot.color.palette for the
# generator that consumes these). Kept here, not in mudplot.color.palette,
# so this plain data stays reachable without importing numpy -- capabilities()
# is part of the dependency-free pure core (see tests/test_no_deps.py).
PALETTE_PRESETS: dict[str, dict] = {
    # General-purpose default: verified CVD-safe + true-greyscale-safe for
    # n=3..6 categories (see tests/test_palette_presets.py).
    "paper": {
        "params": {
            "lightness": 60.0,
            "chroma": 58.0,
            "hue_start": 270.0,
            "lightness_jitter": 18.0,
        },
        "max_verified_n": 6,
        "description": "Balanced default; safe for up to 6 categories.",
    },
    # Higher chroma for slides/posters; also verified for n=3..6.
    "vivid": {
        "params": {
            "lightness": 68.0,
            "chroma": 52.0,
            "hue_start": 315.0,
            "lightness_jitter": 18.0,
        },
        "max_verified_n": 6,
        "description": "More saturated; safe for up to 6 categories.",
    },
    # Lower-chroma, lighter set for large-area fills (bar/heatmap
    # backgrounds) where full saturation is visually too heavy; only
    # verified safe up to n=5 -- combine with .encoding(hatches=[...]) or
    # more categories.
    "soft": {
        "params": {
            "lightness": 68.0,
            "chroma": 36.0,
            "hue_start": 280.0,
            "lightness_jitter": 18.0,
        },
        "max_verified_n": 5,
        "description": "Muted/pastel; safe for up to 5 categories.",
    },
}


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


# What each output format actually preserves. Reference metadata
# (citation/href) is backend-dependent -- raster formats can only show
# plain text, SVG can make an entry a clickable link, and PGF emits real
# \figcite{...}/\href{...}{...} macros the *document* resolves at TeX-compile
# time. Exposed so an agent/editor can warn e.g. "citations are only kept in
# PGF export" instead of that being implicit renderer behaviour.
BACKEND_CAPABILITIES = {
    "png": {
        "vector": False,
        "citations": False,
        "hyperlinks": False,
        "requires_tex": False,
    },
    "pdf": {
        "vector": True,
        "citations": False,
        "hyperlinks": False,
        "requires_tex": False,
    },
    "svg": {
        "vector": True,
        "citations": False,
        "hyperlinks": True,
        "requires_tex": False,
    },
    "pgf": {
        "vector": True,
        "citations": True,
        "hyperlinks": True,
        "requires_tex": True,
    },
}


def _journal_profiles() -> dict:
    """Merged view of a journal name that has *both* a style (``.journal()``,
    ``theme.AVAILABLE_JOURNALS``/``journal_overrides()``) and a known TeX
    document geometry (``.tex_size()``, ``tex.TEX_PRESETS``) -- these are
    two independently-maintained registries for two different concerns (a
    theme's rcParams vs. a document class's column widths), which happen to
    overlap for names that are both a journal *and* a well-known LaTeX
    class. Combined here so an agent doesn't have to separately cross-
    reference "journals" and "tex_presets" to build a coherent look for one
    named journal. A ``tex_presets`` name with no matching journal theme
    (e.g. "article"/"revtex"/"acm" -- generic document classes, not house
    styles) is intentionally *not* included here; see each section on its
    own for the full list either registry supports independently.
    """
    from .tex import TEX_PRESETS
    from .theme import JOURNAL_SIZES, journal_overrides

    profiles = {}
    for name in AVAILABLE_JOURNALS:
        ctx = TEX_PRESETS.get(name)
        if ctx is None:
            continue
        rc = journal_overrides(name)
        profiles[name] = {
            "figure_size_in": JOURNAL_SIZES.get(name),
            "base_font_pt": rc.get("font.size"),
            "tick_font_pt": rc.get("xtick.labelsize"),
            "line_width_pt": rc.get("axes.linewidth"),
            "columnwidth_pt": ctx.columnwidth_pt,
            "textwidth_pt": ctx.textwidth_pt,
            "columns": ctx.columns,
        }
    return profiles


def capabilities() -> dict:
    """Return a machine-readable summary of the engine's capabilities."""
    from .tex import TEX_PRESETS

    return {
        "spec_version": _spec_version(),
        "layers": LAYER_TYPES,
        "themes": list(AVAILABLE_THEMES),
        "journals": list(AVAILABLE_JOURNALS),
        "palettes": PALETTE_KINDS,
        "palette_presets": PALETTE_PRESETS,
        "backends": BACKEND_CAPABILITIES,
        "tex_presets": {
            name: {
                "columnwidth_pt": ctx.columnwidth_pt,
                "textwidth_pt": ctx.textwidth_pt,
                "fontsize_pt": ctx.fontsize_pt,
                "columns": ctx.columns,
            }
            for name, ctx in TEX_PRESETS.items()
        },
        "journal_profiles": _journal_profiles(),
        "actions": action_vocabulary(),
    }


def _spec_version() -> str:
    from .spec import SPEC_VERSION

    return SPEC_VERSION
