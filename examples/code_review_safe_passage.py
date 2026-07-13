"""
Example: Code Review Safe Passage with skénna.

Traditional code review prescribes architecture: "Use pattern X here."
skénna-based review charts code hazards — patterns that sink projects —
and lets any code path through the safe space pass review.

The review doesn't prescribe architecture. It charts rocks.
"""

from skenna import NegativeSpaceNavigator, Hazard, HazardType, AIHarness


def main():
    # Set up the code review navigator
    reviewer = NegativeSpaceNavigator()

    # Chart code hazards — patterns that sink projects
    print("Charting code hazards...")
    reviewer.add_hazard(Hazard(
        location="sql_injection",
        severity=1.0,
        hazard_type=HazardType.SECURITY,
        label="SQL Injection",
    ))
    reviewer.add_hazard(Hazard(
        location="eval_exec",
        severity=0.9,
        hazard_type=HazardType.SECURITY,
        label="Code Injection (eval/exec)",
    ))
    reviewer.add_hazard(Hazard(
        location="hardcoded_secret",
        severity=1.0,
        hazard_type=HazardType.SECURITY,
        label="Hardcoded Secret",
    ))
    reviewer.add_hazard(Hazard(
        location="command_injection",
        severity=1.0,
        hazard_type=HazardType.SECURITY,
        label="Command Injection",
    ))
    reviewer.add_hazard(Hazard(
        location="path_traversal",
        severity=0.9,
        hazard_type=HazardType.SECURITY,
        label="Path Traversal",
    ))
    reviewer.add_hazard(Hazard(
        location="unbounded_recursion",
        severity=0.6,
        hazard_type=HazardType.RELIABILITY,
        label="Unbounded Recursion",
    ))

    harness = AIHarness(reviewer)

    # Code samples to review
    samples = {
        "clean_code": '''
def get_user(user_id: int) -> User:
    """Fetch user by ID using parameterized query."""
    return db.execute("SELECT * FROM users WHERE id = %s", (user_id,))
''',
        "vulnerable_code": '''
def get_user(user_id):
    # WARNING: potential sql_injection vulnerability
    query = f"SELECT * FROM users WHERE id = {user_id}"
    return db.execute(query)
''',
        "dangerous_code": '''
def run_command(user_input):
    # eval_exec pattern — extremely dangerous
    result = eval(user_input)
    return result
''',
    }

    print(f"\n{'='*60}")
    print("Code Review Results")
    print(f"{'='*60}")

    for name, code in samples.items():
        result = harness.review_code(code)
        verdict_emoji = "✅" if result["is_safe"] else "🚨"

        print(f"\n{verdict_emoji} {name}: {result['verdict']}")
        if result["violations"]:
            for v in result["violations"]:
                print(f"   ⚠️  {v['hazard']} (severity: {v['severity']})")
        else:
            print(f"   All clear — navigates safely through {result['hazards_checked']} hazard zones")

    # The point: we didn't prescribe HOW to write safe code.
    # We charted WHERE the unsafe patterns are. Any code that
    # stays in the safe space passes. The architecture is free.
    print(f"\n{'='*60}")
    print("The review charted rocks. It didn't prescribe architecture.")
    print("Any code that stays where the rocks aren't is safe passage.")


if __name__ == "__main__":
    main()
