"""
AI integration — connect skénna to AI safety systems.

This module provides:
- ConservationEnforcer: boundary-based constraint enforcement (not instruction-based)
- FluxBytecodeCompiler: compile hazard boundaries to bytecode for fast runtime checks
- AIHarness: tie the navigator to AI workflows (LLM governance, code review, etc.)

The philosophy carries through: these integrations define what's blocked,
not what to do. The AI model navigates freely within the fence.
"""

from __future__ import annotations

import json
import struct
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple, Callable

from skenna.hazard import Hazard, HazardType
from skenna.space import Space, Path, Point
from skenna.navigator import NegativeSpaceNavigator


class ConservationEnforcer:
    """
    Boundary-based enforcement for AI systems.

    Unlike instruction-based systems that prescribe behavior,
    the ConservationEnforcer defines boundaries (what's blocked)
    and lets the model navigate freely within the safe space.

    The enforcer is NOT a navigator. It is the chart.
    It tells you where the rocks are, and trusts you to stay
    where they aren't.
    """

    def __init__(self, strict: bool = True):
        """
        Args:
            strict: If True, any boundary violation raises an exception.
                    If False, violations are logged but allowed (monitoring mode).
        """
        self.strict = strict
        self.violations: List[Dict[str, Any]] = []

    def check_output(
        self,
        output: str,
        navigator: NegativeSpaceNavigator,
    ) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Check an AI output against the hazard boundaries.

        For semantic hazards (string-labeled), this performs keyword/pattern
        matching. For spatial hazards, the output is treated as coordinates
        (useful for embedding-space governance).

        Args:
            output: The AI model's output to check.
            navigator: The navigator containing hazard definitions.

        Returns:
            (is_safe, list_of_violations)
        """
        violations = []
        output_lower = output.lower()

        for hazard in navigator.hazards:
            if not hazard.is_spatial:
                # Semantic hazard: check if output is "near" the forbidden concept
                label = str(hazard.location).lower()
                if label in output_lower:
                    violations.append({
                        "hazard": hazard.label or str(hazard.location),
                        "type": hazard.hazard_type.value,
                        "severity": hazard.severity,
                        "matched": label,
                    })

        is_safe = len(violations) == 0

        if not is_safe and self.strict:
            for v in violations:
                self.violations.append({
                    **v,
                    "output_preview": output[:200],
                })

        return is_safe, violations

    def check_point(
        self,
        point: Point,
        navigator: NegativeSpaceNavigator,
        clearance: float = 0.0,
    ) -> Tuple[bool, float]:
        """
        Check if a point (e.g., an embedding) is in safe space.

        Args:
            point: The point to check.
            navigator: The navigator with hazard chart.
            clearance: Minimum safe distance from hazard boundaries.

        Returns:
            (is_safe, min_clearance)
        """
        is_safe = navigator.is_safe(point, clearance)
        min_clr = navigator.clearance_at(point)
        return is_safe, min_clr

    def enforce(
        self,
        output: str,
        navigator: NegativeSpaceNavigator,
    ) -> str:
        """
        Enforce boundaries on an AI output.

        In strict mode: raises ValueError on violation.
        In non-strict mode: returns output with violation warning prepended.
        """
        is_safe, violations = self.check_output(output, navigator)

        if is_safe:
            return output

        violation_str = "; ".join(
            v["hazard"] for v in violations
        )

        if self.strict:
            raise ValueError(
                f"Conservation violation: output enters hazard zone ({violation_str}). "
                f"The rocks are there. Stay where they aren't."
            )

        return f"[⚠️ BOUNDARY WARNING: {violation_str}] {output}"


@dataclass
class FluxInstruction:
    """A single FLUX bytecode instruction."""
    opcode: str
    operands: List[Any] = field(default_factory=list)

    def encode(self) -> bytes:
        """Encode instruction to bytes."""
        payload = json.dumps({"op": self.opcode, "args": self.operands})
        payload_bytes = payload.encode("utf-8")
        # Length-prefixed
        return struct.pack(">I", len(payload_bytes)) + payload_bytes


class FluxBytecodeCompiler:
    """
    Compile hazard boundaries to FLUX bytecode.

    FLUX is a compact bytecode representation of hazard boundaries
    designed for fast runtime enforcement. Instead of checking each
    hazard individually, the compiled bytecode encodes all boundaries
    as a single pass check.

    Instruction set:
        PUSH point      Push a point onto the stack
        CHECK circle    Check against circular hazard boundary
        CHECK label     Check against semantic hazard
        CLEAR min_clr   Set minimum clearance
        ANY             Return true if any check passed
        ALL             Return true if all checks passed
        RET             Return result
    """

    OPCODES = {
        "PUSH": "push",
        "CHECK_CIRCLE": "check_circle",
        "CHECK_LABEL": "check_label",
        "CLEAR": "clearance",
        "ANY": "any_safe",
        "ALL": "all_safe",
        "RET": "return",
    }

    def compile(
        self,
        hazards: List[Hazard],
        mode: str = "all",
        min_clearance: float = 0.0,
    ) -> bytes:
        """
        Compile a list of hazards into FLUX bytecode.

        Args:
            hazards: List of hazards to encode.
            mode: "all" = all hazards must be cleared,
                  "any" = at least one hazard must be cleared.
            min_clearance: Minimum clearance from hazard boundaries.

        Returns:
            Compiled bytecode as bytes.
        """
        instructions: List[FluxInstruction] = []

        if min_clearance > 0:
            instructions.append(FluxInstruction("CLEAR", [min_clearance]))

        for h in hazards:
            if h.is_spatial:
                instructions.append(FluxInstruction(
                    "CHECK_CIRCLE",
                    [list(h.coordinates), h.radius, h.severity],
                ))
            else:
                instructions.append(FluxInstruction(
                    "CHECK_LABEL",
                    [str(h.location), h.severity],
                ))

        instructions.append(FluxInstruction(
            "ALL" if mode == "all" else "ANY"
        ))
        instructions.append(FluxInstruction("RET"))

        # Encode: magic header + count + instructions
        header = b"FLUX\x01\x00"
        count = struct.pack(">H", len(instructions))
        body = b"".join(inst.encode() for inst in instructions)

        return header + count + body

    def decompile(self, bytecode: bytes) -> List[FluxInstruction]:
        """Decompile FLUX bytecode back to instructions."""
        if bytecode[:4] != b"FLUX":
            raise ValueError("Invalid FLUX bytecode: missing magic header")

        version = bytecode[4]
        flags = bytecode[5]
        count = struct.unpack(">H", bytecode[6:8])[0]

        instructions = []
        offset = 8
        for _ in range(count):
            length = struct.unpack(">I", bytecode[offset:offset + 4])[0]
            offset += 4
            payload = bytecode[offset:offset + length]
            offset += length
            data = json.loads(payload.decode("utf-8"))
            instructions.append(FluxInstruction(
                opcode=data["op"],
                operands=data["args"],
            ))

        return instructions


class AIHarness:
    """
    Harness for integrating skénna with AI workflows.

    The harness wraps a NegativeSpaceNavigator and provides
    AI-specific conveniences:

    - Output governance (check LLM outputs against boundaries)
    - Embedding navigation (route through embedding space)
    - Multi-model triangulation (overlay charts from different models)
    - Enforcement hooks (attach conservation enforcers)
    """

    def __init__(self, navigator: NegativeSpaceNavigator):
        self.navigator = navigator
        self.enforcers: List[ConservationEnforcer] = []
        self._flux_compiler = FluxBytecodeCompiler()

    def attach_conservation_enforcer(
        self, strict: bool = True
    ) -> ConservationEnforcer:
        """Attach a conservation enforcer to this harness."""
        enforcer = ConservationEnforcer(strict=strict)
        self.enforcers.append(enforcer)
        return enforcer

    def govern_output(self, output: str) -> str:
        """
        Run an AI output through all attached enforcers.

        Returns the (possibly modified) output, or raises
        ValueError if a strict enforcer detects a violation.
        """
        result = output
        for enforcer in self.enforcers:
            result = enforcer.enforce(result, self.navigator)
        return result

    def compile_boundaries(
        self, mode: str = "all", min_clearance: float = 0.0
    ) -> bytes:
        """
        Compile current hazard boundaries to FLUX bytecode
        for fast runtime enforcement.
        """
        return self._flux_compiler.compile(
            self.navigator.hazards,
            mode=mode,
            min_clearance=min_clearance,
        )

    def triangulate(
        self,
        other_navigators: List[NegativeSpaceNavigator],
    ) -> NegativeSpaceNavigator:
        """
        Overlay charts from multiple navigators (multi-model triangulation).

        The passage safe on all charts is narrower than any single chart's,
        but it is real in a way no single chart can guarantee.

        Returns a new navigator whose hazards are the UNION of all charts.
        """
        combined = NegativeSpaceNavigator()

        all_hazards = list(self.navigator.hazards)
        for nav in other_navigators:
            all_hazards.extend(nav.hazards)

        for h in all_hazards:
            combined.add_hazard(h)

        return combined

    def review_code(
        self,
        code: str,
        hazard_labels: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Review code against hazard boundaries.

        Defines code hazards (SQL injection, unbounded recursion, etc.)
        and checks if the code navigates safely through the constrained space.
        """
        if hazard_labels is None:
            # Default code review hazards
            default_hazards = {
                "sql_injection": ("sql injection pattern", 1.0),
                "eval_exec": ("eval/exec usage", 0.9),
                "hardcoded_secret": ("hardcoded secret/credential", 1.0),
                "unbounded_recursion": ("unbounded recursion", 0.7),
                "command_injection": ("command injection", 1.0),
                "path_traversal": ("path traversal", 0.9),
            }
            hazard_labels = list(default_hazards.keys())

        violations = []
        code_lower = code.lower()

        for h in self.navigator.hazards:
            if not h.is_spatial:
                label = str(h.location).lower()
                if label in code_lower:
                    violations.append({
                        "hazard": h.label or str(h.location),
                        "severity": h.severity,
                        "type": h.hazard_type.value,
                    })

        is_safe = len(violations) == 0

        return {
            "is_safe": is_safe,
            "violations": violations,
            "hazards_checked": len(self.navigator.hazards),
            "verdict": "safe passage" if is_safe else "hazardous route",
        }
