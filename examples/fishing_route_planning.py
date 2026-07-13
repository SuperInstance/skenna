"""
Example: Fishing Route Planning with skénna.

A fisherman navigates coastal waters to reach fishing grounds.
He doesn't plan toward the grounds — he stays where the rocks aren't.

This example uses the marine navigation API to chart hazards
and plan a safe route through coastal waters.
"""

from skenna import NegativeSpaceNavigator, Hazard, HazardType
from skenna.space import BoundingBox


def main():
    # Initialize the navigator with charted territory
    navigator = NegativeSpaceNavigator(
        bounds=BoundingBox(mins=(48.0, -123.5), maxs=(49.0, -122.5))
    )

    # Chart the rocks — that's all the fisherman does
    print("Charting hazards...")
    navigator.add_hazard(Hazard(
        location=(48.5, -123.0),
        radius=0.05,
        severity=1.0,
        hazard_type=HazardType.REEF,
        label="Discovery Reef",
    ))
    navigator.add_hazard(Hazard(
        location=(48.6, -122.9),
        radius=0.04,
        severity=0.8,
        hazard_type=HazardType.SHOAL,
        label="Middle Shoal",
    ))
    navigator.add_hazard(Hazard(
        location=(48.4, -122.8),
        radius=0.03,
        severity=0.9,
        hazard_type=HazardType.WRECK,
        label="Sunken Tug",
    ))

    # Chart the safe space — where the rocks aren't
    safe_space = navigator.chart_safe_space()
    print(f"\nSafe waters: {safe_space.coverage_fraction():.1%} of charted territory")
    print(f"Excluded zones: {len(safe_space.excluded_regions)}")

    # Navigate from harbor to fishing grounds
    print("\nPlanning route from harbor to fishing grounds...")
    path = navigator.navigate(
        start=(48.3, -123.2),   # Harbor
        goal=(48.8, -122.7),    # Fishing grounds
    )

    print(f"\nRoute summary:")
    print(f"  Waypoints:     {len(path.waypoints)}")
    print(f"  Distance:      {path.total_distance:.3f}")
    print(f"  Min clearance: {path.min_clearance:.3f}")
    print(f"  Safety score:  {path.safety_score:.3f}")
    print(f"  First 5 waypoints:")
    for i, wp in enumerate(path.waypoints[:5]):
        print(f"    {i}: ({wp[0]:.4f}, {wp[1]:.4f})")
    if len(path.waypoints) > 5:
        print(f"    ... ({len(path.waypoints) - 5} more)")

    # Check safety at each waypoint
    print(f"\nSafety at each waypoint:")
    for i, wp in enumerate(path.waypoints[:5]):
        score = navigator.safety_score(wp)
        clearance = navigator.clearance_at(wp)
        print(f"  WP {i}: safety={score:.3f}, clearance={clearance:.3f}")

    print(f"\n{'='*50}")
    print(navigator.summary())


if __name__ == "__main__":
    main()
