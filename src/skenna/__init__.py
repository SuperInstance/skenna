"""
skénna — negative-space navigation for AI systems.

Navigate by where the rocks aren't, not where they are.

The core insight: safe space is defined by boundary (what's blocked),
not by instruction (what to do). The model navigates freely within the fence.

Two layers of navigation:

1. **Spatial navigation** — chart physical hazards, plan safe routes.
   NegativeSpaceNavigator + Hazard + AvoidancePlanner.

2. **Cognitive navigation** — navigate the γ/η space between models.
   The Socratic protocol: thin-chart models explore η (discovery),
   thick-chart models synthesize γ (architecture).

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
from skenna.space import Space, Path, Point, BoundingBox
from skenna.navigator import NegativeSpaceNavigator
from skenna.planner import AvoidancePlanner
from skenna.ai_integration import AIHarness, FluxBytecodeCompiler, ConservationEnforcer
from skenna.cognitive import (
    CognitiveNavigator,
    CognitiveDimension,
    ModelChart,
    ChartThickness,
    Sounding,
    CognitiveRoute,
    ConsensusReport,
)

__version__ = "0.2.0"
__all__ = [
    # Spatial navigation
    "NegativeSpaceNavigator",
    "Hazard",
    "HazardType",
    "Space",
    "Path",
    "Point",
    "BoundingBox",
    "AvoidancePlanner",
    # AI integration
    "AIHarness",
    "FluxBytecodeCompiler",
    "ConservationEnforcer",
    # Cognitive navigation
    "CognitiveNavigator",
    "CognitiveDimension",
    "ModelChart",
    "ChartThickness",
    "Sounding",
    "CognitiveRoute",
    "ConsensusReport",
]
