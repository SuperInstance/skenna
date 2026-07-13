"""
Hazard definitions — the rocks.

A Hazard is anything that makes a region of space unsafe.
The navigator doesn't plan around hazards — it plans away from them.
The distinction matters: avoidance is the primary act, not an obstacle
to be worked around on the way to a goal.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Tuple, Union


class HazardType(Enum):
    """Classification of hazards by domain."""
    REEF = "reef"
    SHOAL = "shoal"
    WRECK = "wreck"
    CURRENT = "current"
    CONTENT_VIOLATION = "content_violation"
    SECURITY = "security"
    RELIABILITY = "reliability"
    PERFORMANCE = "performance"
    CUSTOM = "custom"


@dataclass
class Hazard:
    """
    A hazard — a rock in the water, a forbidden output, a code smell.

    The hazard occupies space defined by its location and radius.
    Severity scales the repulsion: a severity-1.0 hazard is a hard
    boundary (never enter), while lower severity creates gradients
    of increasing danger (strongly avoid).

    Attributes:
        location: The center of the hazard. Tuple of floats for spatial
                  hazards, or a string label for semantic/conceptual hazards.
        radius: The spatial extent of the hazard. How far the danger
                reaches from its center.
        severity: Danger level from 0.0 (mild) to 1.0 (lethal).
                  Controls repulsion strength in the planner.
        hazard_type: Classification of the hazard domain.
        label: Optional human-readable name for the hazard.
        metadata: Optional dict of additional properties.
    """
    location: Union[Tuple[float, ...], str]
    radius: float = 1.0
    severity: float = 1.0
    hazard_type: HazardType = HazardType.CUSTOM
    label: str = ""
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        if self.severity < 0.0 or self.severity > 1.0:
            raise ValueError(f"Severity must be in [0.0, 1.0], got {self.severity}")
        if self.radius < 0.0:
            raise ValueError(f"Radius must be non-negative, got {self.radius}")

    @property
    def is_spatial(self) -> bool:
        """Whether this hazard has a spatial (numeric) location."""
        return isinstance(self.location, (tuple, list))

    @property
    def coordinates(self) -> Tuple[float, ...]:
        """Spatial coordinates. Raises if hazard is non-spatial."""
        if not self.is_spatial:
            raise TypeError(f"Hazard '{self.label}' is non-spatial: {self.location}")
        return tuple(self.location)

    @property
    def dimensions(self) -> int:
        """Number of spatial dimensions."""
        return len(self.coordinates) if self.is_spatial else 0

    def distance_to(self, point: Tuple[float, ...]) -> float:
        """
        Euclidean distance from the hazard center to a point.

        For non-spatial hazards, returns 0.0 if the point matches
        the hazard label, otherwise infinity.
        """
        if not self.is_spatial:
            if isinstance(point, str) and point == self.location:
                return 0.0
            return float("inf")

        p = tuple(point)
        if len(p) != self.dimensions:
            raise ValueError(
                f"Point has {len(p)} dimensions, hazard has {self.dimensions}"
            )
        return sum(
            (a - b) ** 2 for a, b in zip(self.coordinates, p)
        ) ** 0.5

    def clearance_at(self, point: Tuple[float, ...]) -> float:
        """
        How far a point is from the hazard boundary.
        Positive = outside the hazard (safe).
        Negative = inside the hazard (dangerous).
        """
        return self.distance_to(point) - self.radius

    def contains(self, point: Tuple[float, ...]) -> bool:
        """Whether a point is inside the hazard zone."""
        return self.clearance_at(point) < 0

    def repulsion_at(self, point: Tuple[float, ...]) -> float:
        """
        Repulsion force at a given point, in [0, 1].
        Zero far from the hazard, one at its center.
        Falls off with distance, scaled by severity.
        """
        d = self.distance_to(point)
        if d > self.radius * 3:  # beyond influence
            return 0.0
        # Inverse falloff within influence radius
        influence = self.radius * 3
        raw = max(0.0, 1.0 - (d / influence))
        return raw * self.severity

    def __repr__(self) -> str:
        loc = self.location if self.is_spatial else f"'{self.location}'"
        return (
            f"Hazard(loc={loc}, r={self.radius}, sev={self.severity}, "
            f"type={self.hazard_type.value})"
        )
