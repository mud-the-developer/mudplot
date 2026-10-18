"""Colour engine: conversions, colour-difference, CVD simulation, palettes."""

try:
    from . import convert, cvd, distance, palette  # noqa: F401
    from .palette import Palette, diverging, qualitative, sequential  # noqa: F401
except ModuleNotFoundError as error:
    if error.name != "numpy":
        raise
    raise ImportError(
        "colour operations require NumPy; install 'mudplot[color]'"
    ) from error
