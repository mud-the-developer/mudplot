"""Shared pytest fixtures."""

import pytest


@pytest.fixture(autouse=True)
def _close_figures():
    """Close all matplotlib figures after each test to avoid the pyplot
    'too many open figures' warning across the whole suite."""
    yield
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        return
    plt.close("all")
