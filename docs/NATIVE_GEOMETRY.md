# Native planar geometry

[Korean](NATIVE_GEOMETRY.ko.md) · [Runnable example](../examples/native_planar_geometry.py)

These calls draw supplied geometry, not estimated values. Existing calls without
new declarations retain their original meaning. Serialize `AddLayer`/`ReplaceLayer`
normally and edit the materialized layer; do not pass arbitrary Matplotlib setters.

## Line, error, band and span

- `line(..., native_style=ComponentStyleSpec(...))` and `scatter(...)` can
  declare native glyph, stroke, colour and alpha. Stroke widths and marker
  diameters are points, so scatter stores area as diameter squared in Matplotlib.
  Named `none` on a collection stroke sets width to zero, without hiding its fill.
  Raw chosen style cannot compete with a semantic or scalar display mapping for
  the same mark. Exact safe options are listed by `mudplot capabilities`.
- `hlines(SegmentSpec(at, start, end))` takes y values and actual x endpoints;
  `vlines` takes x values and actual y endpoints. These are data coordinates in
  the selected x/y/y2 axes, including declared dates; they are not the old
  `hline`/`vline` reference axis fractions. Shape arrays are equal and finite.
- `errorbar(x, y, magnitudes=ErrorMagnitudesSpec(x=["left", "right"],
  y=["below", "above"]))` takes original nonnegative magnitude columns.
  The bounds are `centre - lower` and `centre + upper`. A declared numeric
  clock converts magnitudes with its input unit, **without** the clock origin;
  ISO-clock magnitudes are in days. Missing required values omit that physical
  error observation. A real endpoint must be representable and in its native
  calendar/log/logit domain; zero magnitude is valid. A legacy symmetric mode
  can be used on the other axis, never a second owner on the same axis.
- `band(along, lower, upper, orient="v"|"h", fill=FillSpec(...))` calls real
  `fill_between`/`fill_betweenx`. `where` names a Boolean column (missing
  maps to false); an interval is filled only when its adjacent samples allow it.
  Missing coordinate/bound values break the path, not just its fill color.
  Step uses `pre`, `post` or `mid`; `interpolate=True` uses the native curves'
  intersection at a Boolean mask boundary. It does not impute missing samples.
- `hspan(SpanSpec(start, end, fractions))` shades an actual sorted y interval;
  `vspan` uses x. The orthogonal interval is an increasing pair of axes
  fractions in `[0,1]` (default `[0,1]`), not a second value interval. Both are
  real native patches, with optional body style.

Use appropriate Cartesian axes, at most 10,000 extended paired source rows
and 64 raw groups, under existing native managed work/path bounds. The preserved
scientific recipe is the source table and named declarations, not backend arrays.

## Supplied bars and pie wedges

[Executable example](../examples/native_bars_and_pie.py).
`bar(position, value, geometry=BarGeometrySpec(...))` opts into explicit native
placement; `barh(position, value, ...)` rotates those roles, so `bottom` means
left. `align="edge"` puts the supplied position on the first native edge.
`bottom` is a constant or a named numeric column, and `bar_width` is a position
span (a duration in the declared input unit for a numerical clock). With
`multiple="stack"`, selected groups align by raw category or actual coordinate,
one row per group/category and one bottom per category. Positive and negative
heights accumulate separately from that same base. No missing segment is
fabricated and category identities distinguish Boolean `True` from numeric `1`.

`styles` optionally supplies one body style/null per original row, not a style
per visible sorted position. `labels` names a text column instead of formatting
the supplied signed `value_format`; neither prints cumulative tops. Typed bar
geometry does not transfer legacy y-error controls; add an independent
`errorbar` for precomputed endpoints.

`pie(label, value, geometry=PieGeometrySpec(...))` draws the original
nonnegative sequence (64 rows maximum). Radius, start angle/direction, center,
native explode, wedge width and body styles control actual wedges. `labels`,
`label_distance`, `rotate_labels`, text colour/size and `value_distance` control
actual native text. `value="raw"` formats the original values;
`"percent"` formats normalized mass or the supplied fraction ×100 when
`normalize=False`. Partial pies require total ≤1. `annotations` is a row-aligned
list of optional literal callouts anchored at the actual wedge edge; text offset
is in points. No callable or arbitrary formatting expression is persisted.

## Literal patches, tables and annotation coordinates

[Executable example](../examples/native_annotations.py).
`patch(PatchSpec(...))` accepts rectangles, ellipses, polygons and literal native
paths. A rectangle/ellipse needs two increasing corners; a polygon needs at
least three points. A path uses a parallel list of `MOVETO`, `LINETO`, `CURVE3`,
`CURVE4`, `CLOSEPOLY` codes: two quadratic or three cubic codes/vertices per
curve and a drawable subpath for every move. The `CLOSEPOLY` vertex is a native
placeholder; it does not create a second drawing point. Choose `data`, `axes`,
or `figure`; fractions must be in `[0,1]`. No new axes are created. `hspan` and
`vspan` use the same span primitive described above.

`table(LiteralTableSpec(...))` draws rectangular literal strings in an axes
rectangle `[left, bottom, width, height]`; optional row/column headers occupy
space inside that same rectangle. Text alignment, finite font size, borders and
the three named colour roles apply to actual native cells. Table contents are not
data columns, computations or HTML.

`AnnotationSpec` gives `text`/`annotate` independent `at_coordinates` and
`to_coordinates`, named arrows, alignments, font size and rotation. The
`data` frame uses actual numeric axis coordinates (native UTC days for clock
axes). Axes and figure frames use fractions. The editor only advertises native
drag handles for Cartesian data text anchors on supported scales; fraction
anchors remain editable by `SetLayerAt` or ordinary layer replacement, not by
an incorrectly projected data drag. The arrow target never moves with the text.

`path_effects=[PathEffectSpec("stroke", ...), PathEffectSpec("shadow", ...)]`
adds ordered native effects and then the normal draw. Stroke width and offsets
are points. Effects apply only to enumerated native artists; no hidden callable,
arbitrary transform or clipping-dependent replacement is saved.
