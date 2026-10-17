"""DATA-02: malformed rectangular inputs must never silently truncate values."""

from __future__ import annotations

import copy
import sqlite3

import mudplot as mp
import pytest
from mudplot.data import to_columns


@pytest.mark.parametrize(
    "rows",
    [
        [[1, 2], [3, 4, 5]],
        [[1, 2], [3]],
        [[], [1]],
        [[1], []],
    ],
)
def test_data_02_ragged_positional_rows_report_location_and_preserve_input(rows):
    before = copy.deepcopy(rows)
    with pytest.raises(ValueError, match=r"row 1.*expected"):
        to_columns(rows)
    assert rows == before


@pytest.mark.parametrize("rows", [[[1, 2, 3]], [[1]], [[]]])
def test_data_02_db_cursor_row_width_matches_description_before_pivot(rows):
    class Cursor:
        description = (("x",), ("y",))

        def fetchall(self):
            return rows

    before = copy.deepcopy(rows)
    with pytest.raises(ValueError, match=r"DB result row 0.*expected"):
        to_columns(Cursor())
    assert rows == before


@pytest.mark.parametrize("invalid", [None, 3, ["x"], "x"])
@pytest.mark.parametrize("entry", [to_columns, mp.plot], ids=["adapter", "builder"])
def test_data_02_mixed_records_report_the_invalid_record_index(invalid, entry):
    records = [{"x": 1}, invalid]
    before = copy.deepcopy(records)
    with pytest.raises(TypeError, match=r"record 1.*mapping"):
        entry(records)
    assert records == before


@pytest.mark.parametrize("invalid", ["ab", b"ab", {"x": 3, "y": 4}, None, 3])
@pytest.mark.parametrize("entry", ["rows", "cursor"])
def test_data_02_mixed_rows_do_not_become_character_or_key_columns(invalid, entry):
    rows = [[1, 2], invalid]
    before = copy.deepcopy(rows)

    class Cursor:
        description = (("x",), ("y",))

        def fetchall(self):
            return rows

    with pytest.raises(TypeError, match=r"row 1.*sequence"):
        to_columns(Cursor() if entry == "cursor" else rows)
    assert rows == before


def test_data_02_record_key_collision_reports_record_index():
    with pytest.raises(ValueError, match=r"record 1.*duplicate '1'"):
        to_columns([{"x": 1}, {1: 2, "1": 3}])


def test_data_02_sparse_records_keep_union_order_and_missing_values():
    records = [{"y": 4}, {"x": 2, "y": 5}, {}]
    before = copy.deepcopy(records)
    assert to_columns(records) == {"y": [4, 5, None], "x": [None, 2, None]}
    assert records == before


@pytest.mark.parametrize("source", ["mapping", "dataframe", "arrow", "to_dict"])
def test_data_02_mismatched_columns_are_preserved_then_rejected_by_validation(source):
    columns = {"x": [1, 2], "y": [3]}
    before = copy.deepcopy(columns)

    class DataFrameLike:
        @property
        def columns(self):
            return tuple(columns)

        def __getitem__(self, name):
            return columns[name]

    class ArrowLike:
        def to_pydict(self):
            return columns

    class DictLike:
        def to_dict(self):
            return columns

    inputs = {
        "mapping": columns,
        "dataframe": DataFrameLike(),
        "arrow": ArrowLike(),
        "to_dict": DictLike(),
    }
    plot = mp.plot(inputs[source]).line("x", "y")
    assert plot.spec.data.columns == columns
    issues = mp.validate(plot.spec)
    assert any("mismatched lengths: {'x': 2, 'y': 1}" in issue for issue in issues)
    with pytest.raises(ValueError, match="mismatched lengths"):
        mp.assert_valid(plot.spec)
    assert columns == before


@pytest.mark.parametrize("field", ["x", "y", "group"])
@pytest.mark.parametrize("kind", ["line", "scatter"])
def test_data_02_missing_column_error_identifies_the_layer_and_column(field, kind):
    plot = mp.plot({"x": [1], "y": [2], "g": ["A"]})
    getattr(plot, kind)("x", "y", group="g")
    spec = plot.spec
    setattr(spec.panels[0].layers[0], field, "missing_column")
    before = copy.deepcopy(spec)
    assert any(
        f"panel 0 layer 0 ({kind}): column 'missing_column' not found" in issue
        for issue in mp.validate(spec)
    )
    with pytest.raises(ValueError, match="missing_column"):
        mp.assert_valid(spec)
    assert spec == before


@pytest.mark.parametrize("names", [("x", "x"), (1, "1")])
def test_data_02_real_pandas_duplicate_names_fail_without_input_changes(names):
    pd = pytest.importorskip("pandas")
    frame = pd.DataFrame([[1, 2]], columns=list(names))
    before = frame.copy(deep=True)
    with pytest.raises(ValueError, match="DataFrame column names must be unique"):
        to_columns(frame)
    pd.testing.assert_frame_equal(frame, before)


@pytest.mark.parametrize("invalid", ["x", "y", "g", "length"])
def test_data_02_bad_editor_data_preserves_state_history_preview_and_redo(invalid):
    from dashboard.editor_server import EditorSession
    from mudplot import actions as A

    valid = (
        mp.plot({"x": [1, 2], "y": [2, 3], "g": ["A", "A"]})
        .line("x", "y", group="g")
        .size(4, 3)
    )
    session = EditorSession()
    session.load_spec(valid.to_json())
    session.dispatch_safe(A.SetTitle("redo survives"))
    session.undo()
    before, history, preview = session.store.state, session.store.history, session.png
    columns = copy.deepcopy(before.data.columns)
    if invalid == "length":
        columns["y"].pop()
    else:
        del columns[invalid]
    candidate = copy.deepcopy(before)
    candidate.data.columns = columns
    with pytest.raises(ValueError):
        session.load_spec(mp.to_json(candidate))
    assert session.store.state == before and session.store.history == history
    assert session.png == preview
    session.dispatch_safe(A.SetData(columns))
    assert session.error
    assert session.store.state == before and session.store.history == history
    assert session.png == preview
    session.redo()
    assert session.store.state.panels[0].title == "redo survives"


@pytest.mark.parametrize("invalid", ["x", "y", "g", "length"])
def test_data_02_bad_cli_data_action_preserves_input_and_existing_output(
    invalid, tmp_path, capsys
):
    import json

    from mudplot.__main__ import main

    valid = mp.plot({"x": [1, 2], "y": [2, 3], "g": ["A", "A"]}).line(
        "x", "y", group="g"
    )
    columns = valid.spec.data.columns
    if invalid == "length":
        columns["y"].pop()
    else:
        del columns[invalid]
    source, action, output = (
        tmp_path / name for name in ("valid.json", "action.json", "keep.json")
    )
    mp.save_spec(valid.spec, source)
    before = source.read_bytes()
    action.write_text(
        json.dumps({"type": "SetData", "columns": columns}), encoding="utf-8"
    )
    output.write_bytes(b"previous complete spec")
    assert main(["apply", str(source), str(action), "-o", str(output)]) == 1
    assert capsys.readouterr().err.startswith("error:")
    assert (
        source.read_bytes() == before
        and output.read_bytes() == b"previous complete spec"
    )


def test_data_02_sqlite_row_objects_remain_supported():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    try:
        columns = to_columns(connection, query="select ? as x, ? as y", params=(1, 2))
        assert columns == {"x": [1], "y": [2]}
        assert connection.execute("select 1").fetchone()[0] == 1
    finally:
        connection.close()


def test_data_02_valid_positional_and_db_rows_keep_values_and_order():
    rows = [[1, 2], [3, 4], [5, 6]]

    class Cursor:
        description = (("x",), ("y",))

        def fetchall(self):
            return rows

    assert to_columns(rows) == {"c0": [1, 3, 5], "c1": [2, 4, 6]}
    assert to_columns(Cursor()) == {"x": [1, 3, 5], "y": [2, 4, 6]}
    assert to_columns([[], []]) == {}
