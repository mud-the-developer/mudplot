"""Auto-generated documentation from the engine's own introspection.

The same data that powers ``capabilities()`` / ``json_schema()`` for AI agents
is turned into human-readable Markdown here — one source of truth, two
audiences. Pure and dependency-free; used by the CLI (``mudplot docs``) and by
``dashboard/`` to render a reference page alongside the interactive editor.
"""

from __future__ import annotations

from .capabilities import capabilities
from .theme import JOURNAL_SIZES, journal_overrides

__all__ = ["reference_markdown"]


def _layers_section(caps: dict) -> str:
    lines = ["## Layers\n"]
    for name, spec in sorted(caps["layers"].items()):
        req = ", ".join(f"`{f}`" for f in spec["required"]) or "—"
        opt = ", ".join(f"`{f}`" for f in spec["optional"]) or "—"
        lines.append(f"### `{name}`\n")
        lines.append(f"- **required**: {req}")
        lines.append(f"- **optional**: {opt}\n")
    return "\n".join(lines)


def _actions_section(caps: dict) -> str:
    lines = ["## Actions (JSON action vocabulary)\n"]
    lines.append("Every mutation is one of these — send as ")
    lines.append('`{"type": "<Name>", ...}` to `mp.apply([...])`.\n')
    for name, field_list in sorted(caps["actions"].items()):
        lines.append(f"### `{name}`\n")
        lines.append("| field | type | required | default |")
        lines.append("|---|---|---|---|")
        for f in field_list:
            lines.append(
                f"| `{f['name']}` | `{f['type']}` | {f['required']} | "
                f"`{f['default']!r}` |"
            )
        lines.append("")
    return "\n".join(lines)


def _themes_section(caps: dict) -> str:
    lines = ["## Themes\n", f"Available presets: {', '.join(caps['themes'])}.\n"]
    lines.append("## Journals\n")
    for name in caps["journals"]:
        rc = journal_overrides(name)
        size = JOURNAL_SIZES.get(name)
        fs = rc.get("font.size")
        lines.append(f"- **{name}**: default figure size {size}, base font {fs}pt")
    lines.append("")
    return "\n".join(lines)


def _palettes_section(caps: dict) -> str:
    lines = ["## Palettes\n"]
    lines.append(
        "LCH-based, colourblind-safe by default. Kinds: "
        + ", ".join(f"`{k}`" for k in caps["palettes"])
        + ".\n"
    )
    lines.append(
        "- `qualitative`: equal(-ish) lightness, maximum hue contrast, "
        "worst-case ΔE00 across normal + CVD vision maximised. A small "
        "`lightness_jitter` (default 6) keeps greyscale/print distinguishable.\n"
        "- `sequential` / `diverging`: perceptually-uniform ramps, gamut-clipped.\n"
    )
    return "\n".join(lines)


def _tex_section(caps: dict) -> str:
    lines = ["## TeX presets (WYSIWYG sizing)\n"]
    lines.append("| preset | columnwidth (pt) | textwidth (pt) | font (pt) | cols |")
    lines.append("|---|---|---|---|---|")
    for name, p in sorted(caps["tex_presets"].items()):
        lines.append(
            f"| `{name}` | {p['columnwidth_pt']} | {p['textwidth_pt']} | "
            f"{p['fontsize_pt']} | {p['columns']} |"
        )
    lines.append("")
    return "\n".join(lines)


def reference_markdown() -> str:
    """Render the full engine reference as a Markdown document."""
    caps = capabilities()
    parts = [
        "# mudplot engine reference\n",
        "_Auto-generated from `mudplot.capabilities()` / `mudplot.json_schema()` "
        f"— spec version `{caps['spec_version']}`. Do not edit by hand; "
        "regenerate with `python -m mudplot docs`._\n",
        _layers_section(caps),
        _palettes_section(caps),
        _themes_section(caps),
        _tex_section(caps),
        _actions_section(caps),
    ]
    return "\n".join(parts)
