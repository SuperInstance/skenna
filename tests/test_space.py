"""Tests for skenna.space — Space, Path, BoundingBox."""
import pytest
import math
from skenna.space import Space, Path, BoundingBox, Point


class TestBoundingBox:
    def test_2d_box(self):
        bb = BoundingBox(mins=(0.0, 0.0), maxs=(10.0, 10.0))
        assert bb.dimensions == 2
        assert bb.center == (5.0, 5.0)
        assert bb.extents == (10.0, 10.0)
        assert bb.area == 100.0

    def test_contains(self):
        bb = BoundingBox(mins=(0.0, 0.0), maxs=(10.0, 10.0))
        assert bb.contains((5.0, 5.0))
        assert bb.contains((0.0, 0.0))  # inclusive
        assert not bb.contains((-1.0, 5.0))
        assert not bb.contains((5.0, 15.0))

    def test_expand(self):
        bb = BoundingBox(mins=(0.0, 0.0), maxs=(10.0, 10.0))
        expanded = bb.expand(2.0)
        assert expanded.mins == (-2.0, -2.0)
        assert expanded.maxs == (12.0, 12.0)

    def test_3d_box(self):
        bb = BoundingBox(mins=(0, 0, 0), maxs=(2, 3, 4))
        assert bb.area == 24.0

    def test_sample_grid(self):
        bb = BoundingBox(mins=(0.0, 0.0), maxs=(1.0, 1.0))
        points = bb.sample(resolution=0.5)
        # Should produce a 3x3 grid = 9 points
        assert len(points) == 9


class TestSpace:
    def test_empty_space_is_safe(self):
        space = Space(bounds=BoundingBox(mins=(0, 0), maxs=(10, 10)))
        assert space.is_safe((5.0, 5.0))

    def test_excluded_region(self):
        space = Space(
            bounds=BoundingBox(mins=(0, 0), maxs=(10, 10)),
            excluded_regions=[((5.0, 5.0), 1.0)],
        )
        assert not space.is_safe((5.0, 5.0))
        assert space.is_safe((8.0, 8.0))

    def test_clearance(self):
        space = Space(
            bounds=BoundingBox(mins=(0, 0), maxs=(10, 10)),
            excluded_regions=[((5.0, 5.0), 1.0)],
        )
        assert not space.is_safe((5.8, 5.0), clearance=0.5)
        assert space.is_safe((7.0, 5.0), clearance=0.5)

    def test_safe_area(self):
        space = Space(
            bounds=BoundingBox(mins=(0, 0), maxs=(10, 10)),
            excluded_regions=[((5.0, 5.0), 2.0)],
        )
        excluded = math.pi * 4
        assert space.safe_area == pytest.approx(100 - excluded, rel=0.01)

    def test_unbounded_space(self):
        space = Space()
        assert space.is_unbounded
        assert space.safe_area == float("inf")

    def test_coverage_fraction(self):
        space = Space(
            bounds=BoundingBox(mins=(0, 0), maxs=(4, 4)),
            excluded_regions=[((2.0, 2.0), 0.5)],
            resolution=1.0,
        )
        frac = space.coverage_fraction()
        assert 0.0 < frac < 1.0

    def test_safe_points(self):
        space = Space(
            bounds=BoundingBox(mins=(0, 0), maxs=(2, 2)),
            excluded_regions=[((1.0, 1.0), 0.3)],
            resolution=1.0,
        )
        points = space.safe_points()
        assert len(points) > 0
        for p in points:
            assert space.is_safe(p)


class TestPath:
    def test_empty_path(self):
        p = Path()
        assert len(p) == 0
        assert p.start is None
        assert p.end is None

    def test_path_properties(self):
        p = Path(waypoints=[(0, 0), (3, 0), (3, 4)])
        assert p.start == (0, 0)
        assert p.end == (3, 4)
        lengths = p.segment_lengths()
        assert lengths[0] == pytest.approx(3.0)
        assert lengths[1] == pytest.approx(4.0)

    def test_resample(self):
        p = Path(waypoints=[(0, 0), (10, 0)])
        resampled = p.resample(interval=1.0)
        assert len(resampled.waypoints) > 2
        assert resampled.waypoints[0] == (0, 0)

    def test_repr(self):
        p = Path(waypoints=[(0, 0), (1, 1)], total_distance=1.414,
                 min_clearance=0.5, safety_score=0.9)
        r = repr(p)
        assert "Path" in r
        assert "clearance" in r

    def test_iter(self):
        waypoints = [(0, 0), (1, 1), (2, 2)]
        p = Path(waypoints=waypoints)
        assert list(p) == waypoints
