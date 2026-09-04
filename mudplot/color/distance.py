"""Perceptual colour-difference metrics (CIE76, CIEDE2000)."""

from __future__ import annotations

import numpy as np

from .convert import _as_array

__all__ = ["delta_e76", "delta_e2000"]


def delta_e76(lab1, lab2) -> np.ndarray:
    """CIE76 colour difference: plain Euclidean distance in CIELAB."""
    a = _as_array(lab1)
    b = _as_array(lab2)
    return np.sqrt(np.sum((a - b) ** 2, axis=-1))


def delta_e2000(lab1, lab2, kL: float = 1.0, kC: float = 1.0, kH: float = 1.0):
    """CIEDE2000 colour difference (Sharma et al. 2005 formulation).

    Accepts broadcastable arrays of shape (..., 3) in CIELAB and returns
    the ΔE00 values with the broadcasted leading shape.
    """
    lab1 = _as_array(lab1)
    lab2 = _as_array(lab2)

    L1, a1, b1 = lab1[..., 0], lab1[..., 1], lab1[..., 2]
    L2, a2, b2 = lab2[..., 0], lab2[..., 1], lab2[..., 2]

    C1 = np.hypot(a1, b1)
    C2 = np.hypot(a2, b2)
    Cbar = 0.5 * (C1 + C2)

    C7 = Cbar**7
    G = 0.5 * (1.0 - np.sqrt(C7 / (C7 + 25.0**7)))

    a1p = (1.0 + G) * a1
    a2p = (1.0 + G) * a2
    C1p = np.hypot(a1p, b1)
    C2p = np.hypot(a2p, b2)

    h1p = np.degrees(np.arctan2(b1, a1p)) % 360.0
    h2p = np.degrees(np.arctan2(b2, a2p)) % 360.0

    dLp = L2 - L1
    dCp = C2p - C1p

    dhp = h2p - h1p
    dhp = np.where(dhp > 180.0, dhp - 360.0, dhp)
    dhp = np.where(dhp < -180.0, dhp + 360.0, dhp)
    # when either chroma is zero, hue difference is undefined -> 0
    zero_chroma = (C1p * C2p) == 0.0
    dhp = np.where(zero_chroma, 0.0, dhp)
    dHp = 2.0 * np.sqrt(C1p * C2p) * np.sin(np.radians(dhp) / 2.0)

    Lbarp = 0.5 * (L1 + L2)
    Cbarp = 0.5 * (C1p + C2p)

    hsum = h1p + h2p
    habs = np.abs(h1p - h2p)
    hbarp = np.where(
        zero_chroma,
        hsum,
        np.where(
            habs <= 180.0,
            0.5 * hsum,
            np.where(hsum < 360.0, 0.5 * (hsum + 360.0), 0.5 * (hsum - 360.0)),
        ),
    )

    T = (
        1.0
        - 0.17 * np.cos(np.radians(hbarp - 30.0))
        + 0.24 * np.cos(np.radians(2.0 * hbarp))
        + 0.32 * np.cos(np.radians(3.0 * hbarp + 6.0))
        - 0.20 * np.cos(np.radians(4.0 * hbarp - 63.0))
    )

    dtheta = 30.0 * np.exp(-(((hbarp - 275.0) / 25.0) ** 2))
    Cbarp7 = Cbarp**7
    Rc = 2.0 * np.sqrt(Cbarp7 / (Cbarp7 + 25.0**7))
    Rt = -np.sin(np.radians(2.0 * dtheta)) * Rc

    Lbarp_m = (Lbarp - 50.0) ** 2
    Sl = 1.0 + (0.015 * Lbarp_m) / np.sqrt(20.0 + Lbarp_m)
    Sc = 1.0 + 0.045 * Cbarp
    Sh = 1.0 + 0.015 * Cbarp * T

    term_L = dLp / (kL * Sl)
    term_C = dCp / (kC * Sc)
    term_H = dHp / (kH * Sh)

    return np.sqrt(term_L**2 + term_C**2 + term_H**2 + Rt * term_C * term_H)
