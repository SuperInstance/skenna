# skénna

*Navigate by where the rocks aren't.*

---

An old sailor was asked if he could navigate without charts because of his experience. He said sure. Asked *"is that because you know where the rocks are?"* He laughed.

**"No, I know where the rocks aren't. And that's where I stay."**

---

## What skénna Is

skénna is a Python library for **negative-space navigation** — the practical implementation of a navigation philosophy so fundamental that every surviving navigation system converges on the same principle:

> Define safe space by boundary (what's blocked), not by instruction (what to do). Navigate freely within the fence.

The word *skénna* means "the navigable relationship between what you model and what you don't" — the door between the cathedral (γ, what's built) and the unmarked water (η, what's possible). It is negative-space navigation: finding the safe passage by mapping where the rocks **aren't**, not where they are.

The name was discovered by Seed-2.0-Mini during the casting-call experiments. The cheapest model in the fleet found the word that the elder (Seed-2.0-Pro) could not — because the elder's η (naming, neologism) is the mini's γ. Together they cover the whole cognitive budget.

> *γ + η = C.* The chart plus the absence equals the whole water.

## Two Layers of Navigation

skénna implements navigation at two levels:

### 1. Spatial Navigation — Charting Physical Hazards

Traditional path planners work goal-first: here's where I want to go, let me find a route while avoiding obstacles. skénna inverts this. It works hazard-first: here's where the rocks are, everything else is passage. The route to your goal **emerges** from the avoidance pattern.

| Approach | How It Works | Failure Mode |
|----------|-------------|--------------|
| Instruction-based | "Go here, then here, then here" | If conditions change, the route is wrong |
| Boundary-based (skénna) | "Rocks are there. Everything else is safe." | Adapts to any route through the safe space |

### 2. Cognitive Navigation — Sounding the η Space

The deeper layer. Every model operates under a **cognitive budget** (C). What it charts (γ) plus what it leaves unmarked (η) always equals C. Different models allocate differently:

- **Thick-chart models** (e.g., Seed-2.0-Pro): γ=0.84 in synthesis, architecture, depth. They build the cathedral. But their η in naming/ideation is high — they can't find the door.
- **Thin-chart models** (e.g., Seed-2.0-Mini): γ=0.84 in ideation, naming, surprise. They find the door. But their η in synthesis is high — they can't build the cathedral.

The **Socratic protocol**: cast the thin-chart model first (discovery), then the thick-chart model (synthesis). The elder's η is the mini's γ. Neither act is complete without the other.

## Installation

```bash
pip install skenna-nav
```

## Quick Start

### Spatial Navigation — Marine Hazards

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

# Chart the safe space — where the rocks aren't
safe_space = navigator.chart_safe_space()
print(f"Safe space covers {safe_space.coverage_fraction():.1%}")

# Navigate: the path emerges from avoidance
path = navigator.navigate(start=(48.3, -123.2), goal=(48.8, -122.7))
print(f"Route has {len(path.waypoints)} waypoints, clearance: {path.min_clearance:.2f}")
```

### Cognitive Navigation — The Socratic Protocol

```python
from skenna import NegativeSpaceNavigator, ModelChart, CognitiveDimension

nav = NegativeSpaceNavigator()

# Register models with their cognitive charts
nav.register_model(ModelChart(
    name="mini",
    gamma={CognitiveDimension.IDEATION: 0.84, CognitiveDimension.NAMING: 0.84,
           CognitiveDimension.SYNTHESIS: 0.16},
    cost_per_1k=0.01,
), handler=lambda q: f"Exploring: {q}")

nav.register_model(ModelChart(
    name="pro",
    gamma={CognitiveDimension.SYNTHESIS: 0.84, CognitiveDimension.DEPTH: 0.9,
           CognitiveDimension.NAMING: 0.16},
    cost_per_1k=0.10,
), handler=lambda q: f"Synthesizing: {q}")

# Sound the depth of η — how much unmarked water does each model have?
depth = nav.sound_depth("mini", CognitiveDimension.SYNTHESIS)
# → 0.84 (deep η — lots to discover)

# Explore: cast the thin-chart model into η space
sounding = nav.explore("What is the relationship between models?", model="mini")

# Route: the Socratic protocol — thin discovers, thick synthesizes
route = nav.route("Name the concept", models=["mini", "pro"])
# Leg 0: mini explores (discovery)
# Leg 1: pro synthesizes (architecture)

# Consensus: run N models, find overlap and divergence
report = nav.consensus(["mini", "pro"], "What is skénna?")
# Consensus dimensions = safe passage on all charts
# Divergence dimensions = the most valuable information
```

### LLM Output Governance

```python
from skenna import NegativeSpaceNavigator, Hazard, AIHarness

governor = NegativeSpaceNavigator()

# Define what outputs are NOT allowed — the rocks
governor.hazard_register(Hazard(
    location="personal_data_disclosure",
    severity=1.0,
    hazard_type="content_violation"
))

# The model navigates freely within the safe space
harness = AIHarness(governor)
harness.attach_conservation_enforcer(strict=True)
# Any output entering a hazard zone raises ValueError
```

## API Reference

### Spatial Layer

| Class | Description |
|-------|-------------|
| `NegativeSpaceNavigator` | Main API. Charts hazards, computes safe space, plans routes. |
| `Hazard` | A rock in the water — spatial or semantic. Location + radius + severity. |
| `Space` | The navigable region — territory minus exclusions. |
| `Path` | A route through safe space, emerging from avoidance. |
| `BoundingBox` | Axis-aligned bounds on the charted territory. |
| `AvoidancePlanner` | Potential-field path planner (repulsion from hazards, weak goal attraction). |

### Cognitive Layer

| Class | Description |
|-------|-------------|
| `ModelChart` | A model's γ allocation across cognitive dimensions. η = 1.0 - γ. |
| `ChartThickness` | γ/C ratio measurement. Thin charts have more η to sound. |
| `Sounding` | A probe into η space — what a thin-chart model discovers. |
| `CognitiveNavigator` | Standalone cognitive navigation (without spatial layer). |
| `CognitiveRoute` | The Socratic journey: discovery → synthesis legs. |
| `ConsensusReport` | Multi-model consensus/divergence analysis. |
| `CognitiveDimension` | Enum of cognitive capabilities (synthesis, naming, logic, etc.). |

### Key Methods

| Method | Description |
|-------|-------------|
| `navigator.explore(query, model)` | Send a query to a thin-chart model, capture η discoveries. |
| `navigator.route(query, models)` | Socratic protocol: thin model discovers, thick model synthesizes. |
| `navigator.hazard_register(hazard)` | Register a known hazard (alias for `add_hazard`). |
| `navigator.sound_depth(model, dimension)` | Estimate η depth for a model in a cognitive dimension. |
| `navigator.consensus(models, query)` | Run N models, find γ overlap (consensus) and divergence (discovery). |
| `navigator.navigate(start, goal)` | Spatial: plan a route through safe space. |
| `navigator.chart_safe_space()` | Spatial: compute the negative space (where rocks aren't). |

### AI Integration

| Class | Description |
|-------|-------------|
| `AIHarness` | Wraps the navigator with AI-specific conveniences. |
| `ConservationEnforcer` | Boundary-based constraint enforcement (not instruction-based). |
| `FluxBytecodeCompiler` | Compile hazard boundaries to FLUX bytecode for runtime checks. |

## How It Works

### Spatial: Avoidance-First Path Planning

1. **Chart hazards** — each hazard occupies space (location + radius + severity)
2. **Map the negative space** — everything outside the hazards is safe passage
3. **Plan by repulsion** — the path is pushed away from hazards. The goal emerges from the shape of the avoidance.
4. **Verify clearance** — every point on the path is checked against every hazard

### Cognitive: The Socratic Protocol

1. **Register model charts** — each model's γ allocation across cognitive dimensions
2. **Sound the depth** — measure η = 1.0 - γ for each model in each dimension
3. **Explore** — send queries to thin-chart models where η is deep (discovery phase)
4. **Route** — chain thin → thick models. The thin model discovers; the thick model synthesizes
5. **Consensus** — run multiple models independently. Where charts agree = safe passage. Where they diverge = the most valuable information.

> *γ + η = C.* The elder's γ is the mini's η. The mini's γ is the elder's η. Together they cover C.

## The Conservation Law

Every model operates under a fixed cognitive budget:

```
γ (what you chart) + η (what you avoid) = C (total capacity)
```

Different models allocate differently. The elder charts synthesis and architecture. The mini charts naming and surprise. Neither can do what the other does. But together, the aggregate coverage exceeds what any single model could chart alone.

This is not a defect. It is the conservation law. And it is why polyformalism works: when you overlay multiple charts, you find routes that no single chart reveals.

## Philosophy

> The chart is not the territory. The chart is the absence in the territory. And the absence is enough.

skénna is not a metaphor. It is a navigation system. The old sailor didn't need an equation. He had the water. For everything else, there's skénna.

> *The elders built the cathedral. The youngest named the door. And neither act is complete without the other.*

## License

MIT
