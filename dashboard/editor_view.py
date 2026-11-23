"""Pure HTML rendering for the interactive editor.

No I/O here — every function takes plain data (the current spec, the action
log, an optional error, and a bit of last-render layout info) and returns an
HTML string. This keeps the view layer testable without spinning up a real
HTTP server, and keeps `editor_server.py` a thin wiring layer around it.

``render_page`` returns the full page (used for the initial ``GET /``);
``render_app_body`` returns just the inner content htmx swaps in after every
action, so edits update in place instead of a full page navigation.

English by default (per project convention); this is the human-facing UI.
"""

from __future__ import annotations

import html
import json
from pathlib import Path

from mudplot.actions import (
    ReplaceLayer,
    SetFacetTemplate,
    SetSharedGuides,
    action_to_dict,
)
from mudplot.capabilities import COORDINATE_PIPELINE, LAYER_TYPES, PROJECTIONS
from mudplot.spec import FigureSpec
from mudplot.theme import AVAILABLE_JOURNALS, AVAILABLE_THEMES

from .samples import FIGURE_SAMPLES, SAMPLES

__all__ = ["render_app_body", "render_docs_page", "render_page"]

_PALETTE_KINDS = ("qualitative", "sequential", "diverging")
_SERIES_LAYER_TYPES = ("line", "scatter", "bar", "errorbar", "band")
# focus-scroll:false: htmx otherwise scrolls the refocused element into
# view after a swap, yanking the sidebar away from where the user was.
_SWAP = "innerHTML focus-scroll:false"

_STYLE = """
:root {
  color-scheme: light;
  --bg: #f6f7f9; --panel: #ffffff; --border: #e4e6eb; --text: #1a1d23;
  --muted: #6b7280; --accent: #2563eb; --accent-ink: #ffffff;
  --danger-bg: #fef2f2; --danger-border: #fca5a5; --danger-ink: #991b1b;
  --radius: 10px;
}
* { box-sizing: border-box; }
body { font-family: -apple-system, "Segoe UI", Inter, Helvetica, Arial, sans-serif;
       margin: 0; color: var(--text); background: var(--bg); }
header { padding: .8rem 1.4rem; background: #14161a; color: white;
         display: flex; align-items: baseline; gap: 1rem; flex-wrap: wrap; }
header h1 { margin: 0; font-size: 1.05rem; font-weight: 600; }
header .sub { color: #9aa1ad; font-size: .8rem; flex: 1 1 auto; }
main { padding: 1rem; }
#app-body { display: grid; grid-template-columns: 320px minmax(0, 1fr); gap: 1rem;
       align-items: start; }
.inspector { height: calc(100dvh - 100px); overflow: auto; padding-right: .5rem; }
.workspace { min-width: 0; position: sticky; top: 1rem; }
.workspace > .panel:first-child { min-height: 65vh; background: #e9edf3;
       background-image: radial-gradient(#cbd2dc 1px, transparent 1px);
       background-size: 16px 16px; padding: 1.5rem; }
.workspace figure { display: grid; place-items: center; min-height: 55vh; }
.workspace .preview-wrap { box-shadow: 0 12px 40px #18243a20; }
details summary { cursor: pointer; font-size: .85rem; font-weight: 600;
       padding: .7rem 0; color: var(--text); }
details summary:focus-visible { outline: 2px solid var(--accent); }
@media (max-width: 800px) {
  #app-body { grid-template-columns: minmax(0, 1fr); }
  .workspace { grid-row: 1; position: static; }
  .inspector { height: auto; overflow: visible; }
  .workspace > .panel:first-child { min-height: 0; padding: .5rem; }
  .workspace figure { min-height: 0; }
  header .sub { display: none; }
}
.panel { background: var(--panel); border: 1px solid var(--border);
         border-radius: var(--radius); padding: .9rem 1rem; margin-bottom: .85rem;
         box-shadow: 0 1px 2px rgba(16,24,40,.04); }
.panel h2 { font-size: .82rem; margin: 0 0 .6rem; color: #374151;
            text-transform: uppercase; letter-spacing: .04em; font-weight: 700; }
label, .field-label { display: block; font-size: .78rem; color: var(--muted);
        margin: .55rem 0 .2rem; font-weight: 500; }
label > input, label > select, label > textarea { margin-top: .2rem; }
input, select, textarea { width: 100%; box-sizing: border-box; padding: .4rem .55rem;
       border: 1px solid #d1d5db; border-radius: 6px; font-size: .85rem;
       background: white; color: var(--text); }
input:focus, select:focus, textarea:focus { outline: 2px solid var(--accent);
       outline-offset: 1px; border-color: var(--accent); }
textarea { font-family: ui-monospace, "SF Mono", monospace; min-height: 4.5rem; }
button, a.button-link { margin-top: .6rem; padding: .42rem .85rem; border: none;
         border-radius: 6px; background: var(--accent); color: var(--accent-ink);
         cursor: pointer; font-size: .82rem; font-weight: 600;
         transition: filter .1s ease; }
a.button-link { display: inline-block; text-decoration: none; }
button:hover, a.button-link:hover { filter: brightness(1.08); }
button.secondary, a.button-link.secondary { background: #eef0f3; color: var(--text);
         border: 1px solid #d7dae0; }
button.danger { background: #fff; color: #b91c1c; border: 1px solid #fca5a5; }
.row { display: flex; gap: .5rem; }
.row > * { flex: 1; }
.error { background: var(--danger-bg); border: 1px solid var(--danger-border);
         color: var(--danger-ink); padding: .6rem .8rem; border-radius: var(--radius);
         margin-bottom: 1rem; font-size: .84rem; white-space: pre-wrap; }
figure { margin: 0; text-align: center; }
.preview-wrap { position: relative; display: inline-block; max-width: 100%;
       border: 1px solid var(--border); border-radius: 8px; overflow: visible;
       background: repeating-conic-gradient(
       #f0f1f3 0% 25%, white 0% 50%) 50% / 16px 16px; }
.preview-wrap img { display: block; max-width: 100%; border: 0;
             border-radius: 8px; background: white; }
.log { font-family: ui-monospace, "SF Mono", monospace; font-size: .72rem;
       color: #4b5563; max-height: 220px; overflow: auto; background: #fafbfc;
       padding: .6rem; border-radius: 8px; border: 1px solid var(--border); }
.log div { padding: .18rem 0; border-bottom: 1px solid #eef0f2; word-break: break-all; }
.log div:last-child { border-bottom: none; }
.hint { font-size: .74rem; color: var(--muted); margin-top: .35rem; line-height: 1.4; }
.samples { display: flex; flex-wrap: wrap; gap: .4rem; }
.samples button { margin-top: 0; }
.layer-row { display: flex; justify-content: space-between; align-items: center;
             gap: .5rem; padding: .35rem 0; border-bottom: 1px solid #f0f1f3;
             font-size: .8rem; }
.layer-row:last-child { border-bottom: none; }
.layer-row form { margin: 0; }
.layer-row button { margin-top: 0; padding: .2rem .55rem; font-size: .75rem; }
.layer-row code { background: #f0f1f3; padding: .05rem .35rem; border-radius: 4px; }
.btn-row { display: flex; gap: .5rem; flex-wrap: wrap; }
.panel-btn { min-width: 2.2rem; }
.panel-btn.active { background: var(--accent); color: var(--accent-ink); }
.btn-row form { margin: 0; }
.drag-handle { position: absolute; width: 20px; height: 20px; margin: -10px 0 0 -10px;
       padding: 0; border: 0; border-radius: 50%; display: flex;
       align-items: center; justify-content: center; cursor: grab; font-size: 11px;
       user-select: none; touch-action: none; color: white;
       box-shadow: 0 0 0 2px white, 0 1px 3px rgba(0,0,0,.35); }
.drag-handle:active { cursor: grabbing; }
.drag-handle:focus { outline: 2px solid #0a5; outline-offset: 1px; }
.drag-handle.legend { background: #2563eb; }
.drag-handle.title { background: #7c3aed; }
.drag-handle.layer-at { background: #059669; }
nav.tabs { display: flex; gap: 1.1rem; }
nav.tabs .navtab { color: #9aa1ad; text-decoration: none; font-size: .84rem;
       padding-bottom: .15rem; font-weight: 500; }
nav.tabs .navtab.active { color: white; border-bottom: 2px solid var(--accent); }
.docs { max-width: 880px; margin: 0 auto; padding: 1.4rem 1.6rem; background: white;
       border-radius: var(--radius); border: 1px solid var(--border); }
.docs h1, .docs h2, .docs h3 { color: #1f2430; }
.docs table { border-collapse: collapse; width: 100%; margin: .75rem 0 1.25rem; }
.docs th, .docs td { border: 1px solid #e4e6eb; padding: .4rem .6rem; text-align: left;
       font-size: .86em; }
"""

# The two editors serve the same external, CSP-safe interaction client.
_DRAG_JS = (Path(__file__).parent / "static" / "editor.js").read_text(encoding="utf-8")


def _nav_html(active: str) -> str:
    def tab(href: str, label: str, key: str) -> str:
        cls = " active" if key == active else ""
        current = ' aria-current="page"' if key == active else ""
        return f'<a class="navtab{cls}" href="{href}"{current}>{label}</a>'

    return (
        '<nav class="tabs">'
        + tab("/", "Editor", "editor")
        + tab("/docs", "Docs", "docs")
        + "</nav>"
    )


def _esc(s) -> str:
    return html.escape(str(s))


def _option(value: str, selected: str) -> str:
    sel = " selected" if value == selected else ""
    return f'<option value="{_esc(value)}"{sel}>{_esc(value)}</option>'


def _select(name: str, options, selected: str, extra: str = "") -> str:
    opts = "".join(_option(o, selected) for o in options)
    return f'<select name="{_esc(name)}" {extra}>{opts}</select>'


def _column_datalist(spec: FigureSpec, list_id: str) -> str:
    opts = "".join(f'<option value="{_esc(c)}">' for c in spec.data.columns)
    return f'<datalist id="{list_id}">{opts}</datalist>'


def _field(label: str, control: str) -> str:
    """A label bound to its control.

    Nesting gives the association implicitly, so there are no ids to keep
    unique across fragments that get swapped in and out -- without it a
    screen reader (and any assistive tech) reads an unlabelled input.
    """
    return f"<label>{label}{control}</label>"


def _hx_form(action: str, hidden: dict, body: str, button: str = "Apply") -> str:
    hidden_inputs = "".join(
        f'<input type="hidden" name="{_esc(k)}" value="{_esc(v)}">'
        for k, v in hidden.items()
    )
    return (
        f'<form method="post" action="{_esc(action)}" '
        f'hx-post="{_esc(action)}" hx-target="#app-body" '
        f'hx-swap="{_SWAP}">'
        f"{hidden_inputs}{body}"
        f'<button type="submit">{_esc(button)}</button>'
        "</form>"
    )


def _samples_panel() -> str:
    buttons = "".join(
        _hx_form(
            "/action",
            {"type": "load_sample", "name": name},
            "",
            name,
        ).replace("<button", '<button class="secondary"')
        for name in SAMPLES
    )
    figures = "".join(
        f'<a class="button-link secondary" href="/?example={_esc(name)}#open-figure">'
        f"{_esc(label)}</a>"
        for name, (label, _, _) in FIGURE_SAMPLES.items()
    )
    return (
        f'<div class="panel samples"><h2>Sample data</h2>{buttons}</div>'
        '<div class="panel"><h2>Complete figure drafts</h2>'
        '<p class="hint">Loads the Open form only. Your current figure stays '
        "unchanged until you press Open figure.</p>"
        f'<div class="btn-row">{figures}</div></div>'
    )


def _theme_panel(spec: FigureSpec) -> str:
    theme_select = _select("name", AVAILABLE_THEMES, spec.theme.name)
    theme_form = _hx_form(
        "/action", {"type": "set_theme"}, _field("Theme", theme_select)
    )
    journal_opts = ("none", *AVAILABLE_JOURNALS)
    journal_select = _select("name", journal_opts, spec.journal or "none")
    journal_form = _hx_form(
        "/action", {"type": "set_journal"}, _field("Journal", journal_select)
    )
    body = theme_form + journal_form
    return f'<div class="panel"><h2>Theme &amp; journal</h2>{body}</div>'


def _palette_panel(spec: FigureSpec) -> str:
    p = spec.theme.palette
    kind_select = _select("kind", _PALETTE_KINDS, p.kind)
    body = (
        _field("Kind", kind_select)
        + _field(
            "Hue start",
            f'<input type="number" name="hue_start" value="{p.hue_start:g}" step="1">',
        )
        + _field(
            "Chroma",
            f'<input type="number" name="chroma" value="{p.chroma:g}" step="1">',
        )
        + _field(
            "Lightness",
            f'<input type="number" name="lightness" value="{p.lightness:g}" step="1">',
        )
    )
    form = _hx_form("/action", {"type": "set_palette"}, body)
    return f'<div class="panel"><h2>Palette</h2>{form}</div>'


def _panels_panel(spec: FigureSpec, active: int) -> str:
    """Grid size, plus which panel every other control edits."""
    # layout=None means "1 x n_panels" (the renderer's own default), so show
    # what will actually be drawn rather than a blank field.
    rows, cols = spec.layout or [1, max(len(spec.panels), 1)]
    size_body = (
        '<div class="row"><div>'
        + _field("Rows", f'<input type="number" min="1" name="rows" value="{rows}">')
        + "</div><div>"
        + _field("Columns", f'<input type="number" min="1" name="cols" value="{cols}">')
        + "</div></div>"
    )
    layout_form = _hx_form("/action", {"type": "set_layout"}, size_body, "Set grid")
    projection_form = _hx_form(
        "/action",
        {"type": "set_projection"},
        _field(
            "Active panel projection",
            _select(
                "projection",
                PROJECTIONS,
                spec.panels[active].projection if spec.panels else "2d",
            ),
        ),
        "Set projection",
    )

    n = len(spec.panels)
    if n <= 1:
        picker = '<div class="hint">One panel. Add rows/columns to split it.</div>'
    else:
        buttons = "".join(
            _hx_form(
                "/select-panel",
                {"panel": i},
                "",
                f"{i}: {spec.panels[i].panel_id or '(anonymous)'}",
            ).replace(
                "<button",
                '<button aria-pressed="true" class="panel-btn active"'
                if i == active
                else '<button aria-pressed="false" class="panel-btn secondary"',
            )
            for i in range(n)
        )
        picker = (
            '<div role="group" aria-label="Active panel">'
            '<span class="field-label">Editing panel</span>'
            f'<div class="btn-row">{buttons}</div></div>'
        )
    return (
        f'<div class="panel"><h2>Panels</h2>{layout_form}{picker}'
        f"{projection_form}</div>"
    )


def _layout_panel(spec: FigureSpec, active: int) -> str:
    """Typed public-action forms, not a second layout implementation."""
    from mudplot._layout import allocated_ids

    panel = spec.panels[active]
    ids = [p.panel_id for p in spec.panels]

    def action_form(label, value):
        body = _field(
            label,
            '<textarea name="json" rows="6">'
            + _esc(json.dumps(value, indent=2))
            + "</textarea>",
        )
        return _hx_form("/action/raw", {}, body, label)

    forms = []
    if spec.panel_layout is not None:
        placements = {}
        for item in spec.panels:
            assert item.placement is not None
            placements[item.panel_id] = item.placement.to_dict()
        assert panel.placement is not None
        forms.append(
            action_form(
                "Apply complete panel layout",
                {
                    "type": "SetPanelLayout",
                    "layout": spec.panel_layout.to_dict(),
                    "placements": placements,
                },
            )
        )
        forms.append(
            action_form(
                "Move active panel",
                {
                    "type": "SetPanelPlacement",
                    "panel_id": panel.panel_id,
                    "placement": panel.placement.to_dict(),
                },
            )
        )
    mosaic_ids = allocated_ids(spec)
    forms.append(
        action_form(
            "Apply mosaic",
            {
                "type": "SetMosaic",
                "rows": [mosaic_ids],
                "width_ratios": [1] * len(ids),
            },
        )
    )
    forms.append(
        action_form(
            "Nest current grid",
            {
                "type": "NestLayout",
                "rows": 1,
                "cols": 2,
                "row": 0,
                "col": 0,
                "width_ratios": [3, 1],
            },
        )
    )
    if panel.panel_id is not None:
        forms.append(
            action_form(
                "Add inset panel",
                {
                    "type": "AddInset",
                    "parent": panel.panel_id,
                    "bounds": [0.1, 0.1, 0.3, 0.3],
                },
            )
        )
        forms.append(
            action_form(
                "Rename active panel",
                {
                    "type": "RenamePanel",
                    "panel_id": panel.panel_id,
                    "new_id": panel.panel_id,
                },
            )
        )
        forms.append(
            action_form(
                "Reorder panels",
                {
                    "type": "ReorderPanels",
                    "panel_ids": ids,
                },
            )
        )
        forms.append(
            action_form(
                "Remove active leaf panel",
                {
                    "type": "RemovePanel",
                    "panel_id": panel.panel_id,
                },
            )
        )
    return (
        '<details data-key="panel-layout">'
        "<summary>Layout · mosaic, nested, inset</summary>"
        '<div class="panel"><p class="hint">Edit these typed JSON actions. Mosaic rows '
        "use stable IDs or null empty positions; repeated IDs must form rectangles. "
        "Cell spans use zero-based row/col; inset bounds are parent-axes fractions. "
        "First choose mosaic/nest to assign anonymous panels IDs. All existing IDs "
        "must remain present unless explicitly removed. Nesting, reordering and "
        "placement preserve live facet ownership; removing a live cell leaves "
        "saved materialized views.</p>" + "".join(forms) + "</div></details>"
    )


def _layer_panel(spec: FigureSpec) -> str:
    type_select = _select("layer_type", _SERIES_LAYER_TYPES, "line")
    dl = _column_datalist(spec, "cols")
    available = _esc(", ".join(spec.data.columns)) or "(none — load sample data first)"
    body = (
        _field("Layer type", type_select)
        + _field("x column", '<input name="x" list="cols" placeholder="x">')
        + _field("y column", '<input name="y" list="cols" placeholder="y">')
        + _field(
            "group column (optional)",
            '<input name="group" list="cols" placeholder="">',
        )
        + _field("Legend label (optional)", '<input name="label" placeholder="">')
        + _reference_fields()
        + f"{dl}"
        f'<div class="hint">Available columns: {available}</div>'
    )
    form = _hx_form("/action", {"type": "add_layer"}, body, "Add layer")
    return f'<div class="panel"><h2>Add layer</h2>{form}</div>'


def _reference_fields() -> str:
    """Citation/link metadata, rendered per output format (see mudplot.PREAMBLE)."""
    return (
        _field(
            "Citation key (optional)",
            '<input name="citation" placeholder="fischler1981">',
        )
        + _field(
            "Link (optional)", '<input name="href" placeholder="https://doi.org/...">'
        )
        + '<div class="hint">PGF export turns these into \\figcite{}/\\href{} for '
        "the paper to resolve; SVG makes a clickable link; PNG/PDF ignore them.</div>"
    )


def _annotation_panel() -> str:
    body = (
        _field("Kind", _select("layer_type", ("text", "annotate"), "text"))
        + _field("Text", '<input name="text" placeholder="label">')
        + '<div class="row">'
        + "<div>"
        + _field("x", '<input type="number" step="any" name="x" value="0">')
        + "</div><div>"
        + _field("y", '<input type="number" step="any" name="y" value="0">')
        + "</div></div>"
        + '<div class="hint">Data coordinates -- drag it into place afterwards on '
        + "the preview.</div>"
    )
    form = _hx_form("/action", {"type": "add_layer"}, body, "Add annotation")
    return f'<div class="panel"><h2>Add text / annotation</h2>{form}</div>'


def _all_layers_panel() -> str:
    options = "".join(
        f'<option value="{_esc(name)}">{_esc(name)} — required: '
        f"{_esc(', '.join(meta['required']) or 'none')}</option>"
        for name, meta in LAYER_TYPES.items()
    )
    field_reference = "".join(
        '<div class="layer-field-reference">'
        f"<code>{_esc(name)}</code><br>"
        f"required: {_esc(', '.join(meta['required']) or 'none')}<br>"
        f"optional: {_esc(', '.join(meta['optional']) or 'none')}"
        "</div>"
        for name, meta in LAYER_TYPES.items()
    )
    body = (
        _field("Layer type", f'<select name="layer_type">{options}</select>')
        + _field(
            "Layer fields (JSON object)",
            '<textarea name="layer_json" spellcheck="false">'
            "{\n  &quot;x&quot;: &quot;x&quot;,\n  &quot;y&quot;: &quot;y&quot;\n}"
            "</textarea>",
        )
        + '<div class="hint">The selected type is authoritative. Any '
        "<code>LayerSpec</code> field is accepted, including citation/href and "
        "array-valued at/to/levels/bins. Invalid or unknown fields are rejected."
        "</div>"
        + (
            '<details data-key="coordinate-pipeline"><summary>Coordinate '
            "pipeline</summary>"
        )
        + "<p>Include <code>&quot;transforms&quot;:[{&quot;role&quot;:"
        "&quot;x&quot;,&quot;name&quot;:&quot;log&quot;}]</code> "
        "in Layer fields. On one role choose identity, log, standardize, or log then "
        "standardize. Omit the field or use null to clear. Transforms run before "
        "the statistic; "
        "the layer move and panel scale remain separate.</p><ul>"
        + "".join(
            f"<li><code>{_esc(kind)}</code>: {_esc(', '.join(roles))}</li>"
            for kind, roles in COORDINATE_PIPELINE["roles"].items()
        )
        + "</ul></details>"
        + '<details data-key="layer-fields"><summary>Fields by layer type</summary>'
        + field_reference
        + "</details>"
    )
    form = _hx_form("/action", {"type": "add_layer_json"}, body, "Add layer")
    return f'<div class="panel"><h2>Any layer · advanced</h2>{form}</div>'


def _cluster_cut_panel(layout, active, view_generation):
    controls = []
    for axis, item in layout.get("matrix_cuts", {}).items():
        name = "Row" if axis == "row" else "Column"
        hidden = {
            "type": "set_cluster_cut",
            "panel": active,
            "axis": axis,
            "view_generation": view_generation,
        }
        height = "" if item["height"] is None else item["height"]
        options = ['<option value="">No selected group</option>']
        for leaf in item["items"]:
            index = leaf["index"]
            selected = " selected" if index == item["anchor"] else ""
            options.append(
                f'<option value="{index}"{selected}>'
                f"{_esc(leaf['label'])} [{index}]</option>"
            )
        body = _field(
            f"{name} cut height",
            '<input type="number" min="0" step="any" '
            f'name="height" value="{height}" required>',
        )
        body += _field(
            f"{name} original index",
            '<select name="anchor">' + "".join(options) + "</select>",
        )
        controls.append(_hx_form("/action", hidden, body, f"Apply {name.lower()} cut"))
        partition = item["partition"]
        if partition is not None:
            selected = ", ".join(str(i) for i in partition["selected"]) or "None"
            controls.append(
                '<p class="hint" role="status">'
                f"{name} selected original indices: {selected}</p>"
            )
            controls.append(
                _hx_form(
                    "/action", {**hidden, "clear": "1"}, "", f"Clear {name.lower()} cut"
                )
            )
    if not controls:
        return ""
    return '<div class="panel"><h2>Cluster cuts</h2>' + "".join(controls) + "</div>"


def _layers_panel(spec: FigureSpec, active: int) -> str:
    layers = spec.panels[active].layers if spec.panels else []
    if not layers:
        rows = '<div class="hint">(no layers yet)</div>'
    else:
        parts = []
        for i, layer in enumerate(layers):
            if layer.type in ("text", "annotate"):
                desc = f"{_esc(layer.type)} {_esc(layer.text or '')!r}"
            else:
                desc = (
                    f"{_esc(layer.type)} x={_esc(layer.x) or '-'} "
                    f"y={_esc(layer.y) or '-'}"
                    f"{f' group={_esc(layer.group)}' if layer.group else ''}"
                )
            parts.append(
                '<div class="layer-row">'
                f"<span>{i}: <code>{desc}</code></span>"
                + _hx_form(
                    "/action", {"type": "remove_layer", "layer_index": i}, "", "Remove"
                ).replace("<button", '<button class="danger"')
                + "</div>"
            )
            replacement = json.dumps(
                action_to_dict(ReplaceLayer(i, layer, panel=active)),
                ensure_ascii=False,
                indent=2,
            )
            parts.append(
                f'<details data-key="replace-layer-{active}-{i}">'
                f"<summary>Edit panel {active}, layer {i}</summary>"
                + _hx_form(
                    "/action/raw",
                    {},
                    _field(
                        f"Replace layer {i} · full typed action JSON",
                        '<textarea name="json" rows="8" spellcheck="false">'
                        f"{_esc(replacement)}</textarea>",
                    )
                    + '<div class="hint">Authoritative existing-layer replacement; '
                    "indices and order stay fixed. Regression uses one confidence "
                    "and optional bootstrap {n_boot, seed}, partial "
                    "{columns, reference, method}, sampling {train, query}, "
                    "diagnostics {kind, trend}, components {fit, scatter, "
                    "show_fit, show_scatter}. Edit these inside regression. "
                    "Line predictor/resampling/calibration/family, units, semantics "
                    "and boxen.band_components/hue_components stay independent. "
                    "Coordinate pipeline: edit the ordered transforms list or use "
                    "null to clear. "
                    "This edit changes only this cell.</div>",
                    "Replace layer",
                )
                + "</details>"
            )
        rows = "".join(parts)
    return f'<div class="panel"><h2>Current layers</h2>{rows}</div>'


def _figure_panel(spec: FigureSpec) -> str:
    body = _field("Suptitle", f'<input name="text" value="{_esc(spec.suptitle)}">')
    suptitle_form = _hx_form("/action", {"type": "set_suptitle"}, body, "Set suptitle")
    size_body = (
        '<div class="row"><div>'
        + _field(
            "Width (in)",
            f'<input type="number" step="0.1" name="width" value="{spec.size[0]:g}">',
        )
        + "</div><div>"
        + _field(
            "Height (in)",
            f'<input type="number" step="0.1" name="height" value="{spec.size[1]:g}">',
        )
        + "</div></div>"
    )
    size_form = _hx_form("/action", {"type": "set_size"}, size_body, "Set size")
    shared_action = json.dumps(
        action_to_dict(SetSharedGuides(spec.shared_guides)),
        ensure_ascii=False,
        indent=2,
    )
    shared_form = (
        '<details data-key="shared-guides">'
        "<summary>Figure-wide shared semantic guides</summary>"
        '<p class="hint">One authoritative request list. Membership is the stored '
        "SemanticSpec.scale_id, across every compatible member "
        "and empty facet template. "
        'Use guides: [{"scale_id": "your-scope"}]; null clears all requests. '
        "Each strict request also accepts location (outside right/top/bottom), title, "
        "frame and a finite [x,y] figure-fraction bbox_to_anchor. Dataset labels and "
        "unrelated scales remain panel-owned.</p>"
        + _hx_form(
            "/action/raw",
            {},
            _field(
                "SetSharedGuides · populated authoritative action",
                '<textarea name="json" rows="9" spellcheck="false">'
                + _esc(shared_action)
                + "</textarea>",
            ),
            "Set shared guides",
        )
        + "</details>"
    )
    template_form = ""
    if spec.facet_template is not None:
        template_action = json.dumps(
            action_to_dict(SetFacetTemplate(spec.facet_template.template)),
            ensure_ascii=False,
            indent=2,
        )
        template_form = (
            '<details data-key="live-facet-template">'
            "<summary>Whole live facet template</summary>"
            '<p class="hint">Saved panels are authoritative local views. This explicit '
            "whole-template action replaces every frozen cell and supersedes local "
            "overrides, preserving selectors, N13 IDs/placements "
            "and shared-guide membership. "
            "SetData and reopening never apply it automatically. Omitted same-channel "
            "orders retain reservations; reset_orders recaptures them. "
            "Edit the layers' transforms here to update all fixed cells.</p>"
            + _hx_form(
                "/action/raw",
                {},
                _field(
                    "SetFacetTemplate · populated authoritative action",
                    '<textarea name="json" rows="14" spellcheck="false">'
                    + _esc(template_action)
                    + "</textarea>",
                ),
                "Replace whole facet template",
            )
            + "</details>"
        )
    return (
        f'<div class="panel"><h2>Figure</h2>{suptitle_form}{size_form}'
        f"{shared_form}{template_form}</div>"
    )


def _labels_panel(spec: FigureSpec, active: int) -> str:
    if not spec.panels:
        return ""
    panel = spec.panels[active]
    forms = []
    for key, label, value in (
        ("title", "Panel title", panel.title),
        ("x", "X-axis label", panel.x.label),
        ("y", "Y-axis label", panel.y.label),
    ):
        fields = {"type": "set_title", "panel": active}
        if key != "title":
            fields.update(type="set_axis_label", axis=key)
        body = _field(label, f'<input name="text" value="{_esc(value)}">')
        if key == "title":
            body += _reference_fields_prefilled(panel)
        forms.append(_hx_form("/action", fields, body, "Apply"))
    return (
        '<div class="panel"><h2>Titles &amp; axes</h2>'
        f'<p class="hint">Editing panel {active + 1}. Empty text clears a label.</p>'
        + "".join(forms)
        + "</div>"
    )


def _axis_controls_panel(spec: FigureSpec, active: int) -> str:
    if not spec.panels:
        return ""
    panel = spec.panels[active]

    def limits_inputs(axis) -> str:
        lo, hi = axis.limits if axis is not None and axis.limits else ("", "")
        return (
            '<div class="row"><div>'
            + _field(
                "Lower limit",
                f'<input type="number" step="any" name="lo" value="{_esc(lo)}">',
            )
            + "</div><div>"
            + _field(
                "Upper limit",
                f'<input type="number" step="any" name="hi" value="{_esc(hi)}">',
            )
            + "</div></div>"
        )

    forms = []
    axes = [("x", panel.x), ("y", panel.y)]
    if panel.y2 is not None:
        axes.append(("y2", panel.y2))
    if panel.z is not None:
        axes.append(("z", panel.z))
    for name, axis in axes:
        forms.append(f'<div class="field-label">{name.upper()} axis</div>')
        if name in ("y2", "z"):
            forms.append(
                _hx_form(
                    "/action",
                    {"type": "set_axis_label", "axis": name},
                    _field("Label", f'<input name="text" value="{_esc(axis.label)}">'),
                    "Apply label",
                )
            )
        forms.append(
            _hx_form(
                "/action",
                {"type": "set_scale", "axis": name},
                _field(
                    "Scale",
                    _select(
                        "scale",
                        ("linear", "log", "symlog", "asinh", "logit")
                        if panel.projection == "2d" and name != "z"
                        else ("linear", "log"),
                        axis.scale,
                    ),
                ),
                "Apply scale",
            )
        )
        forms.append(
            _hx_form(
                "/action",
                {"type": "set_limits", "axis": name},
                limits_inputs(axis),
                "Apply limits",
            )
        )

    if panel.projection == "2d":
        if panel.y2 is None:
            forms.append(
                _hx_form(
                    "/action",
                    {"type": "set_secondary_axis"},
                    "",
                    "Enable secondary axis",
                )
            )
        else:
            forms.append(
                _hx_form(
                    "/action",
                    {"type": "clear_secondary_axis"},
                    "",
                    "Remove secondary axis",
                )
            )
    if panel.projection == "3d" and panel.z is None:
        forms.append(_hx_form("/action", {"type": "set_z_axis"}, "", "Set up z axis"))

    return (
        '<div class="panel"><h2>Axis scales &amp; limits</h2>'
        '<p class="hint">Leave both limits blank for automatic limits.</p>'
        + "".join(forms)
        + "</div>"
    )


def _reference_fields_prefilled(panel) -> str:
    return _field(
        "Citation key (optional)",
        f'<input name="citation" value="{_esc(panel.title_citation or "")}">',
    ) + _field(
        "Link (optional)",
        f'<input name="href" value="{_esc(panel.title_href or "")}">',
    )


def _position_panel(spec: FigureSpec, active: int) -> str:
    """Drag-to-position toggles for the legend and the panel title."""
    panel = spec.panels[active] if spec.panels else None
    leg_active = panel is not None and panel.legend.bbox_to_anchor is not None
    title_active = panel is not None and panel.title_position is not None

    def row(label: str, kind: str, is_set: bool, default_xy=(0.8, 0.5)) -> str:
        enable = _hx_form(
            "/action",
            {
                "type": f"set_{kind}_position",
                "x": f"{default_xy[0]:g}",
                "y": f"{default_xy[1]:g}",
                "panel": active,
            },
            "",
            "Enable" if not is_set else "Re-centre",
        ).replace("<button", '<button class="secondary"')
        reset = (
            _hx_form(
                "/action",
                {"type": f"reset_{kind}_position", "panel": active},
                "",
                "Reset",
            )
            if is_set
            else ""
        )
        # a group of buttons, not one control: labelled as a group rather
        # than with a <label>, which must point at a single form element
        return (
            f'<div role="group" aria-label="{_esc(label)} position">'
            f'<span class="field-label">{label}</span>'
            f'<div class="btn-row">{enable}{reset}</div></div>'
        )

    body = row("Legend", "legend", leg_active)
    if panel is None or panel.projection != "3d":
        body += row("Title", "title", title_active, default_xy=(0.5, 0.9))
    body += (
        '<div class="hint">Once enabled, drag the coloured handle on the '
        "preview, or click it and use the arrow keys (Shift = bigger step). "
        "Titles support Cartesian/polar axes fractions; text/annotation data "
        "dragging supports Cartesian 2-D panels. 3-D title/data dragging is "
        "unavailable.</div>"
    )
    return f'<div class="panel"><h2>Position (drag on preview)</h2>{body}</div>'


def _history_panel() -> str:
    def btn(action: str, label: str) -> str:
        return _hx_form(action, {}, "", label).replace(
            "<button ", '<button class="secondary" ', 1
        )

    buttons = btn("/undo", "Undo") + btn("/redo", "Redo") + btn("/reset", "Reset")
    return (
        f'<div class="panel"><h2>History</h2><div class="btn-row">{buttons}</div></div>'
    )


def _advanced_panel() -> str:
    example = (
        "{&quot;type&quot;: &quot;SetTitle&quot;, &quot;text&quot;: &quot;t&quot;}"
    )
    body = _field(
        f"Raw JSON action (agent-facing) &mdash; e.g. <code>{example}</code>",
        '<textarea name="json"></textarea>',
    )
    form = _hx_form("/action/raw", {}, body, "Dispatch JSON action")
    return f'<div class="panel"><h2>Advanced</h2>{form}</div>'


def _open_panel(draft_json: str = "") -> str:
    """Open a saved .mplot.json (the same file the Export card writes)."""
    body = _field(
        "Spec file",
        '<input type="file" accept=".json,.mplot.json,application/json" '
        'id="spec-file">',
    ) + _field(
        "Spec JSON",
        '<textarea name="json" id="spec-json" placeholder="...or paste the '
        f'spec JSON here">{_esc(draft_json)}</textarea>',
    )
    form = _hx_form("/open", {}, body, "Open figure").replace(
        "<form ", '<form hx-replace-url="/" ', 1
    )
    return (
        '<div class="panel"><h2>Open</h2>'
        + form
        + (
            '<p class="hint" role="status">Draft not applied yet.</p>'
            if draft_json
            else ""
        )
        + '<div class="hint">Replaces the current figure. Undo history starts '
        "fresh, so export first if the current one matters.</div></div>"
    )


def _export_panel() -> str:
    links = "".join(
        f'<a class="button-link secondary" href="{href}" download="{name}">{label}</a>'
        for href, name, label in (
            ("/fig.pdf", "figure.pdf", "PDF (vector)"),
            ("/fig.svg", "figure.svg", "SVG (vector)"),
            ("/fig.png", "figure.png", "PNG"),
            ("/spec.json", "figure.mplot.json", "Spec (.json)"),
        )
    )
    return (
        '<div class="panel"><h2>Export</h2>'
        f'<div class="btn-row">{links}</div>'
        '<div class="hint">PDF/SVG are rendered at the exact configured '
        "figure size for TeX placement; the PNG is the preview raster.</div>"
        "</div>"
    )


def _action_log_html(action_log: list[dict]) -> str:
    if not action_log:
        return '<div class="log">(no actions yet)</div>'
    rows = "".join(f"<div>{_esc(json.dumps(a))}</div>" for a in reversed(action_log))
    return f'<div class="log">{rows}</div>'


def _drag_handle_html(
    *,
    kind: str,
    label: str,
    symbol: str,
    img_x: float,
    img_y: float,
    extra_data: dict,
    fields: dict,
) -> str:
    data_attrs = " ".join(f'data-{k}="{_esc(v)}"' for k, v in extra_data.items())
    field_attrs = " ".join(
        f'data-field{i}="{_esc(k)}={_esc(v)}"'
        for i, (k, v) in enumerate(fields.items())
    )
    # Stable across swaps, so keyboard focus can be restored onto the same
    # handle after the edit it just dispatched replaced the whole overlay.
    identity = extra_data.get("panel-id", fields.get("panel", 0))
    handle_id = f"{kind}:{fields.get('layer_index', '')}:{identity}"
    instruction = f"Move {label}; drag or use arrow keys"
    return (
        f'<button type="button" class="drag-handle {kind}" '
        f'aria-label="{_esc(instruction)}" data-handle-id="{_esc(handle_id)}" '
        f'data-imgx="{img_x:.17g}" data-imgy="{img_y:.17g}" '
        f'style="left:{img_x * 100:g}%; top:{(1 - img_y) * 100:g}%" '
        f"{data_attrs} {field_attrs} "
        f'title="{_esc(instruction)}">{symbol}</button>'
    )


def _preview_handles_html(
    spec: FigureSpec, layout: dict, active: int, view_generation: int = 0
) -> str:
    """Overlay the exact native artist anchors extracted with the saved PNG."""
    handles = []
    for entry in layout.get("handles", []):
        kind = entry["kind"]
        panel = spec.panels[active]
        if kind == "legend" and panel.legend.bbox_to_anchor is None:
            continue
        if kind == "title" and panel.title_position is None:
            continue
        fields = {
            "type": "set_layer_at" if kind == "layer-at" else f"set_{kind}_position",
            "panel": active,
        }
        extra = {
            "space": "figure" if kind == "legend" else "axes",
            "post-url": "/action",
        }
        if panel.panel_id is not None:
            extra["panel-id"] = panel.panel_id
        extra["bbox"] = json.dumps(
            layout["figure_bbox"] if kind == "legend" else layout["panel_bbox"]
        )
        if kind == "layer-at":
            fields["layer_index"] = entry["layer_index"]
            extra.update(
                {
                    "data": "1",
                    "xlim": json.dumps(entry["xlim"]),
                    "ylim": json.dumps(entry["ylim"]),
                    "xscale": entry["xscale"],
                    "yscale": entry["yscale"],
                }
            )
            extra["bbox"] = json.dumps(entry["bbox"])
        fields["view_generation"] = view_generation
        handles.append(
            _drag_handle_html(
                kind=kind,
                label=entry.get("label", "panel title" if kind == "title" else kind),
                symbol="T" if kind == "title" else "✥" if kind == "legend" else "•",
                img_x=entry["imgx"],
                img_y=entry["imgy"],
                extra_data=extra,
                fields=fields,
            )
        )
    return "".join(handles)


def render_app_body(
    spec: FigureSpec,
    action_log: list[dict],
    layout: dict | None = None,
    *,
    error: str | None = None,
    active_panel: int = 0,
    draft_json: str = "",
    view_generation: int = 0,
) -> str:
    """The inner ``#app-body`` content: everything htmx swaps after an
    action, and what ``render_page`` embeds for the first load.

    ``active_panel`` is which panel the side controls edit; it is editor
    state, not figure state, so it is passed in rather than read off the
    spec.
    """
    layout = layout or {}
    active = min(active_panel, max(len(spec.panels) - 1, 0))
    error_html = f'<div class="error" role="alert">{_esc(error)}</div>' if error else ""
    open_attr = " open" if draft_json else ""
    left = (
        '<details data-key="samples"><summary>Start from a sample</summary>'
        + _samples_panel()
        + "</details>"
        + _figure_panel(spec)
        + _panels_panel(spec, active)
        + _layout_panel(spec, active)
        + _labels_panel(spec, active)
        + _axis_controls_panel(spec, active)
        + _theme_panel(spec)
        + _palette_panel(spec)
        + _layer_panel(spec)
        + _annotation_panel()
        + '<details data-key="all-layers"><summary>Add any layer</summary>'
        + _all_layers_panel()
        + "</details>"
        + _layers_panel(spec, active)
        + _cluster_cut_panel(layout, active, view_generation)
        + _position_panel(spec, active)
        + _history_panel()
        + '<details data-key="advanced"><summary>Advanced · JSON actions</summary>'
        + _advanced_panel()
        + "</details>"
        + _export_panel()
        + f'<details id="open-figure" data-key="open"{open_attr}>'
        "<summary>Open a saved figure</summary>"
        + _open_panel(draft_json)
        + "</details>"
    )
    handles_html = _preview_handles_html(spec, layout, active, view_generation)
    drag_status = (
        f'<p class="hint" role="status">{_esc(layout["data_drag_reason"])}</p>'
        if layout.get("data_drag_reason")
        else ""
    )
    right = (
        '<div class="panel"><h2>Preview</h2><figure><div class="preview-wrap">'
        f'<img src="/fig.png?view_generation={view_generation}" alt="figure preview">'
        f"{handles_html}</div></figure>"
        f"{drag_status}"
        '<p class="hint">Preview fits this workspace. Check exported dimensions '
        "and the actual-size reading examples separately.</p></div>"
        '<details class="panel" data-key="history"><summary>Action history · '
        f"{len(action_log)} actions</summary>"
        f"{_action_log_html(action_log)}</details>"
    )
    return (
        '<aside class="inspector" aria-label="Figure properties">'
        f"{error_html}{left}</aside>"
        f'<section class="workspace" aria-label="Figure canvas">{right}</section>'
    )


def render_page(
    spec: FigureSpec,
    action_log: list[dict],
    layout: dict | None = None,
    *,
    error: str | None = None,
    active_panel: int = 0,
    draft_json: str = "",
    view_generation: int = 0,
) -> str:
    """Render the full editor page (used for the initial ``GET /`` only)."""
    body = render_app_body(
        spec,
        action_log,
        layout,
        error=error,
        active_panel=active_panel,
        draft_json=draft_json,
        view_generation=view_generation,
    )
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="htmx-config"
      content='{{"selfRequestsOnly":true,"allowScriptTags":false,"allowEval":false}}'>
<title>mudplot editor</title>
<script src="/static/htmx.min.js"></script>
<style>{_STYLE}</style>
</head>
<body hx-history="false">
<header>
  <h1>mudplot editor</h1>
  <div class="sub">Figure studio · Edit, refine, export</div>
  {_nav_html("editor")}
</header>
<main><div id="app-body">{body}</div></main>
<script src="/static/editor.js"></script>
</body>
</html>"""


def render_docs_page(body_html: str) -> str:
    """Wrap the engine reference (already-rendered HTML body) in the same
    page shell/nav as the editor, as a separate tab rather than a separate
    process/command.
    """
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>mudplot docs</title>
<style>{_STYLE}</style>
</head>
<body>
<header>
  <h1>mudplot editor</h1>
  <div class="sub">Engine reference, generated live from
  <code>mudplot.reference_markdown()</code> — never hand-written, never stale.</div>
  {_nav_html("docs")}
</header>
<main style="display:block">
  <div class="docs">{body_html}</div>
</main>
</body>
</html>"""
