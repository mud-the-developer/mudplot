"""mudplot — perceptually-uniform, colorblind-safe plotting for papers.

The pure engine (spec / actions / reducer / store / io / tex sizing) has **no
third-party dependencies** and is importable on its own. Anything that needs
numpy (``color``) or matplotlib (``render`` / ``tex_preview``) is loaded lazily
on first access, so ``import mudplot`` stays dependency-free.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

# -- pure engine: zero third-party dependencies (eager) --------------------
from . import actions
from .actions import action_from_dict, action_to_dict
from .api import Plot, apply, color_palette, plot
from .capabilities import capabilities
from .docs import reference_markdown
from .io import from_json, load_spec, save_spec, to_json
from .reducer import reduce, reduce_all
from .schema import json_schema
from .spec import FigureSpec
from .store import Store
from .tex import TEX_PRESETS, TexContext, figsize_for
from .validate import assert_valid, validate

__version__ = "0.0.1"

# -- effect layer: needs numpy / matplotlib (lazy via PEP 562) -------------
_LAZY = {
    "color": "mudplot.color",
    "render": "mudplot.render:render",
    "save": "mudplot.render:save",
    "tex_preview": "mudplot.tex:tex_preview",
}

if TYPE_CHECKING:  # help type checkers/IDEs see the lazy names
    from . import color
    from .render import render, save
    from .tex import tex_preview


def __getattr__(name: str):
    import importlib

    target = _LAZY.get(name)
    if target is None:
        raise AttributeError(f"module 'mudplot' has no attribute {name!r}")
    mod_name, _, _attr = target.partition(":")
    mod = importlib.import_module(mod_name)
    # Importing a submodule has the side effect of binding it onto this
    # package's namespace under *its own* name -- e.g. importing
    # "mudplot.render" sets ``mudplot.render`` to that submodule directly in
    # mudplot.__dict__, bypassing __getattr__ entirely on every future
    # lookup. When a _LAZY key shares a name with its submodule ("render"
    # does), or when resolving a *different* key that happens to import the
    # same submodule (e.g. "save" also lives in mudplot.render), that side
    # effect pre-emptively squats on the "render" slot with the raw module
    # instead of the function -- so a plain "cache what I just resolved"
    # fix isn't enough; every _LAZY entry backed by this same submodule has
    # to be fixed up together, in one pass, regardless of which one was
    # actually requested.
    for key, other_target in _LAZY.items():
        other_mod_name, _, other_attr = other_target.partition(":")
        if other_mod_name == mod_name:
            globals()[key] = getattr(mod, other_attr) if other_attr else mod
    return globals()[name]


def __dir__():
    return sorted([*globals(), *_LAZY])


__all__ = [
    "TEX_PRESETS",
    "FigureSpec",
    "Plot",
    "Store",
    "TexContext",
    "action_from_dict",
    "action_to_dict",
    "actions",
    "apply",
    "assert_valid",
    "capabilities",
    "color",
    "color_palette",
    "figsize_for",
    "from_json",
    "json_schema",
    "load_spec",
    "plot",
    "reduce",
    "reduce_all",
    "reference_markdown",
    "render",
    "save",
    "save_spec",
    "tex_preview",
    "to_json",
    "validate",
]
