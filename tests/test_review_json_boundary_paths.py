"""Shared JSON-02/06/07 corpus: API/CLI/editor results, not merely parser collection."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import mudplot as mp
import pytest
from mudplot.__main__ import main

CORPUS = json.loads(
    (Path(__file__).parent / "fixtures/review_json_boundaries.json").read_text(
        encoding="utf-8"
    )
)


def test_boundary_corpus_cannot_hide_failures_behind_missing_version_or_equal_states():
    cases = [case for group in CORPUS.values() for case in group]
    assert len({case["id"] for case in cases}) == len(cases)
    for case in CORPUS["invalid_specs"]:
        if not case["id"].startswith("JSON-07"):
            assert '"version":"0.1"' in case["text"]
    accepted = [mp.from_json(case["text"]) for case in CORPUS["valid_specs"]]
    assert accepted[0] != accepted[1]
    assert r"\ud83d\ude00" in CORPUS["valid_specs"][1]["text"]


@pytest.mark.parametrize("case", CORPUS["invalid_specs"], ids=lambda case: case["id"])
@pytest.mark.parametrize("entry", ["from_json", "plot", "file"])
def test_boundary_api_rejection(case, entry, tmp_path):
    with pytest.raises(ValueError, match="invalid FigureSpec JSON"):
        if entry == "from_json":
            mp.from_json(case["text"])
        elif entry == "plot":
            mp.Plot.from_json(case["text"])
        else:
            path = tmp_path / "bad.json"
            path.write_text(case["text"], encoding="utf-8")
            mp.load_spec(path)


@pytest.mark.parametrize("case", CORPUS["invalid_specs"], ids=lambda case: case["id"])
@pytest.mark.parametrize("command", ["validate", "migrate", "apply", "render"])
def test_boundary_cli_rejection_preserves_existing_output(
    case, command, tmp_path, capsys
):
    source, action, output = (
        tmp_path / name for name in ("bad.json", "action.json", "keep.png")
    )
    source.write_text(case["text"], encoding="utf-8")
    action.write_text('{"type":"SetTitle","text":"never"}', encoding="utf-8")
    output.write_bytes(b"previous complete output")
    args = [command, str(source)]
    if command == "apply":
        args.append(str(action))
    if command == "render":
        args.append(str(output))
    elif command != "validate":
        args.extend(["-o", str(output)])
    assert main(args) == 1
    error = capsys.readouterr().err
    assert error.startswith("error:") and "Traceback" not in error
    assert output.read_bytes() == b"previous complete output"


@pytest.mark.parametrize("case", CORPUS["invalid_actions"], ids=lambda case: case["id"])
def test_boundary_cli_action_rejection_preserves_input_and_output(
    case, tmp_path, capsys
):
    source, action, output = (
        tmp_path / name for name in ("base.json", "bad-action.json", "keep.json")
    )
    mp.save_spec(mp.FigureSpec(), source)
    before = source.read_bytes()
    action.write_text(case["text"], encoding="utf-8")
    output.write_bytes(b"previous complete output")
    assert main(["apply", str(source), str(action), "-o", str(output)]) == 1
    assert capsys.readouterr().err.startswith("error:")
    assert source.read_bytes() == before
    assert output.read_bytes() == b"previous complete output"


@pytest.fixture(scope="module")
def boundary_session():
    from dashboard.editor_server import EditorSession

    session = EditorSession()
    session.load_spec(
        mp.plot({"x": [1, 2], "y": [2, 3]}).line("x", "y").size(4, 3).to_json()
    )
    return session


@pytest.mark.parametrize("case", CORPUS["invalid_specs"], ids=lambda case: case["id"])
def test_boundary_editor_rejection_preserves_committed_state(case, boundary_session):
    session = boundary_session
    state, history, preview = session.store.state, session.store.history, session.png
    with pytest.raises(ValueError, match="invalid figure spec"):
        session.load_spec(case["text"])
    assert session.store.state == state and session.store.history == history
    assert session.png == preview


@pytest.mark.parametrize("case", CORPUS["valid_specs"], ids=lambda case: case["id"])
def test_valid_unicode_and_current_or_omitted_version_round_trip(
    case, tmp_path, boundary_session
):
    expected = mp.from_json(case["text"])
    assert expected.version == "0.1"
    assert expected.data.columns["unused"] == ["한글 <&> Ω 😀"]
    source, output = tmp_path / "valid.json", tmp_path / "normalized.json"
    source.write_text(case["text"], encoding="utf-8")
    assert main(["migrate", str(source), "-o", str(output)]) == 0
    assert mp.load_spec(output) == expected
    boundary_session.load_spec(case["text"])
    assert boundary_session.store.state == expected


@pytest.mark.parametrize("key", [1, False, None])
@pytest.mark.parametrize("nested", [False, True])
def test_nonstring_python_map_keys_are_not_silently_stringified(key, nested):
    spec = mp.FigureSpec()
    spec.data.columns = {"unused": [{key: "value"}]} if nested else {key: [1]}
    with pytest.raises(ValueError, match="object keys must be strings"):
        mp.to_json(spec)
