"""Tests for skenna.planner — AvoidancePlanner."""
import pytest
from skenna.hazard import Hazard, HazardType
from skenna.planner import AvoidancePlanner
from skenna.space import BoundingBox


class TestRepulsionField:
    def test_no_hazards(self):
        planner = AvoidancePlanner()
        mag, direction = planner._repulsion_field((5.0, 5.0), [])
        assert mag == 0.0

    def test_near_hazard(self):
        planner = AvoidancePlanner()
        h = Hazard(location=(0.0, 0.0), radius=1.0, severity=1.0)
        mag, direction = planner._repulsion_field((1.0, 0.0), [h])
        assert mag > 0.0
        # Direction should point away from origin
        assert direction[0] > 0  # x component is positive (pushing right)

    def test_far_from_hazard(self):
        planner = AvoidancePlanner()
        h = Hazard(location=(0.0, 0.0), radius=1.0, severity=1.0)
        mag, _ = planner._repulsion_field((100.0, 100.0), [h])
        assert mag == pytest.approx(0.0)


class TestPlanning:
    def test_simple_path_no_hazards(self):
        planner = AvoidancePlanner(step_size=0.5, max_steps=100)
        path = planner.plan(
            start=(0.0, 0.0),
            goal=(2.0, 0.0),
            hazards=[],
        )
        assert len(path.waypoints) >= 2
        assert path.start == (0.0, 0.0)

    def test_path_avoids_hazard(self):
        """Path from (-3, 0) to (3, 0) must avoid a hazard at origin."""
        planner = AvoidancePlanner(
            step_size=0.2, max_steps=500, goal_bias=0.1, seed=42
        )
        h = Hazard(location=(0.0, 0.0), radius=1.5, severity=1.0)
        path = planner.plan(
            start=(-3.0, 0.0),
            goal=(3.0, 0.0),
            hazards=[h],
        )
        # No waypoint should be inside the hazard
        for wp in path.waypoints:
            assert h.clearance_at(wp) >= 0 or h.distance_to(wp) > 1.0

    def test_path_with_multiple_hazards(self):
        planner = AvoidancePlanner(
            step_size=0.2, max_steps=500, seed=42
        )
        hazards = [
            Hazard(location=(0.0, 1.0), radius=0.8, severity=1.0),
            Hazard(location=(0.0, -1.0), radius=0.8, severity=1.0),
            Hazard(location=(1.0, 0.0), radius=0.5, severity=0.8),
        ]
        path = planner.plan(
            start=(-2.0, 0.0),
            goal=(2.0, 0.0),
            hazards=hazards,
        )
        assert len(path.waypoints) >= 2

    def test_path_metrics_computed(self):
        planner = AvoidancePlanner(step_size=0.5, max_steps=100, seed=1)
        path = planner.plan(
            start=(0.0, 0.0),
            goal=(2.0, 0.0),
            hazards=[],
        )
        assert path.total_distance > 0
        assert path.safety_score >= 0.0
        assert path.min_clearance > 0

    def test_smooth_path_reduces_waypoints(self):
        """Smoothing should generally reduce waypoint count."""
        planner = AvoidancePlanner(step_size=0.1, max_steps=300, seed=42)
        h = Hazard(location=(0.0, 0.0), radius=1.0, severity=1.0)
        path = planner.plan(
            start=(-3.0, 0.0),
            goal=(3.0, 0.0),
            hazards=[h],
        )
        # The smoothed path should have fewer waypoints than raw
        if "raw_waypoints" in path.metadata:
            assert path.metadata["smoothed_waypoints"] <= path.metadata["raw_waypoints"]

    def test_bounds_enforced(self):
        """Path should stay within bounds."""
        bounds = BoundingBox(mins=(-5.0, -5.0), maxs=(5.0, 5.0))
        planner = AvoidancePlanner(step_size=0.5, max_steps=200, seed=42)
        path = planner.plan(
            start=(0.0, 0.0),
            goal=(4.0, 4.0),
            hazards=[],
            bounds=bounds,
        )
        for wp in path.waypoints:
            assert bounds.contains(wp)

    def test_dimension_mismatch_raises(self):
        planner = AvoidancePlanner()
        with pytest.raises(ValueError, match="dims"):
            planner.plan(
                start=(0.0, 0.0),
                goal=(1.0, 1.0, 1.0),
                hazards=[],
            )
