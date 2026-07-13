"""Tests for skenna.navigator — NegativeSpaceNavigator."""
import pytest
from skenna.hazard import Hazard, HazardType
from skenna.navigator import NegativeSpaceNavigator
from skenna.space import BoundingBox


class TestNavigatorBasics:
    def test_empty_navigator(self):
        nav = NegativeSpaceNavigator()
        assert len(nav.hazards) == 0
        assert nav.safe_space is None
        assert repr(nav) == "NegativeSpaceNavigator(hazards=0)"

    def test_add_hazard(self):
        nav = NegativeSpaceNavigator()
        h = Hazard(location=(0.0, 0.0), radius=1.0, severity=1.0)
        nav.add_hazard(h)
        assert len(nav.hazards) == 1
        assert nav.safe_space is None  # invalidated

    def test_remove_hazard(self):
        nav = NegativeSpaceNavigator()
        h = Hazard(location=(0.0, 0.0), radius=1.0)
        nav.add_hazard(h)
        removed = nav.remove_hazard(0)
        assert removed == h
        assert len(nav.hazards) == 0

    def test_clear_hazards(self):
        nav = NegativeSpaceNavigator()
        nav.add_hazard(Hazard(location=(0, 0)))
        nav.add_hazard(Hazard(location=(1, 1)))
        nav.clear_hazards()
        assert len(nav.hazards) == 0


class TestChartSafeSpace:
    def test_chart_with_bounds(self):
        nav = NegativeSpaceNavigator(bounds=BoundingBox(
            mins=(0, 0), maxs=(10, 10)
        ))
        nav.add_hazard(Hazard(location=(5, 5), radius=1.0))
        space = nav.chart_safe_space()
        assert space is not None
        assert len(space.excluded_regions) == 1
        assert space.coverage_fraction() < 1.0

    def test_chart_unbounded(self):
        nav = NegativeSpaceNavigator()
        nav.add_hazard(Hazard(location=(0, 0), radius=1.0))
        space = nav.chart_safe_space()
        assert space.is_unbounded
        assert space.safe_area == float("inf")

    def test_chart_caching(self):
        nav = NegativeSpaceNavigator()
        nav.add_hazard(Hazard(location=(0, 0), radius=1.0))
        s1 = nav.chart_safe_space()
        nav.add_hazard(Hazard(location=(5, 5), radius=1.0))
        assert nav.safe_space is None  # adding hazard invalidates
        s2 = nav.chart_safe_space()
        assert len(s2.excluded_regions) == 2


class TestNavigation:
    def test_navigate_no_hazards(self):
        nav = NegativeSpaceNavigator()
        path = nav.navigate(start=(0.0, 0.0), goal=(5.0, 0.0))
        assert len(path.waypoints) >= 2
        assert path.start == (0.0, 0.0)

    def test_navigate_with_hazard(self):
        nav = NegativeSpaceNavigator()
        nav.add_hazard(Hazard(
            location=(2.5, 0.0), radius=1.0, severity=1.0
        ))
        path = nav.navigate(start=(0.0, 0.0), goal=(5.0, 0.0))
        assert len(path.waypoints) >= 2
        # Path should avoid the hazard zone
        h = nav.hazards[0]
        for wp in path.waypoints:
            assert not h.contains(wp) or h.distance_to(wp) > 0.5

    def test_is_safe(self):
        nav = NegativeSpaceNavigator()
        nav.add_hazard(Hazard(location=(0, 0), radius=1.0))
        assert not nav.is_safe((0.5, 0.0))
        assert nav.is_safe((5.0, 5.0))

    def test_clearance_at(self):
        nav = NegativeSpaceNavigator()
        nav.add_hazard(Hazard(location=(0, 0), radius=2.0))
        assert nav.clearance_at((3.0, 0.0)) == pytest.approx(1.0)
        assert nav.clearance_at((1.0, 0.0)) == pytest.approx(-1.0)

    def test_clearance_no_hazards(self):
        nav = NegativeSpaceNavigator()
        assert nav.clearance_at((0, 0)) == float("inf")

    def test_safety_score(self):
        nav = NegativeSpaceNavigator()
        nav.add_hazard(Hazard(location=(0, 0), radius=1.0))
        # Far from hazard -> high safety
        assert nav.safety_score((100, 100)) > 0.9
        # Inside hazard -> zero safety
        assert nav.safety_score((0, 0)) == 0.0


class TestSummary:
    def test_summary_no_hazards(self):
        nav = NegativeSpaceNavigator()
        s = nav.summary()
        assert "0" in s
        assert "skénna" in s

    def test_summary_with_hazards(self):
        nav = NegativeSpaceNavigator(
            bounds=BoundingBox(mins=(0, 0), maxs=(10, 10))
        )
        nav.add_hazard(Hazard(location=(5, 5), radius=1.0,
                               hazard_type=HazardType.REEF))
        nav.chart_safe_space()
        s = nav.summary()
        assert "1" in s
        assert "reef" not in s  # summary doesn't list types
