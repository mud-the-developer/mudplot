export const repoUrl = 'https://github.com/mud-the-developer/mudplot';
export const languages = ['en', 'ko'];

// Each row is [slug, English source, Korean source]. A missing translation
// stays English-only, except explicitly shared bilingual documents.
export const overview = ['index', 'docs/GUIDE.md', 'docs/GUIDE.ko.md'];
export const groups = [
  {
    slug: 'start',
    titles: ['Getting started', '시작하기'],
    pages: [
      ['install', 'docs/INSTALL.md', 'docs/INSTALL.ko.md'],
      ['examples', 'examples/README.md', 'examples/README.ko.md'],
      ['compatibility', 'docs/COMPATIBILITY.md', 'docs/COMPATIBILITY.ko.md'],
      ['security', 'SECURITY.md', 'SECURITY.ko.md'],
    ],
  },
  {
    slug: 'plotting',
    titles: ['Plotting workflows', '플로팅 워크플로'],
    pages: [
      ['plot-gallery', 'docs/PLOT_GALLERY.md', 'docs/PLOT_GALLERY.md'],
      ['comparisons', 'docs/COMPARISONS.md', 'docs/COMPARISONS.ko.md'],
      ['uncertainty', 'docs/UNCERTAINTY.md', 'docs/UNCERTAINTY.ko.md'],
      ['statistical-estimates', 'docs/STATISTICAL_WORKFLOW.md', 'docs/STATISTICAL_WORKFLOW.ko.md'],
      ['weighted-counts', 'docs/WEIGHTED_COUNTS.md', 'docs/WEIGHTED_COUNTS.ko.md'],
      ['regression', 'docs/REGRESSION.md', 'docs/REGRESSION.ko.md'],
      ['lines', 'docs/LINE_WORKFLOW.md', 'docs/LINE_WORKFLOW.ko.md'],
      ['density-fields', 'docs/DENSITY_FIELDS.md', 'docs/DENSITY_FIELDS.ko.md'],
      ['boxes', 'docs/BOX_WORKFLOW.md', 'docs/BOX_WORKFLOW.ko.md'],
      ['violins', 'docs/VIOLIN_WORKFLOW.md', 'docs/VIOLIN_WORKFLOW.ko.md'],
      ['histogram-count-roles', 'docs/SEMANTIC_BODIES.md', 'docs/SEMANTIC_BODIES.ko.md'],
      ['swarm-size', 'docs/SWARM_SIZE.md', 'docs/SWARM_SIZE.ko.md'],
      ['swarm-categorical-size', 'docs/SWARM_CATEGORICAL_SIZE.md', 'docs/SWARM_CATEGORICAL_SIZE.ko.md'],
      ['swarm-shared-size', 'docs/SWARM_SHARED_SIZE.md', 'docs/SWARM_SHARED_SIZE.ko.md'],
      ['swarm-facets', 'docs/SWARM_FACETS.md', 'docs/SWARM_FACETS.ko.md'],
      ['heatmaps', 'docs/HEATMAP.md', 'docs/HEATMAP.ko.md'],
      ['clustermaps', 'docs/CLUSTERMAP.md', 'docs/CLUSTERMAP.ko.md'],
      ['facets', 'docs/FACETS.md', 'docs/FACETS.ko.md'],
      ['pair-grids', 'docs/PAIR_GRID.md', 'docs/PAIR_GRID.ko.md'],
      ['joint-grids', 'docs/JOINT_GRID.md', 'docs/JOINT_GRID.ko.md'],
      ['panel-layouts', 'docs/PANEL_LAYOUTS.md', 'docs/PANEL_LAYOUTS.ko.md'],
      ['native-geometry', 'docs/NATIVE_GEOMETRY.md', 'docs/NATIVE_GEOMETRY.ko.md'],
      ['interval-bands', 'docs/BROKEN_BARH.md', 'docs/BROKEN_BARH.ko.md'],
      ['event-trains', 'docs/EVENTPLOT.md', 'docs/EVENTPLOT.ko.md'],
      ['stairs', 'docs/STAIRS.md', 'docs/STAIRS.ko.md'],
      ['stems', 'docs/STEM.md', 'docs/STEM.ko.md'],
      ['temporal-axes', 'docs/TEMPORAL_AXES.md', 'docs/TEMPORAL_AXES.ko.md'],
      ['coordinate-pipeline', 'docs/COORDINATE_PIPELINE.md', 'docs/COORDINATE_PIPELINE.ko.md'],
    ],
  },
  {
    slug: 'guides',
    titles: ['Publication and tools', '출판과 도구'],
    pages: [
      ['publication', 'docs/PUBLICATION.md', 'docs/PUBLICATION.ko.md'],
      ['demos', 'docs/DEMO.md', 'docs/DEMO.md'],
      ['visual-quality', 'docs/VISUAL_QUALITY.md', 'docs/VISUAL_QUALITY.ko.md'],
      ['scientific-quality', 'docs/SCIENTIFIC_QUALITY.md'],
      ['provenance', 'docs/OUTPUT_PROVENANCE.md'],
      ['automation', 'docs/AUTOMATION.md', 'docs/AUTOMATION.ko.md'],
      ['performance', 'docs/PERFORMANCE.md', 'docs/PERFORMANCE.ko.md'],
    ],
  },
  {
    slug: 'reference',
    titles: ['Reference', '레퍼런스'],
    pages: [
      ['api', 'docs/REFERENCE.md'],
      ['coverage', 'docs/FEATURE_COVERAGE.md', 'docs/FEATURE_COVERAGE.ko.md'],
      ['design', 'DESIGN.md', 'DESIGN.ko.md'],
      ['changelog', 'CHANGELOG.md', 'CHANGELOG.md'],
    ],
  },
];
