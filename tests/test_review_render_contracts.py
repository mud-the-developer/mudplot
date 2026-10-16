"""JSON-05: exact JSON integers are not a promise of arbitrary-precision rendering."""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mudplot as mp
import pytest
from mudplot.__main__ import main


@pytest.mark.parametrize("kind", ["x", "y", "matrix", "style", "size"])
@pytest.mark.parametrize("extension", ["png", "pdf", "svg"])
def test_json_05_unrepresentable_values_preserve_output_and_close_figures(
    tmp_path, capsys, kind, extension
):
    huge = 10**1000
    if kind == "matrix":
        plot = mp.plot().matrix("m", [[huge]]).heatmap("m")
    else:
        columns = {"x": [huge if kind == "x" else 1], "y": [huge if kind == "y" else 2]}
        plot = mp.plot(columns).line(
            "x", "y", line_width=huge if kind == "style" else None
        )
        if kind == "size":
            plot.size(huge, 3)
    text = plot.to_json()
    assert str(huge) in text and mp.Plot.from_json(text).spec == plot.spec
    source = tmp_path / "structurally-valid.json"
    source.write_text(text, encoding="utf-8")
    destination = tmp_path / f"previous.{extension}"
    destination.write_bytes(b"previous complete output")
    figures = set(plt.get_fignums())
    assert main(["render", str(source), str(destination)]) == 1
    error = capsys.readouterr().err
    assert error.startswith("error:") and "Traceback" not in error
    assert destination.read_bytes() == b"previous complete output"
    assert set(plt.get_fignums()) == figures
    assert sorted(path.name for path in tmp_path.iterdir()) == sorted(
        [source.name, destination.name]
    )


def test_json_05_failed_editor_open_preserves_state_history_preview_and_recovery():
    from dashboard.editor_server import EditorSession

    valid = mp.plot({"x": [1, 2], "y": [2, 3]}).line("x", "y").size(4, 3)
    session = EditorSession()
    session.load_spec(valid.to_json())
    before, history, preview = session.store.state, session.store.history, session.png
    invalid = mp.plot({"x": [1], "y": [10**1000]}).line("x", "y")
    with pytest.raises(ValueError, match="floating-point range"):
        session.load_spec(invalid.to_json())
    assert session.store.state == before and session.store.history == history
    assert session.png == preview
    valid.labels(title="recovered")
    session.load_spec(valid.to_json())
    assert session.store.state.panels[0].title == "recovered"
