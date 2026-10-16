"""DATA-02: malformed rectangular inputs must never silently truncate values."""

from __future__ import annotations

import copy

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


def test_data_02_valid_positional_and_db_rows_keep_values_and_order():
    rows = [[1, 2], [3, 4], [5, 6]]

    class Cursor:
        description = (("x",), ("y",))

        def fetchall(self):
            return rows

    assert to_columns(rows) == {"c0": [1, 3, 5], "c1": [2, 4, 6]}
    assert to_columns(Cursor()) == {"x": [1, 3, 5], "y": [2, 4, 6]}
    assert to_columns([[], []]) == {}
