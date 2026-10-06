"""Guard generated schemas, reference docs, and publication demo artifacts.

If a generated-artifact check breaks, run ``python -m scripts.render_docs_demo``
or the schema/capabilities commands named by ``scripts/check_schema_sync.py``.
"""

import json
from pathlib import Path

import mudplot as mp
import pytest
from dashboard.plot_gallery import GALLERY_EXAMPLES, build_example, gallery_markdown
from mudplot.capabilities import LAYER_TYPES

ROOT = Path(__file__).resolve().parent.parent
SCHEMAS_DIR = ROOT / "schemas"


def _assert_demo_value(actual, expected):
    # Seeded floating-point calculations can differ by a few ULPs across
    # NumPy/CPU versions. Schema, shape, strings, integers and booleans stay exact.
    if isinstance(expected, dict):
        assert isinstance(actual, dict) and actual.keys() == expected.keys()
        for key, value in expected.items():
            _assert_demo_value(actual[key], value)
    elif isinstance(expected, list):
        assert isinstance(actual, list) and len(actual) == len(expected)
        for left, right in zip(actual, expected, strict=True):
            _assert_demo_value(left, right)
    elif type(expected) is float:
        assert type(actual) in (int, float)
        assert actual == pytest.approx(expected, rel=1e-12, abs=1e-14)
    else:
        assert type(actual) is type(expected) and actual == expected


def test_figure_spec_schema_file_is_in_sync():
    path = SCHEMAS_DIR / "figure_spec.schema.json"
    on_disk = json.loads(path.read_text())
    assert on_disk == mp.json_schema()


def test_capabilities_file_is_in_sync():
    path = SCHEMAS_DIR / "capabilities.json"
    on_disk = json.loads(path.read_text())
    assert on_disk == mp.capabilities()


def test_reference_docs_file_is_in_sync():
    docs = SCHEMAS_DIR.parent / "docs"
    assert (docs / "REFERENCE.md").read_text() == mp.reference_markdown()
    assert (docs / "PLOT_GALLERY.md").read_text() == gallery_markdown()


def test_demo_specs_are_current():
    images = ROOT / "docs" / "images"
    paths = sorted(images.rglob("*.mplot.json"))
    assert paths
    assert {
        path.name.removesuffix(".mplot.json")
        for path in (images / "plots").glob("*.mplot.json")
    } == set(LAYER_TYPES)
    for path in paths:
        contents = path.read_text(encoding="utf-8")
        assert mp.to_json(mp.from_json(contents)) == contents, path.name
    for example in GALLERY_EXAMPLES:
        contents = (images / "plots" / f"{example.name}.mplot.json").read_text(
            encoding="utf-8"
        )
        spec = build_example(example).spec
        _assert_demo_value(json.loads(mp.to_json(spec)), json.loads(contents))
        assert example.name in {
            layer.type for panel in spec.panels for layer in panel.layers
        }
        if example.name == "hist":
            # Explicit shared edges prevent each group choosing its own range.
            assert isinstance(spec.panels[0].layers[0].bins, list)


def test_demo_pdfs_omit_volatile_timestamps():
    paths = sorted((ROOT / "docs" / "images").glob("*.pdf"))
    assert paths
    for path in paths:
        payload = path.read_bytes()
        assert b"/CreationDate" not in payload, path.name
        assert b"/ModDate" not in payload, path.name


def test_schema_is_valid_json_schema_shape():
    schema = mp.json_schema()
    assert schema["$schema"].startswith("https://json-schema.org/")
    assert schema["title"] == "FigureSpec"
    assert "LayerSpec" in schema["$defs"]
    # union with None should produce anyOf, not a bare {"default": null}
    wr = schema["properties"]["width_ratios"]
    assert "anyOf" in wr or "type" in wr
