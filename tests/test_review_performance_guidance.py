"""Keep explicit data-reduction guidance executable without runtime rewrites."""

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("name", ["PERFORMANCE.md", "PERFORMANCE.ko.md"])
def test_documented_explicit_aggregation_keeps_counts_and_original(name):
    text = (ROOT / "docs" / name).read_text(encoding="utf-8")
    code = text.split("```python\n", 1)[1].split("```", 1)[0]
    namespace = {}
    exec(compile(code, "trusted-explicit-aggregation-example", "exec"), namespace)
    original = namespace["original"]
    preview = namespace["preview"]
    assert original == [(i, float(i * i)) for i in range(25)]
    assert preview["n"] == [10, 10, 5] and sum(preview["n"]) == 25
    assert preview["x"] == [4.5, 14.5, 22]
    assert len(preview["y"]) == 3 and "SLA" in text
