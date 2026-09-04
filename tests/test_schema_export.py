"""Guard: the checked-in schema files must match the live generators.

If a spec/capabilities change breaks this, regenerate with:
    python -m mudplot schema --out schemas/figure_spec.schema.json
    python -m mudplot capabilities > schemas/capabilities.json
"""

import json
from pathlib import Path

import mudplot as mp

SCHEMAS_DIR = Path(__file__).resolve().parent.parent / "schemas"


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


def test_schema_is_valid_json_schema_shape():
    schema = mp.json_schema()
    assert schema["$schema"].startswith("https://json-schema.org/")
    assert schema["title"] == "FigureSpec"
    assert "LayerSpec" in schema["$defs"]
    # union with None should produce anyOf, not a bare {"default": null}
    wr = schema["properties"]["width_ratios"]
    assert "anyOf" in wr or "type" in wr
