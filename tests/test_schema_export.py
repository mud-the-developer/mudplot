"""Guard generated schemas, reference docs, and publication demo artifacts.

If a generated-artifact check breaks, run ``python -m scripts.render_docs_demo``
or the schema/capabilities commands named by ``scripts/check_schema_sync.py``.
"""

import json
from pathlib import Path

import mudplot as mp

ROOT = Path(__file__).resolve().parent.parent
SCHEMAS_DIR = ROOT / "schemas"


def test_figure_spec_schema_file_is_in_sync():
    path = SCHEMAS_DIR / "figure_spec.schema.json"
    on_disk = json.loads(path.read_text())
    assert on_disk == mp.json_schema()


def test_capabilities_file_is_in_sync():
    path = SCHEMAS_DIR / "capabilities.json"
    on_disk = json.loads(path.read_text())
    assert on_disk == mp.capabilities()


def test_reference_docs_file_is_in_sync():
    path = SCHEMAS_DIR.parent / "docs" / "REFERENCE.md"
    on_disk = path.read_text()
    assert on_disk == mp.reference_markdown()


def test_demo_specs_are_current():
    paths = sorted((ROOT / "docs" / "images").glob("*.mplot.json"))
    assert paths
    for path in paths:
        contents = path.read_text(encoding="utf-8")
        assert mp.to_json(mp.from_json(contents)) == contents, path.name


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
