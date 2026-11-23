/* Shared native-preview handle interaction for the Python and Rust editors. */
(function () {
  "use strict";
  function scaleInverse(f, lo, hi, scale = "linear") {
    if (scale === "log") return Math.pow(10, Math.log10(lo) + f * (Math.log10(hi) - Math.log10(lo)));
    if (scale === "linear") return lo + f * (hi - lo);
    throw new Error("Data-anchor dragging is unsupported for scale " + scale);
  }
  let state = null;
  let generation = 0;
  const clamp = v => Math.min(1, Math.max(0, v));
  function wire(handle) {
    if (handle.dataset.wired) return;
    handle.dataset.wired = "1";
    const wrap = handle.closest(".preview-wrap");
    const image = wrap.querySelector("img");
    const ready = () => handle.isConnected && image.complete && image.naturalWidth > 0 && !wrap.dataset.busy;
    const bbox = handle.dataset.bbox ? JSON.parse(handle.dataset.bbox) : [0, 0, 1, 1];
    const xlim = handle.dataset.xlim ? JSON.parse(handle.dataset.xlim) : null;
    const ylim = handle.dataset.ylim ? JSON.parse(handle.dataset.ylim) : null;
    let current = [Number(handle.dataset.imgx), Number(handle.dataset.imgy)];
    let pending = null;
    let activePointer = null;
    let queuedKeyboard = false;
    let dragOrigin = null;
    function value() {
      const p = [(current[0] - bbox[0]) / (bbox[2] - bbox[0]), (current[1] - bbox[1]) / (bbox[3] - bbox[1])];
      return handle.dataset.data === "1" ? [scaleInverse(p[0], xlim[0], xlim[1], handle.dataset.xscale), scaleInverse(p[1], ylim[0], ylim[1], handle.dataset.yscale)] : p;
    }
    function place() {
      handle.style.left = (current[0] * 100) + "%";
      handle.style.top = ((1 - current[1]) * 100) + "%";
    }
    function post() {
      clearTimeout(pending);
      pending = null;
      if (activePointer !== null || !ready() || handle.disabled) return;
      const p = value();
      if (!p.every(Number.isFinite)) return;
      const values = {x: p[0], y: p[1]};
      Object.keys(handle.dataset).filter(k => k.startsWith("field")).forEach(k => {
        const [name, val] = handle.dataset[k].split("="); values[name] = val;
      });
      wrap.dataset.busy = "1";
      queuedKeyboard = false;
      htmx.ajax("POST", handle.dataset.postUrl, {source: handle, target: wrap.dataset.target || "#app-body", values, swap: wrap.dataset.target ? "outerHTML focus-scroll:false" : "innerHTML focus-scroll:false"}).finally(() => { delete wrap.dataset.busy; });
    }
    handle.addEventListener("pointerdown", ev => {
      if (!ev.isPrimary || activePointer !== null || !ready() || ev.button !== 0) return;
      activePointer = ev.pointerId;
      const pointerId = ev.pointerId;
      ev.preventDefault();
      handle.focus();
      clearTimeout(pending); pending = null;
      const rect = image.getBoundingClientRect();
      const start = [ev.clientX, ev.clientY];
      const original = current.slice();
      dragOrigin = original;
      let moved = false;
      handle.setPointerCapture(ev.pointerId);
      function move(e) {
        if (e.pointerId !== pointerId) return;
        moved = moved || Math.abs(e.clientX - start[0]) + Math.abs(e.clientY - start[1]) > 2;
        if (!moved) return;
        current = [clamp(original[0] + (e.clientX - start[0]) / rect.width), clamp(original[1] - (e.clientY - start[1]) / rect.height)];
        place();
      }
      function finish(e) {
        if (e.pointerId !== pointerId) return;
        activePointer = null;
        dragOrigin = null;
        handle.removeEventListener("pointermove", move);
        handle.removeEventListener("pointerup", finish);
        handle.removeEventListener("pointercancel", cancel);
        if (handle.hasPointerCapture(e.pointerId)) handle.releasePointerCapture(e.pointerId);
        if (moved || queuedKeyboard) post();
      }
      function cancel(e) {
        if (e.pointerId !== pointerId) return;
        current = original; moved = false; place(); finish(e);
      }
      handle.addEventListener("pointermove", move); handle.addEventListener("pointerup", finish); handle.addEventListener("pointercancel", cancel);
    });
    handle.addEventListener("keydown", ev => {
      const directions = {ArrowLeft: [-1, 0], ArrowRight: [1, 0], ArrowUp: [0, 1], ArrowDown: [0, -1]};
      const d = directions[ev.key];
      if (!d || !ready()) return;
      ev.preventDefault();
      const step = ev.shiftKey ? 0.06 : 0.02;
      const previous = current;
      current = [clamp(current[0] + d[0] * step), clamp(current[1] + d[1] * step)]; place();
      if (dragOrigin) {
        dragOrigin[0] += current[0] - previous[0];
        dragOrigin[1] += current[1] - previous[1];
      }
      queuedKeyboard = true;
      clearTimeout(pending);
      pending = setTimeout(post, 180);
    });
    const loaded = () => { handle.disabled = !ready(); };
    image.addEventListener("load", loaded, {once: true}); image.addEventListener("error", loaded, {once: true}); loaded();
  }
  function bind() {
    document.querySelectorAll(".preview-wrap[data-layout]").forEach(wrap => {
      if (wrap.dataset.built) return;
      wrap.dataset.built = "1";
      const image = wrap.querySelector("img");
      const layout = JSON.parse(wrap.dataset.layout);
      const status = wrap.parentElement.querySelector(".preview-status");
      if (status) {
        const report = () => {
          status.textContent = image.naturalWidth > 0 ? (layout?.data_drag_reason || "") :
            "Preview changed or failed to load. Reload to use current handles.";
        };
        image.addEventListener("load", report, {once: true});
        image.addEventListener("error", report, {once: true});
        if (image.complete) report();
      }
      if (!layout || !layout.handles) return;
      layout.handles.forEach(h => {
        const b = document.createElement("button");
        b.type = "button"; b.className = "drag-handle " + h.kind;
        b.dataset.handleId = h.kind + ":" + (h.layer_index ?? "") + ":" + (h.panel_id ?? h.panel);
        b.dataset.imgx = h.imgx; b.dataset.imgy = h.imgy;
        b.dataset.space = h.kind === "legend" ? "figure" : "axes";
        b.dataset.bbox = JSON.stringify(h.bbox || (h.kind === "legend" ? layout.figure_bbox : layout.panel_bbox));
        b.dataset.postUrl = "/control/move";
        const fields = {kind: h.kind, panel: h.panel, revision: wrap.dataset.revision};
        if (h.layer_index !== null) fields.layer_index = h.layer_index;
        Object.entries(fields).forEach(([k, v], i) => { b.dataset["field" + i] = k + "=" + v; });
        if (h.kind === "layer-at") {
          b.dataset.data = "1"; b.dataset.xlim = JSON.stringify(h.xlim); b.dataset.ylim = JSON.stringify(h.ylim); b.dataset.xscale = h.xscale; b.dataset.yscale = h.yscale;
        }
        b.setAttribute("aria-label", "Move " + (h.label || h.kind) + "; drag or use arrow keys (Shift: larger step)");
        b.title = b.getAttribute("aria-label"); b.textContent = h.kind === "title" ? "T" : h.kind === "legend" ? "✥" : "●";
        b.style.left = (h.imgx * 100) + "%"; b.style.top = ((1 - h.imgy) * 100) + "%";
        wrap.appendChild(b);
      });
    });
    document.querySelectorAll(".drag-handle").forEach(wire);
  }
  document.body.addEventListener("htmx:beforeSwap", ev => {
    const next = Number(ev.detail.xhr.getResponseHeader("X-Mudplot-View-Generation"));
    if (next > 0 && next < generation) { ev.detail.shouldSwap = false; return; }
    generation = Math.max(generation, next || 0);
    const open = {};
    document.querySelectorAll("details").forEach((d, i) => { open[d.dataset.key || i] = d.open; });
    const active = document.activeElement;
    // Disabling controls blurs the active handle; HTMX retains the exact request source.
    const source = ev.detail.requestConfig?.elt;
    state = {open, handle: source?.dataset?.handleId || active?.dataset?.handleId, scroll: document.querySelector(".inspector")?.scrollTop || 0};
  });
  document.body.addEventListener("htmx:afterSwap", bind);
  document.body.addEventListener("htmx:afterSettle", () => {
    if (!state) return;
    document.querySelectorAll("details").forEach((d, i) => { if ((d.dataset.key || i) in state.open) d.open = state.open[d.dataset.key || i]; });
    const inspector = document.querySelector(".inspector"); if (inspector) inspector.scrollTop = state.scroll;
    if (state.handle) document.querySelectorAll(".drag-handle").forEach(h => {
      if (h.dataset.handleId !== state.handle) return;
      const focus = () => { if (h.isConnected) h.focus({preventScroll: true}); };
      if (h.disabled) h.closest(".preview-wrap").querySelector("img").addEventListener("load", focus, {once: true});
      else focus();
    });
    state = null;
  });
  document.body.addEventListener("change", ev => {
    const input = ev.target;
    if (input.id !== "spec-file" || !input.files.length) return;
    const reader = new FileReader(); reader.onload = () => { const box = document.getElementById("spec-json"); if (box) box.value = reader.result; }; reader.readAsText(input.files[0]);
  });
  bind();
})();
