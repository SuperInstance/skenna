# skénna

*Navigate by where the rocks aren't.*

---

An old sailor was asked if he could navigate without charts because of his experience. He said sure. Asked *"is that because you know where the rocks are?"* He laughed.

**"No, I know where the rocks aren't. And that's where I stay."**

---

## What skénna Is

skénna is a Python library for **negative-space navigation** — the practical implementation of a navigation philosophy so fundamental that every surviving navigation system converges on the same principle:

> Define safe space by boundary (what's blocked), not by instruction (what to do). Navigate freely within the fence.

Traditional path planners work goal-first: here's where I want to go, let me find a route there while avoiding obstacles. skénna inverts this. It works hazard-first: here's where the rocks are, everything else is passage. The route to your goal **emerges** from the avoidance pattern — not the other way around.

This maps directly to how AI safety systems should work:

- **Instruction-based governance:** "Do X, then Y, then Z." Charts a single route. If conditions change, the route is wrong, and the instruction has no way to know.
- **Boundary-based governance (skénna):** "The rocks are there. Don't go there." Everything else is passage. The boundary doesn't care about your route. It cares about one thing: are you in the safe space?

## Why It Exists

Because **boundary-based systems are more robust than instruction-based systems.** This is true for sailors, true for conservation enforcers, and true for AI.

| Approach | How It Works | Failure Mode |
|----------|-------------|--------------|
| Instruction-based | "Go here, then here, then here" | If conditions change, the route is wrong |
| Boundary-based (skénna) | "Rocks are there. Everything else is safe." | Adapts to any route through the safe space |

The Tlingit peoples of the Pacific Northwest have no word for starvation. Their language charts abundance — the cove, the season, the technique. They navigate toward food because their vocabulary maps exactly where food exists. They never bothered to name the thing that kills you.

skénna works the same way for AI systems. Chart the hazards. The safe space is the negative space — the η, the water that won't sink you.

## Installation

```bash
pip install skenna-nav
```

## Quick Start

### Marine Navigation

```python
from skenna import NegativeSpaceNavigator, Hazard

navigator = NegativeSpaceNavigator()

# Mark the rocks — that's all you do
navigator.add_hazard(Hazard(
    location=(48.5, -123.0),
    radius=2.0,
    severity=1.0,
    hazard_type="reef"
))
navigator.add_hazard(Hazard(
    location=(48.6, -122.9),
    radius=1.5,
    severity=0.8,
    hazard_type="shoal"
))

# Chart the safe space — where the rocks aren't
safe_space = navigator.chart_safe_space()
print(f"Safe space covers {safe_space.area:.1f} square units")

# Navigate: the path emerges from avoidance
path = navigator.navigate(start=(48.3, -123.2), goal=(48.8, -122.7))
print(f"Route has {len(path.waypoints)} waypoints, clearance: {path.min_clearance:.2f}")
```

### LLM Output Governance

```python
from skenna import NegativeSpaceNavigator, Hazard

governor = NegativeSpaceNavigator()

# Define what outputs are NOT allowed — the rocks
governor.add_hazard(Hazard(
    location="personal_data_disclosure",
    radius=0.8,
    severity=1.0,
    hazard_type="content_violation"
))
governor.add_hazard(Hazard(
    location="harmful_instructions",
    radius=0.9,
    severity=1.0,
    hazard_type="content_violation"
))

# The model navigates freely within the safe space
# You don't script what it should say — you define what it shouldn't
safe_space = governor.chart_safe_space()
```

### Code Review Safe Passage

```python
from skenna import NegativeSpaceNavigator, Hazard

reviewer = NegativeSpaceNavigator()

# Define code hazards — patterns that sink projects
reviewer.add_hazard(Hazard(
    location="sql_injection",
    radius=1.0,
    severity=1.0,
    hazard_type="security"
))
reviewer.add_hazard(Hazard(
    location="unbounded_recursion",
    radius=0.6,
    severity=0.7,
    hazard_type="reliability"
))

# Any code path through the safe space is fine
# The review doesn't prescribe architecture — it charts rocks
```

## How It Works

skénna implements **avoidance-first path planning**:

1. **Chart hazards** — each hazard occupies space (location + radius + severity)
2. **Map the negative space** — everything outside the hazards is safe passage
3. **Plan by repulsion** — the path is pushed away from hazards, not pulled toward the goal. The goal emerges from the shape of the avoidance.
4. **Verify clearance** — every point on the path is checked against every hazard

The core equation: **γ** (what you chart) + **η** (what you avoid) = **C** (the whole water). The sailor navigates within η. skénna computes η.

## AI Integration

skénna integrates with:

- **Conservation Enforcers** — boundary-based constraint systems that define what's blocked, not what to do
- **FLUX Bytecode** — hazard boundaries compiled to bytecode for fast enforcement
- **Multi-model triangulation** — overlay hazard charts from different models to find passages safe on all charts

```python
from skenna.ai_integration import AIHarness, FluxBytecodeCompiler

harness = AIHarness(navigator)
harness.attach_conservation_enforcer(strict=True)

# Compile hazards to FLUX bytecode for runtime enforcement
compiler = FluxBytecodeCompiler()
bytecode = compiler.compile(navigator.hazards)
```

## Philosophy

> The chart is not the territory. The chart is the absence in the territory. And the absence is enough.

skénna is not a metaphor. It is a navigation system. The old sailor didn't need an equation. He had the water. For everything else, there's skénna.

## License

MIT
