import mudplot as mp
from mudplot import io
from mudplot.spec import FigureSpec, LayerSpec


def _demo_plot():
    data = {"x": [1, 2, 3, 4], "y": [1, 4, 9, 16], "g": ["a", "a", "b", "b"]}
    return (
        mp.plot(data)
        .line(x="x", y="y", group="g")
        .labels(x="X", y="Y", title="demo")
        .legend(title="grp")
        .theme("boxed")
        .journal("nature")
        .palette("qualitative", hue_start=45, chroma=60)
    )


def test_default_spec_roundtrip():
    spec = FigureSpec()
    assert FigureSpec.from_dict(spec.to_dict()).to_dict() == spec.to_dict()


def test_builder_json_roundtrip_lossless():
    p = _demo_plot()
    rebuilt = mp.Plot.from_json(p.to_json())
    assert rebuilt.spec.to_dict() == p.spec.to_dict()


def test_nested_types_preserved():
    p = _demo_plot()
    spec2 = io.from_json(io.to_json(p.spec))
    assert isinstance(spec2.panels[0].layers[0], LayerSpec)
    assert spec2.theme.palette.hue_start == 45
    assert spec2.theme.axes.spines == "LRTB"
    assert spec2.journal == "nature"
    assert spec2.panels[0].legend.title == "grp"


def test_save_load_file(tmp_path):
    p = _demo_plot()
    path = tmp_path / "fig.mplot.json"
    io.save_spec(p.spec, path)
    loaded = io.load_spec(path)
    assert loaded.to_dict() == p.spec.to_dict()


def test_builder_mutates_spec_only():
    # every builder call should be reflected in the spec (single source of truth)
    p = mp.plot({"a": [1], "b": [2]}).line("a", "b").xscale("log").ylim(0, 10)
    assert p.spec.panels[0].x.scale == "log"
    assert p.spec.panels[0].y.limits == [0, 10]
    assert p.spec.panels[0].layers[0].type == "line"
