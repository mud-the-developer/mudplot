"""Bounded PERF-02 core history matrix; observed budgets are not an OS sandbox."""

from __future__ import annotations

import hashlib
import json
import math
import os
import platform
import statistics
import subprocess
import sys
import time
from pathlib import Path

import mudplot as mp
from scripts.check_request_body_limits import _memory

ROOT = Path(__file__).resolve().parents[1]
SIZES = (1000, 10000, 100000)
HISTORIES = (10, 100, 1000)
DISPATCH_SECONDS = 2.5
CHILD_SECONDS = 12
RSS_BYTES = 512 * 1024 * 1024


def sample_summary(values: list[float]) -> dict:
    assert values and all(value >= 0 for value in values)
    ordered = sorted(values)
    return {
        "samples": len(values),
        "median_ms": statistics.median(values) * 1000,
        "p95_nearest_rank_ms": ordered[math.ceil(0.95 * len(values)) - 1] * 1000,
    }


def emit(row: dict) -> None:
    print(json.dumps(row), flush=True)


def case(count: int, history: int) -> int:
    if count not in SIZES or history not in HISTORIES:
        raise ValueError("rows/history must use the bounded declared matrix")
    columns = {
        "x": list(range(count)),
        "y": [i % 13 for i in range(count)],
        "notes": [f"synthetic-{i}" for i in range(count)],
    }
    store = mp.Store(mp.plot(columns).line("x", "y").spec)
    before = _memory(os.getpid())
    emit({"stage": "ready", "rows": count, "target_history": history, "before": before})
    started = time.perf_counter()
    timings = []
    stopped = None
    for index in range(history):
        if time.perf_counter() - started >= DISPATCH_SECONDS:
            stopped = "dispatch_time_budget"
            break
        if index % 10 == 0 and _memory(os.getpid())["rss_bytes"] > RSS_BYTES:
            stopped = "rss_observation_budget"
            break
        begin = time.perf_counter()
        result = store.dispatch(mp.actions.SetTitle(text=f"history-{index}"))
        timings.append(time.perf_counter() - begin)
    completed = len(timings)
    assert len(store.history) == completed
    if completed:
        assert result.data.columns == columns
    row = {
        "stage": "dispatch",
        "rows": count,
        "target_history": history,
        "completed_actions": completed,
        "target_reached": completed == history,
        "stop_reason": stopped,
        "seconds": time.perf_counter() - started,
        "latency": sample_summary(timings) if timings else None,
        "memory": _memory(os.getpid()),
        "undo_ms": None,
        "redo_ms": None,
    }
    emit(row)
    if completed != history:
        return 0  # The stopped workload is explicit, not a zero-latency success.
    begin = time.perf_counter()
    previous = store.undo()
    row["undo_ms"] = (time.perf_counter() - begin) * 1000
    assert len(store.history) == history - 1
    if history > 1:
        assert previous.panels[0].title == f"history-{history - 2}"
    row["stage"] = "undo"
    emit(row)
    begin = time.perf_counter()
    restored = store.redo()
    row["redo_ms"] = (time.perf_counter() - begin) * 1000
    assert (
        len(store.history) == history
        and restored.panels[0].title == f"history-{history - 1}"
    )
    assert restored.data.columns == columns
    row["stage"] = "completed"
    row["memory"] = _memory(os.getpid())
    emit(row)
    return 0


def collect_case(count: int, history: int) -> dict:
    argv = [sys.executable, str(Path(__file__).resolve()), str(count), str(history)]
    started = time.monotonic()
    try:
        result = subprocess.run(
            argv,
            cwd=ROOT,
            env={
                **os.environ,
                "PYTHONPATH": str(ROOT),
                "PYTHONUTF8": "1",
                "PYTHONIOENCODING": "utf-8",
            },
            capture_output=True,
            timeout=CHILD_SECONDS,
        )
        raw, stderr = result.stdout, result.stderr
        exit_code, timed_out = result.returncode, False
    except subprocess.TimeoutExpired as error:
        raw, stderr = error.stdout or b"", error.stderr or b""
        exit_code, timed_out = None, True
    lines = raw.split(b"\n")
    incomplete_last_line = bool(lines.pop())
    checkpoints = []
    invalid_checkpoint = None
    for line in lines:
        if not line:
            continue
        try:
            checkpoint = json.loads(line)
            if not isinstance(checkpoint, dict) or "stage" not in checkpoint:
                raise ValueError("checkpoint must be an object with a stage")
            checkpoints.append(checkpoint)
        except (json.JSONDecodeError, UnicodeError, ValueError) as error:
            invalid_checkpoint = type(error).__name__
            break
    status = "timeout" if timed_out else "child_error" if exit_code else "stopped"
    if not timed_out and exit_code == 0:
        if invalid_checkpoint or incomplete_last_line or not checkpoints:
            status = "protocol_error"
        elif checkpoints[-1]["stage"] == "completed":
            status = "completed"
    last = checkpoints[-1] if checkpoints else {}
    return {
        "rows": count,
        "target_history": history,
        "completed_actions": last.get("completed_actions"),
        "undo_ms": last.get("undo_ms"),
        "redo_ms": last.get("redo_ms"),
        "process_seconds": time.monotonic() - started,
        "exit_code": exit_code,
        "timed_out": timed_out,
        "status": status,
        "checkpoints": checkpoints,
        "incomplete_last_line": incomplete_last_line,
        "invalid_checkpoint": invalid_checkpoint,
        "stderr": stderr.decode("utf-8", errors="replace"),
    }


def main() -> int:
    assert sample_summary([0.001, 0.002, 0.003, 0.004])["p95_nearest_rank_ms"] == 4
    rows = [collect_case(count, history) for count in SIZES for history in HISTORIES]
    report = {
        "environment": {
            "python": sys.version,
            "platform": platform.platform(),
            "processor": platform.processor(),
        },
        "source_sha256": {
            p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest()
            for p in (
                "mudplot/store.py",
                "mudplot/reducer.py",
                "mudplot/spec.py",
                "scripts/check_request_body_limits.py",
                "scripts/profile_history_costs.py",
            )
        },
        "budgets": {
            "per_child_seconds": CHILD_SECONDS,
            "dispatch_seconds": DISPATCH_SECONDS,
            "rss_observation_bytes": RSS_BYTES,
        },
        "scope": (
            "Each core-only child has its own process lifetime RSS/peak; "
            "no renderer descendants, concurrent/cold startup comparison, "
            "OS hard RSS limit or long-lived GUI leak guarantee. First dispatch "
            "is retained; timings exclude child import/startup. Incomplete/timeout "
            "checkpoints retain unknown times as null, never zero."
        ),
        "cases": rows,
    }
    print(json.dumps(report, indent=2))
    return int(any(row["status"] in {"child_error", "protocol_error"} for row in rows))


if __name__ == "__main__":
    if len(sys.argv) == 3:
        raise SystemExit(case(int(sys.argv[1]), int(sys.argv[2])))
    raise SystemExit(main())
