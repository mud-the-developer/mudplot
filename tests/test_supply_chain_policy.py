"""Source/guard checks are not a substitute for exact artifact verification."""

import subprocess
from pathlib import Path

import pytest
from scripts import audit_dependencies as audit

ROOT = Path(__file__).resolve().parents[1]


def workflow(name):
    return (ROOT / ".github/workflows" / name).read_text(encoding="utf-8")


def test_review_jobs_are_read_only_and_do_not_run_privileged_pr_events():
    for name in ("ci.yml", "tex-matrix.yml"):
        text = workflow(name)
        assert "permissions:\n  contents: read" in text
        assert "contents: write" not in text and "id-token: write" not in text
        assert "pull_request_target:" not in text and "workflow_run:" not in text
        assert "continue-on-error:" not in text
        assert "persist-credentials: false" in text


def test_release_writes_are_scoped_and_failed_build_cannot_publish():
    text = workflow("release.yml")
    build, publisher = text.split("\n  github-release:", 1)
    assert 'tags: ["v*"]' in text
    assert "contents: read" in build and "contents: write" not in build
    assert "id-token: write" in build and "attestations: write" in build
    assert "needs: build" in publisher and "contents: write" in publisher
    assert "id-token: write" not in publisher and "attestations: write" not in publisher
    assert "if: always()" not in publisher and "continue-on-error:" not in text
    assert "--clobber" not in publisher and "gh release upload" not in publisher
    assert "--verify-tag" in publisher and "immutable" in publisher


def test_release_source_and_artifact_guards_are_explicit():
    text = workflow("release.yml")
    assert ".verification.verified" in text and "release tag must be annotated" in text
    assert "target_sha" in text and "checkout_sha" in text and "!= commit" in text
    assert "--require-hashes" in (ROOT / "scripts/audit_dependencies.py").read_text(
        encoding="utf-8"
    )
    assert "diff -u" in text and "sha256sum --check --strict SHA256SUMS" in text
    assert (
        "dist/*.whl" in text and "dist/*.tar.gz" in text and "dist/SHA256SUMS" in text
    )
    assert "subject-path:" in text and "gh release view" in text and "exit 1" in text


def test_audit_exports_all_locks_with_hashes_and_no_ignored_advisories(monkeypatch):
    calls = []

    def run(argv, **kwargs):
        calls.append(argv)
        assert kwargs.get("check") is True

    monkeypatch.setattr(audit.subprocess, "run", run)
    assert audit.main() == 0 and len(calls) == 6
    assert all("--locked" in argv for argv in calls[::2])
    assert all(
        "--require-hashes" in argv and "--disable-pip" in argv for argv in calls[1::2]
    )
    assert all("--ignore-vuln" not in argv for argv in calls)
    assert sum("--script" in argv for argv in calls[::2]) == 2


@pytest.mark.parametrize("failure_call", [1, 2])
def test_audit_export_or_vulnerability_failure_stops_without_bypass(
    monkeypatch, failure_call
):
    calls = []

    def run(argv, **kwargs):
        calls.append(argv)
        if len(calls) == failure_call:
            raise subprocess.CalledProcessError(7, argv)

    monkeypatch.setattr(audit.subprocess, "run", run)
    with pytest.raises(subprocess.CalledProcessError):
        audit.main()
    assert len(calls) == failure_call
