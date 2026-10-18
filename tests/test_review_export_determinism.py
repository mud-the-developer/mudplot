"""OUT-01/02 and LAY-01/02: fixed-environment bytes and real file dimensions."""

from __future__ import annotations

import hashlib
import os
import struct
import subprocess
import sys
import time
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mudplot as mp
import pytest
from mudplot import actions as A

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("extension", ["png", "pdf", "svg"])
def test_time_spaced_and_fresh_process_exports_are_byte_identical(tmp_path, extension):
    plot = mp.plot({"x": [0, 1, 2], "y": [1, 4, 2], "g": ["A", "B", "A"]})
    plot.line("x", "y", group="g").labels(title="Repeated output Ω").size(4, 3)
    plot.dispatch(A.SetDpi(100))
    spec = tmp_path / "input.json"
    mp.save_spec(plot.spec, spec)
    outputs = [tmp_path / f"{index}.{extension}" for index in range(3)]
    plt.close(mp.save(plot.spec, outputs[0]))
    time.sleep(1.05)  # cross a timestamp boundary, rather than two same-second saves
    plt.close(mp.save(mp.load_spec(spec), outputs[1]))
    code = (
        "import sys,matplotlib;matplotlib.use('Agg');"
        "import matplotlib.pyplot as p;import mudplot as m;"
        "p.close(m.save(m.load_spec(sys.argv[1]),sys.argv[2]));"
        "assert not p.get_fignums()"
    )
    subprocess.run(
        [sys.executable, "-c", code, str(spec), str(outputs[2])],
        cwd=tmp_path,
        env={**os.environ, "PYTHONPATH": str(ROOT), "MPLBACKEND": "Agg"},
        check=True,
        timeout=45,
    )
    hashes = [hashlib.sha256(path.read_bytes()).hexdigest() for path in outputs]
    assert hashes[0] == hashes[1] == hashes[2]
    data = outputs[0].read_bytes()
    if extension == "png":
        assert struct.unpack(">II", data[16:24]) == (400, 300)
    elif extension == "pdf":
        assert b"/MediaBox [ 0 0 288 216 ]" in data
        assert b"/CreationDate" not in data and b"/ModDate" not in data
    else:
        text = data.decode("utf-8")
        assert 'width="288pt" height="216pt"' in text
        assert "Repeated output" in text
        assert "<dc:date>" not in text
    assert not plt.get_fignums()


def test_tight_export_is_explicit_and_does_not_change_the_saved_spec(tmp_path):
    plot = mp.plot({"x": [1, 2], "y": [2, 3]}).line("x", "y").size(4, 3)
    plot.dispatch(A.SetDpi(100))
    before = plot.to_json()
    exact, cropped = tmp_path / "exact.png", tmp_path / "cropped.png"
    with plt.rc_context({"savefig.bbox": "tight"}):
        plt.close(plot.save(exact))
        plt.close(plot.save(cropped, tight=True))
    assert struct.unpack(">II", exact.read_bytes()[16:24]) == (400, 300)
    assert struct.unpack(">II", cropped.read_bytes()[16:24]) != (400, 300)
    assert plot.to_json() == before
