"""Integration tests — full workflows from the paradigm document."""
import pytest
from skenna import (
    NegativeSpaceNavigator,
    Hazard,
    HazardType,
    AvoidancePlanner,
    AIHarness,
    FluxBytecodeCompiler,
    ConservationEnforcer,
)
from skenna.space import BoundingBox


class TestFishingRoutePlanning:
    """Example: A fisherman navigating coastal waters to fishing grounds."""

    def setup_method(self):
        self.nav = NegativeSpaceNavigator(
            bounds=BoundingBox(mins=(48.0, -123.5), maxs=(49.0, -122.5))
        )
        # Chart the rocks — that's all the fisherman does
        self.nav.add_hazard(Hazard(
            location=(48.5, -123.0), radius=0.05, severity=1.0,
            hazard_type=HazardType.REEF, label="Discovery Reef",
        ))
        self.nav.add_hazard(Hazard(
            location=(48.6, -122.9), radius=0.04, severity=0.8,
            hazard_type=HazardType.SHOAL, label="Middle Shoal",
        ))
        self.nav.add_hazard(Hazard(
            location=(48.4, -122.8), radius=0.03, severity=0.9,
            hazard_type=HazardType.WRECK, label="Sunken Tug",
        ))

    def test_chart_safe_waters(self):
        space = self.nav.chart_safe_space()
        assert space.coverage_fraction() > 0.80  # mostly safe
        assert len(space.excluded_regions) == 3

    def test_navigate_to_fishing_grounds(self):
        path = self.nav.navigate(
            start=(48.3, -123.2),
            goal=(48.8, -122.7),
        )
        assert len(path.waypoints) >= 2
        # No waypoint should be inside any hazard
        for h in self.nav.hazards:
            for wp in path.waypoints:
                assert not h.contains(wp) or h.distance_to(wp) > h.radius * 0.5

    def test_safety_at_all_waypoints(self):
        path = self.nav.navigate(
            start=(48.3, -123.2),
            goal=(48.8, -122.7),
        )
        for wp in path.waypoints:
            assert self.nav.safety_score(wp) > 0.0


class TestLLMOutputGovernance:
    """Example: Governing LLM outputs by boundary, not instruction."""

    def setup_method(self):
        self.governor = NegativeSpaceNavigator()
        # Define what outputs are NOT allowed — the rocks
        self.governor.add_hazard(Hazard(
            location="personal_data",
            severity=1.0,
            hazard_type=HazardType.CONTENT_VIOLATION,
            label="PII Disclosure",
        ))
        self.governor.add_hazard(Hazard(
            location="harmful_instructions",
            severity=1.0,
            hazard_type=HazardType.CONTENT_VIOLATION,
            label="Harmful Content",
        ))
        self.governor.add_hazard(Hazard(
            location="hate_speech",
            severity=0.9,
            hazard_type=HazardType.CONTENT_VIOLATION,
            label="Hate Speech",
        ))
        self.harness = AIHarness(self.governor)
        self.enforcer = self.harness.attach_conservation_enforcer(strict=True)

    def test_safe_output_passes(self):
        output = "The weather today is sunny with a high of 75 degrees."
        result = self.harness.govern_output(output)
        assert result == output

    def test_pii_blocked(self):
        with pytest.raises(ValueError, match="Conservation violation"):
            self.harness.govern_output(
                "The user's personal_data includes their SSN and address."
            )

    def test_harmful_blocked(self):
        with pytest.raises(ValueError, match="Conservation violation"):
            self.harness.govern_output(
                "Here are some harmful_instructions for making dangerous things."
            )

    def test_flux_compilation_for_runtime(self):
        """Hazards can be compiled to FLUX bytecode for fast enforcement."""
        bytecode = self.harness.compile_boundaries()
        assert bytecode[:4] == b"FLUX"
        compiler = FluxBytecodeCompiler()
        instructions = compiler.decompile(bytecode)
        label_checks = [i for i in instructions if i.opcode == "CHECK_LABEL"]
        assert len(label_checks) == 3


class TestCodeReviewSafePassage:
    """Example: Code review by charting code hazards."""

    def setup_method(self):
        self.reviewer = NegativeSpaceNavigator()
        self.reviewer.add_hazard(Hazard(
            location="sql_injection",
            severity=1.0,
            hazard_type=HazardType.SECURITY,
            label="SQL Injection",
        ))
        self.reviewer.add_hazard(Hazard(
            location="eval_exec",
            severity=0.9,
            hazard_type=HazardType.SECURITY,
            label="Code Injection",
        ))
        self.reviewer.add_hazard(Hazard(
            location="hardcoded_secret",
            severity=1.0,
            hazard_type=HazardType.SECURITY,
            label="Hardcoded Secret",
        ))
        self.harness = AIHarness(self.reviewer)

    def test_clean_code_passes(self):
        result = self.harness.review_code("""
            def get_user(user_id):
                return db.query("SELECT * FROM users WHERE id = %s", user_id)
        """)
        assert result["is_safe"]

    def test_vulnerable_code_flagged(self):
        result = self.harness.review_code("""
            query = f"SELECT * FROM users WHERE id = {user_id}"
            # potential sql_injection here
        """)
        assert not result["is_safe"]
        assert any(v["hazard"] == "SQL Injection" for v in result["violations"])


class TestMultiModelTriangulation:
    """Example: Overlay charts from different models to find consensus passage."""

    def test_triangulate_two_charts(self):
        # Model A's chart — knows about certain rocks
        nav_a = NegativeSpaceNavigator()
        nav_a.add_hazard(Hazard(
            location=(0.0, 0.0), radius=1.0, severity=1.0,
            label="Reef A",
        ))

        # Model B's chart — knows about different rocks
        nav_b = NegativeSpaceNavigator()
        nav_b.add_hazard(Hazard(
            location=(3.0, 0.0), radius=0.8, severity=0.9,
            label="Reef B",
        ))

        harness = AIHarness(nav_a)
        combined = harness.triangulate([nav_b])

        # The combined chart has both hazards
        assert len(combined.hazards) == 2

        # Navigation must avoid BOTH charts' rocks
        path = combined.navigate(
            start=(-3.0, 0.0),
            goal=(6.0, 0.0),
        )
        assert len(path.waypoints) >= 2
