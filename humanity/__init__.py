"""Humanity.sh: a GUI-independent, reproducible society simulation."""

__version__ = "0.3.0"

from .engine.simulation import Simulation

__all__ = ["Simulation", "__version__"]
