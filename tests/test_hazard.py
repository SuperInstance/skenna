"""Tests for skenna.hazard — Hazard dataclass."""
import pytest
from skenna.hazard import Hazard, HazardType


class TestHazardCreation:
    def test_basic_spatial_hazard(self):
        h = Hazard(location=(0.0, 0.0), radius=1.0, severity=0.8)
        assert h.is_spatial
        assert h.coordinates == (0.0, 0.0)
        assert h.dimensions == 2
        assert h.radius == 1.0
        assert h.severity == 0.8

    def test_semantic_hazard(self):
        h = Hazard(
            location="sql_injection",
            radius=0.5,
            severity=1.0,
            hazard_type=HazardType.SECURITY,
        )
        assert not h.is_spatial
        assert h.dimensions == 0

    def test_3d_hazard(self):
        h = Hazard(location=(1.0, 2.0, 3.0), radius=0.5)
        assert h.dimensions == 3

    def test_default_hazard_type(self):
        h = Hazard(location=(0, 0))
        assert h.hazard_type == HazardType.CUSTOM

    def test_severity_out_of_range(self):
        with pytest.raises(ValueError, match="Severity"):
            Hazard(location=(0, 0), severity=1.5)
        with pytest.raises(ValueError, match="Severity"):
            Hazard(location=(0, 0), severity=-0.1)

    def test_negative_radius(self):
        with pytest.raises(ValueError, match="Radius"):
            Hazard(location=(0, 0), radius=-1.0)

    def test_label_and_metadata(self):
        h = Hazard(
            location=(48.5, -123.0),
            radius=2.0,
            label="Discovery Reef",
            metadata={"discovered": "1792", "charted_by": "Vancouver"},
        )
        assert h.label == "Discovery Reef"
        assert h.metadata["charted_by"] == "Vancouver"


class TestDistanceTo:
    def test_distance_2d(self):
        h = Hazard(location=(0.0, 0.0), radius=1.0)
        assert h.distance_to((3.0, 4.0)) == pytest.approx(5.0)

    def test_distance_to_center(self):
        h = Hazard(location=(1.0, 1.0), radius=0.5)
        assert h.distance_to((1.0, 1.0)) == pytest.approx(0.0)

    def test_dimension_mismatch(self):
        h = Hazard(location=(0.0, 0.0), radius=1.0)
        with pytest.raises(ValueError, match="dimensions"):
            h.distance_to((1.0, 2.0, 3.0))

    def test_semantic_match(self):
        h = Hazard(location="sql_injection", radius=0.5)
        assert h.distance_to("sql_injection") == 0.0

    def test_semantic_no_match(self):
        h = Hazard(location="sql_injection", radius=0.5)
        assert h.distance_to("safe_code") == float("inf")


class TestClearance:
    def test_outside_hazard(self):
        h = Hazard(location=(0.0, 0.0), radius=2.0)
        assert h.clearance_at((5.0, 0.0)) == pytest.approx(3.0)

    def test_inside_hazard(self):
        h = Hazard(location=(0.0, 0.0), radius=5.0)
        assert h.clearance_at((1.0, 0.0)) == pytest.approx(-4.0)

    def test_on_boundary(self):
        h = Hazard(location=(0.0, 0.0), radius=3.0)
        assert h.clearance_at((3.0, 0.0)) == pytest.approx(0.0)

    def test_contains_inside(self):
        h = Hazard(location=(0.0, 0.0), radius=2.0)
        assert h.contains((1.0, 1.0))

    def test_contains_outside(self):
        h = Hazard(location=(0.0, 0.0), radius=1.0)
        assert not h.contains((5.0, 5.0))


class TestRepulsion:
    def test_zero_at_center_inside(self):
        h = Hazard(location=(0.0, 0.0), radius=1.0, severity=1.0)
        # At center, distance is 0, so repulsion should be max
        assert h.repulsion_at((0.0, 0.0)) == pytest.approx(1.0)

    def test_zero_far_away(self):
        h = Hazard(location=(0.0, 0.0), radius=1.0, severity=1.0)
        assert h.repulsion_at((100.0, 100.0)) == pytest.approx(0.0)

    def test_severity_scales_repulsion(self):
        h1 = Hazard(location=(0.0, 0.0), radius=1.0, severity=0.5)
        h2 = Hazard(location=(0.0, 0.0), radius=1.0, severity=1.0)
        near = (0.5, 0.0)
        assert h2.repulsion_at(near) > h1.repulsion_at(near)

    def test_falloff_with_distance(self):
        h = Hazard(location=(0.0, 0.0), radius=1.0, severity=1.0)
        near = h.repulsion_at((0.5, 0.0))
        far = h.repulsion_at((2.0, 0.0))
        assert near > far


class TestRepr:
    def test_repr(self):
        h = Hazard(location=(1.0, 2.0), radius=1.5, severity=0.9,
                    hazard_type=HazardType.REEF)
        r = repr(h)
        assert "Hazard" in r
        assert "reef" in r
