"""PERF-06: deterministic owned-render overlap, not arbitrary pyplot thread safety."""

import threading
from concurrent.futures import ThreadPoolExecutor

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mudplot as mp
import pytest


def specs():
    base = mp.plot({"x": [0, 1, 2], "y": [1, 3, 2]}).line("x", "y").size(4, 3)
    a = mp.reduce(base.spec, mp.actions.SetFont(params={"size": 8}))
    b = mp.reduce(base.spec, mp.actions.SetFont(params={"size": 24}))
    a.suptitle, b.suptitle = "A", "B"
    return a, b


@pytest.mark.parametrize("entrypoint", ["render", "tex_preview"])
def test_distinct_render_rc_contexts_do_not_overlap_or_leak(monkeypatch, entrypoint):
    from mudplot import _render

    a, b = specs()
    baseline = matplotlib.rcParams.copy()
    first_inside = threading.Event()
    second_attempt = threading.Event()
    second_inside = threading.Event()
    first_returned = threading.Event()
    observed = {}
    figures = []
    original = _render._draw_panel

    def draw(ax, spec, panel, **kwargs):
        if spec.suptitle == "A":
            first_inside.set()
            assert second_attempt.wait(5)
            second_inside.wait(0.3)
        else:
            second_inside.set()
            assert first_returned.wait(10)
        observed[spec.suptitle] = matplotlib.rcParams["font.size"]
        return original(ax, spec, panel, **kwargs)

    def first():
        try:
            return getattr(mp, entrypoint)(a)
        finally:
            first_returned.set()

    def second():
        assert first_inside.wait(5)
        second_attempt.set()
        return getattr(mp, entrypoint)(b)

    monkeypatch.setattr(_render, "_draw_panel", draw)
    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = (pool.submit(first), pool.submit(second))
            figures.extend(f.result(timeout=20) for f in futures)
        assert observed == {"A": 8, "B": 24}
        assert matplotlib.rcParams["font.size"] == baseline["font.size"]
        assert [fig._suptitle.get_fontsize() for fig in figures] == pytest.approx(
            [9.6, 28.8]
        )
    finally:
        for fig in figures:
            plt.close(fig)
        matplotlib.rcParams.update(baseline)


def test_independent_editor_sessions_share_effect_serialization():
    from dashboard.editor_server import EditorSession

    a, b = specs()
    sessions = [EditorSession(), EditorSession()]
    expected = []
    for session, spec in zip(sessions, (a, b), strict=True):
        session.load_spec(mp.to_json(spec))
        expected.append((session.png, session.export("svg"), session.layout))
    assert sessions[0].lock is not sessions[1].lock
    barrier = threading.Barrier(2)

    def load(index):
        barrier.wait(timeout=5)
        with sessions[index].lock:
            sessions[index].load_spec(mp.to_json((a, b)[index]))
            return (
                sessions[index].png,
                sessions[index].export("svg"),
                sessions[index].layout,
            )

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert list(pool.map(load, (0, 1))) == expected
    assert expected[0][0] != expected[1][0]


@pytest.mark.parametrize("extension", ["png", "pdf", "svg"])
def test_concurrent_public_saves_match_distinct_serial_bytes(tmp_path, extension):
    a, b = specs()
    expected = []
    for index, spec in enumerate((a, b)):
        path = tmp_path / f"serial-{index}.{extension}"
        plt.close(mp.save(spec, str(path)))
        expected.append(path.read_bytes())
    barrier = threading.Barrier(2)

    def save(index):
        barrier.wait(timeout=5)
        path = tmp_path / f"parallel-{index}.{extension}"
        return mp.save((a, b)[index], str(path)), path.read_bytes()

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(save, (0, 1)))
    try:
        assert [data for _fig, data in results] == expected
        assert expected[0] != expected[1]
        assert not list(tmp_path.glob("*.tmp"))
    finally:
        for fig, _data in results:
            plt.close(fig)
