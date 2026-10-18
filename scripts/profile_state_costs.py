"""Bounded PERF-01/03 measurements; no performance thresholds or optimizations."""

from __future__ import annotations

import cProfile
import hashlib
import importlib.metadata
import json
import math
import platform
import pstats
import statistics
import sys
import tempfile
import time
import tracemalloc
from collections.abc import Callable
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mudplot as mp

ROOT = Path(__file__).resolve().parents[1]


def summary(samples: list[float]) -> dict:
    ordered = sorted(samples)
    assert ordered and all(value >= 0 for value in ordered)
    return {
        "samples": len(ordered),
        "median_ms": statistics.median(ordered) * 1000,
        "p95_nearest_rank_ms": ordered[math.ceil(0.95 * len(ordered)) - 1] * 1000,
    }


def measure(call: Callable[[], object], repeats: int) -> dict:
    call()  # Warm this path; startup/import/font discovery is a separate workload.
    times = []
    for _ in range(repeats):
        start = time.perf_counter()
        call()
        times.append(time.perf_counter() - start)
    return summary(times)


def noop_listener(_state, _action) -> None:
    pass


def collect_row(count: int, output: Path) -> dict:
    columns = {
        "x": [i * 6.28 / (count - 1) for i in range(count)],
        "y": [math.sin(i * 6.28 / (count - 1)) for i in range(count)],
        "note": [f"synthetic-row-{i}" for i in range(count)],
    }
    spec = mp.plot(columns).line("x", "y").size(4, 3).spec
    spec.dpi = 72
    base_json = mp.to_json(spec, indent=None)
    assert mp.validate(spec) == []
    store = mp.Store(spec)
    subscribed = mp.Store(spec)
    listener_calls = []
    subscribed.subscribe(lambda _state, _action: listener_calls.append(1))
    title = mp.actions.SetTitle(text="measured title")
    style = mp.actions.SetFont(params={"size": 10})

    def render():
        plt.close(mp.render(spec))

    def save():
        plt.close(mp.save(spec, str(output)))

    stages = {
        "reducer_title": measure(lambda: mp.reduce(spec, title), 20),
        "reducer_font": measure(lambda: mp.reduce(spec, style), 20),
        "store_dispatch_title_no_listener": measure(lambda: store.dispatch(title), 20),
        "store_dispatch_font_no_listener": measure(lambda: store.dispatch(style), 20),
        "store_dispatch_one_counting_listener": measure(
            lambda: subscribed.dispatch(title), 20
        ),
        "store_snapshot": measure(lambda: store.state, 20),
        "validation": measure(lambda: mp.validate(spec), 20),
        "to_json": measure(lambda: mp.to_json(spec, indent=None), 20),
        "from_json": measure(lambda: mp.from_json(base_json), 20),
        "model_to_figure_and_close": measure(render, 10),
        "public_png_save_and_close": measure(save, 10),
    }
    assert len(listener_calls) == 21 and len(store.history) == 42
    assert (
        store.state.data.columns == columns
        and mp.to_json(spec, indent=None) == base_json
    )
    assert output.read_bytes().startswith(b"\x89PNG") and not plt.get_fignums()
    row = {
        "count": count,
        "json_bytes": len(base_json.encode()),
        "stages": stages,
        "history_length_end": len(store.history),
        "listener_calls": len(listener_calls),
    }
    if count != 100000:
        return row

    observed = mp.Store(spec)
    observed.subscribe(noop_listener)
    profiler = cProfile.Profile()
    profiler.enable()
    for index in range(10):
        observed.dispatch(mp.actions.SetTitle(text=f"profile-{index}"))
    profiler.disable()
    stats = pstats.Stats(profiler).get_stats_profile()
    entries = [
        {
            "file": Path(value.file_name).name,
            "line": value.line_number,
            "function": name,
            "calls": value.ncalls,
            "self_seconds": value.tottime,
            "cumulative_seconds": value.cumtime,
        }
        for name, value in stats.func_profiles.items()
    ]
    copy_time = sum(
        e["cumulative_seconds"]
        for e in entries
        if e["file"] == "copy.py" and e["function"] == "deepcopy"
    )
    assert not any(
        e["file"] == "_render.py" and e["function"] in ("render", "save")
        for e in entries
    )
    allocation_store = mp.Store(spec)
    tracemalloc.start()
    result = allocation_store.dispatch(title)
    current, peak = tracemalloc.get_traced_memory()
    allocations = tracemalloc.take_snapshot().statistics("lineno")[:8]
    tracemalloc.stop()
    assert result.data.columns == columns
    row["dispatch_profile"] = {
        "actions": 10,
        "listeners": 1,
        "total_seconds": stats.total_tt,
        "deepcopy_cumulative_seconds": copy_time,
        "deepcopy_fraction": copy_time / stats.total_tt,
        "render_calls": 0,
        "validation_calls": sum(
            int(e["calls"].split("/")[0])
            for e in entries
            if e["file"] == "validate.py" and e["function"] == "validate"
        ),
        "hot_paths": sorted(
            entries, key=lambda e: e["cumulative_seconds"], reverse=True
        )[:12],
    }
    row["python_allocations_one_separate_dispatch"] = {
        "current_bytes": current,
        "peak_bytes": peak,
        "not_native_or_rss": True,
        "hot_lines": [
            {"location": str(a.traceback), "bytes": a.size, "count": a.count}
            for a in allocations
        ],
    }
    return row


def main() -> int:
    assert summary([0.001, 0.002, 0.003, 0.004]) == {
        "samples": 4,
        "median_ms": 2.5,
        "p95_nearest_rank_ms": 4.0,
    }
    report = {
        "environment": {
            "python": sys.version,
            "platform": platform.platform(),
            "processor": platform.processor(),
            "versions": {
                name: importlib.metadata.version(name)
                for name in ("numpy", "matplotlib", "mudplot")
            },
        },
        "source_sha256": {
            p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest()
            for p in (
                "mudplot/store.py",
                "mudplot/reducer.py",
                "mudplot/spec.py",
                "mudplot/io.py",
                "mudplot/_render.py",
                "scripts/profile_state_costs.py",
            )
        },
        "scope": (
            "Warm single-process synthetic three-column line plot; short history. "
            "No cold startup, native RSS, long-history matrix, concurrency or "
            "latency promise. Close is included in render/save timing; "
            "tracemalloc/cProfile are separate instrumented trials."
        ),
        "rows": [],
    }
    with tempfile.TemporaryDirectory(prefix="mudplot-state-costs-") as directory:
        output = Path(directory) / "figure.png"
        for count in (1000, 10000, 100000):
            report["rows"].append(collect_row(count, output))
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
