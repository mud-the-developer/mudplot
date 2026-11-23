# Executable v2 workflows and upgrade guide

[한국어](README.ko.md) · [Workflow index and evidence](../docs/V2_EXAMPLE_EVIDENCE.md) · [66 layer examples](../docs/PLOT_GALLERY.md)

This unpublished local **2.0.0** candidate includes bounded v2 workflows and keeps FigureSpec schema **0.1**. It is not full Seaborn or Matplotlib parity. Final qualification, including same-artifact TeX compilation, is not complete.

## Run and edit an example

Use Python 3.11 or later. The core has no required third-party dependencies. In the matching source checkout or unpacked sdist, install `.[render]` in a local environment (NumPy ≥1.23.5, Matplotlib ≥3.8, Pillow ≥13). Add `regression` or `cluster` only for the optional models that need them (`.[regression]`, `.[cluster]`); `all` includes both. The engine wheel does not contain the dashboard, example sources or Rust editor.

```sh
mkdir -p /tmp/mudplot-example
python examples/scalar_display.py /tmp/mudplot-example
python -m mudplot validate /tmp/mudplot-example/scalar-display.mplot.json
python -m mudplot render /tmp/mudplot-example/scalar-display.mplot.json /tmp/mudplot-example/reopened.svg
```

The sample uses explicit scalar colour ranges and separate raw-unit guides; it writes editable JSON and PNG/SVG/PDF. Start the [matching Rust editor](../mudplot-editor/README.md) with this environment's Python; open the loopback page and load the JSON. Edit a guide using the layer form or a supported raw action, undo, redo, download a copy and reopen it. This is an unauthenticated local tool, not a remote or shared editor. Some options use a generic typed form or raw action, not a dedicated widget.

Other workflows include [explicit clocks](temporal_axes.py), [live facet builders](facet_builders.py), [weighted pair and joint grids](weighted_grids.py), [native anchored marks](native_annotations.py), and [explicit 3-D geometry](spatial_workflow.py). Use each script's explicit output argument; several defaults write to documentation directories. The [row-by-row index](../docs/V2_EXAMPLE_EVIDENCE.md#workflow-index) includes the scientific examples and their verification boundary.

## Reopen an older 0.1 file

Keep the original, then open or validate it before editing. Omitted options retain their compatible defaults. Current examples opt in to explicit clocks, named scales, topology and compound layouts; the loader does not reinterpret old columns or infer new science. To write a separate validated copy run `python -m mudplot migrate old.mplot.json --out reopened.mplot.json`. Explicit null or unsupported spec versions reject. Unknown historic keys are not a place to store custom metadata. New options saved under 0.1 may not be readable by older package releases; retaining the original is safer than attempting to downgrade a changed file. See [compatibility](../docs/COMPATIBILITY.md).
