# v2 workflow index and evidence boundary

[Run and upgrade (English)](../examples/README.md) · [실행·업그레이드(한국어)](../examples/README.ko.md) · [Finite scope and acceptance gates](V2_SCOPE.md)

## Workflow index

The examples use synthetic or literal inputs; they are starting points, not acceptance of every option combination. The linked source determines the output arguments and any optional providers.

| Row | Runnable starting point and scope / 실행 예제와 범위 |
| --- | --- |
| F01 | [Shared semantics](../examples/shared_semantic_families.py), [raw hue bars](../examples/semantic_colourbars.py), [regression glyphs](../examples/regression_glyphs.py): physical size depends on the mark; hue does not select a regression cohort. |
| F02 | [Explicit calendars](../examples/temporal_axes.py), [mixed temporal grids](../examples/temporal_grids.py): no implicit conversion of strings. |
| C01 | [Nested strip geometry](../examples/strip_categories.py): declared positions, bounded jitter, retained rows. |
| C02 | [Swarm workflow](../examples/swarm_workflow.py), [facets](../examples/swarm_facets.py): bounded native packing. |
| C03 | [Box workflow](../examples/box_workflow.py): supplied summaries and component styling. |
| C04 | [Weighted violin](../examples/weighted_violin.py), [split workflow](../examples/violin_workflow.py): configured Gaussian fits and component ownership. |
| C05 | [Weighted letter values](../examples/weighted_letter_values.py): observed tails and declared mass. |
| C06 | [Weighted counts](../examples/weighted_counts.py), [statistical scales](../examples/statistical_scales.py): explicit denominators and log-domain limits. |
| C07 | [Stable estimates](../examples/statistical_categories.py), [uncertainty](../examples/bar_uncertainty.py): `.bar()` still draws precomputed values. |
| D01 | [Line workflow](../examples/line_workflow.py): pointwise and simultaneous inference are different requests. |
| D02 | [Binning](../examples/histogram_binning.py), [geometries](../examples/histogram_modes.py): preserve mass and declared width semantics. |
| D03 | [Density fields](../examples/density_fields.py): use paired rows, weights and actual bin edges. |
| D04 | [KDE fields](../examples/kde2d_semantics.py), [KDE grids](../examples/kde_grids.py): numeric density, CDF and level mass have different units. |
| D05 | [Full-model HDR](../examples/density_fields.py): declared tolerance, not exact infinite-support mass. |
| D06 | [ECDF semantics](../examples/ecdf_semantics.py), [paired CDF](../examples/density_fields.py): empirical mass is neither a smoothed density nor fitted survival. |
| D07 | [Rug workflow](../examples/rug_workflow.py): tick height does not change observations or the value scale. |
| O01 | [Named pipeline](../examples/coordinate_pipeline.py): bounded transforms, moves and scales; not an upstream objects API. |
| R01 | [Regression modes](../examples/regression_modes.py), [configured regression](../examples/regression_workflow.py): optional advanced effects and explicit inference. |
| R02 | [Diagnostics](../examples/regression_workflow.py), [held-out glyphs](../examples/regression_glyphs.py): model, diagnostics and trend remain separate. |
| M01 | [Heatmap controls](../examples/heatmap_controls.py): annotations need not be calibration values. |
| M02 | [Matrix workflow](../examples/matrix_workflow.py), [cluster profiles](../examples/clustered_profiles.py): optional SciPy, aligned tracks and explicitly handled missingness. |
| G01 | [Facet builders](../examples/facet_builders.py), [faceted responses](../examples/faceted_responses.py): fixed cell identities and deliberate template replacement. |
| G02 | [Pair observations](../examples/pair_observations.py), [weighted grids](../examples/weighted_grids.py): per-cell complete cases and complementary diagonals. |
| G03 | [Joint observations](../examples/joint_observations.py), [weighted grids](../examples/weighted_grids.py), [temporal grids](../examples/temporal_grids.py): linked selectors, not one shared measurement/density axis. |
| N01 | [Planar marks](../examples/native_planar_geometry.py): finite segments and signed asymmetric endpoints. |
| N02 | [Bars and pie](../examples/native_bars_and_pie.py): original signed input, explicit bases and wedge geometry. |
| N03 | [Stem workflow](../examples/stem_workflow.py): true baseline and actual native coordinates. |
| N04 | [Stairs workflow](../examples/stairs_workflow.py): supplied or derived bins, explicit measure and no invented missing heights. |
| N05 | [Event lanes](../examples/native_lane_workflow.py): original positions and explicit train spacing. |
| N06 | [Interval lanes](../examples/native_lane_workflow.py): original intervals and elapsed durations. |
| N07 | [Grid fields](../examples/grid_field_workflow.py): nonuniform cells, masks and direct pixels are distinct. |
| N08 | [Triangle workflow](../examples/triangle_workflow.py): explicit topology and declared scalar owner. |
| N09 | [Vector workflow](../examples/vector_workflow.py): native barbs and trajectories, no cross-provider path-equality guarantee. |
| N10 | [Spatial workflow](../examples/spatial_workflow.py): full grids, physical extents and display-only camera. |
| N11 | [Signal spectra](../examples/signal_spectra.py): explicit FFT/window and sampling units. |
| N12 | [Axis controls](../examples/axis_controls.py): bounded locators and finite named conversions. |
| N13 | [Panel layouts](../examples/panel_layouts.py): stable IDs, actual insets and named sharing. |
| N14 | [Native annotations](../examples/native_annotations.py): anchors, table geometry and finite effects; not arbitrary callbacks. |
| P01 | [Scalar display](../examples/scalar_display.py): common raw domain and individually positioned guide ticks. |
| E01 | [Local edit–undo–redo–export walkthrough](../examples/README.md#run-and-edit-an-example); installed usability is assessed feature by feature. |
| Q01 | [Scientific quality](../examples/scientific_quality.py): representative synthetic readability and failure checks, not physical print certification. |
| DOC01 | [Source and old-file recipe](../examples/README.md), [editable layer gallery](PLOT_GALLERY.md); verify documented old 0.1 reopening and actual example output. |
| REL01 | [Required local artifact gates](V2_SCOPE.md#product-wide-rows) and [contributor check commands](../CONTRIBUTING.md); a rendered example cannot substitute for release qualification. |

## How to read the evidence

- The [scope ledger](V2_SCOPE.md) and its linked local receipts distinguish source-focused checks, scoped installed milestones, missing applicability and full-product gates. A valid JSON document, rendered figure or passing source test alone does not verify every applicable row.
- P01's earlier installed milestone covered raw colour guides and real local editor actions. The grid milestone covered live facets, weighted corner pairs and a joint calendar case without fixed authored ticks; the fixed-tick input was a separate recorded failure and source correction. Native art has its own later source and scoped installed evidence. None of those results is the final 2.0.0 deliverable or a claim for all combinations.
- The frozen local **2.0.0** source (serialized spec **0.1**) recorded **6,651 passed, 46 optional skips, and zero failures** in the locked Linux Python 3.12 run. Required Chromium and TeX cases ran. This public source preserves the upstream audit changes and presents local evidence paths symbolically: `$CHECKOUT` denotes the source checkout, `$LOCAL_EVIDENCE` denotes local run records or artifacts, and `$PROVIDER` denotes tool or runtime providers. These symbols are not download links. Measured hashes in the evidence identify the original local inputs and records, not this public projection. This is not a publication, all-platform validation, or physical-print qualification.
