"""A declared 8 Hz sine: density and derived Hz, never raw signal coordinates."""

import math

import mudplot as mp

plot = mp.plot({"signal": [math.sin(2 * math.pi * 8 * j / 64) for j in range(256)]})
plot.theme("publication").spectrum("signal", fs=64, nfft=64, window="hann")
plot.labels(title="Welch power density: 8 Hz signal")
