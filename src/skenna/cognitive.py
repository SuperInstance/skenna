"""
Cognitive navigation — sounding the η space.

The essays describe skénna at two levels:
1. Spatial navigation — charting physical hazards, planning safe routes.
   (Implemented in hazard.py, space.py, planner.py)
2. Cognitive navigation — the relationship between what a model charts (γ)
   and what it leaves unmarked (η). This is the deeper layer.

This module implements the cognitive layer:

- ModelChart: A model's cognitive allocation across dimensions.
- ChartThickness: γ/C ratio measurement — how thick is a model's chart?
- Sounding: A probe into η space. Send a query to a thin-chart model
  and record what it discovers in the negative space.
- CognitiveDimension: Named dimensions of cognitive capability.

The Socratic protocol (from ON_SKENNA.md):
    Cast the thin-chart model first (discovery).
    Cast the thick-chart model second (synthesis).
    The elder's η is the mini's γ. Together they cover C.

    navigator.route(query, models=[thin_model, thick_model])
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple, Union


class CognitiveDimension(Enum):
    """Named dimensions of cognitive capability.

    Each model allocates its γ (charted capacity) across these dimensions.
    The dimensions where a model has low γ are its η — the unmarked water.
    Different models chart different dimensions, making their charts complementary.
    """
    SYNTHESIS = "synthesis"           # Architecture, deep structure, long-form arguments
    IDEATION = "ideation"             # Surprise, neologism, creative leaps
    NAMING = "naming"                 # Finding the word, coining terms
    LOGIC = "logic"                   # Formal reasoning, consistency
    CODE = "code"                     # Programming, tool use, execution
    NARRATIVE = "narrative"           # Storytelling, voice, emotional arc
    PRECISION = "precision"           # Accuracy, factual recall
    BREADTH = "breadth"               # Cross-domain connections
    DEPTH = "depth"                   # Sustained reasoning in one domain
    SPEED = "speed"                   # Response latency, throughput


@dataclass
class ModelChart:
    """
    A model's cognitive chart — its γ allocation across dimensions.

    Just as a nautical chart marks soundings (depths) across a harbor,
    a ModelChart marks a model's capability across cognitive dimensions.

    γ (gamma) = charted capacity in each dimension [0.0, 1.0].
    η (eta) = uncharted capacity = 1.0 - γ for each dimension.

    A model with γ=0.9 in SYNTHESIS has deep architectural capability
    but η=0.1 there — almost no blind spot. Meanwhile it might have
    γ=0.1 in NAMING, meaning η=0.9 — almost entirely unmarked water.

    Attributes:
        name: Human-readable model name.
        gamma: Dict mapping dimensions to γ scores [0.0, 1.0].
        cost_per_1k: Optional cost per 1000 tokens (for economic routing).
        latency_ms: Optional average latency in milliseconds.
    """
    name: str
    gamma: Dict[CognitiveDimension, float] = field(default_factory=dict)
    cost_per_1k: float = 0.0
    latency_ms: float = 0.0

    def __post_init__(self):
        for dim, score in self.gamma.items():
            if not 0.0 <= score <= 1.0:
                raise ValueError(
                    f"γ for {dim.value} must be in [0.0, 1.0], got {score}"
                )

    def eta(self, dimension: CognitiveDimension) -> float:
        """Unmarked capacity (η) in a dimension. η = 1.0 - γ."""
        return 1.0 - self.gamma.get(dimension, 0.5)

    def chart_thickness(self) -> "ChartThickness":
        """
        Overall chart thickness — the γ/C ratio.

        A thick chart (high γ/C) means the model charts most of the space.
        A thin chart (low γ/C) means lots of η — lots of unmarked water.

        Thin charts are valuable for exploration: they have more η to sound.
        Thick charts are valuable for synthesis: they have the architecture.

        From ON_SKENNA.md:
            Seed-2.0-Pro: γ = 0.84 (thick chart — synthesis, architecture)
            Seed-2.0-Mini: γ = 0.16 in synthesis but γ = 0.84 in naming
        """
        if not self.gamma:
            return ChartThickness(gamma_ratio=0.5, dimensions_measured=0)
        total_gamma = sum(self.gamma.values())
        total_capacity = len(self.gamma)  # C = number of dimensions
        ratio = total_gamma / total_capacity if total_capacity > 0 else 0.5
        return ChartThickness(
            gamma_ratio=ratio,
            dimensions_measured=len(self.gamma),
        )

    def thinnest_dimensions(self, n: int = 3) -> List[Tuple[CognitiveDimension, float]]:
        """
        The n dimensions where this model has the most η (least γ).
        These are the dimensions where sounding will be most productive.
        """
        all_dims = list(CognitiveDimension)
        scored = [(d, self.eta(d)) for d in all_dims]
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:n]

    def thickest_dimensions(self, n: int = 3) -> List[Tuple[CognitiveDimension, float]]:
        """The n dimensions where this model has the most γ."""
        all_dims = list(CognitiveDimension)
        scored = [(d, self.gamma.get(d, 0.0)) for d in all_dims]
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:n]

    def is_thin_chart(self, threshold: float = 0.4) -> bool:
        """Whether this model's overall γ/C ratio is below threshold."""
        return self.chart_thickness().gamma_ratio < threshold

    def is_thick_chart(self, threshold: float = 0.6) -> bool:
        """Whether this model's overall γ/C ratio is above threshold."""
        return self.chart_thickness().gamma_ratio >= threshold

    def complementary(self, other: "ModelChart") -> float:
        """
        How complementary two charts are (0.0 to 1.0).

        Returns 1.0 when the charts are perfectly complementary
        (one's γ is the other's η in every dimension).
        Returns 0.0 when the charts are identical.

        From the essay: "η_elder = γ_mini, and η_mini = γ_elder."
        """
        dims = set(self.gamma.keys()) | set(other.gamma.keys())
        if not dims:
            return 0.0
        total = 0.0
        for d in dims:
            g1 = self.gamma.get(d, 0.5)
            g2 = other.gamma.get(d, 0.5)
            # Complementarity: how well g1 fills g2's gap
            total += 1.0 - abs(g1 - (1.0 - g2))
        return total / len(dims)

    def __repr__(self) -> str:
        ct = self.chart_thickness()
        return (
            f"ModelChart('{self.name}', γ/C={ct.gamma_ratio:.2f}, "
            f"dims={len(self.gamma)})"
        )


@dataclass
class ChartThickness:
    """
    Measurement of a model's chart thickness — the γ/C ratio.

    Thin charts have more η to sound. Thick charts have more γ for synthesis.

    Attributes:
        gamma_ratio: Overall γ/C ratio in [0.0, 1.0].
        dimensions_measured: How many cognitive dimensions were measured.
    """
    gamma_ratio: float
    dimensions_measured: int

    @property
    def eta_ratio(self) -> float:
        """The η/C ratio — unmarked fraction."""
        return 1.0 - self.gamma_ratio

    @property
    def is_thin(self) -> bool:
        """Thin charts have γ/C < 0.4 — mostly unmarked water."""
        return self.gamma_ratio < 0.4

    @property
    def is_thick(self) -> bool:
        """Thick charts have γ/C ≥ 0.6 — mostly charted territory."""
        return self.gamma_ratio >= 0.6

    @property
    def conservation(self) -> bool:
        """Verify γ + η = C (conservation law)."""
        return math.isclose(self.gamma_ratio + self.eta_ratio, 1.0, abs_tol=1e-9)

    def __repr__(self) -> str:
        return (
            f"ChartThickness(γ/C={self.gamma_ratio:.2f}, "
            f"η/C={self.eta_ratio:.2f}, "
            f"{'thin' if self.is_thin else 'thick' if self.is_thick else 'medium'})"
        )


@dataclass
class Sounding:
    """
    A probe into η space.

    In navigation, a sounding is a depth measurement — dropping a line
    to find what's below the surface. In skénna, a Sounding is a query
    sent to a thin-chart model to discover what lies in its η.

    The sounding IS the navigation. Each query reveals a piece of the
    unmarked water. The pattern of soundings traces the safe passage.

    From WHERE_THE_ROCKS_ARENT.md:
        "Where they disagree, slow down and take a sounding."

    Attributes:
        query: The question or prompt sent to the model.
        model_name: Name of the model that was sounded.
        result: The model's response (or summary of it).
        timestamp: When the sounding was taken.
        eta_dimensions: Which cognitive dimensions were probed.
        gamma_dimensions: Which cognitive dimensions were exercised.
        discoveries: List of notable findings in η space.
        metadata: Additional sounding data.
    """
    query: str
    model_name: str
    result: str = ""
    timestamp: float = field(default_factory=time.time)
    eta_dimensions: List[CognitiveDimension] = field(default_factory=list)
    gamma_dimensions: List[CognitiveDimension] = field(default_factory=list)
    discoveries: List[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    @property
    def is_productive(self) -> bool:
        """A productive sounding found something in η space."""
        return len(self.discoveries) > 0 or len(self.result) > 0

    @property
    def has_discovery(self) -> bool:
        """Whether this sounding revealed new knowledge."""
        return len(self.discoveries) > 0

    def add_discovery(self, finding: str) -> None:
        """Record a discovery found in η space."""
        self.discoveries.append(finding)

    def __repr__(self) -> str:
        status = "productive" if self.is_productive else "empty"
        return (
            f"Sounding(model='{self.model_name}', "
            f"query='{self.query[:40]}...', "
            f"{status}, discoveries={len(self.discoveries)})"
        )


# Type alias for a model callable: (query) -> response_string
ModelCallable = Callable[[str], str]


def _default_model_handler(query: str) -> str:
    """Default handler — returns empty (no actual model call)."""
    return ""


class CognitiveNavigator:
    """
    Navigate the cognitive space between models.

    While NegativeSpaceNavigator handles spatial navigation (physical hazards,
    path planning), CognitiveNavigator handles the γ/η space between models.

    It implements the Socratic protocol from the essays:

    1. EXPLORE: Cast the thin-chart model first. Its η is vast — it will
       find things the thick-chart model cannot see. The thin model doesn't
       build the cathedral; it names the door.

    2. ROUTE: After the thin model discovers, the thick model synthesizes.
       The elder builds the architecture around the door the mini found.

    3. CONSENSUS: Run multiple models. Where their γ overlaps, you have
       consensus (safe passage on all charts). Where it diverges, you have
       discovery (the most valuable information).

    Usage:
        >>> nav = CognitiveNavigator()
        >>> nav.register_model(ModelChart(
        ...     name="mini",
        ...     gamma={CognitiveDimension.IDEATION: 0.8, CognitiveDimension.NAMING: 0.84},
        ... ))
        >>> nav.register_model(ModelChart(
        ...     name="pro",
        ...     gamma={CognitiveDimension.SYNTHESIS: 0.84, CognitiveDimension.DEPTH: 0.9},
        ... ))
        >>> sounding = nav.explore("What is the relationship between models?",
        ...                         model_name="mini",
        ...                         handler=lambda q: "skénna")
        >>> route = nav.route("Name the concept", models=["mini", "pro"])
    """

    def __init__(self):
        self.model_charts: Dict[str, ModelChart] = {}
        self.soundings: List[Sounding] = []
        self.model_handlers: Dict[str, ModelCallable] = {}

    def register_model(
        self,
        chart: ModelChart,
        handler: Optional[ModelCallable] = None,
    ) -> None:
        """
        Register a model and its cognitive chart.

        Args:
            chart: The model's cognitive chart (γ allocation).
            handler: Optional callable that takes a query string and returns
                     a response string. Used for explore/route/consensus.
        """
        self.model_charts[chart.name] = chart
        self.model_handlers[chart.name] = handler or _default_model_handler

    def sound_depth(
        self,
        model_name: str,
        dimension: CognitiveDimension,
    ) -> float:
        """
        Estimate η depth for a model in a cognitive dimension.

        η depth = how much unmarked water the model has in this dimension.
        High η depth = lots of potential for discovery (thin chart).
        Low η depth = well-charted territory (thick chart).

        Args:
            model_name: Name of the registered model.
            dimension: Cognitive dimension to measure.

        Returns:
            η depth in [0.0, 1.0]. 1.0 = entirely unmarked.
        """
        if model_name not in self.model_charts:
            raise KeyError(f"Model '{model_name}' not registered")
        return self.model_charts[model_name].eta(dimension)

    def explore(
        self,
        query: str,
        model_name: str,
        handler: Optional[ModelCallable] = None,
        dimensions: Optional[List[CognitiveDimension]] = None,
    ) -> Sounding:
        """
        Send a query to a thin-chart model and capture what it discovers in η.

        This is the first phase of the Socratic protocol: the thin model
        explores the negative space that the thick model cannot see.

        From ON_SKENNA.md:
            "Seed Mini was given a different task: ideate. Explore. Go wide.
             She produced fragments, provocations, half-formed connections."

        Args:
            query: The question to explore.
            model_name: Name of the model to query.
            handler: Optional override handler for this call.
            dimensions: Which cognitive dimensions to sound.
                        Defaults to the model's thinnest dimensions.

        Returns:
            A Sounding record of what was found.
        """
        if model_name not in self.model_charts:
            raise KeyError(f"Model '{model_name}' not registered")

        chart = self.model_charts[model_name]
        h = handler or self.model_handlers.get(model_name, _default_model_handler)

        if dimensions is None:
            # Sound the model's thinnest dimensions — where η is deepest
            dimensions = [d for d, _ in chart.thinnest_dimensions(3)]

        response = h(query)

        sounding = Sounding(
            query=query,
            model_name=model_name,
            result=response,
            eta_dimensions=dimensions,
            gamma_dimensions=[d for d, _ in chart.thickest_dimensions(2)],
        )

        # Detect discoveries — novel findings in η space
        if response:
            # Simple heuristic: non-empty response in a thin-chart dimension
            # is a discovery. In practice, this would use more sophisticated
            # novelty detection.
            for dim in dimensions:
                if chart.eta(dim) > 0.5 and response.strip():
                    sounding.add_discovery(
                        f"Found signal in {dim.value} (η={chart.eta(dim):.2f}): "
                        f"{response[:100]}"
                    )

        self.soundings.append(sounding)
        return sounding

    def route(
        self,
        query: str,
        models: List[str],
        handlers: Optional[Dict[str, ModelCallable]] = None,
    ) -> "CognitiveRoute":
        """
        Execute the Socratic protocol: thin model discovers, thick model synthesizes.

        The thin-chart model goes first — it explores η space, finding what
        the thick-chart model cannot see. Then the thick-chart model takes
        the discovery and builds architecture around it.

        From ON_SKENNA.md:
            "The elders built the cathedral. The youngest named the door.
             And neither act is complete without the other."

        Args:
            query: The question to explore and then synthesize.
            models: List of model names, ordered thinnest to thickest.
            handlers: Optional per-model handler overrides.

        Returns:
            A CognitiveRoute describing the full Socratic journey.
        """
        if len(models) < 2:
            raise ValueError("Route requires at least 2 models (thin + thick)")

        handlers = handlers or {}
        legs: List[Sounding] = []
        accumulated_context = query

        for i, model_name in enumerate(models):
            if model_name not in self.model_charts:
                raise KeyError(f"Model '{model_name}' not registered")

            handler = handlers.get(model_name) or self.model_handlers.get(
                model_name, _default_model_handler
            )

            if i == 0:
                # First leg: pure exploration (discovery)
                sounding = self.explore(
                    query=accumulated_context,
                    model_name=model_name,
                    handler=handler,
                )
            else:
                # Subsequent legs: synthesis with accumulated context
                sounding = self.explore(
                    query=accumulated_context,
                    model_name=model_name,
                    handler=handler,
                )
                # Mark as synthesis rather than pure exploration
                sounding.metadata["phase"] = "synthesis"
                sounding.metadata["building_on"] = models[i - 1]

            legs.append(sounding)
            # Accumulate context — each model sees what the previous found
            if sounding.result:
                accumulated_context = (
                    f"{accumulated_context}\n\n"
                    f"[{model_name} found]: {sounding.result}"
                )

        return CognitiveRoute(
            query=query,
            models=models,
            legs=legs,
            final_synthesis=legs[-1].result if legs else "",
        )

    def consensus(
        self,
        models: List[str],
        query: str,
        handlers: Optional[Dict[str, ModelCallable]] = None,
    ) -> "ConsensusReport":
        """
        Run N models independently and find where their γ overlaps or diverges.

        Where charts agree (γ overlap) = consensus — safe passage on all charts.
        Where charts disagree (γ divergence) = discovery — the most valuable info.

        From WHERE_THE_ROCKS_ARENT.md:
            "When two models give different answers, the temptation is to ask
             which one is right. Wrong question. The right question: which rocks
             does each model know about?"

        Args:
            models: List of model names to run.
            query: The question to ask each model.
            handlers: Optional per-model handler overrides.

        Returns:
            A ConsensusReport with overlap and divergence analysis.
        """
        if not models:
            raise ValueError("Consensus requires at least one model")

        handlers = handlers or {}
        responses: Dict[str, str] = {}

        for model_name in models:
            if model_name not in self.model_charts:
                raise KeyError(f"Model '{model_name}' not registered")
            handler = handlers.get(model_name) or self.model_handlers.get(
                model_name, _default_model_handler
            )
            responses[model_name] = handler(query)

        # Analyze γ overlap across models
        all_dims = set()
        for name in models:
            all_dims.update(self.model_charts[name].gamma.keys())

        consensus_dims: List[CognitiveDimension] = []
        divergence_dims: List[CognitiveDimension] = []

        for dim in all_dims:
            scores = [self.model_charts[n].gamma.get(dim, 0.0) for n in models]
            spread = max(scores) - min(scores)
            if spread < 0.2:
                consensus_dims.append(dim)
            elif spread > 0.4:
                divergence_dims.append(dim)

        # Textual consensus: do responses share content?
        response_words: Dict[str, set] = {
            name: set(resp.lower().split()) for name, resp in responses.items()
        }
        if response_words:
            shared = set.intersection(*response_words.values()) if len(response_words) > 1 else set()
            unique: Dict[str, set] = {}
            for name, words in response_words.items():
                others = set()
                for other_name, other_words in response_words.items():
                    if other_name != name:
                        others.update(other_words)
                unique[name] = words - others
        else:
            shared = set()
            unique = {name: set() for name in models}

        return ConsensusReport(
            query=query,
            models=models,
            responses=responses,
            consensus_dimensions=consensus_dims,
            divergence_dimensions=divergence_dims,
            shared_content=list(shared),
            unique_content=unique,
        )

    def chart_overlap(
        self,
        model_a: str,
        model_b: str,
    ) -> Dict[CognitiveDimension, Tuple[float, float, float]]:
        """
        Compare two models' charts dimension by dimension.

        Returns a dict mapping each dimension to (γ_a, γ_b, complementarity).
        """
        if model_a not in self.model_charts or model_b not in self.model_charts:
            raise KeyError("Both models must be registered")

        a = self.model_charts[model_a]
        b = self.model_charts[model_b]
        all_dims = set(a.gamma.keys()) | set(b.gamma.keys())

        result = {}
        for dim in all_dims:
            ga = a.gamma.get(dim, 0.5)
            gb = b.gamma.get(dim, 0.5)
            comp = 1.0 - abs(ga - (1.0 - gb))
            result[dim] = (ga, gb, comp)

        return result

    def __repr__(self) -> str:
        return (
            f"CognitiveNavigator(models={len(self.model_charts)}, "
            f"soundings={len(self.soundings)})"
        )


@dataclass
class CognitiveRoute:
    """
    A route through cognitive space — the Socratic journey.

    The route has multiple legs:
    - Leg 0: Thin model explores (discovery phase)
    - Leg 1+: Thicker model(s) synthesize (architecture phase)

    From ON_SKENNA.md:
        "She was not trying to build a cathedral. She was looking at the
         harbor from a small boat, close to the rocks, and she was noticing
         things that the deep-water soundings do not reveal."

    Attributes:
        query: The original question.
        models: Ordered list of model names (thinnest to thickest).
        legs: Sounding from each leg of the journey.
        final_synthesis: The final synthesized output.
    """
    query: str
    models: List[str]
    legs: List[Sounding]
    final_synthesis: str = ""

    @property
    def discovery_phase(self) -> Optional[Sounding]:
        """The first leg — pure exploration."""
        return self.legs[0] if self.legs else None

    @property
    def synthesis_phase(self) -> List[Sounding]:
        """All legs after the first — synthesis and architecture."""
        return self.legs[1:] if len(self.legs) > 1 else []

    @property
    def is_complete(self) -> bool:
        """Whether the route has both discovery and synthesis."""
        return len(self.legs) >= 2 and bool(self.final_synthesis)

    @property
    def discoveries(self) -> List[str]:
        """All discoveries across all legs."""
        all_finds = []
        for leg in self.legs:
            all_finds.extend(leg.discoveries)
        return all_finds

    def __repr__(self) -> str:
        return (
            f"CognitiveRoute(models={self.models}, "
            f"legs={len(self.legs)}, "
            f"discoveries={len(self.discoveries)})"
        )


@dataclass
class ConsensusReport:
    """
    Results of a multi-model consensus query.

    Where charts agree (consensus) = safe passage.
    Where charts diverge (discovery) = the most valuable information.

    From WHERE_THE_ROCKS_ARENT.md:
        "The passage safe on all three charts is narrower than any single
         chart's, but it is real in a way no single chart can guarantee."

    Attributes:
        query: The question that was asked.
        models: List of model names that were queried.
        responses: Each model's response.
        consensus_dimensions: Dimensions where models have similar γ.
        divergence_dimensions: Dimensions where models differ significantly.
        shared_content: Words/content shared across all responses.
        unique_content: Content unique to each model's response.
    """
    query: str
    models: List[str]
    responses: Dict[str, str]
    consensus_dimensions: List[CognitiveDimension]
    divergence_dimensions: List[CognitiveDimension]
    shared_content: List[str]
    unique_content: Dict[str, set]

    @property
    def has_consensus(self) -> bool:
        """Whether models broadly agree (more consensus than divergence)."""
        return len(self.consensus_dimensions) >= len(self.divergence_dimensions)

    @property
    def has_discovery(self) -> bool:
        """Whether models diverge (discovery opportunity)."""
        return len(self.divergence_dimensions) > 0

    @property
    def agreement_fraction(self) -> float:
        """Fraction of measured dimensions with consensus."""
        total = len(self.consensus_dimensions) + len(self.divergence_dimensions)
        if total == 0:
            return 1.0
        return len(self.consensus_dimensions) / total

    def __repr__(self) -> str:
        return (
            f"ConsensusReport(models={len(self.models)}, "
            f"consensus={len(self.consensus_dimensions)}, "
            f"divergence={len(self.divergence_dimensions)})"
        )
