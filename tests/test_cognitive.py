"""
Tests for skenna.cognitive — ModelChart, ChartThickness, Sounding,
CognitiveNavigator, CognitiveRoute, ConsensusReport.

These tests cover the cognitive navigation layer: the γ/η conservation
law, the Socratic protocol (thin → thick model routing), soundings,
and multi-model consensus/divergence.
"""
import pytest
from skenna.cognitive import (
    CognitiveDimension,
    CognitiveNavigator,
    ModelChart,
    ChartThickness,
    Sounding,
    CognitiveRoute,
    ConsensusReport,
)


# ─── ModelChart ────────────────────────────────────────────────────────

class TestModelChart:
    def test_creation_with_gamma(self):
        chart = ModelChart(
            name="pro",
            gamma={CognitiveDimension.SYNTHESIS: 0.84, CognitiveDimension.DEPTH: 0.9},
        )
        assert chart.name == "pro"
        assert chart.gamma[CognitiveDimension.SYNTHESIS] == 0.84

    def test_eta_is_complement(self):
        chart = ModelChart(
            name="test",
            gamma={CognitiveDimension.LOGIC: 0.7},
        )
        assert chart.eta(CognitiveDimension.LOGIC) == pytest.approx(0.3)

    def test_eta_for_unspecified_dimension(self):
        chart = ModelChart(name="test", gamma={})
        # Unspecified dimension defaults to γ=0.5, so η=0.5
        assert chart.eta(CognitiveDimension.CODE) == pytest.approx(0.5)

    def test_invalid_gamma_raises(self):
        with pytest.raises(ValueError, match="γ"):
            ModelChart(name="bad", gamma={CognitiveDimension.LOGIC: 1.5})

    def test_thin_chart_detection(self):
        thin = ModelChart(
            name="mini",
            gamma={CognitiveDimension.IDEATION: 0.3, CognitiveDimension.NAMING: 0.2},
        )
        assert thin.is_thin_chart()
        assert not thin.is_thick_chart()

    def test_thick_chart_detection(self):
        thick = ModelChart(
            name="pro",
            gamma={CognitiveDimension.SYNTHESIS: 0.9, CognitiveDimension.DEPTH: 0.85,
                   CognitiveDimension.LOGIC: 0.8, CognitiveDimension.PRECISION: 0.9},
        )
        assert thick.is_thick_chart()
        assert not thick.is_thin_chart()

    def test_thinnest_dimensions(self):
        chart = ModelChart(
            name="test",
            gamma={CognitiveDimension.SYNTHESIS: 0.9, CognitiveDimension.NAMING: 0.1,
                   CognitiveDimension.CODE: 0.5},
        )
        thinnest = chart.thinnest_dimensions(2)
        assert thinnest[0][0] == CognitiveDimension.NAMING
        assert thinnest[0][1] == pytest.approx(0.9)  # η = 0.9

    def test_thickest_dimensions(self):
        chart = ModelChart(
            name="test",
            gamma={CognitiveDimension.SYNTHESIS: 0.9, CognitiveDimension.NAMING: 0.1},
        )
        thickest = chart.thickest_dimensions(1)
        assert thickest[0][0] == CognitiveDimension.SYNTHESIS

    def test_complementary_charts(self):
        """The elder's η is the mini's γ — from ON_SKENNA.md."""
        elder = ModelChart(
            name="pro",
            gamma={CognitiveDimension.SYNTHESIS: 0.84, CognitiveDimension.NAMING: 0.16},
        )
        mini = ModelChart(
            name="mini",
            gamma={CognitiveDimension.SYNTHESIS: 0.16, CognitiveDimension.NAMING: 0.84},
        )
        comp = elder.complementary(mini)
        # Perfectly complementary: 1.0
        assert comp > 0.9

    def test_identical_charts_not_complementary(self):
        # Two charts with γ=0.8 in the same dimension are NOT complementary
        # because 0.8 != (1.0 - 0.8)
        a = ModelChart(name="a", gamma={CognitiveDimension.LOGIC: 0.8})
        b = ModelChart(name="b", gamma={CognitiveDimension.LOGIC: 0.8})
        assert a.complementary(b) < 0.6

    def test_repr(self):
        chart = ModelChart(name="test", gamma={CognitiveDimension.LOGIC: 0.7})
        r = repr(chart)
        assert "ModelChart" in r
        assert "test" in r


# ─── ChartThickness ────────────────────────────────────────────────────

class TestChartThickness:
    def test_thickness_from_thick_chart(self):
        chart = ModelChart(
            name="pro",
            gamma={CognitiveDimension.SYNTHESIS: 0.9, CognitiveDimension.DEPTH: 0.85,
                   CognitiveDimension.LOGIC: 0.8},
        )
        ct = chart.chart_thickness()
        assert ct.gamma_ratio > 0.8
        assert ct.is_thick
        assert not ct.is_thin

    def test_thickness_from_thin_chart(self):
        chart = ModelChart(
            name="mini",
            gamma={CognitiveDimension.NAMING: 0.2, CognitiveDimension.CODE: 0.1},
        )
        ct = chart.chart_thickness()
        assert ct.gamma_ratio < 0.4
        assert ct.is_thin
        assert not ct.is_thick

    def test_conservation_law(self):
        """γ + η = C (always conserved)."""
        chart = ModelChart(name="x", gamma={CognitiveDimension.LOGIC: 0.6})
        ct = chart.chart_thickness()
        assert ct.conservation  # γ + η = 1.0
        assert ct.gamma_ratio + ct.eta_ratio == pytest.approx(1.0)

    def test_empty_chart(self):
        chart = ModelChart(name="empty")
        ct = chart.chart_thickness()
        assert ct.dimensions_measured == 0

    def test_thickness_repr(self):
        ct = ChartThickness(gamma_ratio=0.3, dimensions_measured=5)
        assert "thin" in repr(ct)
        ct2 = ChartThickness(gamma_ratio=0.8, dimensions_measured=5)
        assert "thick" in repr(ct2)


# ─── Sounding ──────────────────────────────────────────────────────────

class TestSounding:
    def test_basic_sounding(self):
        s = Sounding(
            query="What is skénna?",
            model_name="mini",
            result="skénna is negative-space navigation",
        )
        assert s.query == "What is skénna?"
        assert s.model_name == "mini"
        assert s.is_productive
        assert not s.has_discovery  # no discoveries added

    def test_add_discovery(self):
        s = Sounding(query="q", model_name="m", result="r")
        assert not s.has_discovery
        s.add_discovery("Found the door")
        assert s.has_discovery
        assert len(s.discoveries) == 1

    def test_empty_sounding(self):
        s = Sounding(query="q", model_name="m", result="")
        assert not s.is_productive

    def test_timestamp_auto_set(self):
        s = Sounding(query="q", model_name="m")
        assert s.timestamp > 0

    def test_repr(self):
        s = Sounding(query="What is the meaning?", model_name="test", result="42")
        r = repr(s)
        assert "Sounding" in r
        assert "test" in r


# ─── CognitiveNavigator ────────────────────────────────────────────────

class TestCognitiveNavigator:
    def setup_method(self):
        self.nav = CognitiveNavigator()
        self.nav.register_model(
            ModelChart(
                name="mini",
                gamma={CognitiveDimension.IDEATION: 0.8, CognitiveDimension.NAMING: 0.84,
                       CognitiveDimension.SYNTHESIS: 0.16},
                cost_per_1k=0.01,
            ),
            handler=lambda q: f"Mini explores: {q}",
        )
        self.nav.register_model(
            ModelChart(
                name="pro",
                gamma={CognitiveDimension.SYNTHESIS: 0.84, CognitiveDimension.DEPTH: 0.9,
                       CognitiveDimension.NAMING: 0.16},
                cost_per_1k=0.10,
            ),
            handler=lambda q: f"Pro synthesizes: {q}",
        )

    def test_register_model(self):
        assert "mini" in self.nav.model_charts
        assert "pro" in self.nav.model_charts

    def test_register_unregistered_model_errors(self):
        with pytest.raises(KeyError, match="not registered"):
            self.nav.explore("q", model_name="unknown")

    def test_sound_depth(self):
        # Mini has γ=0.16 in SYNTHESIS, so η=0.84 (deep unmarked water)
        depth = self.nav.sound_depth("mini", CognitiveDimension.SYNTHESIS)
        assert depth == pytest.approx(0.84)

    def test_sound_depth_thick_chart(self):
        # Pro has γ=0.84 in SYNTHESIS, so η=0.16 (well-charted)
        depth = self.nav.sound_depth("pro", CognitiveDimension.SYNTHESIS)
        assert depth < 0.2

    def test_explore(self):
        sounding = self.nav.explore("What is skénna?", model_name="mini")
        assert sounding.model_name == "mini"
        assert "Mini explores" in sounding.result
        assert sounding.is_productive

    def test_explore_records_sounding(self):
        self.nav.explore("test", model_name="mini")
        assert len(self.nav.soundings) == 1

    def test_explore_finds_discoveries(self):
        # Mini has deep η in SYNTHESIS (0.84), and the default handler returns text
        sounding = self.nav.explore(
            "test query", model_name="mini",
            dimensions=[CognitiveDimension.SYNTHESIS],
        )
        # Since η=0.84 > 0.5 and response is non-empty, discovery should be added
        assert sounding.has_discovery

    def test_explore_no_discovery_in_thick_dimension(self):
        # Pro has γ=0.84 in SYNTHESIS (η=0.16 < 0.5), so no discovery
        sounding = self.nav.explore(
            "test query", model_name="pro",
            dimensions=[CognitiveDimension.SYNTHESIS],
        )
        assert not sounding.has_discovery

    def test_route_socratic_protocol(self):
        route = self.nav.route("Name the concept", models=["mini", "pro"])
        assert len(route.legs) == 2
        assert route.discovery_phase.model_name == "mini"
        assert route.synthesis_phase[0].model_name == "pro"
        assert route.is_complete

    def test_route_accumulates_context(self):
        route = self.nav.route("test", models=["mini", "pro"])
        # Pro's query should include mini's output
        pro_query = route.legs[1].query
        assert "Mini explores" in pro_query

    def test_route_requires_two_models(self):
        with pytest.raises(ValueError, match="at least 2"):
            self.nav.route("q", models=["mini"])

    def test_route_unknown_model(self):
        with pytest.raises(KeyError, match="not registered"):
            self.nav.route("q", models=["mini", "unknown"])

    def test_route_discoveries_collected(self):
        route = self.nav.route("concept", models=["mini", "pro"])
        # Mini should have discoveries from exploring its thin dimensions
        assert len(route.discoveries) > 0

    def test_consensus(self):
        report = self.nav.consensus(["mini", "pro"], "What is skénna?")
        assert len(report.models) == 2
        assert "mini" in report.responses
        assert "pro" in report.responses

    def test_consensus_finds_divergence(self):
        # Mini and Pro diverge in SYNTHESIS (0.16 vs 0.84)
        report = self.nav.consensus(["mini", "pro"], "test")
        assert CognitiveDimension.SYNTHESIS in report.divergence_dimensions

    def test_consensus_agreement_fraction(self):
        report = self.nav.consensus(["mini", "pro"], "test")
        assert 0.0 <= report.agreement_fraction <= 1.0

    def test_chart_overlap(self):
        overlap = self.nav.chart_overlap("mini", "pro")
        # SYNTHESIS: mini γ=0.16, pro γ=0.84
        syn_overlap = overlap[CognitiveDimension.SYNTHESIS]
        assert syn_overlap[0] == pytest.approx(0.16)
        assert syn_overlap[1] == pytest.approx(0.84)

    def test_chart_overlap_complementarity(self):
        overlap = self.nav.chart_overlap("mini", "pro")
        # In SYNTHESIS: mini γ=0.16, pro γ=0.84 → perfectly complementary
        syn_comp = overlap[CognitiveDimension.SYNTHESIS][2]
        assert syn_comp > 0.9  # near-perfect complementarity

    def test_explore_override_handler(self):
        sounding = self.nav.explore(
            "custom", model_name="mini",
            handler=lambda q: "custom response",
        )
        assert "custom response" in sounding.result

    def test_repr(self):
        r = repr(self.nav)
        assert "CognitiveNavigator" in r
        assert "models=2" in r


# ─── CognitiveRoute ────────────────────────────────────────────────────

class TestCognitiveRoute:
    def test_route_basic(self):
        legs = [
            Sounding(query="q", model_name="mini", result="discovery"),
            Sounding(query="q", model_name="pro", result="synthesis"),
        ]
        route = CognitiveRoute(
            query="q", models=["mini", "pro"],
            legs=legs, final_synthesis="synthesis",
        )
        assert route.is_complete
        assert route.discovery_phase.model_name == "mini"
        assert len(route.synthesis_phase) == 1

    def test_route_empty(self):
        route = CognitiveRoute(query="q", models=[], legs=[])
        assert not route.is_complete
        assert route.discovery_phase is None

    def test_route_discoveries(self):
        legs = [
            Sounding(query="q", model_name="mini", result="d"),
            Sounding(query="q", model_name="pro", result="s"),
        ]
        legs[0].add_discovery("found A")
        legs[1].add_discovery("found B")
        route = CognitiveRoute(query="q", models=["mini", "pro"], legs=legs)
        assert len(route.discoveries) == 2

    def test_route_repr(self):
        route = CognitiveRoute(
            query="q", models=["a", "b"],
            legs=[Sounding(query="q", model_name="a", result="r")],
        )
        r = repr(route)
        assert "CognitiveRoute" in r


# ─── ConsensusReport ───────────────────────────────────────────────────

class TestConsensusReport:
    def test_basic_report(self):
        report = ConsensusReport(
            query="q", models=["a", "b"],
            responses={"a": "hello world", "b": "hello there"},
            consensus_dimensions=[CognitiveDimension.LOGIC],
            divergence_dimensions=[CognitiveDimension.NAMING],
            shared_content=["hello"],
            unique_content={"a": {"world"}, "b": {"there"}},
        )
        assert report.has_consensus
        assert report.has_discovery
        assert report.agreement_fraction == pytest.approx(0.5)

    def test_all_consensus(self):
        report = ConsensusReport(
            query="q", models=["a", "b"],
            responses={},
            consensus_dimensions=[CognitiveDimension.LOGIC, CognitiveDimension.CODE],
            divergence_dimensions=[],
            shared_content=[], unique_content={},
        )
        assert report.has_consensus
        assert not report.has_discovery
        assert report.agreement_fraction == 1.0

    def test_all_divergence(self):
        report = ConsensusReport(
            query="q", models=["a", "b"],
            responses={},
            consensus_dimensions=[],
            divergence_dimensions=[CognitiveDimension.LOGIC, CognitiveDimension.CODE],
            shared_content=[], unique_content={},
        )
        assert not report.has_consensus
        assert report.has_discovery
        assert report.agreement_fraction == 0.0

    def test_repr(self):
        report = ConsensusReport(
            query="q", models=["a", "b"], responses={},
            consensus_dimensions=[], divergence_dimensions=[],
            shared_content=[], unique_content={},
        )
        r = repr(report)
        assert "ConsensusReport" in r


# ─── Integration with NegativeSpaceNavigator ──────────────────────────

class TestNavigatorIntegration:
    def test_navigator_cognitive_methods_exist(self):
        from skenna import NegativeSpaceNavigator
        nav = NegativeSpaceNavigator()
        nav.register_model(ModelChart(
            name="test",
            gamma={CognitiveDimension.LOGIC: 0.5},
        ))
        sounding = nav.explore("q", model="test")
        assert isinstance(sounding, Sounding)

    def test_navigator_route(self):
        from skenna import NegativeSpaceNavigator
        nav = NegativeSpaceNavigator()
        nav.register_model(
            ModelChart(name="thin", gamma={CognitiveDimension.NAMING: 0.2}),
            handler=lambda q: "a discovery",
        )
        nav.register_model(
            ModelChart(name="thick", gamma={CognitiveDimension.SYNTHESIS: 0.9}),
            handler=lambda q: "a synthesis",
        )
        route = nav.route("concept", models=["thin", "thick"])
        assert route.is_complete

    def test_navigator_consensus(self):
        from skenna import NegativeSpaceNavigator
        nav = NegativeSpaceNavigator()
        nav.register_model(
            ModelChart(name="a", gamma={CognitiveDimension.LOGIC: 0.3}),
            handler=lambda q: "response a",
        )
        nav.register_model(
            ModelChart(name="b", gamma={CognitiveDimension.LOGIC: 0.8}),
            handler=lambda q: "response b",
        )
        report = nav.consensus(["a", "b"], "query")
        assert len(report.responses) == 2

    def test_hazard_register_alias(self):
        from skenna import NegativeSpaceNavigator, Hazard
        nav = NegativeSpaceNavigator()
        h = Hazard(location="bad_thing", severity=1.0)
        nav.hazard_register(h)
        assert len(nav.hazards) == 1

    def test_sound_depth_via_navigator(self):
        from skenna import NegativeSpaceNavigator
        nav = NegativeSpaceNavigator()
        nav.register_model(ModelChart(
            name="test",
            gamma={CognitiveDimension.CODE: 0.3},
        ))
        depth = nav.sound_depth("test", CognitiveDimension.CODE)
        assert depth == pytest.approx(0.7)
