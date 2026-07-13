"""
Avoidance-first path planner.

The fundamental difference: this planner does NOT plan toward the goal.
It plans AWAY from hazards. The goal emerges from the avoidance pattern.

This works by constructing a potential field:
- Each hazard creates a repulsion field (push away)
- The goal creates a weak attraction field (pull, but gently)
- The path follows the gradient of minimum total potential

The repulsion dominates near hazards. The attraction only matters
in the far field, where there are no rocks. This mirrors the old
sailor's wisdom: he doesn't sail toward the harbor — he stays where
the rocks aren't, and the harbor is where he ends up.
"""

from __future__ import annotations

import math
import random
from typing import List, Tuple, Optional

from skenna.hazard import Hazard
from skenna.space import Space, Path, Point, BoundingBox


class AvoidancePlanner:
    """
    Plans paths by avoidance, not attraction.

    The planner uses a potential field approach where hazards generate
    repulsion fields. The path is found by following the gradient of
    minimum repulsion from start to goal. Near hazards, the path is
    dominated by avoidance. Far from hazards, the path drifts toward
    the goal — but only because there's nothing pushing it away.
    """

    def __init__(
        self,
        step_size: float = 0.3,
        max_steps: int = 2000,
        goal_bias: float = 0.15,
        safety_margin: float = 0.5,
        field_influence_scale: float = 3.0,
        seed: Optional[int] = None,
    ):
        """
        Args:
            step_size: Distance per step in the gradient walk.
            max_steps: Maximum gradient steps before giving up.
            goal_bias: Probability of stepping toward goal vs. pure avoidance.
                       Low = strong avoidance behavior, high = more goal-directed.
            safety_margin: Minimum clearance from hazard boundaries.
            field_influence_scale: How far hazard influence reaches (in radius multiples).
            seed: Random seed for reproducible planning.
        """
        self.step_size = step_size
        self.max_steps = max_steps
        self.goal_bias = goal_bias
        self.safety_margin = safety_margin
        self.field_influence_scale = field_influence_scale
        self._rng = random.Random(seed)

    def _repulsion_field(
        self, point: Point, hazards: List[Hazard]
    ) -> Tuple[float, Tuple[float, ...]]:
        """
        Compute total repulsion at a point.
        Returns (magnitude, gradient_direction).
        """
        total_mag = 0.0
        gradient = [0.0] * len(point)

        for h in hazards:
            if not h.is_spatial:
                continue
            d = h.distance_to(point)
            influence = h.radius * self.field_influence_scale

            if d > influence or d < 1e-9:
                if d <= 1e-9:
                    total_mag += h.severity * 1000  # inside hazard center
                continue

            # Repulsion strength: falls off with distance
            ratio = (influence - d) / influence
            strength = h.severity * ratio ** 2
            total_mag += strength

            # Gradient direction: away from hazard center
            diff = tuple(p - c for p, c in zip(point, h.coordinates))
            for i, component in enumerate(diff):
                gradient[i] += (component / d) * strength

        grad_mag = math.sqrt(sum(g ** 2 for g in gradient))
        if grad_mag > 1e-9:
            direction = tuple(g / grad_mag for g in gradient)
        else:
            direction = tuple(0.0 for _ in point)

        return total_mag, direction

    def _attraction_direction(
        self, point: Point, goal: Point
    ) -> Tuple[float, Tuple[float, ...]]:
        """
        Weak attraction toward the goal.
        Returns (magnitude, direction).
        """
        diff = tuple(g - p for g, p in zip(goal, point))
        dist = math.sqrt(sum(d ** 2 for d in diff))
        if dist < 1e-9:
            return 0.0, tuple(0.0 for _ in point)
        direction = tuple(d / dist for d in diff)
        # Gentle attraction: inversely scaled
        magnitude = min(1.0, 5.0 / max(dist, 1.0))
        return magnitude, direction

    def _combined_step(
        self,
        current: Point,
        goal: Point,
        hazards: List[Hazard],
    ) -> Point:
        """
        Compute next step by combining repulsion (dominant) and attraction (weak).
        """
        rep_mag, rep_dir = self._repulsion_field(current, hazards)
        att_mag, att_dir = self._attraction_direction(current, goal)

        # Repulsion always wins when near hazards — the sailor's wisdom
        if rep_mag > 0.01:
            # Blend: repulsion scaled up, attraction scaled down
            blend = 1.0 / (1.0 + rep_mag * 5)  # repulsion dominance
            step = tuple(
                self.step_size * (
                    rep_dir[i] * (1.0 - blend * self.goal_bias) +
                    att_dir[i] * blend * self.goal_bias
                )
                for i in range(len(current))
            )
        else:
            # Far from hazards — drift toward goal
            step = tuple(
                self.step_size * att_dir[i] for i in range(len(current))
            )

        return tuple(c + s for c, s in zip(current, step))

    def _min_clearance(self, point: Point, hazards: List[Hazard]) -> float:
        """Minimum clearance from all hazards."""
        if not hazards:
            return float("inf")
        clearances = []
        for h in hazards:
            if h.is_spatial:
                clearances.append(h.clearance_at(point))
        return min(clearances) if clearances else float("inf")

    def _path_clearance(self, waypoints: List[Point], hazards: List[Hazard]) -> float:
        """Minimum clearance along the entire path."""
        min_c = float("inf")
        dense = []
        for i in range(len(waypoints) - 1):
            a, b = waypoints[i], waypoints[i + 1]
            seg_len = math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))
            n = max(1, int(seg_len / 0.1))
            for s in range(n + 1):
                t = s / n
                dense.append(tuple(a_i + t * (b_i - a_i) for a_i, b_i in zip(a, b)))
        for p in dense:
            c = self._min_clearance(p, hazards)
            if c < min_c:
                min_c = c
        return min_c

    def _path_distance(self, waypoints: List[Point]) -> float:
        total = 0.0
        for i in range(len(waypoints) - 1):
            a, b = waypoints[i], waypoints[i + 1]
            total += math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))
        return total

    def _smooth_path(self, waypoints: List[Point], hazards: List[Hazard]) -> List[Point]:
        """
        Smooth the path by shortcutting between non-adjacent waypoints
        if a direct segment clears all hazards.
        """
        if len(waypoints) <= 2:
            return waypoints

        smoothed = [waypoints[0]]
        i = 0
        while i < len(waypoints) - 1:
            # Try to skip ahead as far as possible
            j = len(waypoints) - 1
            while j > i + 1:
                if self._segment_is_safe(waypoints[i], waypoints[j], hazards):
                    break
                j -= 1
            smoothed.append(waypoints[j])
            i = j

        return smoothed

    def _segment_is_safe(
        self, a: Point, b: Point, hazards: List[Hazard], clearance: float = 0.0
    ) -> bool:
        """Check if a straight segment between a and b clears all hazards."""
        seg_len = math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))
        n = max(2, int(seg_len / 0.05))
        for s in range(n + 1):
            t = s / n
            p = tuple(a_i + t * (b_i - a_i) for a_i, b_i in zip(a, b))
            for h in hazards:
                if h.is_spatial and h.clearance_at(p) < clearance:
                    return False
        return True

    def plan(
        self,
        start: Point,
        goal: Point,
        hazards: List[Hazard],
        bounds: Optional[BoundingBox] = None,
    ) -> Path:
        """
        Plan a path from start to goal using avoidance-first navigation.

        The path does NOT plan toward the goal — it plans AWAY from hazards.
        The goal emerges from the avoidance pattern.

        Args:
            start: Starting point.
            goal: Goal point (the destination that emerges, not the target).
            hazards: List of hazards to avoid.
            bounds: Optional bounding box for the navigable space.

        Returns:
            A Path through safe space.
        """
        if len(start) != len(goal):
            raise ValueError(
                f"Start has {len(start)} dims, goal has {len(goal)}"
            )

        spatial_hazards = [h for h in hazards if h.is_spatial]

        # Gradient descent on repulsion, gentle ascent on attraction
        current = tuple(float(v) for v in start)
        waypoints = [current]
        goal_reached = False
        stall_counter = 0

        for step_num in range(self.max_steps):
            dist_to_goal = math.sqrt(
                sum((a - b) ** 2 for a, b in zip(current, goal))
            )

            if dist_to_goal < self.step_size:
                goal_reached = True
                break

            next_point = self._combined_step(current, goal, spatial_hazards)

            # Enforce bounds if provided
            if bounds is not None:
                next_point = tuple(
                    max(bounds.mins[i], min(bounds.maxs[i], next_point[i]))
                    for i in range(len(next_point))
                )

            # Check if next point is inside a hazard — if so, add random perturbation
            stuck = False
            for h in spatial_hazards:
                if h.contains(next_point):
                    # Random walk to escape local minimum
                    perturbation = tuple(
                        self._rng.gauss(0, self.step_size) for _ in current
                    )
                    next_point = tuple(
                        c + p for c, p in zip(current, perturbation)
                    )
                    stuck = True
                    break

            # Detect stalling
            move_dist = math.sqrt(
                sum((a - b) ** 2 for a, b in zip(current, next_point))
            )
            if move_dist < self.step_size * 0.05:
                stall_counter += 1
                if stall_counter > 20:
                    # Inject random perturbation to escape
                    perturbation = tuple(
                        self._rng.gauss(0, self.step_size * 2) for _ in current
                    )
                    next_point = tuple(
                        c + p for c, p in zip(current, perturbation)
                    )
                    stall_counter = 0
            else:
                stall_counter = 0

            current = next_point
            waypoints.append(current)

        # Ensure we end at the goal
        if goal_reached or len(waypoints) > 1:
            waypoints.append(tuple(float(v) for v in goal))

        # Smooth the path
        smoothed = self._smooth_path(waypoints, spatial_hazards)

        # Compute metrics
        min_clr = self._path_clearance(smoothed, spatial_hazards)
        total_dist = self._path_distance(smoothed)

        # Safety score: normalized combination of clearance and goal achievement
        safety = min(1.0, max(0.0, min_clr / (self.safety_margin * 5)))
        if not goal_reached:
            safety *= 0.5  # Penalize paths that didn't reach the goal

        return Path(
            waypoints=smoothed,
            min_clearance=min_clr,
            total_distance=total_dist,
            safety_score=safety,
            metadata={
                "goal_reached": goal_reached,
                "raw_waypoints": len(waypoints),
                "smoothed_waypoints": len(smoothed),
                "method": "avoidance_first_gradient",
            },
        )
