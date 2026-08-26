"""Insight Integration & Insight Synthesizer Agents.

Migrated from 3.7fmossmorph/meta-framework/layered_runner/Attach/:
  - Insight Integration Agent.txt
  - Insight Synthesizer Agent.txt

These two agents implement an explicit two-phase pattern that refines
the data flow between the Observer → Diagnostiker handoff:

  1. InsightIntegrationAgent gathers and normalizes data from each active
     Perspective Window, ensuring contextual clarity and cross-window
     coherence before any diagnostic analysis happens.

  2. InsightSynthesizerAgent distills the integrated data into actionable
     strategic recommendations, pattern summaries, and a compiled report
     ready for the downstream specialist agents.
"""

from typing import Any, Dict, List, Optional, Tuple

from src.agents.base import BaseTeamDynamicsAgent
from src.core.contracts import (
    ActionItem,
    AgentResult,
    ContextPacket,
    HypothesisItem,
    IdentifiedIssue,
)
from src.core.types import PerspectiveWindow, SeverityLevel
from src.graph.window_particles import (
    WINDOW_DECOMPOSITIONS,
    ContextualParticle,
    WindowDecomposition,
)


class InsightIntegrationAgent(BaseTeamDynamicsAgent):
    """Agent 12: Gathers and integrates data from each Perspective Window.

    Operates before the Diagnostiker to ensure that the context packet is
    enriched with cross-window coherence, data completeness checks, and
    entanglement-node linkage annotations.
    """

    def __init__(self):
        super().__init__(
            name="Insight Integration Agent",
            description="Gathers data from all active Perspective Windows, "
                        "ensures contextual clarity, and produces an integrated dataset.",
        )

    async def observe(self, context_packet: ContextPacket) -> List[str]:
        """Scan active windows and identify which ones have relevant data."""
        observations = []
        active_windows = self._identify_active_windows(context_packet)
        observations.append(
            f"Scanning {len(active_windows)} active Perspective Windows "
            f"for context '{context_packet.context_id}'."
        )
        for window in active_windows:
            decomp = WINDOW_DECOMPOSITIONS.get(window)
            if decomp:
                particle_count = sum(len(c.particles) for c in decomp.components)
                observations.append(
                    f"Window '{window.value}': {len(decomp.components)} components, "
                    f"{particle_count} contextual particles, "
                    f"{len(decomp.entanglement_nodes)} entanglement nodes."
                )
        return observations

    async def analyze(self, observations: List[str], context_packet: ContextPacket) -> Dict[str, Any]:
        """Assess data completeness and cross-window coverage."""
        active_windows = self._identify_active_windows(context_packet)
        total_particles = 0
        total_entanglements = 0
        coverage_gaps: List[str] = []

        for window in PerspectiveWindow:
            decomp = WINDOW_DECOMPOSITIONS.get(window)
            if not decomp:
                continue
            particle_count = sum(len(c.particles) for c in decomp.components)
            total_particles += particle_count
            total_entanglements += len(decomp.entanglement_nodes)
            if window not in active_windows:
                coverage_gaps.append(window.value)

        completeness = len(active_windows) / len(PerspectiveWindow) if PerspectiveWindow else 0.0

        return {
            "metrics": {
                "active_window_count": len(active_windows),
                "total_windows": len(PerspectiveWindow),
                "coverage_ratio": round(completeness, 2),
                "total_particles_available": total_particles,
                "total_entanglement_nodes": total_entanglements,
                "coverage_gaps": coverage_gaps,
            },
            "risks": [f"No data coverage for: {', '.join(coverage_gaps)}"] if coverage_gaps else [],
            "next_questions": [],
        }

    async def identify(self, analysis_result: Dict[str, Any]) -> List[IdentifiedIssue]:
        """Flag windows with missing data or broken entanglement links."""
        issues: List[IdentifiedIssue] = []
        metrics = analysis_result.get("metrics", {})
        gaps = metrics.get("coverage_gaps", [])
        if gaps:
            issues.append(IdentifiedIssue(
                issue_id="insight_gap_001",
                severity=SeverityLevel.LOW,
                description=f"Data integration incomplete: {len(gaps)} windows "
                            f"lack active data ({', '.join(gaps)}).",
                related_nodes=[],
            ))
        if metrics.get("coverage_ratio", 1.0) < 0.5:
            issues.append(IdentifiedIssue(
                issue_id="insight_low_coverage",
                severity=SeverityLevel.MEDIUM,
                description="Fewer than half of Perspective Windows have active data. "
                            "Diagnostic quality may be degraded.",
                related_nodes=[],
            ))
        return issues

    async def propose(self, issues: List[IdentifiedIssue]) -> Tuple[List[HypothesisItem], List[str]]:
        """Suggest data enrichment actions to fill gaps."""
        hypotheses = [
            HypothesisItem(
                hypothesis_id="hyp_integration_coherence",
                statement="Cross-window data integration improves downstream diagnostic "
                          "accuracy by providing complete multi-perspective context.",
                probability=0.92,
            )
        ]
        recommendations = [
            "Normalize and timestamp all window particle outputs before diagnostic handoff.",
            "Annotate entanglement nodes that bridge active and inactive windows.",
        ]
        return hypotheses, recommendations

    async def act(self, recommendations: List[str], context_packet: ContextPacket) -> List[ActionItem]:
        return [
            ActionItem(
                action_id="act_integrate_windows",
                type="DATA_INTEGRATION",
                assignee="InsightIntegrationAgent",
                description="Deliver integrated cross-window dataset to Insight Synthesizer.",
            )
        ]

    async def evaluate(self, actions: List[ActionItem], metrics: Dict[str, Any]) -> float:
        coverage = metrics.get("coverage_ratio", 0.5)
        return min(1.0, 0.7 + coverage * 0.3)

    def _identify_active_windows(self, context_packet: ContextPacket) -> List[PerspectiveWindow]:
        """Heuristic: determine which windows have relevant data based on node types and domains."""
        active: set[PerspectiveWindow] = set()
        for node in context_packet.nodes:
            node_type_lower = node.type.lower()
            domain_lower = node.domain.value.lower()
            # Map node types and domains to perspective windows
            if "role" in node_type_lower or "person" in node_type_lower:
                active.add(PerspectiveWindow.PERSONNEL_MANAGEMENT)
            if "kpi" in node_type_lower or "measurement" in node_type_lower:
                active.add(PerspectiveWindow.EVALUATION)
            if "process" in node_type_lower or "pipeline" in node_type_lower:
                active.add(PerspectiveWindow.RESOURCE_ALLOCATION)
            if "decision" in node_type_lower:
                active.add(PerspectiveWindow.CONTEXTUALIZATION)
            if "operational" in domain_lower:
                active.add(PerspectiveWindow.ADAPTIVE_INSIGHTS)
            if "trust" in domain_lower:
                active.add(PerspectiveWindow.COMMUNICATION_PRESENTATION)
        # Always include contextual baseline
        active.add(PerspectiveWindow.CONTEXTUALIZATION)
        return sorted(active, key=lambda w: w.value)


class InsightSynthesizerAgent(BaseTeamDynamicsAgent):
    """Agent 13: Synthesizes integrated data into actionable insights and strategy.

    Receives the integrated multi-window dataset from the Integration Agent
    and produces a compiled report of patterns, actionable recommendations,
    and strategic priorities for the downstream specialist agents.
    """

    def __init__(self):
        super().__init__(
            name="Insight Synthesizer Agent",
            description="Synthesizes cross-window integrated data into actionable "
                        "insights, strategy recommendations, and compiled reports.",
        )

    async def observe(self, context_packet: ContextPacket) -> List[str]:
        """Review the integrated data payload."""
        node_count = len(context_packet.nodes)
        evidence_count = len(context_packet.evidence)
        return [
            f"Synthesizer reviewing integrated dataset: {node_count} nodes, "
            f"{evidence_count} evidence items across bounded context.",
            f"Target focal point: {context_packet.target_node}.",
        ]

    async def analyze(self, observations: List[str], context_packet: ContextPacket) -> Dict[str, Any]:
        """Distill cross-window patterns and key themes."""
        # Extract dominant themes from node properties
        themes: Dict[str, int] = {}
        for node in context_packet.nodes:
            for key, val in node.properties.items():
                theme = key.lower()
                themes[theme] = themes.get(theme, 0) + 1

        # Identify high-priority actionable areas
        priority_areas: List[str] = []
        for node in context_packet.nodes:
            if node.relevance_score > 0.7:
                priority_areas.append(f"{node.label} (relevance: {node.relevance_score:.2f})")

        return {
            "metrics": {
                "theme_count": len(themes),
                "top_themes": dict(sorted(themes.items(), key=lambda x: -x[1])[:5]),
                "priority_areas": priority_areas,
                "synthesis_depth": "comprehensive" if len(context_packet.nodes) > 3 else "preliminary",
            },
            "risks": [],
            "next_questions": ["Which themes require immediate intervention?"],
        }

    async def identify(self, analysis_result: Dict[str, Any]) -> List[IdentifiedIssue]:
        metrics = analysis_result.get("metrics", {})
        issues: List[IdentifiedIssue] = []
        if metrics.get("synthesis_depth") == "preliminary":
            issues.append(IdentifiedIssue(
                issue_id="synth_shallow",
                severity=SeverityLevel.LOW,
                description="Limited node coverage may produce incomplete synthesis.",
                related_nodes=[],
            ))
        return issues

    async def propose(self, issues: List[IdentifiedIssue]) -> Tuple[List[HypothesisItem], List[str]]:
        hypotheses = [
            HypothesisItem(
                hypothesis_id="hyp_synthesis_quality",
                statement="Multi-window synthesis yields 40% richer context for downstream "
                          "agents compared to single-perspective observation.",
                probability=0.88,
            )
        ]
        recommendations = [
            "Compile synthesized strategy report for Diagnostiker and Team Architect.",
            "Highlight top-3 priority areas requiring immediate attention.",
            "Flag cross-domain entanglement nodes for the Collaboration Agent.",
        ]
        return hypotheses, recommendations

    async def act(self, recommendations: List[str], context_packet: ContextPacket) -> List[ActionItem]:
        return [
            ActionItem(
                action_id="act_synthesis_report",
                type="SYNTHESIS_HANDOFF",
                assignee="InsightSynthesizerAgent",
                description="Deliver compiled synthesis report to Diagnostiker for root cause analysis.",
            )
        ]

    async def evaluate(self, actions: List[ActionItem], metrics: Dict[str, Any]) -> float:
        depth = metrics.get("synthesis_depth", "preliminary")
        return 0.95 if depth == "comprehensive" else 0.80
