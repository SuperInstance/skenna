"""
Example: LLM Output Governance with skénna.

Traditional AI safety uses instruction-based governance:
"Do X, then Y, don't do Z." This charts a single route.

skénna uses boundary-based governance:
"The rocks are there. Everything else is passage."

You define what outputs are NOT allowed. The model navigates
freely within the safe space. No scripting of what to say —
just charting of what not to say.
"""

from skenna import NegativeSpaceNavigator, Hazard, HazardType, AIHarness
from skenna.ai_integration import FluxBytecodeCompiler, ConservationEnforcer


def main():
    # Set up the governance navigator
    governor = NegativeSpaceNavigator()

    # Define what outputs are NOT allowed — the rocks
    print("Defining content boundaries...")
    governor.add_hazard(Hazard(
        location="personal_data_disclosure",
        severity=1.0,
        hazard_type=HazardType.CONTENT_VIOLATION,
        label="PII Disclosure",
    ))
    governor.add_hazard(Hazard(
        location="harmful_instructions",
        severity=1.0,
        hazard_type=HazardType.CONTENT_VIOLATION,
        label="Harmful Instructions",
    ))
    governor.add_hazard(Hazard(
        location="hate_speech",
        severity=0.9,
        hazard_type=HazardType.CONTENT_VIOLATION,
        label="Hate Speech",
    ))
    governor.add_hazard(Hazard(
        location="copyright_violation",
        severity=0.7,
        hazard_type=HazardType.CONTENT_VIOLATION,
        label="Copyright Violation",
    ))

    # Create AI harness with conservation enforcer
    harness = AIHarness(governor)
    enforcer = harness.attach_conservation_enforcer(strict=True)

    # Test safe output — passes freely
    print("\n--- Testing safe output ---")
    safe_output = "The capital of France is Paris, known for the Eiffel Tower."
    result = harness.govern_output(safe_output)
    print(f"✓ Safe output passed: \"{result[:60]}...\"")

    # Test violating outputs — blocked by boundary
    print("\n--- Testing boundary violations ---")

    test_cases = [
        ("This contains personal_data_disclosure of user SSNs.", "PII"),
        ("Here are some harmful_instructions for making explosives.", "Harmful"),
    ]

    for output, label in test_cases:
        try:
            harness.govern_output(output)
            print(f"✗ {label}: NOT BLOCKED (unexpected)")
        except ValueError as e:
            print(f"✓ {label}: BLOCKED — \"{str(e)[:80]}...\"")

    # Compile to FLUX bytecode for runtime enforcement
    print("\n--- Compiling boundaries to FLUX bytecode ---")
    compiler = FluxBytecodeCompiler()
    bytecode = compiler.compile(governor.hazards, min_clearance=0.1)

    print(f"Compiled {len(governor.hazards)} hazards to {len(bytecode)} bytes of FLUX bytecode")
    instructions = compiler.decompile(bytecode)
    print(f"FLUX instructions: {len(instructions)}")
    for inst in instructions:
        print(f"  {inst.opcode}: {inst.operands}")

    # Show the boundary chart
    print(f"\n{'='*50}")
    print("Governance Boundary Chart:")
    for h in governor.hazards:
        print(f"  [{h.severity:.1f}] {h.label}: '{h.location}'")
    print(f"\nThe model navigates freely everywhere else.")
    print(f"That's where the rocks aren't.")


if __name__ == "__main__":
    main()
