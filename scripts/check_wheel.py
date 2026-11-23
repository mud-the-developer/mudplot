"""Build release distributions and verify their required packaged files."""

from __future__ import annotations

import argparse
import glob
import hashlib
import os
import shutil
import subprocess
import sys
import sysconfig
import tarfile
import tempfile
import textwrap
import zipfile
from email.parser import Parser
from pathlib import Path

HTMX_SHA256 = "449317ade7881e949510db614991e195c3a099c4c791c24dacec55f9f4a2a452"

SDIST_FILES = (
    "LICENSE",
    "README.md",
    "README.ko.md",
    "SECURITY.md",
    "SECURITY.ko.md",
    "pyproject.toml",
    "uv.lock",
    "schemas/capabilities.json",
    "schemas/figure_spec.schema.json",
    "tests/fixtures/review_json_boundaries.json",
    "tests/fixtures/review_state_paths.json",
    "tests/fixtures/review_http_boundaries.json",
    "tests/fixtures/review_full_spec_fields.json",
    "tests/fixtures/sharma_ciede2000.txt",
    "scripts/check_python_bridge_paths.py",
    "scripts/check_request_body_limits.py",
    "docs/PLOT_GALLERY.md",
    "docs/GUIDE.md",
    "docs/GUIDE.ko.md",
    "docs/INSTALL.md",
    "docs/INSTALL.ko.md",
    "docs/PUBLICATION.md",
    "docs/PUBLICATION.ko.md",
    "docs/AUTOMATION.md",
    "docs/AUTOMATION.ko.md",
    "docs/UNCERTAINTY.md",
    "docs/UNCERTAINTY.ko.md",
    "docs/COMPARISONS.md",
    "docs/COMPARISONS.ko.md",
    "examples/README.md",
    "examples/README.ko.md",
    "docs/V2_EXAMPLE_EVIDENCE.md",
    "docs/V2_SCOPE.md",
    "docs/V2_SCOPE.ko.md",
    "docs/WEIGHTED_COUNTS.md",
    "docs/WEIGHTED_COUNTS.ko.md",
    "docs/TEMPORAL_AXES.md",
    "docs/TEMPORAL_AXES.ko.md",
    "examples/temporal_axes.py",
    "examples/temporal_grids.py",
    "examples/histogram_modes.py",
    "examples/histogram_binning.py",
    "examples/weighted_counts.py",
    "examples/shared_semantic_families.py",
    "examples/rug_workflow.py",
    "tests/test_rug.py",
    "docs/DENSITY_FIELDS.md",
    "docs/DENSITY_FIELDS.ko.md",
    "examples/density_fields.py",
    "tests/test_paired_fields.py",
    "tests/test_kernel_fields.py",
    "tests/test_full_hdr.py",
    "mudplot/_density.py",
    "mudplot/_density_input.py",
    "mudplot/_histogram2d.py",
    "mudplot/_ecdf2d.py",
    "mudplot/_kernel_math.py",
    "mudplot/_hdr.py",
    "mudplot/_hdr_render.py",
    "mudplot/_field_budget.py",
    "mudplot/_field_render.py",
    "mudplot/_kde2d_render.py",
    "examples/signal_spectra.py",
    "tests/test_signal_spectra.py",
    "mudplot/_spectrum.py",
    "examples/axis_controls.py",
    "tests/test_axis_controls.py",
    "mudplot/_axis_options.py",
    "mudplot/_axis_render.py",
    "mudplot/_matplotlib_notice.txt",
    "docs/PANEL_LAYOUTS.md",
    "docs/PANEL_LAYOUTS.ko.md",
    "examples/panel_layouts.py",
    "tests/test_panel_layout.py",
    "mudplot/_layout.py",
    "mudplot/_layout_render.py",
    "docs/VIOLIN_WORKFLOW.md",
    "docs/VIOLIN_WORKFLOW.ko.md",
    "examples/violin_workflow.py",
    "tests/test_violin_workflow.py",
    "tests/test_violin_editor_browser.py",
    "mudplot/_violin_render.py",
    "docs/STATISTICAL_WORKFLOW.md",
    "docs/STATISTICAL_WORKFLOW.ko.md",
    "examples/statistical_workflow.py",
    "tests/test_statistical_workflow.py",
    "tests/test_statistical_editor_browser.py",
    "tests/test_semantic_families.py",
    "tests/test_rust_specialized_controls.py",
    "mudplot/_editor.py",
    "examples/swarm_workflow.py",
    "tests/test_swarm_workflow.py",
    "tests/test_live_facet_template.py",
    "tests/test_swarm_editor_browser.py",
    "mudplot/_swarm_scope.py",
    "mudplot/_swarm_semantics.py",
    "mudplot/_box.py",
    "mudplot/_box_render.py",
    "tests/test_box_workflow.py",
    "tests/test_box_editor_browser.py",
    "examples/box_workflow.py",
    "docs/BOX_WORKFLOW.md",
    "docs/BOX_WORKFLOW.ko.md",
    "mudplot/_boxen.py",
    "mudplot/_boxen_render.py",
    "tests/test_weighted_boxen.py",
    "tests/test_boxen_editor_browser.py",
    "examples/weighted_letter_values.py",
    "docs/images/weighted_letter_values.png",
    "docs/images/weighted_letter_values.svg",
    "docs/images/weighted_letter_values.mplot.json",
    "tests/test_weighted_counts.py",
    "tests/test_count_scopes.py",
    "tests/test_temporal_coordinates.py",
    "tests/test_temporal_axes.py",
    "tests/test_temporal_statistics.py",
    "tests/test_temporal_distributions.py",
    "tests/test_temporal_bivariate.py",
    "tests/test_temporal_raw.py",
    "tests/test_temporal_native.py",
    "tests/test_temporal_grids.py",
    "tests/test_temporal_secondary.py",
    "tests/test_histogram_fill.py",
    "tests/test_histogram_modes.py",
    "tests/test_histogram_bin_rules.py",
    "tests/test_histogram_binning.py",
    "mudplot/_histogram_bins.py",
    "mudplot/_temporal.py",
    "mudplot/_temporal_data.py",
    "mudplot/_temporal_render.py",
    "docs/COMPATIBILITY.md",
    "docs/COMPATIBILITY.ko.md",
    "docs/VISUAL_QUALITY.md",
    "docs/VISUAL_QUALITY.ko.md",
    "docs/VISUAL_REVIEW.html",
    "docs/FACETS.md",
    "docs/FACETS.ko.md",
    "docs/JOINT_GRID.md",
    "docs/JOINT_GRID.ko.md",
    "docs/PAIR_GRID.md",
    "docs/PAIR_GRID.ko.md",
    "docs/HEATMAP.md",
    "docs/HEATMAP.ko.md",
    "docs/REGRESSION.md",
    "docs/REGRESSION.ko.md",
    "docs/CLUSTERMAP.md",
    "docs/CLUSTERMAP.ko.md",
    "examples/clustered_profiles.py",
    "docs/images/clustered_profiles.png",
    "docs/images/clustered_profiles.pdf",
    "docs/images/clustered_profiles.svg",
    "docs/images/clustered_profiles.mplot.json",
    "examples/regression_modes.py",
    *(
        f"docs/images/{name}.{extension}"
        for name in (
            "regression_residual",
            "regression_logx",
            "regression_robust",
            "regression_logistic",
            "regression_lowess",
        )
        for extension in ("png", "pdf", "svg", "mplot.json")
    ),
    "examples/heatmap_controls.py",
    "docs/images/heatmap_controls.png",
    "docs/images/heatmap_controls.pdf",
    "docs/images/heatmap_controls.svg",
    "docs/images/heatmap_controls.mplot.json",
    "examples/pair_observations.py",
    "examples/kde_grids.py",
    "docs/images/kde_joint.png",
    "docs/images/kde_joint.pdf",
    "docs/images/kde_joint.svg",
    "docs/images/kde_joint.mplot.json",
    "docs/images/kde_pair.png",
    "docs/images/kde_pair.pdf",
    "docs/images/kde_pair.svg",
    "docs/images/kde_pair.mplot.json",
    "docs/images/pair_observations.png",
    "docs/images/pair_observations.pdf",
    "docs/images/pair_observations.svg",
    "docs/images/pair_observations.mplot.json",
    "examples/joint_observations.py",
    "docs/images/joint_observations.png",
    "docs/images/joint_observations.pdf",
    "docs/images/joint_observations.svg",
    "docs/images/joint_observations.mplot.json",
    "examples/faceted_responses.py",
    "docs/images/faceted_responses.png",
    "docs/images/faceted_responses.pdf",
    "docs/images/faceted_responses.svg",
    "docs/images/faceted_responses.mplot.json",
    "docs/images/visual_before.png",
    "docs/images/visual_before.pdf",
    "docs/images/visual_before.svg",
    "docs/images/visual_before.mplot.json",
    "docs/images/visual_after.png",
    "docs/images/visual_after.pdf",
    "docs/images/visual_after.svg",
    "docs/images/visual_after.mplot.json",
    "docs/images/visual_after_gray.png",
    "docs/images/visual_after_protan.png",
    "docs/images/visual_after_deutan.png",
    "docs/images/visual_quality.json",
    "docs/images/visual_response.png",
    "docs/images/visual_response.pdf",
    "docs/images/visual_response.svg",
    "docs/images/visual_response.mplot.json",
    "docs/images/visual_endpoint.png",
    "docs/images/visual_endpoint.pdf",
    "docs/images/visual_endpoint.svg",
    "docs/images/visual_endpoint.mplot.json",
    "docs/images/visual_response_mobile.png",
    "docs/images/visual_response_mobile.mplot.json",
    "docs/images/visual_endpoint_mobile.png",
    "docs/images/visual_endpoint_mobile.mplot.json",
    "docs/images/visual_response_gray.png",
    "docs/images/visual_response_protan.png",
    "docs/images/visual_response_deutan.png",
    "examples/publication_showcase.py",
    "examples/scientific_quality.py",
    "docs/SCIENTIFIC_QUALITY.md",
    "tests/test_smart_quality.py",
    "tests/test_recommend_precision.py",
    "tests/test_output_atomicity.py",
    "docs/images/scientific_quality/report.json",
    *(
        f"docs/images/scientific_quality/{name}_{phase}.png"
        for name in (
            "legend_collision",
            "shared_legend",
            "temporal_scatter",
            "metric_semantics",
        )
        for phase in ("before", "after")
    ),
    "scripts/render_docs_demo.py",
    "scripts/audit_dependencies.py",
    "scripts/audit_dependencies.py.lock",
    "scripts/check_minimum_versions.py",
    "scripts/check_minimum_versions.py.lock",
    "dashboard/README.md",
    "dashboard/README.ko.md",
    "dashboard/__init__.py",
    "dashboard/__main__.py",
    "dashboard/editor_server.py",
    "dashboard/editor_view.py",
    "dashboard/markdown_lite.py",
    "dashboard/plot_gallery.py",
    "dashboard/samples.py",
    "dashboard/site.py",
    "dashboard/static/htmx.min.js",
    "dashboard/static/editor.js",
    "dashboard/static/htmx.LICENSE",
    "mudplot-editor/Cargo.toml",
    "mudplot-editor/Cargo.lock",
    "mudplot-editor/README.md",
    "mudplot-editor/README.ko.md",
    "mudplot-editor/default_spec.json",
    "mudplot-editor/src/lib.rs",
    "mudplot-editor/src/main.rs",
    "mudplot-editor/src/model.rs",
    "mudplot-editor/src/python.rs",
    "mudplot-editor/src/specialized.rs",
    "mudplot-editor/templates/page.html",
    "mudplot-editor/templates/fragment.html",
)


def _smoke_installed(wheel: str, out_dir: str) -> None:
    prefix = Path(out_dir) / "installed"
    paths = sysconfig.get_paths(vars={"base": str(prefix), "platbase": str(prefix)})
    console = Path(paths["scripts"]) / ("mudplot.exe" if os.name == "nt" else "mudplot")
    subprocess.run(
        [
            "uv",
            "pip",
            "install",
            "--python",
            sys.executable,
            "--no-deps",
            "--no-index",
            "--prefix",
            str(prefix),
            wheel,
        ],
        check=True,
    )
    smoke = textwrap.dedent("""
        import json
        import struct
        import subprocess
        import sys
        from pathlib import Path
        import matplotlib.pyplot as plt
        import mudplot as mp
        import numpy as np

        assert Path(mp.__file__).resolve().is_relative_to(Path(sys.argv[1]).resolve())
        console = sys.argv[2]
        p = (mp.plot({'method':['A','B'], 'score':[0.97,0.99]})
             .bar('method','score',group='method')
             .labels(x='Method',y='Score (a.u.)').ylim(0,1).size(3.5,2.6))
        original = p.to_json()
        spec = Path('scientific input 한글.json')
        mp.save_spec(p.spec, spec)
        for policy, extension in ((None,'png'),('smart','png'),('smart-print','svg')):
            target = Path(f'figure & {policy}.{extension}')
            figure = p.save(target, layout_policy=policy)
            try:
                assert target.stat().st_size > 100
                if policy:
                    assert not any(
                        i['level']=='error' for i in figure.mudplot_quality['issues']
                    )
                    json.dumps(figure.mudplot_quality, allow_nan=False)
                if extension == 'png':
                    assert struct.unpack('>II',target.read_bytes()[16:24]) == (1050,780)
            finally:
                plt.close(figure)
        for args in (
            ['capabilities'],
            ['render',str(spec),'console & smart.png','--layout-policy','smart'],
            ['lint',str(spec),'--layout-policy','smart','--json'],
        ):
            result = subprocess.run(
                [console,*args],check=True,capture_output=True,text=True
            )
            if args[0] in {'capabilities','lint'}:
                payload = json.loads(result.stdout)
                if args[0] == 'lint':
                    assert payload['ok']
        assert Path('console & smart.png').is_file()
        keep = Path('keep.png')
        keep.write_bytes(b'previous output')
        result = subprocess.run(
            [console,'render',str(spec),str(keep),'--layout-policy','invalid'],
            capture_output=True,text=True,
        )
        assert result.returncode == 2 and keep.read_bytes() == b'previous output'
        assert p.to_json() == original == spec.read_text(encoding='utf-8')
        weighted = (
            mp.plot({'x':[1,1,10,10],'g':['u','v','u','v'],'w':[2,3,4,1]})
            .countplot('x',group='g',weights='w',stat='percent',
                       normalize_scope='category',stack=True,baseline=1,
                       native_scale=True)
            .xscale('log').yscale('log').size(4,3)
        )
        weighted_json = weighted.to_json()
        mp.save_spec(weighted.spec, 'weighted.json')
        assert mp.Plot.from_json(weighted_json).spec == weighted.spec
        figure = weighted.save('weighted.png')
        try:
            assert [p.get_y()+p.get_height() for p in
                    figure.axes[0].containers[-1]] == [100,100]
        finally:
            plt.close(figure)
        subprocess.run([console,'render','weighted.json','weighted.svg'],check=True)
        assert Path('weighted.png').stat().st_size > 100
        assert Path('weighted.svg').stat().st_size > 100
        assert weighted.to_json() == weighted_json
        temporal = (
            mp.plot({'t':['2026-01-01','2026-01-02','2026-01-11'],'v':[1,2,3]})
            .line('t','v').date_axis('x',timezone='UTC').size(6,3)
        )
        temporal_json = temporal.to_json()
        mp.save_spec(temporal.spec, 'temporal.json')
        assert mp.Plot.from_json(temporal_json).spec == temporal.spec
        assert mp.apply(temporal.action_log) == temporal.spec
        figure = temporal.save('temporal.png')
        try:
            assert list(figure.axes[0].lines[0].get_xdata()) == [20454,20455,20464]
        finally:
            plt.close(figure)
        subprocess.run([console,'render','temporal.json','temporal.svg'],check=True)
        assert Path('temporal.png').stat().st_size > 100
        assert Path('temporal.svg').stat().st_size > 100
        assert temporal.to_json() == temporal_json
        assert temporal.spec.data.columns['t'] == [
            '2026-01-01','2026-01-02','2026-01-11'
        ]
        from dataclasses import replace
        rug_data = {'v':[4,1,4], 's':[0,1,2], 'g':['A','B','A']}
        rug = (mp.plot(rug_data).size(6,4).secondary_yaxis('Observations')
               .rug('v',orient='h',axis='y2',height=0.2,
                    semantics={'size':'s','sizes':[0,4],
                               'style':'g','dashes':['--',':']}))
        rug_before = rug.to_json()
        layer = rug.spec.panels[0].layers[0]
        rug.dispatch(mp.actions.RemoveLayer(0))
        rug.dispatch(mp.actions.AddLayer(replace(layer,width=0.3)))
        rug_edited = rug.to_json()
        rug.store.undo()
        rug.store.undo()
        assert rug.to_json() == rug_before
        rug.store.redo()
        rug.store.redo()
        assert rug.to_json() == rug_edited
        assert mp.apply(rug.action_log) == rug.spec
        mp.save_spec(rug.spec,'rug.json')
        reopened = mp.Plot.from_json(Path('rug.json').read_text())
        for extension in ('png','svg','pdf'):
            figure = reopened.save('rug.'+extension)
            try:
                collection = figure.axes[1].collections[0]
                assert [s.tolist() for s in collection.get_segments()] == [
                    [[1,4],[0.7,4]], [[1,1],[0.7,1]], [[1,4],[0.7,4]]
                ]
                assert list(collection.get_linewidths()) == [0,2,4]
            finally:
                plt.close(figure)
        subprocess.run([console,'render','rug.json','rug-cli.png'],check=True)
        assert reopened.spec.data.columns == rug_data
        import copy
        swarm_data = {'c':['A','A','B','B'],'v':[1,1.01,2,2.01],
                      'h':['u','v']*2,'s':[1,2]*2,'d':['A','B']*2,
                      'cell':['left']*2+['right']*2}
        swarm = mp.plot(swarm_data).size(9,5)
        for _ in range(2):
            swarm.swarmplot('c','v',pack_scope='physical',semantics={
                'hue':'h','size':'s','sizes':[3,7],'style':'d','markers':['s','^']})
        swarm.facet(col='cell',col_order=['left','empty','right'],live=True)
        local = swarm.to_json()
        template = copy.deepcopy(swarm.spec.facet_template.template)
        for member in template.layers:
            member.semantics.markers = ['D','v']
        swarm.facet_template(template)
        edited = swarm.to_json()
        swarm.store.undo()
        assert swarm.to_json()==local
        swarm.store.redo()
        assert swarm.to_json()==edited
        assert mp.apply(swarm.action_log)==swarm.spec
        mp.save_spec(swarm.spec,'swarm-live.json')
        restored = mp.Plot.from_json(Path('swarm-live.json').read_text())
        from matplotlib.markers import MarkerStyle
        marker = MarkerStyle('D')
        expected_path = marker.get_path().transformed(marker.get_transform())
        for extension in ('png','svg','pdf'):
            figure = restored.save('swarm-live.'+extension)
            try:
                assert [len(a.collections) for a in figure.axes]==[2,0,2]
                collection = figure.axes[0].collections[0]
                assert list(collection.get_sizes())==[9,49]
                assert (collection.get_paths()[0].vertices.tolist()
                        ==expected_path.vertices.tolist())
                assert [float(v[1]) for v in collection.get_offsets()]==[1,1.01]
            finally:
                plt.close(figure)
        subprocess.run([console,'render','swarm-live.json','swarm-live-cli.png'],check=True)
        assert restored.spec.data.columns==swarm_data
        import numpy as np
        raw_box = mp.plot({'c':['A']*4,'v':[1,2,3,30]}).box(
            'c','v',median_ci={'level':90,'n_boot':31,'seed':7},cap_fraction=.8)
        figure = raw_box.save('box-raw.png')
        try:
            assert list(figure.axes[0].lines[4].get_ydata()) == [2.5,2.5]
            assert len(figure.axes[0].patches[0].get_path().vertices) == 12
        finally:
            plt.close(figure)
        box_data = {'c':['2026-01-01','2026-07-01'],'med':[2,4],
            'q1':[1,3],'q3':[3,5],'lo':[.5,2],'hi':[4,6],
            'cl':[1.5,3.5],'ch':[2.5,4.5],'out':[[5],[7]],
            'h':[True,1],'m':[1,3],'s':['A','B'],
            'cohort':['left','right'],'id':['source-b','source-a']}
        boxed = mp.plot(box_data).size(12,7).secondary_yaxis('Response')
        boxed.date_axis('x',timezone='UTC').bxp('c','med',
            q1='q1',q3='q3',whislo='lo',whishi='hi',cilo='cl',cihi='ch',
            fliers='out',notch=True,axis='y2',cap_fraction=.25,
            semantics={'scale_id':'installed-box','hue':'h','size':'m',
                       'size_norm':[1,3],'sizes':[1,2],'style':'s','markers':['D','^']},
            hue_components=[{'level':True,'components':{'cap':{'color':'red'}}},
                            {'level':1,'components':{'cap':{'color':'blue'}}}])
        boxed.facet(col='cohort',col_order=['left','empty','right'],
                    col_wrap=2,live=True).layout(2,2,width_ratios=[3,2])
        boxed.dispatch(mp.actions.SetTitle('Cell-local box',panel=0))
        local_box = boxed.to_json()
        template = copy.deepcopy(boxed.spec.facet_template.template)
        template.layers[0].box.cap_fraction = 1
        boxed.facet_template(template)
        edited_box = boxed.to_json()
        boxed.store.undo()
        assert boxed.to_json() == local_box
        boxed.store.redo()
        assert boxed.to_json() == edited_box
        assert mp.apply(boxed.action_log) == boxed.spec
        mp.save_spec(boxed.spec,'box-live.json')
        boxed = mp.Plot.from_json(Path('box-live.json').read_text())
        for extension in ('png','svg','pdf'):
            figure = boxed.save('box-live.'+extension)
            try:
                axes = [a for a in figure.axes if a.get_ylabel()=='Response']
                real = [
                    [p for p in a.patches if len(p.get_path().vertices)]
                    for a in axes
                ]
                assert [len(p) for p in real] == [1,0,1]
                assert [real[0][0].get_linewidth(),real[2][0].get_linewidth()]==[1,2]
                np.testing.assert_allclose(
                    np.ptp(np.asarray(axes[0].lines[2].get_xdata())),181*.8/2)
                assert axes[0].lines[2].get_color()=='red'
                assert axes[2].lines[2].get_color()=='blue'
                assert list(axes[0].lines[5].get_ydata())==[5]
                assert list(axes[2].lines[5].get_ydata())==[7]
            finally:
                plt.close(figure)
        subprocess.run([console,'render','box-live.json','box-live-cli.png'],check=True)
        assert struct.unpack(
            '>II',Path('box-live-cli.png').read_bytes()[16:24]
        )==(3600,2100)
        accepted_png=Path('box-live-cli.png').read_bytes()
        bad=boxed.spec.to_dict()
        for panel in bad['panels']:
            panel['layers'][0]['box']['summary']['q1']='hi'
        Path('box-bad.json').write_text(json.dumps(bad))
        rejected=subprocess.run([console,'render','box-bad.json','box-live-cli.png'],
                                capture_output=True,text=True)
        assert rejected.returncode != 0
        assert Path('box-live-cli.png').read_bytes()==accepted_png
        assert boxed.spec.data.columns == box_data
        assert reopened.to_json() == rug_edited
        native_source = {'height':[2,4,3],'start':[0,86400,259200],
                         'duration':[21600,43200,21600]}
        native_plots = {
            'stairs': mp.plot(native_source).stairs('height',[
                '2026-01-01','2026-01-02','2026-01-04','2026-01-11'
            ],baseline=1).date_axis('x',timezone='UTC').size(6,3),
            'interval': mp.plot(native_source).broken_barh('start','duration',
                bottom=1,height=0.5).date_axis('x',unit='s',
                origin='2026-01-01T00:00:00Z').size(6,3),
        }
        for name, native in native_plots.items():
            original_native = native.to_json()
            target = f'native-{name}'
            mp.save_spec(native.spec,target+'.json')
            assert mp.Plot.from_json(original_native).spec == native.spec
            figure = native.save(target+'.png')
            try:
                paths = (figure.axes[0].patches[0].get_path()
                         if name=='stairs' else
                         figure.axes[0].collections[0].get_paths()[0])
                xs = [p[0] for p in paths.vertices]
                assert min(xs)==20454
                if name=='stairs':
                    assert max(xs)==20464
                else:
                    assert max(xs)-min(xs)==0.25
            finally:
                plt.close(figure)
            subprocess.run([console,'render',target+'.json',target+'.svg'],check=True)
            assert Path(target+'.svg').stat().st_size > 100
            assert native.to_json()==original_native
            assert native.spec.data.columns==native_source
        grid_source = {'t':['2026-01-01','2026-01-02','2026-01-04','2026-01-11'],
                       'v':[1,3,2,4]}
        grids = {
            'joint': mp.plot(grid_source).scatter('t','v')
                .date_axis('x',timezone='UTC').joint(bins=3).size(7,6),
            'pair': mp.plot(grid_source).pair(['t','v'],bins=3,
                temporal={'t':{'timezone':'UTC'}}).size(8,7),
        }
        for name, grid in grids.items():
            original_grid = grid.to_json()
            target = f'temporal-{name}'
            mp.save_spec(grid.spec,target+'.json')
            assert mp.Plot.from_json(original_grid).spec == grid.spec
            assert mp.apply(json.loads(json.dumps(grid.action_log))) == grid.spec
            figure = grid.save(target+'.png')
            try:
                assert len(figure.axes) == (3 if name=='joint' else 4)
                axis = figure.axes[0 if name=='joint' else 2]
                assert axis.collections[0].get_offsets()[:,0].tolist() == [
                    20454,20455,20457,20464
                ]
            finally:
                plt.close(figure)
            subprocess.run([console,'render',target+'.json',target+'.svg'],check=True)
            assert Path(target+'.svg').stat().st_size > 100
            assert grid.to_json()==original_grid and grid.spec.data.columns==grid_source
        secondary = (mp.plot(grid_source).line('t','v').secondary_yaxis('Density')
            .hist('t',axis='y2',bins=['2026-01-01','2026-01-05','2026-01-12'],
                  stat='density').date_axis('x',timezone='UTC').size(6,3))
        secondary_json = secondary.to_json()
        mp.save_spec(secondary.spec,'temporal-y2.json')
        assert mp.Plot.from_json(secondary_json).spec == secondary.spec
        figure = secondary.save('temporal-y2.png')
        try:
            primary_axis, density_axis = figure.axes
            assert not primary_axis.patches
            assert [(p.get_x(), p.get_width()) for p in density_axis.patches] == [
                (20454, 4), (20458, 7)
            ]
        finally:
            plt.close(figure)
        subprocess.run([console,'render','temporal-y2.json','temporal-y2.svg'],check=True)
        assert Path('temporal-y2.svg').stat().st_size > 100
        assert secondary.to_json()==secondary_json
        secondary_views = {
            'kde': mp.plot(grid_source).secondary_yaxis('Density')
                .kde('t',axis='y2',cut=0).date_axis('x',timezone='UTC'),
            'ecdf': mp.plot(grid_source).secondary_yaxis('Probability')
                .ecdf('t',axis='y2').date_axis('x',timezone='UTC'),
            'semantic': mp.plot(grid_source).secondary_yaxis('Date')
                .scatter('v','t',axis='y2',semantics={'hue':'v'})
                .date_axis('y2',timezone='UTC'),
        }
        for name, view in secondary_views.items():
            original_view = view.to_json()
            assert mp.Plot.from_json(original_view).spec == view.spec
            assert mp.apply(json.loads(json.dumps(view.action_log))) == view.spec
            target = 'temporal-y2-'+name
            mp.save_spec(view.spec,target+'.json')
            figure = view.save(target+'.png')
            try:
                assert len(figure.axes)==2
                routed = figure.axes[1]
                if name=='semantic':
                    assert routed.collections[0].get_offsets()[:,1].tolist()==[
                        20454,20455,20457,20464
                    ]
                else:
                    xs = routed.lines[0].get_xdata()
                    assert xs[0]==20454 and xs[-1]==20464
            finally:
                plt.close(figure)
            subprocess.run([console,'render',target+'.json',target+'.svg'],check=True)
            assert Path(target+'.svg').stat().st_size > 100
            assert view.to_json()==original_view and view.spec.data.columns==grid_source
        dodged = mp.plot({
            'x':[.25,.75,1,2,3], 'g':['A','B','A','B','A'], 'w':[1,2,3,9,6]
        }).hist('x',bins=[0,1,3],group='g',weights='w',stat='count',
                element='step',multiple='dodge',fill=True)
        original_dodged = dodged.to_json()
        assert mp.apply(dodged.action_log)==dodged.spec
        mp.save_spec(dodged.spec,'step-dodge.json')
        figure = dodged.save('step-dodge.png')
        try:
            expected_edges = [[0,0,.5,1,1,2,3],[0,.5,1,1,2,3,3]]
            expected_heights = [[0,1,0,0,9,0],[0,2,0,0,9,0]]
            patches = figure.axes[0].patches
            assert len(patches)==2
            for patch,edges,heights in zip(
                patches,expected_edges,expected_heights,strict=True
            ):
                values,actual_edges,_ = patch.get_data()
                assert values.tolist()==heights and actual_edges.tolist()==edges
                assert patch.get_fill()
        finally:
            plt.close(figure)
        subprocess.run([console,'render','step-dodge.json','step-dodge.svg'],check=True)
        assert Path('step-dodge.svg').stat().st_size > 100
        assert mp.Plot.from_json(original_dodged).spec==dodged.spec
        assert dodged.to_json()==original_dodged
        outlined = mp.plot(dodged.spec.data.columns).hist(
            'x',bins=[0,1,3],weights='w',group='g',stat='count',fill=False)
        original_outlined = outlined.to_json()
        assert mp.apply(outlined.action_log)==outlined.spec
        assert mp.Plot.from_json(original_outlined).spec==outlined.spec
        mp.save_spec(outlined.spec,'outlined-bars.json')
        figure = outlined.save('outlined-bars.png')
        try:
            assert len(figure.axes[0].patches)==4
            assert all(not p.get_fill() and not p.get_hatch()
                       for p in figure.axes[0].patches)
        finally:
            plt.close(figure)
        subprocess.run([console,'render','outlined-bars.json','outlined-bars.svg'],
                       check=True)
        assert Path('outlined-bars.svg').stat().st_size > 100
        assert outlined.to_json()==original_outlined
        invisible = mp.plot(dodged.spec.data.columns).hist(
            'x',bins=[0,1,3],weights='w',group='g',element='step',
            fill=True,alpha=0,line_width=0)
        mp.save_spec(invisible.spec,'zero-opacity.json')
        subprocess.run([console,'render','zero-opacity.json','zero-opacity.svg'],
                       check=True)
        invisible_svg = Path('zero-opacity.svg').read_bytes()
        assert len(invisible_svg)>100 and b'<pattern' not in invisible_svg
        assert mp.load_spec('zero-opacity.json')==invisible.spec
        for filled in (None,True):
            composition = mp.plot(dodged.spec.data.columns).hist(
                'x',bins=[0,1,3],group='g',weights='w',stat='probability',
                common_norm=False,multiple='fill',element='poly',fill=filled)
            tag = 'poly-filled' if filled else 'poly-default'
            original_composition = composition.to_json()
            assert mp.apply(composition.action_log)==composition.spec
            assert mp.Plot.from_json(original_composition).spec==composition.spec
            mp.save_spec(composition.spec,tag+'.json')
            figure = composition.save(tag+'.png')
            try:
                axes = figure.axes[0]
                if filled:
                    assert len(axes.collections)==2 and not axes.lines
                    vertices = axes.collections[0].get_paths()[0].vertices
                    assert min(vertices[:,0])==.5 and max(vertices[:,0])==2
                    assert abs(max(vertices[:,1])-11/21)<1e-12
                else:
                    assert len(axes.lines)==2 and not axes.collections
                    assert axes.lines[0].get_xdata().tolist()==[.5,2]
                    assert all(abs(a-b)<1e-12 for a,b in zip(
                        axes.lines[0].get_ydata(),[11/31,11/21],strict=True))
            finally:
                plt.close(figure)
            subprocess.run([console,'render',tag+'.json',tag+'.svg'],check=True)
            assert Path(tag+'.svg').stat().st_size>100
            assert composition.to_json()==original_composition
        ordinal = (mp.plot({'c':['A','B','A'],'v':[1.,2.,3.]})
            .secondary_yaxis('Density').barplot('c','v',orient='h',errorbar=None)
            .hist('v',axis='y2',bins=3,stat='density'))
        figure = ordinal.render()
        try:
            assert [t.get_text() for t in figure.axes[0].get_yticklabels()]==['A','B']
        finally:
            plt.close(figure)
        assert not plt.get_fignums()
        from mudplot._histogram import histogram_summary
        source = {'x':[0,1,2,3,100,1000,None], 'w':[1,2,3,4,5,0,9]}
        auto = mp.plot(source).hist('x',bins='auto',weights='w')
        summary = histogram_summary(source,auto.spec.panels[0].layers[0])
        assert len(summary.edges)==44 and sum(summary.curves[0].heights)==15
        scaled = {**source,'w':[100*w for w in source['w']]}
        other = histogram_summary(scaled,auto.spec.panels[0].layers[0])
        assert other.edges==summary.edges
        assert sum(other.curves[0].heights)==1500
        for unit in ('s','ms'):
            discrete = (mp.plot({'t':[0,1,2]}).hist('t',discrete=True)
                        .date_axis('x',unit=unit,origin='2026-01-01',timezone='UTC'))
            before = discrete.to_json()
            assert discrete.spec.panels[0].layers[0].bins=='discrete'
            assert mp.Plot.from_json(before).spec==mp.apply(discrete.action_log)
            figure = discrete.render()
            try:
                widths = [patch.get_width() for patch in figure.axes[0].patches]
                expected = 1/(86400*(1000 if unit=='ms' else 1))
                assert len(widths)==3
                assert all(abs(width-expected)<1e-11 for width in widths)
            finally:
                plt.close(figure)
            assert discrete.to_json()==before
        spectral = mp.plot({'signal':[0,1,0,-1]*4}).spectrum(
            'signal',fs=4,nfft=4,window='boxcar',pad_to=5)
        spectral_before = spectral.to_json()
        spectral_figure = spectral.render()
        try:
            axis = spectral_figure.axes[0]
            frequency = axis.lines[0].get_xdata()
            density = axis.lines[0].get_ydata()
            assert abs(sum(density)*4/5-.5)<1e-12
            assert axis.get_xlabel()=='Frequency (Hz)'
        finally:
            plt.close(spectral_figure)
        mp.save_spec(spectral.spec,'spectrum.json')
        assert mp.Plot.from_json(spectral_before).spec==spectral.spec
        for extension in ('png','svg','pdf'):
            subprocess.run([console,'render','spectrum.json','spectrum.'+extension],check=True)
        controlled = (mp.plot({'temperature':[0,50,100],'length':[1,2,3]})
            .line('temperature','length')
            .ticks('x',{'locator':{'kind':'multiple','step':25},
                        'formatter':{'kind':'number','notation':'fixed','precision':0}})
            .secondary_xaxis({'kind':'celsius_fahrenheit'}))
        figure = controlled.render()
        try:
            figure.canvas.draw()
            axis = figure.axes[0]
            assert list(axis.get_xticks())==[-25,0,25,50,75,100,125]
            derived = axis.child_axes[0]
            for celsius,fahrenheit in ((0,32),(50,122),(100,212)):
                left=axis.transData.transform((celsius,0))[0]
                right=derived.transData.transform((fahrenheit,0))[0]
                assert abs(left-right)<1e-8
            assert derived.get_xlabel()=='°F'
        finally:
            plt.close(figure)
        replayed = mp.apply(controlled.action_log)
        assert mp.Plot.from_json(controlled.to_json()).spec==replayed
        mp.save_spec(controlled.spec,'axis-controls.json')
        subprocess.run([console,'validate','axis-controls.json'],check=True)
        for extension in ('png','svg','pdf'):
            subprocess.run([console,'render','axis-controls.json','axis-controls.'+extension],check=True)
        from matplotlib.collections import PolyCollection
        violin_rows = {
            'date':['2026-01-01']*6,'value':[1,4,9]*2,
            'hue':[True]*3+[1]*3,'precision':[1]*3+[3]*3,
            'method':['A']*3+['B']*3,'weight':[1,3,2]*2,
            'id':['a','b','c','d','e','f'],
        }
        profiled = (mp.plot(violin_rows).secondary_yaxis('Response (mm)')
            .date_axis('x',timezone='UTC')
            .violin('date','value',axis='y2',weights='weight',inner='box',
                split=True,violin={'split_policy':'paired'},
                semantics={'hue':'hue','size':'precision','size_norm':[1,3],
                    'sizes':[1,2],'style':'method','markers':['D','^']},
                marker_size=5))
        before_profile = profiled.to_json()
        profiled.labels(title='Actual typed weighted half profiles')
        edited_profile = profiled.to_json()
        profiled.store.undo()
        assert profiled.to_json()==before_profile
        profiled.store.redo()
        assert profiled.to_json()==edited_profile
        figure = profiled.render()
        try:
            target = figure.axes[1]
            native_bodies = [a for a in target.collections
                             if isinstance(a,PolyCollection)]
            assert len(native_bodies)==2
            assert np.allclose([a.get_linewidths()[0] for a in native_bodies],[1,2])
            assert [a.get_marker() for a in target.lines]==['D','^']
            assert np.array_equal([a.get_ydata()[0] for a in target.lines],[4,4])
            assert all(a.get_markersize()==5 for a in target.lines)
        finally:
            plt.close(figure)
        assert profiled.spec.data.columns==violin_rows
        assert mp.apply(profiled.action_log)==profiled.spec
        mp.save_spec(profiled.spec,'violin-workflow.json')
        assert mp.load_spec('violin-workflow.json')==profiled.spec
        for extension in ('png','svg','pdf'):
            subprocess.run([console,'render','violin-workflow.json',
                            'violin-workflow.'+extension],check=True)
        placed = (mp.plot({'x':[1,2,4],'y':[2,4,3]})
            .line('x','y').mosaic([['main','reserved']])
            .nest(1,2,width_ratios=[3,1])
            .inset('main',[.15,.2,.3,.4],panel_id='zoom')
            .line('x','y',panel=2).size(8,4))
        before_placement = placed.to_json()
        placed.place('zoom',{'inset':{'parent':'main','bounds':[.2,.1,.35,.4]}})
        edited_placement = placed.to_json()
        placed.store.undo()
        assert placed.to_json()==before_placement
        placed.store.redo()
        placed = mp.Plot.from_json(placed.to_json())
        assert placed.to_json()==edited_placement
        figure = placed.render()
        try:
            parent = next(a for a in figure.axes
                          if getattr(a,'_mudplot_panel_id',None)=='main')
            child = next(a for a in parent.child_axes
                         if getattr(a,'_mudplot_panel_id',None)=='zoom')
            corners = parent.transAxes.transform([[.2,.1],[.55,.5]])
            assert np.allclose(child.bbox.extents,corners.ravel())
            assert np.array_equal(child.lines[0].get_ydata(),[2,4,3])
        finally:
            plt.close(figure)
        mp.save_spec(placed.spec,'panel-layout.json')
        for extension in ('png','svg','pdf'):
            subprocess.run([console,'render','panel-layout.json',
                            'panel-layout.'+extension],check=True)
        assert 'mudplot-panel-zoom' in Path('panel-layout.svg').read_text()
        from matplotlib.patches import Polygon
        lettered = (mp.plot({'v':[0,10,20],'w':[1,2,1]})
            .boxenplot('v',weights='w',k_depth='full',width_method='area',
                band_components=[{'rank':0,'side':'central',
                                  'body':{'color':'#aa0000','hatch':'/'}}])
            .size(4,3))
        letter_figure=lettered.render()
        try:
            bands=[p for p in letter_figure.axes[0].patches if isinstance(p,Polygon)]
            assert len(bands)==3
            for band,low,high,relative in zip(bands,[0,0,10],[0,10,20],[0,1/3,1]):
                vertices=band.get_xy()
                assert vertices[:,1].min()==low and vertices[:,1].max()==high
                assert abs(np.ptp(vertices[:,0])-.8*relative)<1e-12
        finally:
            plt.close(letter_figure)
        replacement=lettered.spec.panels[0].layers[0]
        replacement.k_depth=1
        before_replace=lettered.to_json()
        lettered.dispatch(mp.actions.ReplaceLayer(0,replacement))
        letter_figure=lettered.render()
        try:
            assert np.array_equal(letter_figure.axes[0].lines[1].get_ydata(),[20])
        finally:
            plt.close(letter_figure)
        lettered.store.undo()
        assert lettered.to_json()==before_replace
        lettered.store.redo()
        mp.save_spec(lettered.spec,'weighted-letter-values.json')
        Path('replace-letter.json').write_text(json.dumps({
            'type':'ReplaceLayer','panel':0,'layer_index':0,
            'layer':replacement.to_dict()}))
        subprocess.run([console,'apply','weighted-letter-values.json',
            'replace-letter.json','-o','replaced-letter.json'],check=True)
        for extension in ('png','svg','pdf'):
            subprocess.run([console,'render','replaced-letter.json',
                'weighted-letter-values.'+extension],check=True)
        accepted_spec=Path('replaced-letter.json').read_bytes()
        Path('bad-replace-letter.json').write_text(json.dumps({
            'type':'ReplaceLayer','panel':0,'layer_index':True,
            'layer':replacement.to_dict()}))
        rejected=subprocess.run([console,'apply','weighted-letter-values.json',
            'bad-replace-letter.json','-o','replaced-letter.json'],capture_output=True)
        assert rejected.returncode!=0
        assert Path('replaced-letter.json').read_bytes()==accepted_spec
        from fractions import Fraction
        from matplotlib.collections import LineCollection
        residual = [1e300,-1e300,1e-300]
        for estimator in ('sum','mean'):
            canonical = (mp.plot({'c':['A']*3,'v':residual,'id':['a','b','c']})
                .barplot('c','v',estimator=estimator,errorbar=None))
            expected = float(sum(map(Fraction,residual),Fraction()) /
                             (3 if estimator=='mean' else 1))
            figure = canonical.render()
            try:
                assert expected>0 and figure.axes[0].patches[0].get_height()==expected
            finally:
                plt.close(figure)
        inferred = (mp.plot({'c':['2026-01-01']*3,'v':[0,10,20],
                            'w':[1,38,1],'id':['a','b','c']})
            .secondary_yaxis('Observed response').date_axis('x',timezone='UTC')
            .pointplot('c','v',weights='w',estimator='median',errorbar=('pi',95),
                       axis='y2',marker='D',semantics={'size':'w','size_norm':[1,38],
                                           'sizes':[2,4]}).size(12,7))
        original_inferred=inferred.to_json()
        figure=inferred.render()
        try:
            axis=next(ax for ax in figure.axes if ax.get_ylabel()=='Observed response')
            intervals=[s for item in axis.collections if isinstance(item,LineCollection)
                       for s in item.get_segments()]
            # Raw size tuples partition the statistical population; retain each
            # selected pair rather than averaging the role into one fake curve.
            marks=[line for line in axis.lines
                   if len(line.get_ydata()) and line.get_marker()=='D']
            assert sorted(float(line.get_ydata()[0]) for line in marks)==[0,10]
            assert sorted(line.get_markersize() for line in marks)==[2,4]
            assert len(intervals)==1
            np.testing.assert_array_equal(intervals[0][:,1],[0,20])
        finally:
            plt.close(figure)
        assert inferred.to_json()==original_inferred
        mp.save_spec(inferred.spec,'statistical-workflow.json')
        for extension in ('png','svg','pdf'):
            subprocess.run([console,'render','statistical-workflow.json',
                            'statistical-workflow.'+extension],check=True)
        dimensions=struct.unpack(
            '>II',Path('statistical-workflow.png').read_bytes()[16:24])
        assert dimensions==(3600,2100)
        accepted_png=Path('statistical-workflow.png').read_bytes()
        bad=inferred.spec.to_dict()
        bad['panels'][0]['layers'][0]['stat']['errorbar']='se'
        Path('statistical-bad.json').write_text(json.dumps(bad))
        rejected=subprocess.run([console,'render','statistical-bad.json',
                                 'statistical-workflow.png'],capture_output=True)
        assert rejected.returncode!=0
        assert Path('statistical-workflow.png').read_bytes()==accepted_png
        print('installed render/CLI smoke OK')
    """)
    # The explicit prefix check prevents an editable checkout from hiding omissions.
    subprocess.run(
        [sys.executable, "-c", smoke, str(prefix), str(console)],
        cwd=out_dir,
        env={
            **os.environ,
            "PYTHONPATH": paths["purelib"],
            "PYTHONOPTIMIZE": "",
            "MPLBACKEND": "Agg",
            "MPLCONFIGDIR": str(Path(out_dir) / "mpl"),
        },
        check=True,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--render",
        action="store_true",
        help="install the wheel with uv and smoke-test the active render dependencies",
    )
    parser.add_argument(
        "--out-dir", help="copy the verified wheel and sdist to this empty directory"
    )
    args = parser.parse_args()

    with tempfile.TemporaryDirectory() as out_dir:
        # With no --wheel/--sdist selector, build creates an sdist and builds
        # the wheel from it. --no-isolation keeps the backend in uv.lock.
        subprocess.run(
            [
                sys.executable,
                "-m",
                "build",
                "--no-isolation",
                "--outdir",
                out_dir,
                ".",
            ],
            check=True,
        )
        wheels = glob.glob(f"{out_dir}/*.whl")
        sdists = glob.glob(f"{out_dir}/*.tar.gz")
        if len(wheels) != 1 or len(sdists) != 1:
            print(
                f"error: expected one wheel and one sdist, got {wheels} and {sdists}",
                file=sys.stderr,
            )
            return 1

        with zipfile.ZipFile(wheels[0]) as archive:
            wheel_names = archive.namelist()
            wheel_metadata = Parser().parsestr(
                archive.read(
                    next(
                        name
                        for name in wheel_names
                        if name.endswith(".dist-info/METADATA")
                    )
                ).decode("utf-8")
            )
        missing = []
        for required in (
            "mudplot/py.typed",
            "mudplot/__main__.py",
            "mudplot/_quality.py",
            "mudplot/_temporal.py",
            "mudplot/_temporal_data.py",
            "mudplot/_temporal_render.py",
            "mudplot/_recommend.py",
            "mudplot/_lint.py",
            "mudplot/_mpl_context.py",
            "mudplot/_axis_options.py",
            "mudplot/_axis_render.py",
            "mudplot/_boxen.py",
            "mudplot/_boxen_render.py",
            "mudplot/_matplotlib_notice.txt",
        ):
            if required not in wheel_names:
                missing.append(f"wheel:{required}")
        if not any(name.endswith("licenses/LICENSE") for name in wheel_names):
            missing.append("wheel:*licenses/LICENSE")
        if not any(
            name.endswith("licenses/mudplot/_matplotlib_notice.txt")
            for name in wheel_names
        ):
            missing.append("wheel:*licenses/mudplot/_matplotlib_notice.txt")
        if wheel_metadata.get("License-Expression") != "MIT AND LicenseRef-Matplotlib":
            missing.append(
                f"wheel:License-Expression={wheel_metadata.get('License-Expression')!r}"
            )
        if set(wheel_metadata.get_all("License-File", [])) != {
            "LICENSE",
            "mudplot/_matplotlib_notice.txt",
        }:
            missing.append(
                "wheel: both own MIT and adapted Matplotlib "
                "license files must be declared"
            )
        wheel_roots = {name.partition("/")[0] for name in wheel_names}
        unexpected_roots = sorted(
            root
            for root in wheel_roots
            if root != "mudplot"
            and not (root.startswith("mudplot-") and root.endswith(".dist-info"))
        )
        if unexpected_roots:
            missing.append(f"wheel unexpected top-level paths: {unexpected_roots}")

        with tarfile.open(sdists[0]) as archive:
            sdist_names = archive.getnames()
            sdist_metadata_file = archive.extractfile(
                next(
                    name
                    for name in sdist_names
                    if name.count("/") == 1 and name.endswith("/PKG-INFO")
                )
            )
            if sdist_metadata_file is None:
                missing.append("sdist:PKG-INFO")
            else:
                sdist_metadata = Parser().parsestr(
                    sdist_metadata_file.read().decode("utf-8")
                )
                if (
                    sdist_metadata.get("License-Expression")
                    != "MIT AND LicenseRef-Matplotlib"
                ):
                    missing.append(
                        f"sdist:License-Expression={sdist_metadata.get('License-Expression')!r}"
                    )
                if set(sdist_metadata.get_all("License-File", [])) != {
                    "LICENSE",
                    "mudplot/_matplotlib_notice.txt",
                }:
                    missing.append("sdist: both license files must be declared")
            htmx_name = next(
                (
                    name
                    for name in sdist_names
                    if name.endswith("/dashboard/static/htmx.min.js")
                ),
                None,
            )
            htmx_file = archive.extractfile(htmx_name) if htmx_name else None
            if htmx_file is not None:
                digest = hashlib.sha256(htmx_file.read()).hexdigest()
                if digest != HTMX_SHA256:
                    missing.append(f"sdist htmx SHA-256 is {digest}")
        missing.extend(
            f"sdist:{required}"
            for required in SDIST_FILES
            if not any(name.endswith(f"/{required}") for name in sdist_names)
        )
        from dashboard.plot_gallery import GALLERY_EXAMPLES
        from mudplot.capabilities import LAYER_TYPES

        names = [example.name for example in GALLERY_EXAMPLES]
        if len(names) != len(set(names)) or set(names) != set(LAYER_TYPES):
            missing.append(
                "plot gallery registry must cover every layer type exactly once"
            )

        expected_examples = {f"{example.name}.py" for example in GALLERY_EXAMPLES}
        packaged_examples = {
            Path(name).name
            for name in sdist_names
            if "/examples/plots/" in name and name.endswith(".py")
        }
        if packaged_examples != expected_examples:
            missing.append(
                "sdist plot examples differ: "
                f"expected {sorted(expected_examples)}, got {sorted(packaged_examples)}"
            )

        expected_gallery_assets = {
            filename
            for example in GALLERY_EXAMPLES
            for filename in (
                f"{example.name}.png",
                f"{example.name}.mplot.json",
            )
        }
        packaged_gallery_assets = {
            Path(name).name for name in sdist_names if "/docs/images/plots/" in name
        }
        if packaged_gallery_assets != expected_gallery_assets:
            missing.append(
                "sdist plot gallery assets differ: "
                f"expected {sorted(expected_gallery_assets)}, "
                f"got {sorted(packaged_gallery_assets)}"
            )
        for forbidden in (
            ".pi",
            "artifacts",
            ".hypothesis",
            "mudplot-editor/target",
            "src/pretext",
            "src/SciencePlots",
            "site",
        ):
            if any(f"/{forbidden}/" in name for name in sdist_names):
                missing.append(f"sdist must not contain {forbidden}")

        for prefix in (".mudplot-pgf-", ".mudplot-write-", ".mudplot-backup-"):
            if any(
                part.startswith(prefix)
                for name in sdist_names
                for part in Path(name).parts
            ):
                missing.append(f"sdist must not contain private {prefix} files")

        if missing:
            print(
                f"error: distributions are missing or contain {missing}",
                file=sys.stderr,
            )
            return 1

        smoke = (
            "import json, mudplot; "
            "assert '.whl' in mudplot.__file__; "
            "advice=mudplot.recommend({'condition':['A','B'],'id':[1,1],'y':[1,None]},"
            "x='condition',y='y',paired='id'); "
            "assert not any(r['kind']=='paired' for r in advice['recommendations']); "
            "assert any(w['code']=='incomplete-pairs' for w in advice['warnings']); "
            "json.dumps(advice,allow_nan=False); "
            "assert mudplot.from_json(mudplot.to_json(mudplot.FigureSpec())).version; "
            "p=mudplot.plot({'x':[1,2],'y':[3,4]}).scatter('x','y'); "
            "p.joint(marginal_kind='kde',kde={'cut':0}); "
            "assert len(p.spec.panels)==3 and mudplot.validate(p.spec)==[]; "
            "assert mudplot.apply(p.action_log)==p.spec; "
            "q=mudplot.plot({'a':[1,2],'b':[3,4]}).pair(['a','b'],diag_kind='kde'); "
            "assert len(q.spec.panels)==4 and mudplot.validate(q.spec)==[]; "
            "assert mudplot.apply(q.action_log)==q.spec; "
            "h=mudplot.plot().matrix('m',[[1,2],[3,4]]); "
            "h.heatmap('m',heatmap={'annot':True}); "
            "assert mudplot.validate(h.spec)==[]; "
            "assert mudplot.apply(h.action_log)==h.spec; "
            "r=mudplot.plot({'x':[1,2,3],'y':[2,3,4]}).residplot('x','y'); "
            "assert mudplot.validate(r.spec)==[]; "
            "u=mudplot.Plot.from_json(r.to_json()).spec; "
            "assert mudplot.apply(r.action_log)==u; "
            "c=mudplot.plot().matrix('m',[[1,2],[3,4]]).clustermap('m'); "
            "assert mudplot.validate(c.spec)==[]; "
            "assert mudplot.apply(c.action_log)==c.spec; "
            "b=mudplot.plot({'x':[0,1,2]}).hist('x',discrete=True); "
            "assert b.spec.panels[0].layers[0].bins=='discrete'; "
            "assert mudplot.validate(b.spec)==[]; "
            "assert mudplot.Plot.from_json(b.to_json()).spec=="
            "mudplot.apply(b.action_log); "
            "n=mudplot.plot({'x':[0,1,2,3,100]}).hist('x',bins='auto'); "
            "assert mudplot.validate(n.spec)==[]; "
            "assert mudplot.Plot.from_json(n.to_json()).spec=="
            "mudplot.apply(n.action_log); "
            "assert 'numpy' not in __import__('sys').modules"
        )
        subprocess.run(
            [sys.executable, "-S", "-c", smoke],
            cwd=out_dir,
            env={**os.environ, "PYTHONPATH": wheels[0], "PYTHONOPTIMIZE": ""},
            check=True,
        )

        if args.render:
            _smoke_installed(wheels[0], out_dir)

        if args.out_dir:
            destination = Path(args.out_dir)
            destination.mkdir(parents=True, exist_ok=True)
            if any(destination.iterdir()):
                print(
                    f"error: output directory is not empty: {destination}",
                    file=sys.stderr,
                )
                return 1
            for artifact in (*sdists, *wheels):
                shutil.copy2(artifact, destination)

        print(f"distribution packaging OK: {sdists[0]}, {wheels[0]}")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
