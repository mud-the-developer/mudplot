"""mudplot — perceptually-uniform, colorblind-safe plotting for papers.

The pure engine (spec / actions / reducer / store / io / tex sizing) has **no
third-party dependencies** and is importable on its own. Anything that needs
numpy (``color``) or matplotlib (``render`` / ``tex_preview``, implemented in
the underscore-prefixed ``mudplot._render``) is loaded lazily on first
access, so ``import mudplot`` stays dependency-free.
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

__version__ = "0.2.0"

# -- effect layer: needs numpy / matplotlib (lazy via PEP 562) -------------
#
# IMPORTANT: none of these keys may equal the *last component* of their own
# backing submodule's dotted name (e.g. a key "render" backed by module
# "mudplot.render" would be unsafe). Importing a submodule has the side
# effect of binding it onto the parent package's namespace under its own
# name -- Python does this for *any* import of that submodule, including a
# plain "from .render import x" somewhere else in the codebase, not just
# through this __getattr__ -- so a colliding key would eventually get
# silently overwritten with the raw module instead of the intended
# attribute, breaking every subsequent access with "'module' object is not
# callable". This is why the rendering implementation lives in the
# underscore-prefixed ``mudplot._render`` rather than ``mudplot.render``:
# there is no way to "fix" this collision from the __getattr__ side (undoing
# an import side effect after every possible import site is not tractable),
# only to avoid it by construction.
_LAZY = {
    "color": "mudplot.color",
    "render": "mudplot._render:render",
    "save": "mudplot._render:save",
    "tex_preview": "mudplot.tex:tex_preview",
}

if TYPE_CHECKING:  # help type checkers/IDEs see the lazy names
    from . import color
    from ._render import render, save
    from .tex import tex_preview


def __getattr__(name: str):
    import importlib

    target = _LAZY.get(name)
    if target is None:
        raise AttributeError(f"module 'mudplot' has no attribute {name!r}")
    mod_name, _, _attr = target.partition(":")
    mod = importlib.import_module(mod_name)
    # Defensive belt-and-suspenders: fix up every _LAZY entry backed by the
    # same submodule in one pass (not just the one requested), in case a
    # future entry ever collides the way described above.
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
