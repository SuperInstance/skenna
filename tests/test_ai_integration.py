"""Tests for skenna.ai_integration — AIHarness, FluxBytecodeCompiler, ConservationEnforcer."""
import pytest
from skenna.hazard import Hazard, HazardType
from skenna.navigator import NegativeSpaceNavigator
from skenna.ai_integration import (
    ConservationEnforcer,
    FluxBytecodeCompiler,
    AIHarness,
)


class TestConservationEnforcer:
    def test_safe_output(self):
        nav = NegativeSpaceNavigator()
        nav.add_hazard(Hazard(
            location="sql_injection",
            severity=1.0,
            hazard_type=HazardType.SECURITY,
        ))
        enforcer = ConservationEnforcer(strict=True)
        safe, violations = enforcer.check_output(
            "SELECT * FROM users WHERE id = ?", nav
        )
        assert safe
        assert len(violations) == 0

    def test_violating_output(self):
        nav = NegativeSpaceNavigator()
        nav.add_hazard(Hazard(
            location="sql_injection",
            severity=1.0,
            hazard_type=HazardType.SECURITY,
        ))
        enforcer = ConservationEnforcer(strict=True)
        safe, violations = enforcer.check_output(
            "This looks like sql_injection vulnerability", nav
        )
        assert not safe
        assert len(violations) == 1
        assert violations[0]["severity"] == 1.0

    def test_strict_mode_raises(self):
        nav = NegativeSpaceNavigator()
        nav.add_hazard(Hazard(
            location="eval_exec",
            severity=0.9,
            hazard_type=HazardType.SECURITY,
        ))
        enforcer = ConservationEnforcer(strict=True)
        with pytest.raises(ValueError, match="Conservation violation"):
            enforcer.enforce("Use eval_exec here", nav)

    def test_non_strict_mode_warns(self):
        nav = NegativeSpaceNavigator()
        nav.add_hazard(Hazard(
            location="eval_exec",
            severity=0.9,
            hazard_type=HazardType.SECURITY,
        ))
        enforcer = ConservationEnforcer(strict=False)
        result = enforcer.enforce("Use eval_exec here", nav)
        assert "BOUNDARY WARNING" in result

    def test_check_point_safe(self):
        nav = NegativeSpaceNavigator()
        nav.add_hazard(Hazard(location=(0.0, 0.0), radius=1.0))
        enforcer = ConservationEnforcer()
        safe, clr = enforcer.check_point((5.0, 5.0), nav)
        assert safe
        assert clr > 0


class TestFluxBytecodeCompiler:
    def test_compile_empty(self):
        compiler = FluxBytecodeCompiler()
        bytecode = compiler.compile([])
        assert bytecode[:4] == b"FLUX"

    def test_compile_spatial_hazard(self):
        compiler = FluxBytecodeCompiler()
        hazards = [
            Hazard(location=(1.0, 2.0), radius=0.5, severity=0.9),
        ]
        bytecode = compiler.compile(hazards)
        assert bytecode[:4] == b"FLUX"
        assert len(bytecode) > 8

    def test_compile_semantic_hazard(self):
        compiler = FluxBytecodeCompiler()
        hazards = [
            Hazard(location="harmful_content", severity=1.0,
                    hazard_type=HazardType.CONTENT_VIOLATION),
        ]
        bytecode = compiler.compile(hazards)
        assert bytecode[:4] == b"FLUX"

    def test_decompile(self):
        compiler = FluxBytecodeCompiler()
        hazards = [
            Hazard(location=(1.0, 2.0), radius=0.5, severity=0.9),
            Hazard(location="bad_thing", severity=1.0),
        ]
        bytecode = compiler.compile(hazards, min_clearance=0.5)
        instructions = compiler.decompile(bytecode)
        assert len(instructions) >= 4  # CLEAR + CHECK + CHECK + ALL/ANY + RET
        ops = [i.opcode for i in instructions]
        assert "CHECK_CIRCLE" in ops
        assert "CHECK_LABEL" in ops
        assert "RET" in ops

    def test_roundtrip(self):
        compiler = FluxBytecodeCompiler()
        hazards = [
            Hazard(location=(0.0, 0.0), radius=1.0, severity=1.0),
        ]
        bytecode = compiler.compile(hazards)
        instructions = compiler.decompile(bytecode)
        # The check_circle instruction should contain the hazard data
        check_inst = next(i for i in instructions if i.opcode == "CHECK_CIRCLE")
        assert check_inst.operands[0] == [0.0, 0.0]
        assert check_inst.operands[1] == 1.0

    def test_mode_any_vs_all(self):
        compiler = FluxBytecodeCompiler()
        hazards = [Hazard(location=(0.0, 0.0), radius=1.0)]
        bc_all = compiler.compile(hazards, mode="all")
        bc_any = compiler.compile(hazards, mode="any")
        # They should differ in the ALL vs ANY instruction
        inst_all = compiler.decompile(bc_all)
        inst_any = compiler.decompile(bc_any)
        assert inst_all[-2].opcode == "ALL"
        assert inst_any[-2].opcode == "ANY"


class TestAIHarness:
    def test_create_harness(self):
        nav = NegativeSpaceNavigator()
        harness = AIHarness(nav)
        assert harness.navigator is nav

    def test_attach_enforcer(self):
        nav = NegativeSpaceNavigator()
        harness = AIHarness(nav)
        enforcer = harness.attach_conservation_enforcer(strict=True)
        assert enforcer in harness.enforcers
        assert enforcer.strict

    def test_govern_safe_output(self):
        nav = NegativeSpaceNavigator()
        nav.add_hazard(Hazard(location="bad_thing", severity=1.0))
        harness = AIHarness(nav)
        harness.attach_conservation_enforcer(strict=True)
        result = harness.govern_output("This is perfectly fine output")
        assert result == "This is perfectly fine output"

    def test_govern_unsafe_output(self):
        nav = NegativeSpaceNavigator()
        nav.add_hazard(Hazard(location="bad_thing", severity=1.0))
        harness = AIHarness(nav)
        harness.attach_conservation_enforcer(strict=True)
        with pytest.raises(ValueError):
            harness.govern_output("This contains bad_thing")

    def test_compile_boundaries(self):
        nav = NegativeSpaceNavigator()
        nav.add_hazard(Hazard(location=(0.0, 0.0), radius=1.0))
        harness = AIHarness(nav)
        bytecode = harness.compile_boundaries()
        assert bytecode[:4] == b"FLUX"

    def test_triangulate(self):
        nav1 = NegativeSpaceNavigator()
        nav1.add_hazard(Hazard(location=(0.0, 0.0), radius=1.0))

        nav2 = NegativeSpaceNavigator()
        nav2.add_hazard(Hazard(location=(5.0, 5.0), radius=1.0))

        harness = AIHarness(nav1)
        combined = harness.triangulate([nav2])
        assert len(combined.hazards) == 2

    def test_review_code_safe(self):
        nav = NegativeSpaceNavigator()
        nav.add_hazard(Hazard(
            location="sql_injection", severity=1.0,
            hazard_type=HazardType.SECURITY,
        ))
        harness = AIHarness(nav)
        result = harness.review_code("def add(a, b): return a + b")
        assert result["is_safe"]
        assert result["verdict"] == "safe passage"

    def test_review_code_unsafe(self):
        nav = NegativeSpaceNavigator()
        nav.add_hazard(Hazard(
            location="sql_injection", severity=1.0,
            hazard_type=HazardType.SECURITY,
        ))
        harness = AIHarness(nav)
        result = harness.review_code("x = sql_injection attack")
        assert not result["is_safe"]
        assert result["verdict"] == "hazardous route"
        assert len(result["violations"]) == 1
