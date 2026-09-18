import mudplot as mp
import pytest
from mudplot import io
from mudplot.spec import SPEC_VERSION, FigureSpec, LayerSpec, migrate_spec_dict


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


def test_save_spec_is_atomic_and_preserves_symlinks(tmp_path, monkeypatch):
    destination = tmp_path / "figure.json"
    destination.write_text("old", encoding="utf-8")
    destination.chmod(0o640)
    link = tmp_path / "linked.json"
    link.symlink_to(destination)

    io.save_spec(FigureSpec(), link)
    assert link.is_symlink()
    assert destination.stat().st_mode & 0o777 == 0o640
    assert b"\r\n" not in destination.read_bytes()
    assert io.load_spec(destination) == FigureSpec()

    destination.chmod(0o440)
    io.save_spec(FigureSpec(), destination)
    assert destination.stat().st_mode & 0o777 == 0o440
    destination.chmod(0o640)
    destination.write_text("keep", encoding="utf-8")

    def fail_replace(source, target):
        raise OSError("simulated replace failure")

    monkeypatch.setattr(io.os, "replace", fail_replace)
    with pytest.raises(OSError, match="simulated"):
        io.save_spec(FigureSpec(), destination)
    assert destination.read_text(encoding="utf-8") == "keep"
    assert sorted(tmp_path.iterdir()) == [destination, link]


def test_current_version_round_trips_unchanged():
    d = FigureSpec().to_dict()
    assert migrate_spec_dict(d) is d


def test_missing_version_field_defaults_to_current():
    d = FigureSpec().to_dict()
    del d["version"]
    restored = FigureSpec.from_dict(d)
    assert restored.version == SPEC_VERSION


def test_unknown_future_version_is_rejected_not_silently_loaded():
    d = FigureSpec().to_dict()
    d["version"] = "99.0"
    with pytest.raises(ValueError, match=r"99\.0"):
        FigureSpec.from_dict(d)


def test_directly_constructed_bad_version_fails_validate():
    spec = FigureSpec(version="99.0")
    issues = mp.validate(spec)
    assert any("spec version" in i for i in issues)


@pytest.mark.parametrize(
    "payload",
    [
        [],
        "not an object",
        {"version": SPEC_VERSION, "panels": "not an array"},
        {"version": SPEC_VERSION, "panels": [{"layers": [[]]}]},
        {"version": SPEC_VERSION, "dpi": "300"},
        {"version": SPEC_VERSION, "theme": {"font": None}},
        {"version": SPEC_VERSION, "data": {"columns": {"x": "not an array"}}},
    ],
)
def test_malformed_json_shapes_fail_at_deserialization_boundary(payload):
    with pytest.raises(TypeError):
        FigureSpec.from_dict(payload)


@pytest.mark.parametrize(
    "text",
    [
        "not json",
        "[]",
        '{"dpi":"fast"}',
        '{"dpi":NaN}',
        '{"dpi":Infinity}',
        '{"dpi":300,"dpi":72}',
        '{"$serde_json::private::Number":"1"}',
        '{"data":{"columns":{"x":[1e400]}}}',
        r'{"data":{"columns":{"label":["\ud800"]}}}',
        "[" * 2_000 + "]" * 2_000,
    ],
)
def test_io_from_json_wraps_malformed_input_with_context(text):
    with pytest.raises(ValueError, match="invalid FigureSpec JSON"):
        io.from_json(text)


def test_to_json_rejects_nonstandard_nonfinite_numbers():
    spec = FigureSpec()
    spec.data.columns = {"value": [float("nan")]}
    with pytest.raises(ValueError, match="finite"):
        io.to_json(spec)


def test_to_json_rejects_lone_unicode_surrogates_and_reserved_keys():
    spec = FigureSpec()
    spec.data.columns = {"label": ["\ud800"]}
    with pytest.raises(ValueError, match="surrogate"):
        io.to_json(spec)

    spec.data.columns = {"$serde_json::private::Number": [1]}
    with pytest.raises(ValueError, match="reserved"):
        io.to_json(spec)


def test_categorical_column_values_remain_valid_plain_data():
    restored = FigureSpec.from_dict(
        {"data": {"columns": {"group": ["control", "treated"]}}}
    )
    assert restored.data.columns["group"] == ["control", "treated"]


def test_unknown_future_fields_ignored_without_crashing():
    d = FigureSpec().to_dict()
    d["some_unrecognized_future_feature"] = {"nested": True}
    d["panels"][0]["future_panel_knob"] = 42
    restored = FigureSpec.from_dict(d)
    assert restored.version == SPEC_VERSION
    assert mp.validate(restored) == []


def test_builder_mutates_spec_only():
    # every builder call should be reflected in the spec (single source of truth)
    p = mp.plot({"a": [1], "b": [2]}).line("a", "b").xscale("log").ylim(0, 10)
    assert p.spec.panels[0].x.scale == "log"
    assert p.spec.panels[0].y.limits == [0, 10]
    assert p.spec.panels[0].layers[0].type == "line"
