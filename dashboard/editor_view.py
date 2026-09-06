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
import math

from mudplot.spec import FigureSpec
from mudplot.theme import AVAILABLE_JOURNALS, AVAILABLE_THEMES

from .samples import SAMPLES

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
button { margin-top: .6rem; padding: .42rem .85rem; border: none; border-radius: 6px;
         background: var(--accent); color: var(--accent-ink); cursor: pointer;
         font-size: .82rem; font-weight: 600; transition: filter .1s ease; }
button:hover { filter: brightness(1.08); }
button.secondary { background: #eef0f3; color: var(--text); border: 1px solid #d7dae0; }
button.danger { background: #fff; color: #b91c1c; border: 1px solid #fca5a5; }
.row { display: flex; gap: .5rem; }
.row > * { flex: 1; }
.error { background: var(--danger-bg); border: 1px solid var(--danger-border);
         color: var(--danger-ink); padding: .6rem .8rem; border-radius: var(--radius);
         margin-bottom: 1rem; font-size: .84rem; white-space: pre-wrap; }
figure { margin: 0; text-align: center; }
.preview-wrap { position: relative; display: inline-block; max-width: 100%;
       border-radius: 8px; overflow: visible; background: repeating-conic-gradient(
       #f0f1f3 0% 25%, white 0% 50%) 50% / 16px 16px; }
.preview-wrap img { display: block; max-width: 100%; border: 1px solid var(--border);
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
       border-radius: 50%; display: flex; align-items: center; justify-content: center;
       cursor: grab; font-size: 11px; user-select: none; color: white;
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

# Generic drag-handle system: any element with class "drag-handle" and the
# data-* attributes below wires up the same way, whether it represents the
# legend, a title, or a text/annotate layer's anchor point. Coordinates are
# resolved through one of two spaces (see data-space):
#   "figure" -- 0..1 directly over the whole preview image (legend).
#   "axes"   -- 0..1 within the panel-0 axes' own box, further mapped to
#               data values (with log-scale support) if data-data="1"
#               (title uses axes-fraction directly; text/annotate layers
#               use the data-coordinate mapping).
_DRAG_SCRIPT = """
<script>
(function () {
  function scaleInverse(f, lo, hi, scale) {
    if (scale === "log") {
      var a = Math.log10(lo), b = Math.log10(hi);
      return Math.pow(10, a + f * (b - a));
    }
    return lo + f * (hi - lo);
  }
  function scaleForward(v, lo, hi, scale) {
    if (scale === "log") {
      var a = Math.log10(lo), b = Math.log10(hi);
      return (Math.log10(v) - a) / (b - a);
    }
    return (v - lo) / (hi - lo);
  }
  window.__mudplotScaleForward = scaleForward;
  window.__mudplotScaleInverse = scaleInverse;

  function wireHandle(handle) {
    var wrap = handle.closest(".preview-wrap");
    var space = handle.dataset.space;
    var bbox = handle.dataset.bbox ? JSON.parse(handle.dataset.bbox) : null;
    var xlim = handle.dataset.xlim ? JSON.parse(handle.dataset.xlim) : null;
    var ylim = handle.dataset.ylim ? JSON.parse(handle.dataset.ylim) : null;
    var xscale = handle.dataset.xscale || "linear";
    var yscale = handle.dataset.yscale || "linear";
    var isData = handle.dataset.data === "1";

    function toValue(imgFracX, imgFracY) {
      if (space === "figure") return [imgFracX, imgFracY];
      var ax = Math.min(1, Math.max(0, (imgFracX - bbox[0]) / (bbox[2] - bbox[0])));
      var ay = Math.min(1, Math.max(0, (imgFracY - bbox[1]) / (bbox[3] - bbox[1])));
      if (!isData) return [ax, ay];
      return [
        scaleInverse(ax, xlim[0], xlim[1], xscale),
        scaleInverse(ay, ylim[0], ylim[1], yscale),
      ];
    }

    function post(value) {
      var values = { x: value[0], y: value[1] };
      for (var k in handle.dataset) {
        if (k.indexOf("field") === 0) {
          var pair = handle.dataset[k].split("=");
          values[pair[0]] = pair[1];
        }
      }
      htmx.ajax("POST", handle.dataset.postUrl, {
        source: handle, target: "#app-body", values: values,
        swap: "innerHTML focus-scroll:false",
      });
    }

    var current = {
      x: parseFloat(handle.dataset.imgx), y: parseFloat(handle.dataset.imgy),
    };

    function place(imgFracX, imgFracY) {
      handle.style.left = (imgFracX * 100) + "%";
      handle.style.top = ((1 - imgFracY) * 100) + "%";
    }

    handle.addEventListener("mousedown", function (ev) {
      ev.preventDefault();
      handle.focus();
      var rect = wrap.getBoundingClientRect();
      var moved = false;
      function onMove(mv) {
        var fx = Math.min(1, Math.max(0, (mv.clientX - rect.left) / rect.width));
        var fy = Math.min(1, Math.max(0, 1 - (mv.clientY - rect.top) / rect.height));
        moved = true;
        current = { x: fx, y: fy };
        place(fx, fy);
      }
      function onUp() {
        document.removeEventListener("mousemove", onMove);
        document.removeEventListener("mouseup", onUp);
        // A plain click (focusing the handle to use the arrow keys) is not
        // an edit: posting here would append a no-op action to the history
        // and swap in a new overlay, stealing the focus the click just set.
        if (moved) post(toValue(current.x, current.y));
      }
      document.addEventListener("mousemove", onMove);
      document.addEventListener("mouseup", onUp);
    });

    // Each post swaps in a fresh overlay, destroying this handle mid-press.
    // Holding an arrow key (or any burst faster than a round trip) would
    // otherwise drop every keypress that lands during a swap, so move the
    // handle immediately and coalesce the posts.
    var pending = null;
    function postSoon(value) {
      if (pending) clearTimeout(pending);
      pending = setTimeout(function () {
        pending = null;
        post(value);
      }, 180);
    }

    handle.addEventListener("keydown", function (ev) {
      var step = ev.shiftKey ? 0.06 : 0.02;
      var dx = 0, dy = 0;
      if (ev.key === "ArrowLeft") dx = -step;
      else if (ev.key === "ArrowRight") dx = step;
      else if (ev.key === "ArrowUp") dy = step;
      else if (ev.key === "ArrowDown") dy = -step;
      else return;
      ev.preventDefault();
      current = {
        x: Math.min(1, Math.max(0, current.x + dx)),
        y: Math.min(1, Math.max(0, current.y + dy)),
      };
      place(current.x, current.y);
      postSoon(toValue(current.x, current.y));
    });
  }

  // A swap replaces the whole inspector, so <details> collapse and the
  // sidebar jumps to the top after every edit. Snapshot both just before
  // the swap and restore them right after.
  // (keyed by data-key, not summary text: the history section's label
  // contains a live action count, so its text changes on every swap.)
  var state = null;
  document.body.addEventListener("htmx:beforeSwap", function () {
    var open = {};
    document.querySelectorAll("details[data-key]").forEach(function (d) {
      open[d.dataset.key] = d.open;
    });
    var inspector = document.querySelector(".inspector");
    // Each nudge dispatches an edit that replaces the overlay, so without
    // remembering which handle had focus, arrow keys move a handle exactly
    // once and then go nowhere.
    var active = document.activeElement;
    state = {
      open: open,
      scroll: inspector ? inspector.scrollTop : 0,
      handle: active && active.dataset ? active.dataset.handleId : null,
    };
  });
  document.body.addEventListener("htmx:afterSwap", function () {
    document.querySelectorAll(".drag-handle").forEach(wireHandle);
  });
  // Restoring scroll has to wait for layout: right after the swap the new
  // content hasn't been laid out yet, so assigning scrollTop gets clamped
  // to the (still short) scroll height and the sidebar jumps anyway.
  document.body.addEventListener("htmx:afterSettle", function () {
    if (!state) return;
    requestAnimationFrame(function () {
      document.querySelectorAll("details[data-key]").forEach(function (d) {
        var was = state.open[d.dataset.key];
        if (was !== undefined) d.open = was;
      });
      var inspector = document.querySelector(".inspector");
      if (inspector) {
        // Force a reflow first: re-opening the <details> above changes the
        // scroll height, and without this the assignment is clamped against
        // the stale (collapsed) height, losing the position anyway.
        void inspector.scrollHeight;
        inspector.scrollTop = state.scroll;
      }
      if (state.handle) {
        var again = document.querySelector(
          '.drag-handle[data-handle-id="' + state.handle + '"]'
        );
        if (again) again.focus({ preventScroll: true });
      }
      state = null;
    });
  });
  document.querySelectorAll(".drag-handle").forEach(wireHandle);
})();
</script>
"""


def _nav_html(active: str) -> str:
    def tab(href: str, label: str, key: str) -> str:
        cls = " active" if key == active else ""
        return f'<a class="navtab{cls}" href="{href}">{label}</a>'

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
        f'<form hx-post="{_esc(action)}" hx-target="#app-body" hx-swap="{_SWAP}">'
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
    return f'<div class="panel samples"><h2>Sample data</h2>{buttons}</div>'


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

    n = len(spec.panels)
    if n <= 1:
        picker = '<div class="hint">One panel. Add rows/columns to split it.</div>'
    else:
        buttons = "".join(
            _hx_form("/select-panel", {"panel": i}, "", f"{i + 1}").replace(
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
    return f'<div class="panel"><h2>Panels</h2>{layout_form}{picker}</div>'


def _layer_panel(spec: FigureSpec) -> str:
    type_select = _select("layer_type", _SERIES_LAYER_TYPES, "line")
    dl = _column_datalist(spec, "cols")
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
        f'<div class="hint">Available columns: '
        f"{', '.join(spec.data.columns) or '(none — load sample data first)'}</div>"
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
    return f'<div class="panel"><h2>Figure</h2>{suptitle_form}{size_form}</div>'


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

    body = row("Legend", "legend", leg_active) + row(
        "Title", "title", title_active, default_xy=(0.5, 0.9)
    )
    body += (
        '<div class="hint">Once enabled, drag the coloured handle on the '
        "preview, or click it and use the arrow keys (Shift = bigger step). "
        "Text/annotation layers are always draggable once added.</div>"
    )
    return f'<div class="panel"><h2>Position (drag on preview)</h2>{body}</div>'


def _history_panel() -> str:
    def btn(action: str, label: str) -> str:
        return (
            f'<form hx-post="{action}" hx-target="#app-body" hx-swap="{_SWAP}">'
            f'<button type="submit" class="secondary">{label}</button></form>'
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


def _export_panel() -> str:
    links = "".join(
        f'<a href="{href}" download="{name}">'
        f'<button type="button" class="secondary">{label}</button></a>'
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


def _axes_frac_to_img_frac(ax_frac: float, lo: float, hi: float) -> float:
    return lo + ax_frac * (hi - lo)


def _data_to_img_frac(value: float, lo: float, hi: float, scale: str, bbox_lo, bbox_hi):
    lo_l = math.log10(lo) if scale == "log" else lo
    hi_l = math.log10(hi) if scale == "log" else hi
    v_l = math.log10(value) if scale == "log" else value
    denom = hi_l - lo_l
    ax_frac = (v_l - lo_l) / denom if denom else 0.5
    ax_frac = min(1.0, max(0.0, ax_frac))
    return _axes_frac_to_img_frac(ax_frac, bbox_lo, bbox_hi)


def _drag_handle_html(
    *,
    kind: str,
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
    handle_id = f"{kind}:{fields.get('layer_index', '')}:{fields.get('panel', 0)}"
    return (
        f'<div class="drag-handle {kind}" tabindex="0" '
        f'data-handle-id="{_esc(handle_id)}" '
        f'data-imgx="{img_x:g}" data-imgy="{img_y:g}" '
        f'style="left:{img_x * 100:g}%; top:{(1 - img_y) * 100:g}%" '
        f"{data_attrs} {field_attrs} "
        f'title="Drag, or click and use arrow keys">{symbol}</div>'
    )


def _preview_handles_html(spec: FigureSpec, layout: dict, active: int) -> str:
    """Draggable overlay handles for the legend, title, and any text/
    annotate layers -- positioned using the layout info from the last
    render (panel bbox / xlim / ylim / scale), see EditorSession.refresh().
    """
    if not spec.panels:
        return ""
    panel = spec.panels[active]
    handles = []

    leg = panel.legend
    if leg.bbox_to_anchor is not None:
        hx, hy = leg.bbox_to_anchor
        handles.append(
            _drag_handle_html(
                kind="legend",
                symbol="\u2725",
                img_x=hx,
                img_y=hy,
                extra_data={"space": "figure", "post-url": "/action"},
                fields={"type": "set_legend_position", "panel": active},
            )
        )

    has_bbox = not layout.get("is_3d") and "panel_bbox" in layout
    if has_bbox:
        bx0, by0, bx1, by1 = layout["panel_bbox"]

    if panel.title and panel.title_position is not None and has_bbox:
        tx, ty = panel.title_position
        handles.append(
            _drag_handle_html(
                kind="title",
                symbol="T",
                img_x=_axes_frac_to_img_frac(tx, bx0, bx1),
                img_y=_axes_frac_to_img_frac(ty, by0, by1),
                extra_data={
                    "space": "axes",
                    "bbox": json.dumps(layout["panel_bbox"]),
                    "post-url": "/action",
                },
                fields={"type": "set_title_position", "panel": active},
            )
        )

    xlim, ylim = layout.get("xlim"), layout.get("ylim")
    xscale, yscale = layout.get("xscale", "linear"), layout.get("yscale", "linear")
    if has_bbox and xlim and ylim:
        for entry in layout.get("text_layers", []):
            ax_v, ay_v = entry["at"]
            handles.append(
                _drag_handle_html(
                    kind="layer-at",
                    symbol="\u2022",
                    img_x=_data_to_img_frac(ax_v, *xlim, xscale, bx0, bx1),
                    img_y=_data_to_img_frac(ay_v, *ylim, yscale, by0, by1),
                    extra_data={
                        "space": "axes",
                        "data": "1",
                        "bbox": json.dumps(layout["panel_bbox"]),
                        "xlim": json.dumps(xlim),
                        "ylim": json.dumps(ylim),
                        "xscale": xscale,
                        "yscale": yscale,
                        "post-url": "/action",
                    },
                    fields={
                        "type": "set_layer_at",
                        "panel": active,
                        "layer_index": entry["index"],
                    },
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
) -> str:
    """The inner ``#app-body`` content: everything htmx swaps after an
    action, and what ``render_page`` embeds for the first load.

    ``active_panel`` is which panel the side controls edit; it is editor
    state, not figure state, so it is passed in rather than read off the
    spec.
    """
    layout = layout or {}
    active = min(active_panel, max(len(spec.panels) - 1, 0))
    error_html = f'<div class="error">{_esc(error)}</div>' if error else ""
    left = (
        '<details data-key="samples"><summary>Start from a sample</summary>'
        + _samples_panel()
        + "</details>"
        + _figure_panel(spec)
        + _panels_panel(spec, active)
        + _labels_panel(spec, active)
        + _theme_panel(spec)
        + _palette_panel(spec)
        + _layer_panel(spec)
        + _annotation_panel()
        + _layers_panel(spec, active)
        + _position_panel(spec, active)
        + _history_panel()
        + '<details data-key="advanced"><summary>Advanced · JSON actions</summary>'
        + _advanced_panel()
        + "</details>"
        + _export_panel()
    )
    handles_html = _preview_handles_html(spec, layout, active)
    right = (
        '<div class="panel"><h2>Preview</h2><figure><div class="preview-wrap">'
        '<img src="/fig.png" alt="figure preview">'
        f"{handles_html}</div></figure></div>"
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
) -> str:
    """Render the full editor page (used for the initial ``GET /`` only)."""
    body = render_app_body(
        spec, action_log, layout, error=error, active_panel=active_panel
    )
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>mudplot editor</title>
<script src="/static/htmx.min.js"></script>
<style>{_STYLE}</style>
</head>
<body>
<header>
  <h1>mudplot editor</h1>
  <div class="sub">Figure studio · Edit, refine, export</div>
  {_nav_html("editor")}
</header>
<main><div id="app-body">{body}</div></main>
{_DRAG_SCRIPT}
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
