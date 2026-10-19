# /// script
# requires-python = ">=3.10,<3.11"
# dependencies = [
#   "matplotlib==3.8.0",
#   "numpy==1.23.0",
#   "pytest==9.0.3",
#   "jsonschema>=4",
#   "statsmodels==0.14.1",
#   "scipy==1.10.0",
# ]
# ///
"""Run the render/layout contract against the declared minimum dependencies."""

from __future__ import annotations

import importlib.metadata
import json
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
TESTS = (
    "tests/test_data.py",
    "tests/test_review_sql_ownership.py",
    "tests/test_review_table_formats.py",
    "tests/test_review_data_contracts.py",
    "tests/test_review_data_edges.py",
    "tests/test_review_group_identity.py",
    "tests/test_review_json_policies.py",
    "tests/test_review_error_context.py",
    "tests/test_review_missing_data.py",
    "tests/test_review_temporal_precision.py",
    "tests/test_review_scalar_boundaries.py",
    "tests/test_review_state_contracts.py",
    "tests/test_required_test_paths.py",
    "tests/test_review_ci_effects.py",
    "tests/test_review_core_boundaries.py",
    "tests/test_review_structure_limits.py",
    "tests/test_review_layer_limits.py",
    "tests/test_review_optional_errors.py",
    "tests/test_review_history_policies.py",
    "tests/test_review_history_checkpoint.py",
    "tests/test_review_performance_guidance.py",
    "tests/test_review_editor_paths.py",
    "tests/test_review_http_boundaries.py",
    "tests/test_review_concurrent_render.py",
    "tests/test_review_output_contracts.py",
    "tests/test_review_provenance_recipe.py",
    "tests/test_review_effect_budget.py",
    "tests/test_review_output_lifecycle.py",
    "tests/test_review_offline_execution.py",
    "tests/test_review_body_framing.py",
    "tests/test_review_full_spec_fields.py",
    "tests/test_review_color_references.py",
    "tests/test_review_palette_reports.py",
    "tests/test_review_redundant_encoding.py",
    "tests/test_review_numeric_geometry.py",
    "tests/test_review_projection_colours.py",
    "tests/test_review_export_determinism.py",
    "tests/test_layers.py",
    "tests/test_layout.py",
    "tests/test_review_preset_sizes.py",
    "tests/test_review_layout_boundaries.py",
    "tests/test_review_font_boundaries.py",
    "tests/test_review_mixed_guides.py",
    "tests/test_review_style_dpi.py",
    "tests/test_facets.py",
    "tests/test_joint_grid.py",
    "tests/test_pair_grid.py",
    "tests/test_grid_kde.py",
    "tests/test_heatmap_options.py",
    "tests/test_regression_models.py",
    "tests/test_review_regression_degenerate.py",
    "tests/test_clustermap.py",
    "tests/test_raw_group_order.py",
    "tests/test_new_layers.py",
    "tests/test_review_bivariate_limits.py",
    "tests/test_stabilization.py",
    "tests/test_references.py",
    "tests/test_review_pgf_bundle.py",
    "tests/test_review_string_boundaries.py",
    "tests/test_dashboard.py",
    "tests/test_review_accessibility.py",
    "tests/test_schema_export.py",
    "tests/test_review_doc_contracts.py",
    "tests/test_review_generated_drift.py",
    "tests/test_review_editor_assets.py",
    "tests/test_visual_quality.py",
    "tests/test_bar_uncertainty.py",
    "tests/test_review_annotation_alpha.py",
    "tests/test_review_coordinate_frames.py",
    "tests/test_review_response_generation.py",
    "tests/test_statistics.py",
    "tests/test_statistical_plots.py",
    "tests/test_lineplot.py",
    "tests/test_line_semantics.py",
    "tests/test_scatter_semantics.py",
    "tests/test_shared_semantics.py",
    "tests/test_weighted_statistics.py",
    "tests/test_categorical_statistics.py",
    "tests/test_box_violin.py",
    "tests/test_swarm.py",
    "tests/test_boxen.py",
    "tests/test_categorical_scales.py",
    "tests/test_violin_options.py",
    "tests/test_weighted_violin.py",
    "tests/test_distribution_components.py",
    "tests/test_statistical_scales.py",
    "tests/test_ecdf.py",
    "tests/test_histogram_statistics.py",
    "tests/test_kde_options.py",
    "tests/test_kde2d.py",
)


def main() -> int:
    print(
        json.dumps(
            {
                "minimum_environment": {
                    "python": sys.version.split()[0],
                    "executable": sys.executable,
                    "versions": {
                        name: importlib.metadata.version(name)
                        for name in (
                            "numpy",
                            "matplotlib",
                            "statsmodels",
                            "scipy",
                            "pytest",
                        )
                    },
                }
            }
        ),
        flush=True,
    )
    os.chdir(ROOT)
    sys.path.insert(0, str(ROOT))
    return pytest.main(
        ["-q", "--disable-warnings", "--durations=25", "-m", "not browser", *TESTS]
    )


if __name__ == "__main__":
    raise SystemExit(main())
