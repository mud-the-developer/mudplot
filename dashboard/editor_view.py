"""Pure HTML rendering for the interactive editor.

No I/O here — every function takes plain data (the current spec, the action
log, an optional error) and returns an HTML string. This keeps the view
layer testable without spinning up a real HTTP server, and keeps
`editor_server.py` a thin wiring layer around it.

English by default (per project convention); this is the human-facing UI.
"""

from __future__ import annotations

import html
import json

from mudplot.spec import FigureSpec
from mudplot.theme import AVAILABLE_JOURNALS, AVAILABLE_THEMES

from .samples import SAMPLES

__all__ = ["render_docs_page", "render_page"]

_PALETTE_KINDS = ("qualitative", "sequential", "diverging")
_LAYER_TYPES = ("line", "scatter", "bar")

_STYLE = """
:root { color-scheme: light; }
body { font-family: -apple-system, "Segoe UI", Helvetica, Arial, sans-serif;
       margin: 0; color: #1a1a1a; background: #fafafa; }
header { padding: .9rem 1.4rem; background: #1a1a1a; color: white; }
header h1 { margin: 0; font-size: 1.15rem; }
header .sub { color: #aaa; font-size: .82rem; }
main { display: grid; grid-template-columns: 340px 1fr; gap: 1.2rem;
       padding: 1.2rem; align-items: start; }
.panel { background: white; border: 1px solid #e2e2e2; border-radius: 8px;
         padding: 1rem 1.1rem; margin-bottom: 1rem; }
.panel h2 { font-size: .95rem; margin: 0 0 .7rem; color: #333; }
label { display: block; font-size: .8rem; color: #555; margin: .5rem 0 .2rem; }
input, select, textarea { width: 100%; box-sizing: border-box; padding: .35rem .5rem;
       border: 1px solid #ccc; border-radius: 5px; font-size: .85rem; }
textarea { font-family: ui-monospace, monospace; min-height: 5rem; }
button { margin-top: .6rem; padding: .4rem .8rem; border: none; border-radius: 5px;
         background: #1a1a1a; color: white; cursor: pointer; font-size: .82rem; }
button.secondary { background: #eee; color: #1a1a1a; border: 1px solid #ccc; }
.row { display: flex; gap: .5rem; }
.row > * { flex: 1; }
.error { background: #fdecea; border: 1px solid #f5b3ac; color: #8a2c22;
         padding: .6rem .8rem; border-radius: 6px; margin-bottom: 1rem;
         font-size: .85rem; white-space: pre-wrap; }
figure { margin: 0; text-align: center; }
figure img { max-width: 100%; border: 1px solid #eee; border-radius: 6px;
             background: white; }
.log { font-family: ui-monospace, monospace; font-size: .75rem; color: #555;
       max-height: 220px; overflow: auto; background: #f5f5f5; padding: .6rem;
       border-radius: 6px; }
.log div { padding: .1rem 0; border-bottom: 1px solid #eaeaea; }
.hint { font-size: .75rem; color: #888; margin-top: .2rem; }
.samples button { margin-right: .4rem; }
.layer-row { display: flex; justify-content: space-between; align-items: center;
             padding: .3rem 0; border-bottom: 1px solid #eee; font-size: .82rem; }
.layer-row form { margin: 0; }
.layer-row button { margin-top: 0; padding: .25rem .6rem; }
.preview-wrap { position: relative; display: inline-block; max-width: 100%; }
.preview-wrap img { display: block; max-width: 100%; }
.legend-handle { position: absolute; width: 22px; height: 22px; margin: -11px 0 0 -11px;
       border-radius: 50%; background: #1a1a1a; color: white; display: flex;
       align-items: center; justify-content: center; cursor: grab;
       font-size: 12px; user-select: none; box-shadow: 0 0 0 2px white; }
.legend-handle:focus { outline: 2px solid #0a5; }
nav.tabs { margin-top: .6rem; }
nav.tabs .navtab { color: #ccc; text-decoration: none; font-size: .85rem;
       margin-right: 1.2rem; padding-bottom: .2rem; }
nav.tabs .navtab.active { color: white; border-bottom: 2px solid #0a5; }
.docs { max-width: 880px; margin: 0 auto; padding: 1.2rem 1.4rem; background: white;
       border-radius: 8px; }
.docs h1, .docs h2, .docs h3 { color: #222; }
.docs table { border-collapse: collapse; width: 100%; margin: .75rem 0 1.25rem; }
.docs th, .docs td { border: 1px solid #ddd; padding: .4rem .6rem; text-align: left;
       font-size: .88em; }
"""

_LEGEND_DRAG_SCRIPT = """
<script>
(function () {
  var handle = document.getElementById("legend-handle");
  if (!handle) return;
  var wrap = handle.parentElement;
  var panel = handle.dataset.panel;

  function post(x, y) {
    var body = "type=set_legend_position&panel=" + panel +
      "&x=" + x.toFixed(4) + "&y=" + y.toFixed(4);
    fetch("/action", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: body,
    }).then(function () { location.reload(); });
  }

  function setStyle(xFrac, yFrac) {
    handle.style.left = (xFrac * 100) + "%";
    handle.style.top = ((1 - yFrac) * 100) + "%";
  }

  var current = { x: parseFloat(handle.dataset.x), y: parseFloat(handle.dataset.y) };

  handle.addEventListener("mousedown", function (ev) {
    ev.preventDefault();
    handle.focus();
    var rect = wrap.getBoundingClientRect();
    function onMove(mv) {
      var xFrac = Math.min(1, Math.max(0, (mv.clientX - rect.left) / rect.width));
      var yFrac = Math.min(1, Math.max(0, 1 - (mv.clientY - rect.top) / rect.height));
      current = { x: xFrac, y: yFrac };
      setStyle(xFrac, yFrac);
    }
    function onUp() {
      document.removeEventListener("mousemove", onMove);
      document.removeEventListener("mouseup", onUp);
      post(current.x, current.y);
    }
    document.addEventListener("mousemove", onMove);
    document.addEventListener("mouseup", onUp);
  });

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
    setStyle(current.x, current.y);
    post(current.x, current.y);
  });
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


def _post_form(action: str, hidden: dict, body: str, button: str = "Apply") -> str:
    hidden_inputs = "".join(
        f'<input type="hidden" name="{_esc(k)}" value="{_esc(v)}">'
        for k, v in hidden.items()
    )
    return (
        f'<form method="post" action="{_esc(action)}">'
        f"{hidden_inputs}{body}"
        f'<button type="submit">{_esc(button)}</button>'
        "</form>"
    )


def _samples_panel() -> str:
    buttons = "".join(
        f'<form method="post" action="/action" style="display:inline">'
        f'<input type="hidden" name="type" value="load_sample">'
        f'<input type="hidden" name="name" value="{_esc(name)}">'
        f'<button type="submit" class="secondary">{_esc(name)}</button>'
        "</form>"
        for name in SAMPLES
    )
    return f'<div class="panel samples"><h2>Sample data</h2>{buttons}</div>'


def _theme_panel(spec: FigureSpec) -> str:
    theme_select = _select("name", AVAILABLE_THEMES, spec.theme.name)
    theme_form = _post_form(
        "/action", {"type": "set_theme"}, f"<label>Theme</label>{theme_select}"
    )
    journal_opts = ("none", *AVAILABLE_JOURNALS)
    journal_select = _select("name", journal_opts, spec.journal or "none")
    journal_form = _post_form(
        "/action", {"type": "set_journal"}, f"<label>Journal</label>{journal_select}"
    )
    body = theme_form + journal_form
    return f'<div class="panel"><h2>Theme &amp; journal</h2>{body}</div>'


def _palette_panel(spec: FigureSpec) -> str:
    p = spec.theme.palette
    kind_select = _select("kind", _PALETTE_KINDS, p.kind)
    body = (
        f"<label>Kind</label>{kind_select}"
        f'<label>Hue start</label><input type="number" name="hue_start" '
        f'value="{p.hue_start:g}" step="1">'
        f'<label>Chroma</label><input type="number" name="chroma" '
        f'value="{p.chroma:g}" step="1">'
        f'<label>Lightness</label><input type="number" name="lightness" '
        f'value="{p.lightness:g}" step="1">'
    )
    form = _post_form("/action", {"type": "set_palette"}, body)
    return f'<div class="panel"><h2>Palette</h2>{form}</div>'


def _layer_panel(spec: FigureSpec) -> str:
    type_select = _select("layer_type", _LAYER_TYPES, "line")
    dl = _column_datalist(spec, "cols")
    body = (
        f"<label>Layer type</label>{type_select}"
        f'<label>x column</label><input name="x" list="cols" placeholder="x">'
        f'<label>y column</label><input name="y" list="cols" placeholder="y">'
        f"<label>group column (optional)</label>"
        f'<input name="group" list="cols" placeholder="">'
        f"{dl}"
        f'<div class="hint">Available columns: '
        f"{', '.join(spec.data.columns) or '(none — load sample data first)'}</div>"
    )
    form = _post_form("/action", {"type": "add_layer"}, body, "Add layer")
    return f'<div class="panel"><h2>Add layer</h2>{form}</div>'


def _layers_panel(spec: FigureSpec) -> str:
    layers = spec.panels[0].layers if spec.panels else []
    if not layers:
        rows = '<div class="hint">(no layers yet)</div>'
    else:
        rows = "".join(
            '<div class="layer-row">'
            f"<span>{i}: <code>{_esc(layer.type)}</code> "
            f"x={_esc(layer.x) or '-'} y={_esc(layer.y) or '-'}"
            f"{f' group={_esc(layer.group)}' if layer.group else ''}</span>"
            + _post_form(
                "/action",
                {"type": "remove_layer", "layer_index": i},
                "",
                "Remove",
            )
            + "</div>"
            for i, layer in enumerate(layers)
        )
    return f'<div class="panel"><h2>Current layers</h2>{rows}</div>'


def _figure_panel(spec: FigureSpec) -> str:
    body = f'<label>Suptitle</label><input name="text" value="{_esc(spec.suptitle)}">'
    suptitle_form = _post_form(
        "/action", {"type": "set_suptitle"}, body, "Set suptitle"
    )
    size_body = (
        '<div class="row">'
        f'<div><label>Width (in)</label><input type="number" step="0.1" '
        f'name="width" value="{spec.size[0]:g}"></div>'
        f'<div><label>Height (in)</label><input type="number" step="0.1" '
        f'name="height" value="{spec.size[1]:g}"></div>'
        "</div>"
    )
    size_form = _post_form("/action", {"type": "set_size"}, size_body, "Set size")
    return f'<div class="panel"><h2>Figure</h2>{suptitle_form}{size_form}</div>'


def _legend_position_panel(spec: FigureSpec) -> str:
    leg = spec.panels[0].legend if spec.panels else None
    active = leg is not None and leg.bbox_to_anchor is not None
    enable = _post_form(
        "/action",
        {"type": "set_legend_position", "x": "0.8", "y": "0.5", "panel": "0"},
        "",
        "Enable drag positioning",
    )
    reset = _post_form(
        "/action", {"type": "reset_legend_position", "panel": "0"}, "", "Reset"
    )
    hint = (
        "Drag the \u2725 handle on the preview, or click it and use the arrow keys."
        if active
        else "Places the legend at an exact spot instead of a named location."
    )
    return (
        '<div class="panel"><h2>Legend position</h2>'
        f"{enable}{reset if active else ''}"
        f'<div class="hint">{hint}</div></div>'
    )


def _history_panel() -> str:
    buttons = (
        '<form method="post" action="/undo" style="display:inline">'
        '<button type="submit" class="secondary">Undo</button></form> '
        '<form method="post" action="/redo" style="display:inline">'
        '<button type="submit" class="secondary">Redo</button></form> '
        '<form method="post" action="/reset" style="display:inline">'
        '<button type="submit" class="secondary">Reset</button></form>'
    )
    return f'<div class="panel"><h2>History</h2>{buttons}</div>'


def _advanced_panel() -> str:
    example = (
        "{&quot;type&quot;: &quot;SetTitle&quot;, &quot;text&quot;: &quot;t&quot;}"
    )
    body = (
        "<label>Raw JSON action (agent-facing) &mdash; e.g. "
        f"<code>{example}</code></label>"
        '<textarea name="json"></textarea>'
    )
    form = _post_form("/action/raw", {}, body, "Dispatch JSON action")
    return f'<div class="panel"><h2>Advanced</h2>{form}</div>'


def _export_panel() -> str:
    spec_btn = '<button type="button" class="secondary">Download spec (.json)</button>'
    png_btn = '<button type="button" class="secondary">Download PNG</button>'
    return (
        '<div class="panel"><h2>Export</h2>'
        f'<a href="/spec.json" download="figure.mplot.json">{spec_btn}</a> '
        f'<a href="/fig.png" download="figure.png">{png_btn}</a>'
        "</div>"
    )


def _action_log_html(action_log: list[dict]) -> str:
    if not action_log:
        return '<div class="log">(no actions yet)</div>'
    rows = "".join(f"<div>{_esc(json.dumps(a))}</div>" for a in reversed(action_log))
    return f'<div class="log">{rows}</div>'


def render_page(
    spec: FigureSpec,
    action_log: list[dict],
    *,
    error: str | None = None,
    image_query: str = "",
) -> str:
    """Render the full editor page for the given state."""
    error_html = f'<div class="error">{_esc(error)}</div>' if error else ""
    left = (
        _samples_panel()
        + _theme_panel(spec)
        + _palette_panel(spec)
        + _layer_panel(spec)
        + _layers_panel(spec)
        + _figure_panel(spec)
        + _legend_position_panel(spec)
        + _history_panel()
        + _advanced_panel()
        + _export_panel()
    )
    leg = spec.panels[0].legend if spec.panels else None
    handle_html = ""
    drag_script = ""
    if leg is not None and leg.bbox_to_anchor is not None:
        hx, hy = leg.bbox_to_anchor
        handle_html = (
            '<div id="legend-handle" class="legend-handle" tabindex="0" '
            f'data-panel="0" data-x="{hx:g}" data-y="{hy:g}" '
            f'style="left:{hx * 100:g}%; top:{(1 - hy) * 100:g}%" '
            'title="Drag, or click and use arrow keys">\u2725</div>'
        )
        drag_script = _LEGEND_DRAG_SCRIPT
    right = (
        f'<div class="panel"><h2>Preview</h2>'
        f'<figure><div class="preview-wrap">'
        f'<img src="/fig.png{image_query}" alt="figure preview">'
        f"{handle_html}</div></figure>"
        "</div>"
        f'<div class="panel"><h2>Action log</h2>{_action_log_html(action_log)}</div>'
    )
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>mudplot editor</title>
<style>{_STYLE}</style>
</head>
<body>
<header>
  <h1>mudplot editor</h1>
  <div class="sub">A thin UI over the same Store/actions/reducer the fluent
  API and any future Rust editor use — nothing here holds its own state.</div>
  {_nav_html("editor")}
</header>
<main>
  <div>{error_html}{left}</div>
  <div>{right}</div>
</main>
{drag_script}
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
