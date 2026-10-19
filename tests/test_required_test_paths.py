"""A green optional-test exit is not evidence of required CI execution."""

import ast
import json
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest
from scripts import check_required_test_paths as gate

ROOT = Path(__file__).resolve().parents[1]


def report(path, profile, state="passed"):
    root = ET.Element("testsuites")
    suite = ET.SubElement(root, "testsuite")
    for index, (module, name) in enumerate(gate.REQUIRED[profile]):
        if index == 0 and state == "missing":
            continue
        case = ET.SubElement(suite, "testcase", classname=f"tests.{module}", name=name)
        if index == 0:
            if state in ("skipped", "xfailed"):
                ET.SubElement(
                    case,
                    "skipped",
                    type=f"pytest.{state}",
                    message="synthetic missing tool",
                )
            elif state == "failed":
                ET.SubElement(case, "failure", message="synthetic regression")
            elif state == "duplicate":
                ET.SubElement(suite, "testcase", classname=f"tests.{module}", name=name)
    optional = ET.SubElement(
        suite, "testcase", classname="tests.test_optional", name="optional_tool"
    )
    ET.SubElement(
        optional, "skipped", type="pytest.skip", message="optional tool absent"
    )
    ET.ElementTree(root).write(path, encoding="utf-8")


@pytest.mark.parametrize("profile", list(gate.REQUIRED))
def test_completed_required_paths_allow_unrelated_optional_skips(tmp_path, profile):
    path = tmp_path / "results.xml"
    report(path, profile)
    result = gate.audit_report(path, profile)
    assert result["ok"] and result["counts"]["skipped"] == 1
    assert result["counts"]["passed"] == len(gate.REQUIRED[profile])


@pytest.mark.parametrize(
    "state", ["missing", "skipped", "xfailed", "failed", "duplicate"]
)
def test_required_missing_skip_xfail_failure_or_ambiguity_cannot_pass(tmp_path, state):
    path = tmp_path / "results.xml"
    report(path, "ci", state)
    assert not gate.audit_report(path, "ci")["ok"]


@pytest.mark.parametrize("present", [False, True])
def test_missing_or_malformed_report_is_explicit_failure(tmp_path, capsys, present):
    path = tmp_path / "results.xml"
    if present:
        path.write_text("<incomplete", encoding="utf-8")
    assert gate.main(["ci", str(path)]) == 1
    result = json.loads(capsys.readouterr().out)
    assert not result["ok"] and result["error"] in ("FileNotFoundError", "ParseError")


@pytest.mark.parametrize(
    "payload",
    [
        b'<!DOCTYPE testsuites [<!ENTITY x SYSTEM "file:///synthetic-private">]>'
        b"<testsuites>&x;</testsuites>",
        b'<!DOCTYPE testsuites [<!ENTITY a "x"><!ENTITY b "&a;&a;">]>'
        b"<testsuites>&b;</testsuites>",
        "<!DOCTYPE testsuites><testsuites/>".encode("utf-16"),
        b"<testsuites>\x00</testsuites>",
    ],
)
def test_dtd_entity_and_non_utf8_reports_are_rejected(tmp_path, payload):
    path = tmp_path / "results.xml"
    path.write_bytes(payload)
    with pytest.raises(ValueError):
        gate.audit_report(path, "ci")


def test_report_size_is_bounded_before_xml_parsing(tmp_path, monkeypatch):
    monkeypatch.setattr(gate, "MAX_JUNIT_BYTES", 32)
    path = tmp_path / "results.xml"
    path.write_bytes(b" " * 33)
    with pytest.raises(ValueError, match="exceeds"):
        gate.audit_report(path, "ci")


def test_utf8_bom_report_is_supported(tmp_path):
    path = tmp_path / "results.xml"
    report(path, "ci")
    path.write_bytes(b"\xef\xbb\xbf" + path.read_bytes())
    assert gate.audit_report(path, "ci")["ok"]


def test_unrelated_failure_still_rejects_report(tmp_path):
    path = tmp_path / "results.xml"
    report(path, "ci")
    tree = ET.parse(path)
    ET.SubElement(next(tree.iter("testcase")), "error", message="synthetic error")
    tree.write(path, encoding="utf-8")
    assert not gate.audit_report(path, "ci")["ok"]


def test_required_identities_reference_real_tests_and_matrix_ids():
    for module, name in gate.REQUIRED["release"]:
        source = (ROOT / "tests" / f"{module}.py").read_text(encoding="utf-8")
        names = {
            node.name
            for node in ast.parse(source).body
            if isinstance(node, ast.FunctionDef)
        }
        assert name.split("[", 1)[0] in names
        if "[" in name:
            assert f'id="{name.split("[", 1)[1][:-1]}"' in source


def test_workflow_result_gates_are_wired_to_distinct_reports():
    ci = " ".join(
        (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8").split()
    )
    tex = (ROOT / ".github/workflows/tex-matrix.yml").read_text(encoding="utf-8")
    release = (ROOT / ".github/workflows/release.yml").read_text(encoding="utf-8")
    assert (
        "check_required_test_paths.py ci ci-results-${{ matrix.python-version }}.xml"
        in ci
    )
    assert "check_required_test_paths.py minimum minimum-results.xml" in ci
    assert "test-results-python-${{ matrix.python-version }}-${{ github.sha }}" in ci
    assert "cache-suffix: python-${{ matrix.python-version }}" in ci
    assert "cache-suffix: minimum-python-3.10" in ci
    assert "cache-suffix: rust-${{ matrix.os }}-python-3.12" in ci
    assert "check_required_test_paths.py tex tex-results.xml" in tex
    assert "check_required_test_paths.py release release-results.xml" in release
