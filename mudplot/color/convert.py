"""Colour-space conversions implemented with NumPy only.

Pipeline (all vectorised, last axis = channels of length 3):

    sRGB (0..1)  <->  linear sRGB  <->  CIE XYZ  <->  CIELAB  <->  CIELCh

Reference white point: D65, CIE 1931 2-degree standard observer.

All functions accept array-likes of shape (..., 3) and return float64
arrays of the same shape.
"""

from __future__ import annotations

import numpy as np

__all__ = [
    "D65",
    "hex_to_srgb",
    "in_gamut",
    "lab_to_lch",
    "lab_to_srgb",
    "lab_to_xyz",
    "lch_to_lab",
    "lch_to_srgb",
    "linear_to_srgb",
    "linear_to_xyz",
    "srgb_to_hex",
    "srgb_to_lab",
    "srgb_to_lch",
    "srgb_to_linear",
    "xyz_to_lab",
    "xyz_to_linear",
]

# D65 white point, normalised so that Y = 1 (2-degree observer).
D65 = np.array([0.95047, 1.00000, 1.08883], dtype=np.float64)

# sRGB (linear) -> XYZ, D65. IEC 61966-2-1.
_RGB_TO_XYZ = np.array(
    [
        [0.4124564, 0.3575761, 0.1804375],
        [0.2126729, 0.7151522, 0.0721750],
        [0.0193339, 0.1191920, 0.9503041],
    ],
    dtype=np.float64,
)
_XYZ_TO_RGB = np.linalg.inv(_RGB_TO_XYZ)

# CIELAB constants (CIE standard).
_LAB_EPS = 216.0 / 24389.0  # (6/29)^3
_LAB_KAPPA = 24389.0 / 27.0  # (29/3)^3


def _as_array(x) -> np.ndarray:
    a = np.asarray(x, dtype=np.float64)
    if a.shape[-1] != 3:
        raise ValueError(f"expected last axis of size 3, got shape {a.shape}")
    return a


# --------------------------------------------------------------------------
# sRGB gamma companding
# --------------------------------------------------------------------------
def srgb_to_linear(srgb) -> np.ndarray:
    """Undo the sRGB transfer function (gamma decode)."""
    c = _as_array(srgb)
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def linear_to_srgb(linear) -> np.ndarray:
    """Apply the sRGB transfer function (gamma encode)."""
    c = _as_array(linear)
    # np.where evaluates both branches; guard the power against negatives
    # (out-of-gamut colours) to avoid NaN warnings, then restore the sign.
    safe = np.abs(c)
    encoded = np.sign(c) * (1.055 * np.power(safe, 1 / 2.4) - 0.055)
    return np.where(np.abs(c) <= 0.0031308, c * 12.92, encoded)


# --------------------------------------------------------------------------
# linear sRGB <-> XYZ
# --------------------------------------------------------------------------
def linear_to_xyz(linear) -> np.ndarray:
    c = _as_array(linear)
    return c @ _RGB_TO_XYZ.T


def xyz_to_linear(xyz) -> np.ndarray:
    c = _as_array(xyz)
    return c @ _XYZ_TO_RGB.T


# --------------------------------------------------------------------------
# XYZ <-> CIELAB
# --------------------------------------------------------------------------
def _lab_f(t: np.ndarray) -> np.ndarray:
    return np.where(t > _LAB_EPS, np.cbrt(t), (_LAB_KAPPA * t + 16.0) / 116.0)


def _lab_f_inv(t: np.ndarray) -> np.ndarray:
    t3 = t**3
    return np.where(t3 > _LAB_EPS, t3, (116.0 * t - 16.0) / _LAB_KAPPA)


def xyz_to_lab(xyz, white=D65) -> np.ndarray:
    c = _as_array(xyz)
    f = _lab_f(c / np.asarray(white, dtype=np.float64))
    fx, fy, fz = f[..., 0], f[..., 1], f[..., 2]
    L = 116.0 * fy - 16.0
    a = 500.0 * (fx - fy)
    b = 200.0 * (fy - fz)
    return np.stack([L, a, b], axis=-1)


def lab_to_xyz(lab, white=D65) -> np.ndarray:
    c = _as_array(lab)
    L, a, b = c[..., 0], c[..., 1], c[..., 2]
    fy = (L + 16.0) / 116.0
    fx = fy + a / 500.0
    fz = fy - b / 200.0
    xyz = np.stack([_lab_f_inv(fx), _lab_f_inv(fy), _lab_f_inv(fz)], axis=-1)
    return xyz * np.asarray(white, dtype=np.float64)


# --------------------------------------------------------------------------
# CIELAB <-> CIELCh  (L, C, H) with H in degrees [0, 360)
# --------------------------------------------------------------------------
def lab_to_lch(lab) -> np.ndarray:
    c = _as_array(lab)
    L, a, b = c[..., 0], c[..., 1], c[..., 2]
    C = np.hypot(a, b)
    H = np.degrees(np.arctan2(b, a)) % 360.0
    return np.stack([L, C, H], axis=-1)


def lch_to_lab(lch) -> np.ndarray:
    c = _as_array(lch)
    L, C, H = c[..., 0], c[..., 1], c[..., 2]
    h = np.radians(H)
    return np.stack([L, C * np.cos(h), C * np.sin(h)], axis=-1)


# --------------------------------------------------------------------------
# Convenience compositions
# --------------------------------------------------------------------------
def srgb_to_lab(srgb) -> np.ndarray:
    return xyz_to_lab(linear_to_xyz(srgb_to_linear(srgb)))


def lab_to_srgb(lab) -> np.ndarray:
    return linear_to_srgb(xyz_to_linear(lab_to_xyz(lab)))


def srgb_to_lch(srgb) -> np.ndarray:
    return lab_to_lch(srgb_to_lab(srgb))


def lch_to_srgb(lch) -> np.ndarray:
    return lab_to_srgb(lch_to_lab(lch))


# --------------------------------------------------------------------------
# hex helpers & gamut test
# --------------------------------------------------------------------------
def hex_to_srgb(value: str) -> np.ndarray:
    """'#RRGGBB' or 'RRGGBB' -> sRGB float array in [0, 1]."""
    s = value.lstrip("#")
    if len(s) == 3:
        s = "".join(ch * 2 for ch in s)
    if len(s) != 6:
        raise ValueError(f"invalid hex colour: {value!r}")
    r = int(s[0:2], 16)
    g = int(s[2:4], 16)
    b = int(s[4:6], 16)
    return np.array([r, g, b], dtype=np.float64) / 255.0


def srgb_to_hex(srgb, clip: bool = True) -> str | list[str]:
    """sRGB float array in [0, 1] -> '#RRGGBB'. Vectorised over leading axes."""
    c = _as_array(srgb)
    if clip:
        c = np.clip(c, 0.0, 1.0)
    ints = np.rint(c * 255.0).astype(int)
    flat = ints.reshape(-1, 3)
    hexes = [f"#{r:02X}{g:02X}{b:02X}" for r, g, b in flat]
    if ints.ndim == 1:
        return hexes[0]
    return hexes


def in_gamut(srgb, tol: float = 1e-4) -> np.ndarray:
    """Boolean mask (over leading axes) of colours inside the sRGB gamut."""
    c = _as_array(srgb)
    inside = np.all((c >= -tol) & (c <= 1.0 + tol), axis=-1)
    return inside
