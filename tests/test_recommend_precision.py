"""Agent advice must not round measurements before describing or ordering them."""

import json
import math

import mudplot as mp
import pytest


@pytest.mark.parametrize("base", [2**53 + 1, -(2**53 + 1)])
@pytest.mark.parametrize("offsets", [[0, 2], [0, 2, 4], [0, 2, 4, 6]])
def test_integer_profiles_preserve_extrema_and_integral_medians(base, offsets):
    values = [base + offset for offset in offsets]
    result = mp.recommend({"y": values}, y="y")
    profile = result["profiles"]["y"]
    assert profile["min"] == values[0]
    assert profile["max"] == values[-1]
    assert profile["median"] == base + sum(offsets) // len(offsets)
    assert isinstance(profile["median"], int)
    assert values == [base + offset for offset in offsets]
    assert any(
        w["code"] == "coordinate-precision" and w["column"] == "y"
        for w in result["warnings"]
    )
    json.dumps(result, allow_nan=False)


def test_fractional_median_remains_a_json_number():
    result = mp.recommend({"y": [1, 2]}, y="y")
    assert result["profiles"]["y"]["median"] == 1.5
    json.dumps(result, allow_nan=False)


@pytest.mark.parametrize("base", [2**53 + 1, -(2**53 + 1)])
@pytest.mark.parametrize(
    ("offsets", "tails"),
    [([0, 1, 2], 0), ([0, 1, 2, 3, 100], 1), ([0, 0, 0, 0, 1], 1), ([0, 2, 4, 6], 0)],
)
def test_tail_candidates_are_translation_invariant_for_integers(base, offsets, tails):
    shifted = [base + value for value in offsets]
    result = mp.recommend({"y": shifted}, y="y")
    assert result["profiles"]["y"]["iqr_tail_count"] == tails
    assert shifted == [base + value for value in offsets]


@pytest.mark.parametrize("grouped", [False, True])
def test_distinct_large_integer_times_are_not_reported_as_repeats(grouped):
    base = 2**53
    data = {"t": [base, base + 1, base + 2], "y": [1, 2, 3]}
    if grouped:
        data = {
            "t": [base, base + 10, base + 1, base + 11],
            "y": [1, 2, 3, 4],
            "g": ["A", "B", "A", "B"],
        }
    before = json.dumps(data)
    result = mp.recommend(data, x="t", y="y", time=True, group="g" if grouped else None)
    assert result["recommendations"][0]["kind"] == "trend"
    codes = {warning["code"] for warning in result["warnings"]}
    assert not codes & {"repeated-time", "unordered-time"}
    precision = [w for w in result["warnings"] if w["code"] == "coordinate-precision"]
    assert len(precision) == 1 and precision[0]["column"] == "t"
    assert json.dumps(data) == before
    assert not result["data_changed"] and not result["units_inferred"]


@pytest.mark.parametrize("offsets", [[0, 0, 1], [2, 1, 0]])
def test_real_repeats_and_reverse_integer_times_still_reject_a_trend(offsets):
    base = 2**53
    result = mp.recommend(
        {"t": [base + v for v in offsets], "y": [1, 2, 3]}, x="t", y="y", time=True
    )
    assert "trend" not in {r["kind"] for r in result["recommendations"]}
    assert "unordered-time" in {w["code"] for w in result["warnings"]}


def test_large_exactly_representable_integers_do_not_get_precision_warning():
    base = 2**53
    result = mp.recommend({"y": [base, base + 2, base + 4]}, y="y")
    assert "coordinate-precision" not in {w["code"] for w in result["warnings"]}


def test_native_event_offset_preserves_the_given_integer_lane():
    lane = 2**53 + 1
    result = mp.recommend(
        {"t": [0, 1], "lane": [lane, lane]}, x="t", y="lane", event=True
    )
    assert result["recommendations"][0]["offset"] == lane
    assert any(
        w["code"] == "coordinate-precision" and w["column"] == "lane"
        for w in result["warnings"]
    )


@pytest.mark.parametrize("times", [[0, None, 1], ["2026-01-01", None, "2026-01-03"]])
def test_missing_times_warn_without_crashing_or_connecting_gaps(times):
    data = {"t": times, "y": [1, 2, 3]}
    before = json.dumps(data)
    result = mp.recommend(data, x="t", y="y", time=True)
    assert "trend" not in {r["kind"] for r in result["recommendations"]}
    assert {"missing-values", "unordered-time"} <= {
        w["code"] for w in result["warnings"]
    }
    assert json.dumps(data) == before


def test_wide_integer_ranges_and_fractional_profiles_remain_json_safe():
    huge = 10**308
    values = [-huge, -huge, 0, huge, huge]
    result = mp.recommend({"y": values}, y="y")
    assert result["profiles"]["y"]["min"] == -huge
    assert result["profiles"]["y"]["max"] == huge
    assert result["profiles"]["y"]["median"] == 0
    assert result["profiles"]["y"]["iqr_tail_count"] is None
    json.dumps(result, allow_nan=False)


def test_integer_precision_warning_does_not_infer_a_temporal_role():
    base = 2**53
    result = mp.recommend(
        {"x": [base, base + 1, base + 2], "y": [1, 2, 3]}, x="x", y="y"
    )
    assert result["recommendations"][0]["kind"] == "relationship"
    assert "coordinate-precision" in {w["code"] for w in result["warnings"]}


def test_visual_qa_reuses_the_coordinate_precision_warning_without_changing_spec():
    base = 2**53
    plot = (
        mp.plot({"x": [base, base + 1, base + 2], "y": [1, 2, 3]})
        .line("x", "y")
        .size(3.5, 2.6)
        .dispatch(mp.actions.SetDpi(100))
    )
    before = plot.to_json()
    report = plot.lint(visual=True)
    assert "coordinate-precision" in {issue.code for issue in report}
    assert plot.to_json() == before


@pytest.mark.parametrize("times", [["0", "1", "2"], [False, True], [0, "1", 2]])
def test_declaring_time_does_not_silently_coerce_non_numeric_columns(times):
    data = {"t": times, "y": list(range(len(times)))}
    before = json.dumps(data)
    result = mp.recommend(data, x="t", y="y", time=True)
    assert "trend" not in {r["kind"] for r in result["recommendations"]}
    assert "unordered-time" in {w["code"] for w in result["warnings"]}
    assert json.dumps(data) == before


@pytest.mark.parametrize("separator", [".", ","])
@pytest.mark.parametrize("declared_time", [None, True])
def test_submicrosecond_iso_times_do_not_invent_repeated_timestamps(
    separator, declared_time
):
    times = [
        f"2026-01-01T00:00:00{separator}{fraction}Z"
        for fraction in ("000000001", "000000002")
    ]
    data = {"t": times, "y": [1, 2]}
    before = json.dumps(data)
    result = mp.recommend(data, x="t", y="y", time=declared_time)
    codes = {warning["code"] for warning in result["warnings"]}
    assert "time-precision" in codes
    assert not codes & {"repeated-time", "unordered-time"}
    assert "trend" not in {r["kind"] for r in result["recommendations"]}
    assert json.dumps(data) == before


def test_iso_fraction_padding_without_precision_loss_still_allows_a_trend():
    times = ["2026-01-01T00:00:00.123456000Z", "2026-01-01T00:00:00.123457000Z"]
    result = mp.recommend({"t": times, "y": [1, 2]}, x="t", y="y")
    assert result["recommendations"][0]["kind"] == "trend"
    assert "time-precision" not in {w["code"] for w in result["warnings"]}


def test_submicrosecond_timezone_offsets_are_not_silently_rounded():
    times = [
        f"2026-01-01T00:00:00+00:00:00.{fraction}"
        for fraction in ("000000001", "000000002")
    ]
    result = mp.recommend({"t": times, "y": [1, 2]}, x="t", y="y")
    codes = {warning["code"] for warning in result["warnings"]}
    assert "time-precision" in codes and "repeated-time" not in codes


@pytest.mark.parametrize(
    ("conditions", "subjects", "values"),
    [
        ([None, "B"], [1, 1], [1, 2]),
        (["A", "B"], [1, 1], [1, None]),
        (["A", "B"], [1, 1], ["low", "high"]),
        (["A", "B"], [None, None], [1, 2]),
        (["A", "B"], [1, 1], [1, 10**1000]),
    ],
    ids=[
        "missing-condition",
        "missing-value",
        "text-value",
        "missing-subject",
        "out-of-range",
    ],
)
def test_paired_advice_requires_complete_numeric_observations(
    conditions, subjects, values
):
    data = {"condition": conditions, "subject": subjects, "value": values}
    before = json.dumps(data)
    result = mp.recommend(data, x="condition", y="value", paired="subject")
    assert "paired" not in {r["kind"] for r in result["recommendations"]}
    assert "incomplete-pairs" in {w["code"] for w in result["warnings"]}
    assert json.dumps(data) == before
    json.dumps(result, allow_nan=False)


@pytest.mark.parametrize(
    ("data", "kwargs"),
    [
        ({"value": [10**1000]}, {}),
        ({"time": [None, None], "value": [1, 1]}, {"x": "time", "event": True}),
        ({"time": [10**1000], "value": [1]}, {"x": "time", "event": True}),
        ({"time": [None, 1], "value": [1, None]}, {"x": "time"}),
    ],
    ids=[
        "unrenderable-value",
        "missing-event-time",
        "unrenderable-event-time",
        "disjoint-values",
    ],
)
def test_advice_requires_at_least_one_usable_observation(data, kwargs):
    result = mp.recommend(data, y="value", **kwargs)
    assert not result["recommendations"]
    assert "insufficient-semantics" in {w["code"] for w in result["warnings"]}
    json.dumps(result, allow_nan=False)


@pytest.mark.parametrize("role", ["x", "group", "paired"])
def test_recommend_rejects_misaligned_role_columns(role):
    data = {"time": [1, 2], "value": [3, 4], "short": [1]}
    with pytest.raises(ValueError, match="same length"):
        mp.recommend(
            data,
            y="value",
            x="short" if role == "x" else "time",
            group="short" if role == "group" else None,
            paired="short" if role == "paired" else None,
        )


@pytest.mark.parametrize("offset", ["+00:00:00.000001", "-000000.000002", "+00:00.1"])
def test_fractional_zero_offsets_are_not_silently_discarded(offset):
    values = [f"2026-10-01T00:00:00{offset}", "2026-10-01T00:00:00+00:00"]
    result = mp.recommend({"time": values, "value": [1, 2]}, x="time", y="value")
    codes = {w["code"] for w in result["warnings"]}
    assert "trend" not in {r["kind"] for r in result["recommendations"]}
    assert "time-precision" in codes and "repeated-time" not in codes
    json.dumps(result, allow_nan=False)


def test_zero_fractional_offset_and_nonzero_exact_offset_remain_supported():
    for offset in ("+00:00:00.000000", "+00:00:01.000001"):
        values = [f"2026-10-01T00:00:00{offset}", f"2026-10-01T00:00:01{offset}"]
        result = mp.recommend({"time": values, "value": [1, 2]}, x="time", y="value")
        assert result["recommendations"][0]["kind"] == "trend"
        assert "time-precision" not in {w["code"] for w in result["warnings"]}
        json.dumps(result, allow_nan=False)


@pytest.mark.parametrize(("start", "rounded"), [(1, 2), (2, 2), (3, 4), (4, 4)])
@pytest.mark.parametrize("sign", [-1, 1])
def test_subnormal_float_medians_round_once(start, rounded, sign):
    values = [math.ldexp(sign * float(v), -1074) for v in (start, start + 1)]
    original = json.dumps(values)
    result = mp.recommend({"y": values}, y="y")
    assert result["profiles"]["y"]["median"] == math.ldexp(sign * float(rounded), -1074)
    assert isinstance(result["profiles"]["y"]["median"], float)
    assert json.dumps(values) == original
    json.dumps(result, allow_nan=False)


@pytest.mark.parametrize("exponent", [-1074, -1022, 0, 1000])
@pytest.mark.parametrize(
    ("values", "tails"), [([0, 0, 1], 0), ([2, 3], 0), ([0, 1, 2, 3, 100], 1)]
)
def test_float_tukey_fences_are_invariant_under_exact_power_of_two_scaling(
    exponent, values, tails
):
    scaled = [math.ldexp(float(value), exponent) for value in values]
    original = json.dumps(scaled)
    result = mp.recommend({"y": scaled}, y="y")
    assert result["profiles"]["y"]["iqr_tail_count"] == tails
    assert ("tail-values" in {w["code"] for w in result["warnings"]}) == bool(tails)
    assert json.dumps(scaled) == original
    json.dumps(result, allow_nan=False)


@pytest.mark.parametrize("sign", [-1, 1])
def test_mixed_integer_float_midpoints_keep_integer_low_bits(sign):
    values = [sign * (2**53 + 1), sign * float(2**53 + 2)]
    result = mp.recommend({"y": values}, y="y")
    assert result["profiles"]["y"]["median"] == sign * float(2**53 + 2)
    json.dumps(result, allow_nan=False)


@pytest.mark.parametrize(
    ("values", "value", "kind"),
    [
        ([1, 3], 2, int),
        ([1.0, 3.0], 2.0, float),
        ([0.0, 2, 4, 6.0], 3, int),
        ([1.0, 2, 3.0], 2, int),
        ([1, 2.0, 3], 2.0, float),
        ([-0.0, -0.0], -0.0, float),
        ([-0.0, 0.0], 0.0, float),
    ],
)
def test_median_scalar_types_and_signed_zero_remain_compatible(values, value, kind):
    median = mp.recommend({"y": values}, y="y")["profiles"]["y"]["median"]
    assert type(median) is kind and median == value
    if median == 0:
        assert math.copysign(1, median) == math.copysign(1, value)
