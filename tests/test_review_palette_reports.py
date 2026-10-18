"""COLOR-03/04/05/08: report final exported colours under explicit conditions."""

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest
from mudplot.capabilities import PALETTE_PRESETS
from mudplot.color import convert as cv
from mudplot.color import cvd
from mudplot.color import palette as P
from mudplot.color.distance import delta_e2000


def minimum_gap(rgb):
    lightness = cv.srgb_to_lab(rgb)[:, 0]
    return min(
        abs(float(a - b)) for i, a in enumerate(lightness) for b in lightness[i + 1 :]
    )


@pytest.mark.parametrize("name", PALETTE_PRESETS)
@pytest.mark.parametrize("offset", [-1, 0, 1])
def test_report_measures_final_hex_at_verified_size_boundaries(name, offset):
    n = PALETTE_PRESETS[name]["max_verified_n"] + offset
    pal = P.preset_qualitative(name, n)
    rgb = np.array([cv.hex_to_srgb(color) for color in pal.hex])
    before = (pal.srgb.copy(), pal.lch.copy(), list(pal.hex))
    report = pal.report()
    expected = minimum_gap(rgb)
    assert report["min_lightness_gap"] == pytest.approx(expected, abs=1e-10)
    assert report["grayscale_safe"] == (expected >= 3)
    assert report["evaluation"]["rgb_encoding"] == "hex_srgb8"
    assert report["evaluation"]["scope"] == "measured_palette_only"
    assert (
        np.array_equal(pal.srgb, before[0])
        and np.array_equal(pal.lch, before[1])
        and pal.hex == before[2]
    )


def test_lightness_method_measures_mapped_rgb_not_nominal_design_lch():
    design = np.array([[50.0, 200.0, 0.0], [65.0, 200.0, 0.0]])
    rgb = np.clip(cv.lch_to_srgb(design), 0, 1)
    pal = P.Palette(list(cv.srgb_to_hex(rgb)), rgb, design, "fixture")
    assert pal.min_lightness_gap() == pytest.approx(minimum_gap(rgb), abs=1e-10)
    assert pal.min_lightness_gap() != pytest.approx(15.0)


@pytest.mark.parametrize("types", [("protan", "deutan"), ("tritan",), ()])
def test_report_states_evaluated_model_types_severity_and_thresholds(types):
    pal = P.preset_qualitative("paper", 4)
    report = pal.report(cvd_types=iter(types))
    conditions = report["evaluation"]
    assert conditions["normal_vision"] is True and conditions["cvd_types"] == list(
        types
    )
    assert conditions["cvd_model"] == ("Machado2009" if types else None)
    assert conditions["severity"] == (1.0 if types else None)
    assert conditions["thresholds"] == {"delta_e_cvd": 8.0, "lightness_gap": 3.0}
    rgb = np.array([cv.hex_to_srgb(c) for c in pal.hex])
    labs = [
        cv.srgb_to_lab(rgb),
        *[cv.srgb_to_lab(cvd.simulate(rgb, t, 1)) for t in types],
    ]
    expected = min(
        float(delta_e2000(lab[i], lab[j]))
        for lab in labs
        for i in range(len(pal))
        for j in range(i + 1, len(pal))
    )
    assert report["min_delta_e_cvd"] == pytest.approx(expected, abs=1e-10)


# Machado/Oliveira/Fernandes authors' Table1, full-severity matrices:
# https://www.inf.ufrgs.br/~oliveira/pubs_files/CVD_Simulation/CVD_Simulation.html
MATRICES = {
    "protan": [
        [0.152286, 1.052583, -0.204868],
        [0.114503, 0.786281, 0.099216],
        [-0.003882, -0.048116, 1.051998],
    ],
    "deutan": [
        [0.367322, 0.860646, -0.227968],
        [0.280085, 0.672501, 0.047413],
        [-0.011820, 0.042940, 0.968881],
    ],
    "tritan": [
        [1.255528, -0.076749, -0.178779],
        [-0.078411, 0.930809, 0.147602],
        [0.004733, 0.691367, 0.303900],
    ],
}


@pytest.mark.parametrize("kind", MATRICES)
def test_cvd_full_severity_matches_authors_linear_rgb_table(kind):
    linear = np.array([[0.2, 0.4, 0.6], [1, 0, 0], [0, 1, 0], [0, 0, 1]])

    def encode(value):
        return np.where(
            value <= 0.0031308, 12.92 * value, 1.055 * np.power(value, 1 / 2.4) - 0.055
        )

    expected = encode(np.clip(linear @ np.array(MATRICES[kind]).T, 0, 1))
    np.testing.assert_allclose(
        cvd.simulate(encode(linear), kind, 1), expected, atol=2e-6
    )


def test_palette_degenerate_equal_distance_tie_uses_first_remaining_candidate():
    pal = P.qualitative(3, chroma=0, lightness_jitter=0, n_candidates=8, hue_start=0)
    np.testing.assert_array_equal(pal.lch[:, 2], [0, 45, 90])
    assert len(set(pal.hex)) == 1 and not pal.report()["grayscale_safe"]


def test_palette_generation_is_deterministic_without_rng_seed_or_process_order(
    tmp_path,
):
    options = {"n": 5, "hue_start": 17.0, "n_candidates": 72}
    state = np.random.get_state()
    pal = P.qualitative(**options)
    expected = hashlib.sha256(json.dumps(pal.hex).encode()).hexdigest()
    assert (
        hashlib.sha256(json.dumps(P.qualitative(**options).hex).encode()).hexdigest()
        == expected
    )
    script = (
        "import hashlib,json;from mudplot.color.palette import qualitative;"
        "p=qualitative(n=5,hue_start=17.,n_candidates=72);"
        "print(hashlib.sha256(json.dumps(p.hex).encode()).hexdigest())"
    )
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=tmp_path,
        env={**os.environ, "PYTHONPATH": str(Path.cwd())},
        capture_output=True,
        text=True,
        check=True,
        timeout=30,
    )
    assert result.stdout.strip() == expected
    current = np.random.get_state()
    assert (
        current[0] == state[0]
        and np.array_equal(current[1], state[1])
        and current[2:] == state[2:]
    )
