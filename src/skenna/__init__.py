"""
skénna — negative-space navigation for AI systems.

Navigate by where the rocks aren't, not where they are.

The core insight: safe space is defined by boundary (what's blocked),
not by instruction (what to do). The model navigates freely within the fence.

Example:
    >>> from skenna import NegativeSpaceNavigator, Hazard
    >>> nav = NegativeSpaceNavigator()
    >>> nav.add_hazard(Hazard(location=(0.0, 0.0), radius=1.0, severity=1.0))
    >>> safe = nav.chart_safe_space()
    >>> path = nav.navigate(start=(-2.0, 0.0), goal=(2.0, 0.0))
    >>> len(path.waypoints) > 0
    True
"""

from skenna.hazard import Hazard, HazardType
from skenna.space import Space, Path, Point
from skenna.navigator import NegativeSpaceNavigator
from skenna.planner import AvoidancePlanner
from skenna.ai_integration import AIHarness, FluxBytecodeCompiler, ConservationEnforcer

__version__ = "0.1.0"
__all__ = [
    "NegativeSpaceNavigator",
    "Hazard",
    "HazardType",
    "Space",
    "Path",
    "Point",
    "AvoidancePlanner",
    "AIHarness",
    "FluxBytecodeCompiler",
    "ConservationEnforcer",
]
