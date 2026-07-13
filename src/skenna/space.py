"""
Space and Path — the water and the route.

Space represents a region of navigable territory.
Path is a route through space — specifically, a route that emerges
from avoidance rather than goal-seeking.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Tuple, List, Optional, Iterator
import math

Point = Tuple[float, ...]
"""A point in n-dimensional space."""


@dataclass
class BoundingBox:
    """
    An axis-aligned bounding box in n-dimensional space.
    Defines the extents of charted territory.
    """
    mins: Tuple[float, ...]
    maxs: Tuple[float, ...]

    @property
    def dimensions(self) -> int:
        return len(self.mins)

    @property
    def center(self) -> Point:
        return tuple((a + b) / 2.0 for a, b in zip(self.mins, self.maxs))

    @property
    def extents(self) -> Tuple[float, ...]:
        return tuple(b - a for a, b in zip(self.mins, self.maxs))

    @property
    def area(self) -> float:
        """Hypervolume of the bounding box."""
        return math.prod(self.extents)

    def contains(self, point: Point) -> bool:
        """Whether a point is inside this bounding box."""
        return all(
            m <= p <= x for m, p, x in zip(self.mins, point, self.maxs)
        )

    def expand(self, margin: float) -> "BoundingBox":
        """Return a bounding box expanded by margin on all sides."""
        return BoundingBox(
            tuple(m - margin for m in self.mins),
            tuple(x + margin for x in self.maxs),
        )

    def sample(self, resolution: float = 0.5) -> List[Point]:
        """
        Generate a grid of sample points within this bounding box
        at the given resolution.
        """
        axes = []
        for m, x in zip(self.mins, self.maxs):
            n = max(2, int((x - m) / resolution) + 1)
            axes.append([m + i * (x - m) / (n - 1) for i in range(n)])

        # Cartesian product
        result = [()]
        for axis in axes:
            result = [r + (v,) for r in result for v in axis]
        return result


@dataclass
class Space:
    """
    The navigable space — where the rocks aren't.

    Defined by a bounding box (the charted territory) and a set
    of excluded regions (the hazards). The safe space is the
    territory minus the exclusions — the negative space.

    Attributes:
        bounds: The bounding box of charted territory.
        excluded_regions: List of (center, radius) tuples marking hazards.
        resolution: Sampling resolution for safe-point queries.
    """
    bounds: Optional[BoundingBox] = None
    excluded_regions: List[Tuple[Point, float]] = field(default_factory=list)
    resolution: float = 0.5

    @property
    def is_unbounded(self) -> bool:
        """Whether this space has no defined bounds."""
        return self.bounds is None

    @property
    def total_excluded_area(self) -> float:
        """Total area of excluded regions."""
        return sum(math.pi * r ** 2 for _, r in self.excluded_regions)

    @property
    def safe_area(self) -> float:
        """Approximate safe area (total minus excluded)."""
        if self.bounds is None:
            return float("inf")
        return self.bounds.area - self.total_excluded_area

    def is_safe(self, point: Point, clearance: float = 0.0) -> bool:
        """
        Check if a point is in safe space.

        A point is safe if it's outside all excluded regions
        (with the specified clearance margin).
        """
        for center, radius in self.excluded_regions:
            d = math.sqrt(sum((a - b) ** 2 for a, b in zip(center, point)))
            if d < radius + clearance:
                return False
        return True

    def safe_points(self) -> List[Point]:
        """
        Enumerate safe sample points within the bounding box.
        Returns only points that are not inside any excluded region.
        """
        if self.bounds is None:
            raise ValueError("Cannot enumerate safe points in unbounded space")
        all_points = self.bounds.sample(self.resolution)
        return [p for p in all_points if self.is_safe(p)]

    def coverage_fraction(self) -> float:
        """Fraction of the bounded space that is safe (0.0 to 1.0)."""
        if self.bounds is None:
            return 1.0
        all_points = self.bounds.sample(self.resolution)
        if not all_points:
            return 1.0
        safe = sum(1 for p in all_points if self.is_safe(p))
        return safe / len(all_points)


@dataclass
class Path:
    """
    A route through safe space.

    The path emerges from avoidance: each waypoint is placed where
    the hazards aren't, and the route between them traces the
    negative space.

    Attributes:
        waypoints: Ordered list of points along the route.
        min_clearance: Minimum distance to any hazard along the path.
        total_distance: Total path length.
        safety_score: Overall safety metric (0.0 to 1.0).
    """
    waypoints: List[Point] = field(default_factory=list)
    min_clearance: float = float("inf")
    total_distance: float = 0.0
    safety_score: float = 1.0
    metadata: dict = field(default_factory=dict)

    def __len__(self) -> int:
        return len(self.waypoints)

    def __iter__(self) -> Iterator[Point]:
        return iter(self.waypoints)

    @property
    def start(self) -> Optional[Point]:
        return self.waypoints[0] if self.waypoints else None

    @property
    def end(self) -> Optional[Point]:
        return self.waypoints[-1] if self.waypoints else None

    def segment_lengths(self) -> List[float]:
        """Length of each segment between consecutive waypoints."""
        lengths = []
        for i in range(len(self.waypoints) - 1):
            a, b = self.waypoints[i], self.waypoints[i + 1]
            d = math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))
            lengths.append(d)
        return lengths

    def resample(self, interval: float = 0.5) -> "Path":
        """
        Return a new path with waypoints interpolated at fixed intervals.
        Useful for dense clearance checking.
        """
        if len(self.waypoints) < 2:
            return Path(
                waypoints=list(self.waypoints),
                min_clearance=self.min_clearance,
                total_distance=self.total_distance,
                safety_score=self.safety_score,
                metadata=dict(self.metadata),
            )

        dense: List[Point] = [self.waypoints[0]]
        for i in range(len(self.waypoints) - 1):
            a, b = self.waypoints[i], self.waypoints[i + 1]
            seg_len = math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))
            n_steps = max(1, int(seg_len / interval))
            for s in range(1, n_steps + 1):
                t = s / n_steps
                dense.append(tuple(a_i + t * (b_i - a_i) for a_i, b_i in zip(a, b)))

        return Path(
            waypoints=dense,
            min_clearance=self.min_clearance,
            total_distance=self.total_distance,
            safety_score=self.safety_score,
            metadata=dict(self.metadata),
        )

    def __repr__(self) -> str:
        return (
            f"Path(waypoints={len(self.waypoints)}, "
            f"distance={self.total_distance:.2f}, "
            f"clearance={self.min_clearance:.2f}, "
            f"safety={self.safety_score:.3f})"
        )
