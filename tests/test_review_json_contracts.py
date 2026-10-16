"""Review JSON-03/04/06/07: strict entry points and structural fidelity."""

from __future__ import annotations

import json

import mudplot as mp
import pytest
from mudplot.__main__ import main

DUPLICATE_SPECS = [
    '{"dpi":100,"dpi":100}',
    '{"dpi":100,"dpi":200}',
    '{"theme":{"font":{"size":11,"size":11}}}',
    '{"theme":{"font":{"size":11,"size":12}}}',
    '{"data":{"columns":{"unused":[{"key":1,"key":1}]}}}',
    '{"data":{"columns":{"unused":[{"key":1,"key":2}]}}}',
]
DUPLICATE_ACTIONS = [
    '{"type":"SetTitle","text":"A","text":"A"}',
    '{"type":"SetTitle","text":"A","text":"B"}',
    '{"type":"SetFont","params":{"size":11,"size":11}}',
    '{"type":"SetFont","params":{"size":11,"size":12}}',
    '{"type":"SetData","columns":{"unused":[{"key":1,"key":1}]}}',
    '{"type":"SetData","columns":{"unused":[{"key":1,"key":2}]}}',
]


@pytest.mark.parametrize("text", DUPLICATE_SPECS)
@pytest.mark.parametrize("entry", ["from_json", "plot", "file"])
def test_json_03_public_loaders_reject_equal_and_different_duplicates_at_all_depths(
    text, entry, tmp_path
):
    with pytest.raises(ValueError, match="duplicate JSON object key"):
        if entry == "from_json":
            mp.from_json(text)
        elif entry == "plot":
            mp.Plot.from_json(text)
        else:
            path = tmp_path / "duplicate.json"
            path.write_text(text, encoding="utf-8")
            mp.load_spec(path)


@pytest.mark.parametrize("text", DUPLICATE_SPECS)
@pytest.mark.parametrize("command", ["validate", "migrate", "apply", "render"])
def test_json_03_cli_rejects_duplicate_specs_and_preserves_output(
    text, command, tmp_path, capsys
):
    source, action, output = (
        tmp_path / name for name in ("source.json", "action.json", "output.json")
    )
    source.write_text(text, encoding="utf-8")
    action.write_text('{"type":"SetTitle","text":"never"}', encoding="utf-8")
    output.write_bytes(b"previous output")
    args = [command, str(source)]
    if command == "apply":
        args.append(str(action))
    if command == "render":
        args.append(str(output))
    elif command != "validate":
        args.extend(["-o", str(output)])
    assert main(args) == 1
    assert "duplicate JSON object key" in capsys.readouterr().err
    assert output.read_bytes() == b"previous output"


@pytest.mark.parametrize("text", DUPLICATE_ACTIONS)
def test_json_03_cli_action_duplicates_do_not_apply_a_partial_result(
    text, tmp_path, capsys
):
    source, action, output = (
        tmp_path / name for name in ("source.json", "action.json", "output.json")
    )
    mp.save_spec(mp.FigureSpec(), source)
    before = source.read_bytes()
    action.write_text(text, encoding="utf-8")
    output.write_bytes(b"previous output")
    assert main(["apply", str(source), str(action), "-o", str(output)]) == 1
    assert "duplicate JSON object key" in capsys.readouterr().err
    assert source.read_bytes() == before and output.read_bytes() == b"previous output"


@pytest.mark.parametrize("literal", ["NaN", "Infinity", "-Infinity", "1e400", "-1e400"])
@pytest.mark.parametrize("command", ["validate", "migrate", "apply", "render"])
def test_json_02_nonfinite_raw_spec_numbers_fail_without_output_change(
    literal, command, tmp_path, capsys
):
    source, action, output = (
        tmp_path / name for name in ("bad.json", "action.json", "keep.png")
    )
    source.write_text(
        '{"data":{"columns":{"unused":[' + literal + "]}}}", encoding="utf-8"
    )
    action.write_text('{"type":"SetTitle","text":"never"}', encoding="utf-8")
    output.write_bytes(b"previous output")
    args = [command, str(source)]
    if command == "apply":
        args.append(str(action))
    if command == "render":
        args.append(str(output))
    elif command != "validate":
        args.extend(["-o", str(output)])
    assert main(args) == 1
    assert "error:" in capsys.readouterr().err
    assert output.read_bytes() == b"previous output"


@pytest.mark.parametrize("kind", ["missing", "positive_infinity", "negative_infinity"])
@pytest.mark.parametrize("shape", ["mapping", "records", "rows", "numpy", "pandas"])
def test_json_02_adapter_missing_normalization_is_separate_from_infinity_rejection(
    shape,
    kind,
):
    from mudplot.data import to_columns

    values = (
        [1.0, float("nan"), None]
        if kind == "missing"
        else [float("inf") if kind == "positive_infinity" else -float("inf")]
    )
    if shape == "mapping":
        source = {"value": values}
    elif shape == "records":
        source = [{"value": value} for value in values]
    elif shape == "rows":
        source = [[value] for value in values]
    elif shape == "numpy":
        np = pytest.importorskip("numpy")
        source = np.array([[value] for value in values], dtype=float)
    else:
        pd = pytest.importorskip("pandas")
        source = pd.DataFrame({"value": pd.Series(values, dtype="Float64")})
    columns = to_columns(source)
    spec = mp.FigureSpec()
    spec.data.columns = columns
    if kind == "missing":
        assert list(columns.values()) == [[1.0, None, None]]
        assert mp.from_json(mp.to_json(spec)) == spec
    else:
        assert list(columns.values()) == [values]
        with pytest.raises(ValueError, match="finite"):
            mp.to_json(spec)


def test_json_04_known_data_fields_preserve_signed_integer_boundaries():
    positives = [
        2**53 - 1,
        2**53,
        2**53 + 1,
        2**63 - 1,
        2**63,
        2**64 - 1,
        2**64,
        10**80 + 1,
    ]
    integers = [value for number in positives for value in (number, -number)]
    spec = mp.FigureSpec()
    spec.data.columns = {"unused_integer": integers}
    restored = mp.from_json(mp.to_json(spec))
    assert restored.data.columns["unused_integer"] == integers
    assert all(type(value) is int for value in restored.data.columns["unused_integer"])


@pytest.mark.parametrize(
    "text",
    [
        r'{"data":{"columns":{"label":["한글 <&> Ω 😀"]}}}',
        r'{"data":{"columns":{"label":["\ud55c\uae00 <&> \u03a9 \ud83d\ude00"]}}}',
    ],
)
def test_json_06_normal_unicode_and_valid_surrogate_pairs_remain_structural_data(text):
    spec = mp.from_json(text)
    assert spec.data.columns["label"] == ["한글 <&> Ω 😀"]
    assert mp.from_json(mp.to_json(spec)) == spec


@pytest.mark.parametrize(
    "text",
    [
        r'{"data":{"columns":{"unused":[{"$serde_json::private::Number":"1"}]}}}',
        r'{"data":{"columns":{"unused":[{"value":"\ud800"}]}}}',
        r'{"data":{"columns":{"unused":[{"value":"\udfff"}]}}}',
    ],
)
def test_json_06_nested_reserved_keys_and_lone_surrogates_are_rejected(text):
    with pytest.raises(ValueError):
        mp.from_json(text)


@pytest.mark.parametrize("version", ["99.0", "0.0", "", 1, False, None, []])
def test_json_07_unknown_or_malformed_versions_never_replace_cli_output(
    version, tmp_path, capsys
):
    source, output = tmp_path / "source.json", tmp_path / "previous.json"
    source.write_text(json.dumps({"version": version}), encoding="utf-8")
    output.write_bytes(b"previous output")
    assert main(["migrate", str(source), "-o", str(output)]) == 1
    assert "error:" in capsys.readouterr().err
    assert output.read_bytes() == b"previous output"
