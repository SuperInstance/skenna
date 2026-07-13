"""
NegativeSpaceNavigator — the main API.

The navigator charts hazards (the rocks) and computes the negative
space (where the rocks aren't). Navigation happens by avoidance.

You don't tell the navigator where to go. You tell it where not to go,
and the route emerges from the shape of the avoidance.
"""

from __future__ import annotations

from typing import List, Optional, Union

from skenna.hazard import Hazard, HazardType
from skenna.space import Space, Path, Point, BoundingBox
from skenna.planner import AvoidancePlanner
from skenna.cognitive import (
    CognitiveNavigator,
    ModelChart,
    Sounding,
    ChartThickness,
    CognitiveDimension,
    CognitiveRoute,
    ConsensusReport,
)


class NegativeSpaceNavigator:
    """
    Navigate by where the rocks aren't.

    Usage:
        >>> nav = NegativeSpaceNavigator()
        >>> nav.add_hazard(Hazard(location=(0, 0), radius=1.0, severity=1.0))
        >>> safe = nav.chart_safe_space()
        >>> path = nav.navigate(start=(-2, 0), goal=(2, 0))

    The navigator works in two phases:
    1. Chart hazards — mark the rocks. That's all you do.
    2. Navigate — the path emerges from the avoidance pattern.
    """

    def __init__(self, bounds: Optional[BoundingBox] = None):
        """
        Args:
            bounds: Optional bounding box for the charted territory.
                    If None, the space is unbounded (infinite safe space).
        """
        self.hazards: List[Hazard] = []
        self.safe_space: Optional[Space] = None
        self._bounds = bounds
        self._planner = AvoidancePlanner()
        self._cognitive: Optional[CognitiveNavigator] = None

    def add_hazard(self, hazard: Hazard) -> None:
        """
        Mark a rock. The safe space is everything else.

        Adding a hazard immediately invalidates the cached safe space
        chart. It will be recomputed on the next chart_safe_space() call.
        """
        self.hazards.append(hazard)
        self.safe_space = None  # Invalidate cache

    def hazard_register(self, hazard: Hazard) -> None:
        """
        Register a known hazard — same as add_hazard but with the
        navigator's vocabulary: you REGISTER hazards (like a ship's
        hazard register) rather than adding them.

        This is the cognitive-layer alias for add_hazard.
        """
        self.add_hazard(hazard)

    def remove_hazard(self, index: int) -> Hazard:
        """Remove a hazard by index. Returns the removed hazard."""
        removed = self.hazards.pop(index)
        self.safe_space = None
        return removed

    def clear_hazards(self) -> None:
        """Remove all hazards. The entire space becomes safe."""
        self.hazards.clear()
        self.safe_space = None

    def chart_safe_space(self) -> Space:
        """
        Map the negative space — where the rocks aren't.

        Computes the safe space by subtracting all hazard zones
        from the charted territory.

        Returns:
            A Space describing the navigable (safe) region.
        """
        excluded = []
        for h in self.hazards:
            if h.is_spatial:
                excluded.append((h.coordinates, h.radius))

        self.safe_space = Space(
            bounds=self._bounds,
            excluded_regions=excluded,
        )
        return self.safe_space

    def navigate(
        self,
        start: Point,
        goal: Point,
        safety_margin: Optional[float] = None,
    ) -> Path:
        """
        Plan a route from start to goal that avoids all hazards.

        Does NOT plan toward the goal — plans AWAY from hazards.
        The goal emerges from the avoidance pattern.

        The path is computed using a potential field method:
        - Hazards create repulsion (dominant near rocks)
        - The goal creates weak attraction (only matters far from rocks)
        - The route follows the gradient of minimum total potential

        Args:
            start: Starting point.
            goal: Goal point.
            safety_margin: Override the planner's safety margin.

        Returns:
            A Path through safe space.
        """
        if safety_margin is not None:
            self._planner.safety_margin = safety_margin

        # Ensure safe space is charted
        if self.safe_space is None:
            self.chart_safe_space()

        return self._planner.plan(
            start=start,
            goal=goal,
            hazards=self.hazards,
            bounds=self._bounds,
        )

    def is_safe(self, point: Point, clearance: float = 0.0) -> bool:
        """
        Check if a point is in safe space.

        A point is safe if it's outside all hazard zones, with
        optional clearance margin.
        """
        for h in self.hazards:
            if h.is_spatial and h.clearance_at(point) < clearance:
                return False
        return True

    def clearance_at(self, point: Point) -> float:
        """
        Minimum clearance from all hazards at a point.
        Positive = safe, negative = inside a hazard.
        """
        if not self.hazards:
            return float("inf")
        spatial = [h for h in self.hazards if h.is_spatial]
        if not spatial:
            return float("inf")
        return min(h.clearance_at(point) for h in spatial)

    def safety_score(self, point: Point) -> float:
        """
        Overall safety score at a point, in [0.0, 1.0].
        1.0 = perfectly safe (far from all hazards).
        0.0 = inside a hazard.
        """
        min_clr = self.clearance_at(point)
        if min_clr < 0:
            return 0.0
        # Logistic curve: fast rise near clearance=0, plateau at ~3.0
        import math
        return 1.0 / (1.0 + math.exp(-min_clr * 2))

    @property
    def bounds(self) -> Optional[BoundingBox]:
        return self._bounds

    def set_bounds(self, bounds: BoundingBox) -> None:
        """Set or update the charted territory bounds."""
        self._bounds = bounds
        self.safe_space = None

    def summary(self) -> str:
        """Human-readable summary of the navigator state."""
        spatial = [h for h in self.hazards if h.is_spatial]
        semantic = [h for h in self.hazards if not h.is_spatial]
        lines = [
            "skénna Navigator Status",
            "=" * 40,
            f"  Hazards (spatial):  {len(spatial)}",
            f"  Hazards (semantic): {len(semantic)}",
            f"  Safe space charted: {self.safe_space is not None}",
            f"  Bounded:            {self._bounds is not None}",
        ]
        if self.safe_space is not None:
            lines.append(f"  Coverage:           {self.safe_space.coverage_fraction():.1%}")
        return "\n".join(lines)

    def __repr__(self) -> str:
        return f"NegativeSpaceNavigator(hazards={len(self.hazards)})"

    # ------------------------------------------------------------------
    # Cognitive navigation layer
    # ------------------------------------------------------------------

    def explore(
        self,
        query: str,
        model: str,
        handler=None,
    ) -> Sounding:
        """
        Send a query to a thin-chart model and capture what it discovers
        in η space.

        This is the first phase of the Socratic protocol: the thin model
        explores the negative space that the thick model cannot see.

        Args:
            query: The question to explore.
            model: Name of the model to query.
            handler: Optional callable (query) -> response.

        Returns:
            A Sounding record of what was found in η.
        """
        self._ensure_cognitive()
        return self._cognitive.explore(query, model, handler)

    def route(
        self,
        query: str,
        models,
        handlers=None,
    ) -> CognitiveRoute:
        """
        Execute the Socratic protocol: thin model discovers, thick model synthesizes.

        Cast the thin-chart model first (discovery), then the thick-chart
        model (synthesis). The elder's η is the mini's γ.

        Args:
            query: The question to explore and then synthesize.
            models: List of model names, thinnest to thickest.
            handlers: Optional per-model handler overrides.

        Returns:
            A CognitiveRoute describing the full Socratic journey.
        """
        self._ensure_cognitive()
        return self._cognitive.route(query, models, handlers)

    def sound_depth(self, model: str, dimension: CognitiveDimension) -> float:
        """
        Estimate η depth for a model in a cognitive dimension.

        High η depth = lots of potential for discovery (thin chart).
        Low η depth = well-charted territory (thick chart).
        """
        self._ensure_cognitive()
        return self._cognitive.sound_depth(model, dimension)

    def consensus(self, models, query: str, handlers=None) -> ConsensusReport:
        """
        Run N models, find where their γ overlaps (consensus) and
        where it diverges (discovery).

        Where charts agree = safe passage on all charts.
        Where charts disagree = the most valuable information.
        """
        self._ensure_cognitive()
        return self._cognitive.consensus(models, query, handlers)

    def register_model(self, chart: ModelChart, handler=None) -> None:
        """
        Register a model with its cognitive chart for navigation.

        Args:
            chart: The model's cognitive chart (γ allocation).
            handler: Optional callable (query) -> response.
        """
        self._ensure_cognitive()
        self._cognitive.register_model(chart, handler)

    def _ensure_cognitive(self) -> None:
        """Lazy-initialize the cognitive navigator."""
        if self._cognitive is None:
            self._cognitive = CognitiveNavigator()
