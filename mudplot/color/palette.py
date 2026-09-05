"""Palette generation in LCH space.

Design principles
-----------------
* **Equal lightness** (constant L*) for qualitative palettes, so categories
  stay fair under greyscale printing and no colour dominates by brightness.
* **Maximum contrast**: colours are chosen to maximise the *minimum*
  perceptual distance (CIEDE2000) between every pair.
* **Colourblind-safe**: the pairwise distance that is maximised is the
  *worst case* across normal vision and CVD simulations (protan / deutan),
  so palettes stay distinguishable for red-green colour blindness.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from ..capabilities import PALETTE_PRESETS
from . import convert as cv
from . import cvd
from .distance import delta_e2000

__all__ = [
    "PALETTE_PRESETS",
    "Palette",
    "diverging",
    "preset_qualitative",
    "qualitative",
    "sequential",
]


@dataclass
class Palette:
    """A generated palette plus the parameters used to build it."""

    hex: list[str]
    srgb: np.ndarray  # (n, 3)
    lch: np.ndarray  # (n, 3)
    kind: str
    meta: dict = field(default_factory=dict)

    def __len__(self) -> int:
        return len(self.hex)

    def __iter__(self):
        return iter(self.hex)

    def __getitem__(self, i):
        return self.hex[i]

    def as_mpl_cycler(self):
        from cycler import cycler

        return cycler("color", list(self.hex))

    def to_cmap(self, name: str | None = None):
        from matplotlib.colors import ListedColormap

        return ListedColormap(
            np.clip(self.srgb, 0, 1), name=name or f"mudplot_{self.kind}"
        )

    def min_delta_e(self, cvd_types=("protan", "deutan")) -> float:
        """Worst-case minimum pairwise ΔE00 across normal + given CVD types."""
        return _min_pairwise_worstcase(self.srgb, cvd_types)

    def grayscale_srgb(self) -> np.ndarray:
        """This palette as it would print in true greyscale (luminance-only).

        Uses relative luminance Y (from linear sRGB), matching how a
        black-and-white printer or a full achromatopsia viewer perceives it —
        a stricter test than CIE L*, which most CVD simulations don't reach.
        """
        lin = cv.srgb_to_linear(self.srgb)
        y = lin @ np.array([0.2126, 0.7152, 0.0722])  # relative luminance
        y3 = np.stack([y, y, y], axis=-1)  # triplicate to satisfy the (...,3) API
        return np.clip(cv.linear_to_srgb(y3), 0.0, 1.0)

    def min_lightness_gap(self) -> float:
        """Smallest pairwise CIE L* gap — low values risk blending together in
        greyscale print or for full achromatopsia, even if hues differ."""
        L = self.lch[:, 0]
        if len(L) < 2:
            return float("inf")
        diffs = np.abs(L[:, None] - L[None, :])
        np.fill_diagonal(diffs, np.inf)
        return float(diffs.min())

    def report(self, cvd_types=("protan", "deutan")) -> dict:
        """A human-readable distinguishability report for this palette."""
        min_de = self.min_delta_e(cvd_types) if len(self) > 1 else None
        min_l = self.min_lightness_gap() if len(self) > 1 else None
        grayscale_safe = min_l is None or min_l >= 3.0
        note = None
        if min_l is not None and not grayscale_safe:
            note = (
                "lightness alone may not separate all colours in true "
                "greyscale/print; for line or scatter series consider "
                ".encoding(redundant_encoding=True) to also cycle "
                "marker/line-style"
            )
        return {
            "n": len(self),
            "min_delta_e_cvd": min_de,
            "min_lightness_gap": min_l,
            "cvd_safe": min_de is None or min_de >= 8.0,
            "grayscale_safe": grayscale_safe,
            "note": note,
        }


# --------------------------------------------------------------------------
# gamut helpers
# --------------------------------------------------------------------------
def _max_chroma(L: float, H: float, c_hi: float = 150.0, tol: float = 0.05) -> float:
    """Largest chroma at (L, H) that stays inside the sRGB gamut."""
    lo, hi = 0.0, c_hi
    if cv.in_gamut(cv.lch_to_srgb(np.array([L, lo, H]))).item() is False:
        return 0.0
    while hi - lo > tol:
        mid = 0.5 * (lo + hi)
        if cv.in_gamut(cv.lch_to_srgb(np.array([L, mid, H]))).item():
            lo = mid
        else:
            hi = mid
    return lo


def _cvd_labs(srgb: np.ndarray, cvd_types) -> list[np.ndarray]:
    """CIELAB of colours under normal vision + each CVD type (full severity)."""
    labs = [cv.srgb_to_lab(srgb)]
    for t in cvd_types:
        labs.append(cv.srgb_to_lab(cvd.simulate(srgb, t, severity=1.0)))
    return labs


def _min_pairwise_worstcase(srgb: np.ndarray, cvd_types) -> float:
    """Worst-case (over vision conditions) minimum pairwise ΔE00.

    Fully vectorised: a naive Python double loop over all (i, j) pairs is
    O(n^2) *Python-level* calls and becomes impractically slow for even a
    few hundred colours (e.g. n=1000 took well over a minute); broadcasting
    the whole (n, n) distance matrix through numpy instead is both correct
    and fast.
    """
    n = len(srgb)
    if n < 2:
        return float("inf")
    labs = _cvd_labs(srgb, cvd_types)
    best = np.full((n, n), np.inf)
    for lab in labs:
        d = delta_e2000(lab[:, None, :], lab[None, :, :])
        best = np.minimum(best, d)
    np.fill_diagonal(best, np.inf)
    return float(best.min())


# --------------------------------------------------------------------------
# qualitative (categorical)
# --------------------------------------------------------------------------
def qualitative(
    n: int,
    *,
    lightness: float = 65.0,
    chroma: float = 55.0,
    hue_start: float = 20.0,
    cvd_safe: bool = True,
    cvd_types=("protan", "deutan"),
    n_candidates: int = 720,
    lightness_jitter: float = 6.0,
) -> Palette:
    """Generate ``n`` categorical colours at (near) constant lightness.

    Colours are picked by farthest-point sampling on the worst-case
    perceptual distance across normal + CVD vision, giving a maximally
    contrasting, colourblind-safe set.

    Parameters
    ----------
    lightness : target L* (0..100). Hue selection is optimised at this exact
        lightness (keeping the set perceptually "fair" in weight); see
        ``lightness_jitter`` for a small, deliberate deviation from this.
    chroma : target C*; clipped per-hue to the sRGB gamut.
    hue_start : hue (deg) used to seed the sampling.
    cvd_safe : if True, optimise the worst case over ``cvd_types`` too.
    lightness_jitter : after hues are chosen at constant lightness, alternate
        each colour's L* by ±half of this amount (deg=L* units). Pure equal-L*
        palettes become *indistinguishable in true greyscale* (e.g. B&W
        print, full achromatopsia) since only hue differs — a small,
        barely-visible jitter fixes that while keeping colours near-equal in
        perceived brightness. Set to 0 to disable and keep exact equal-L*.
    """
    if n < 1:
        raise ValueError("n must be >= 1")
    if n > n_candidates:
        # Without this guard, farthest-point sampling would silently run out
        # of distinct candidates and start repeating indices once
        # ``len(selected) > n_candidates``, returning a palette with
        # duplicate colours instead of failing or degrading visibly.
        raise ValueError(
            f"n={n} exceeds n_candidates={n_candidates}; pass a larger "
            "n_candidates (or request fewer colours) -- qualitative palettes "
            "are meant for a handful of categories, not hundreds"
        )

    hues = (hue_start + np.linspace(0.0, 360.0, n_candidates, endpoint=False)) % 360.0
    chromas = np.array([min(chroma, _max_chroma(lightness, h)) for h in hues])
    cand_lch = np.stack([np.full_like(hues, lightness), chromas, hues], axis=-1)
    cand_srgb = np.clip(cv.lch_to_srgb(cand_lch), 0.0, 1.0)

    active_cvd = cvd_types if cvd_safe else ()
    labs = _cvd_labs(cand_srgb, active_cvd)  # list of (n_candidates, 3)

    # Precompute pairwise worst-case distance matrix between candidates.
    m = len(cand_srgb)
    dmat = np.full((m, m), np.inf)
    for lab in labs:
        # pairwise ΔE00 for this vision condition
        d = delta_e2000(lab[:, None, :], lab[None, :, :])
        dmat = np.minimum(dmat, d)

    # Farthest-point sampling seeded at hue_start (index 0).
    selected = [0]
    mindist = dmat[0].copy()
    while len(selected) < n:
        mindist[selected] = -np.inf
        nxt = int(np.argmax(mindist))
        selected.append(nxt)
        mindist = np.minimum(mindist, dmat[nxt])

    idx = np.array(selected)
    # Order the final set by hue for a pleasant, stable ordering.
    order = np.argsort(cand_lch[idx, 2])
    idx = idx[order]

    lch = cand_lch[idx].copy()
    if lightness_jitter and n > 1:
        # Spread L* over a small linear ramp (every colour gets a distinct
        # value) so greyscale/achromatic rendering keeps a luminance cue,
        # without visibly unbalancing the palette's perceived brightness.
        # A simple +/- alternation would repeat values once n > 2 and give
        # zero separation between some pairs, so we use linspace instead.
        ramp = np.linspace(-1.0, 1.0, n) * (lightness_jitter / 2.0)
        jittered_L = np.clip(lch[:, 0] + ramp, 1.0, 99.0)
        jittered_C = np.array(
            [
                min(c, _max_chroma(new_l, h))
                for new_l, c, h in zip(jittered_L, lch[:, 1], lch[:, 2], strict=False)
            ]
        )
        lch[:, 0] = jittered_L
        lch[:, 1] = jittered_C

    srgb = np.clip(cv.lch_to_srgb(lch), 0.0, 1.0)
    pal = Palette(
        hex=list(cv.srgb_to_hex(srgb)),
        srgb=srgb,
        lch=lch,
        kind="qualitative",
        meta={
            "lightness": lightness,
            "chroma": chroma,
            "hue_start": hue_start,
            "cvd_safe": cvd_safe,
            "cvd_types": tuple(active_cvd),
            "lightness_jitter": lightness_jitter,
            "min_delta_e": _min_pairwise_worstcase(srgb, active_cvd) if n > 1 else None,
        },
    )
    return pal


# --------------------------------------------------------------------------
# Named, pre-verified qualitative presets
# --------------------------------------------------------------------------
# The preset data itself lives in ``mudplot.capabilities`` (plain dict, no
# numpy) so the dependency-free pure core can describe available presets
# without importing this (numpy-dependent) module -- see PALETTE_PRESETS
# there for the actual lightness/chroma/hue_start/lightness_jitter values
# and each preset's verified-safe category count.
def preset_qualitative(name: str, n: int, **overrides) -> Palette:
    """A named, pre-verified qualitative palette (see ``PALETTE_PRESETS``).

    ``overrides`` may pass through any other ``qualitative()`` keyword (e.g.
    ``cvd_safe=False``); the preset's own lightness/chroma/hue_start/
    lightness_jitter take precedence unless also present in ``overrides``.
    """
    if name not in PALETTE_PRESETS:
        raise ValueError(
            f"unknown palette preset {name!r}; choose from {sorted(PALETTE_PRESETS)}"
        )
    params = {**PALETTE_PRESETS[name]["params"], **overrides}
    return qualitative(n, **params)


# --------------------------------------------------------------------------
# sequential
# --------------------------------------------------------------------------
def sequential(
    n: int,
    *,
    hue: float = 250.0,
    lightness=(95.0, 25.0),
    chroma=(15.0, 70.0),
    reverse: bool = False,
) -> Palette:
    """Perceptually-uniform single-hue sequential ramp.

    Lightness varies monotonically (light -> dark by default) for an
    unambiguous ordering; chroma ramps alongside. Chroma is clipped to the
    sRGB gamut at each step.
    """
    if n < 1:
        raise ValueError("n must be >= 1")
    t = np.linspace(0.0, 1.0, n)
    L = lightness[0] + t * (lightness[1] - lightness[0])
    C_req = chroma[0] + t * (chroma[1] - chroma[0])
    C = np.array([min(c, _max_chroma(l, hue)) for l, c in zip(L, C_req, strict=False)])
    lch = np.stack([L, C, np.full(n, hue)], axis=-1)
    srgb = np.clip(cv.lch_to_srgb(lch), 0.0, 1.0)
    if reverse:
        srgb = srgb[::-1]
        lch = lch[::-1]
    return Palette(
        hex=list(cv.srgb_to_hex(srgb)) if n > 1 else [cv.srgb_to_hex(srgb[0])],
        srgb=srgb,
        lch=lch,
        kind="sequential",
        meta={"hue": hue, "lightness": lightness, "chroma": chroma},
    )


# --------------------------------------------------------------------------
# diverging
# --------------------------------------------------------------------------
def diverging(
    n: int,
    *,
    hue_low: float = 255.0,
    hue_high: float = 12.0,
    lightness_mid: float = 95.0,
    lightness_end: float = 35.0,
    chroma: float = 65.0,
) -> Palette:
    """Two-hue diverging ramp with a light, low-chroma neutral centre."""
    if n < 2:
        raise ValueError("n must be >= 2 for a diverging palette")
    half = np.linspace(1.0, 0.0, (n + 1) // 2, endpoint=True)

    def arm(hue, ts):
        L = lightness_mid + ts * (lightness_end - lightness_mid)
        C_req = ts * chroma
        C = np.array(
            [min(c, _max_chroma(l, hue)) for l, c in zip(L, C_req, strict=False)]
        )
        return np.stack([L, C, np.full(len(ts), hue)], axis=-1)

    left = arm(hue_low, half)  # dark -> light
    right = arm(hue_high, half[::-1])  # light -> dark
    if n % 2 == 1:
        right = right[1:]  # avoid duplicating the neutral centre
    lch = np.concatenate([left, right], axis=0)
    srgb = np.clip(cv.lch_to_srgb(lch), 0.0, 1.0)
    return Palette(
        hex=list(cv.srgb_to_hex(srgb)),
        srgb=srgb,
        lch=lch,
        kind="diverging",
        meta={"hue_low": hue_low, "hue_high": hue_high, "chroma": chroma},
    )
