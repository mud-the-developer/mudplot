"""Keep stopped/failed performance probes explicit, not fake zero timings."""

import subprocess

from scripts import profile_history_costs as profile


def test_timeout_keeps_complete_checkpoints_and_marks_partial_tail(monkeypatch):
    def timeout(*_args, **_kwargs):
        raise subprocess.TimeoutExpired(
            ["python"],
            profile.CHILD_SECONDS,
            output=b'{"stage":"dispatch","undo_ms":null}\n{"stage":',
        )

    monkeypatch.setattr(profile.subprocess, "run", timeout)
    row = profile.collect_case(100000, 1000)
    assert row["status"] == "timeout" and row["exit_code"] is None
    assert row["incomplete_last_line"]
    assert row["checkpoints"] == [{"stage": "dispatch", "undo_ms": None}]


def test_child_error_keeps_prior_stage_without_claiming_oom(monkeypatch):
    result = subprocess.CompletedProcess(
        ["python"], 7, stdout=b'{"stage":"ready"}\n', stderr=b"synthetic failure"
    )
    monkeypatch.setattr(profile.subprocess, "run", lambda *_args, **_kwargs: result)
    row = profile.collect_case(1000, 10)
    assert row["status"] == "child_error" and row["exit_code"] == 7
    assert row["checkpoints"] == [{"stage": "ready"}]
    assert row["stderr"] == "synthetic failure"


def test_malformed_complete_checkpoint_is_reported_and_prior_rows_survive(monkeypatch):
    result = subprocess.CompletedProcess(
        ["python"], 0, stdout=b'{"stage":"ready"}\nnot-json\n', stderr=b""
    )
    monkeypatch.setattr(profile.subprocess, "run", lambda *_args, **_kwargs: result)
    row = profile.collect_case(1000, 10)
    assert row["status"] == "protocol_error"
    assert row["invalid_checkpoint"] == "JSONDecodeError"
    assert row["checkpoints"] == [{"stage": "ready"}]
