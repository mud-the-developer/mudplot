# Reading-first chart review

*[한국어 / Korean](VISUAL_QUALITY.ko.md)*

The earlier four-panel prototype failed user readability review. Passing font,
bounds and palette heuristics did not make it a good representative figure.
It is retained as a [rejected prototype](images/visual_after.png), not advertised
as an improved design.

## Two questions, two figures

**[Open the desktop/mobile review page](VISUAL_REVIEW.html).** It displays actual
700px and 320px layouts, captions, and a collapsible numerical endpoint table.

1. **How does response change over time?** A single mean/CI line chart, with
   labels beside the final line segments instead of a colour lookup legend.
   [Desktop PNG](images/visual_response.png) ·
   [Mobile PNG](images/visual_response_mobile.png) ·
   [SVG](images/visual_response.svg) · [PDF](images/visual_response.pdf) ·
   [Editable spec](images/visual_response.mplot.json)
2. **How do endpoint means compare?** A horizontal dot/CI chart with readable
   category labels, small mean markers and no redundant box/ECDF panels.
   Numerical values supplement intervals that are short at mobile sizes; the
   axis is not stretched to exaggerate uncertainty.
   [Desktop PNG](images/visual_endpoint.png) ·
   [Mobile PNG](images/visual_endpoint_mobile.png) ·
   [SVG](images/visual_endpoint.svg) · [PDF](images/visual_endpoint.pdf) ·
   [Editable spec](images/visual_endpoint.mplot.json)

Both use the prototype's same independent synthetic observations (12 per method
and timepoint, seed 2026), estimators, pointwise 95% percentile-bootstrap CI
settings (399 resamples, seed 17), and numerical value-axis ranges. The endpoint
view is rotated, not re-estimated differently. Tests compare means and both CI
endpoints with the retained prototype. This is a layout redesign, not a
single-variable style experiment or a causal claim about design preference.

## References and how they are used

| Reference | Applied here |
| --- | --- |
| [ONS typography](https://service-manual.ons.gov.uk/data-visualisation/build-specifications/typography) and [chart elements](https://service-manual.ons.gov.uk/data-visualisation/build-specifications/chart-elements) | Use actual display pixels, a 14px web-text floor and direct labels where practical. The page switches layouts rather than shrinking the desktop chart indefinitely. |
| [Rougier et al., Ten Simple Rules for Better Figures](https://doi.org/10.1371/journal.pcbi.1003833) | Start with a message, adapt to the medium and explain uncertainty in a caption. |
| [Rougier, Scientific Visualization: Python + Matplotlib](https://github.com/rougier/scientific-visualization-book) | Typography and layout are design work, not just selecting a colour palette or trusting defaults. |
| [VisJudgeBench](https://github.com/HKUSTDial/VisJudgeBench) | Keep fidelity, readability and composition separate; do not invent a combined beauty score. Its model and dataset have not been run here. |
| [Heer & Bostock, CHI 2010](https://idl.uw.edu/papers/crowdsourcing-graphical-perception) | Evaluate chart-reading tasks with readers, rather than only checking whether an image rendered. |

The [Nature artwork guide](https://research-figure-guide.nature.com/figures/preparing-figures-our-specifications/)
is a separate reference for journal submissions. A web pixel rule is **not** a
universal paper font-size rule. These PDFs are vector copies of the web layouts,
not journal-compliance certification.

## What is measured

[visual_quality.json](images/visual_quality.json) records checks on the **actual
saved PNG**, not just a separately rendered preview:

- source and intended display dimensions;
- font em-size converted to display pixels, not original point size alone;
- visible text and axes staying inside the canvas;
- pairwise text bounding-box overlaps (1px tolerance at target width);
- existing `Plot.lint()` palette and encoding findings.

The review page is checked in a real browser at viewport widths 900, 600, 360
and 320px. Its image widths are 700, 320, 320 and 280px respectively, with font
sizes still at least 14px. A 700px desktop export deliberately downscaled to
320px fails the font check; it is not accepted as a mobile layout. Arbitrary
Markdown hosts may resize previews differently: use the review page for this
size-specific check.

Text-box checks exclude ticks outside the saved view, but include direct labels
that are outside Matplotlib's automatic layout solver. They do **not** detect
all text/data collisions, evaluate wording, test every foreground/background
contrast pair, or certify accessibility. Label positions are hand-set for these
three separated curves; new data require a fresh layout and review. No core
renderer, default theme, spec schema or required dependency was changed.

[Response greyscale](images/visual_response_gray.png) ·
[Protan view](images/visual_response_protan.png) ·
[Deutan view](images/visual_response_deutan.png). These use linear-sRGB luminance
and the existing Machado simulation. They are review aids, not certification.

## Separate the six VisJudgeBench criteria

| Criterion | Evidence / remaining judgement |
| --- | --- |
| Data fidelity | Raw data, numerical axes, means, CI bounds and RNG isolation are regression-tested. |
| Semantic readability | Font/bounds/text-box checks plus reading tasks; independent reader evaluation pending. |
| Insight discovery | One question per figure; whether readers actually find the intended comparison is unmeasured. |
| Design style | Conventional and restrained; novelty is not rewarded merely for being novel. |
| Visual composition | Browser layout and text boxes checked; human judgement of hierarchy/spacing remains. |
| Color harmony | Consistent groups and grey/CVD views; no independent aesthetic rating. |

Automated pass/fail findings are not values for these six scores. Both
`independent_human_review` and `model_judge` remain `not_run` in the report.
Research such as [ChartJudgeBench](https://arxiv.org/abs/2609.24210) also cautions
against treating an LMM critic's approval as a reliable final judgement.

## Reader check, not yet performed

Show the variants at their intended sizes without “before/after” praise. Ask:

1. Which method has the highest mean at 12 h?
2. Approximately what is the Reference mean at 12 h?
3. Do the bands show observation spread or uncertainty in a mean?

Record correctness and reading time. Leave the numerical table closed during
approximate-reading tasks; use it afterwards for precise lookup. Counterbalance
version order when comparing designs. A small pilot is usability feedback, not
proof of a universally superior design. No reader results have been collected.

## Use the figures in the product

`python -m dashboard build --out dashboard/site_build` rebuilds the reading
layouts, exports and local review/criteria pages under `reading/`, alongside
the existing layer gallery. These are rendered from source, not copied preview
PNGs; links and editable specs are checked.

In `python -m dashboard serve`, use **Start from a sample → Complete figure
drafts**. Choosing an example is a read-only draft request, not a figure edit.
Only **Open figure** replaces the current figure and starts fresh undo history;
export current work first. Failed imports keep both the figure and the submitted
JSON for correction. The editor does not keep page-body snapshots in htmx's
localStorage history cache. Its fit-to-workspace preview is not an actual-size
readability evaluation.

## Regenerate

From a source checkout with render/dev extras:

```bash
uv run python examples/publication_showcase.py
uv run pytest -q tests/test_visual_quality.py tests/test_lint.py tests/test_schema_export.py
uv run pytest -q tests/test_editor_browser.py -k test_visual_review
```

The generator writes desktop PNG/PDF/SVG/specs, mobile PNG/specs, response
vision previews and JSON QA. `python -m scripts.render_docs_demo` includes it.
The old four-panel assets remain historical fixtures and are not regenerated or
called a successful readability baseline.
