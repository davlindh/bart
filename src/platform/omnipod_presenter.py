"""Omnipod Presenter — Formats multi-agent output and graph state into 9-window presentation payloads.

Transforms raw ContextPackets, AgentResults, and WindowDecompositions into
structured client viewmodels across the 4 presentation tiers:
  - HUMAN_L1_SUMMARY: Executive dashboard cards & high-level indicators
  - HUMAN_L2_DETAIL: Full analytical breakdown, evidence, and hypothesis traces
  - MACHINE_JSON: Strongly-typed API payload
  - NAVIGATION_NEXT_NODES: Predictive focal points for UI breadcrumbs & drilldowns
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from src.core.contracts import AgentResult, ContextPacket
from src.core.types import PerspectiveWindow, PresentationTier
from src.graph.window_particles import WINDOW_DECOMPOSITIONS


class WindowPresentationPayload(BaseModel):
    """Client-ready UI representation of an Omnipod Perspective Window."""
    window: PerspectiveWindow
    window_name: str
    l1_summary: str = Field(description="Executive overview card (Human L1)")
    l2_details: Dict[str, Any] = Field(default_factory=dict, description="Detailed drill-down data (Human L2)")
    active_particles: List[Dict[str, Any]] = Field(default_factory=list)
    entangled_links: List[str] = Field(default_factory=list)
    recommended_actions: List[str] = Field(default_factory=list)
    metrics: Dict[str, Any] = Field(default_factory=dict)


class OmnipodPresenter:
    """Formats full system state and execution telemetry for client-side rendering."""

    @staticmethod
    def present_window(
        window: PerspectiveWindow,
        context_packet: ContextPacket,
        agent_results: Optional[List[AgentResult]] = None,
    ) -> WindowPresentationPayload:
        """Constructs a WindowPresentationPayload for a single Perspective Window."""
        decomp = WINDOW_DECOMPOSITIONS.get(window)
        results = agent_results or []

        # 1. Filter agent actions & metrics relevant to this window
        actions: List[str] = []
        metrics: Dict[str, Any] = {}
        for r in results:
            for act in r.actions:
                actions.append(f"[{r.agent_name}] {act.description}")
            for k, v in r.metrics.items():
                metrics[f"{r.agent_name}:{k}"] = v

        # 2. Extract particles
        particles = []
        entangled = []
        if decomp:
            for comp in decomp.components:
                for p in comp.particles:
                    particles.append({
                        "particle_id": p.particle_id,
                        "label": p.label,
                        "description": p.description,
                        "type": p.output_type,
                    })
            for ent in decomp.entanglement_nodes:
                entangled.append(f"{ent.label} (bridges: {', '.join(w.value for w in ent.linked_windows)})")

        # 3. Formulate L1 summary and L2 details
        l1 = (
            f"Window: {window.value} | Focal Target: {context_packet.target_node} | "
            f"Active Nodes: {len(context_packet.nodes)} | Evidence: {len(context_packet.evidence)}"
        )

        l2 = {
            "purpose": context_packet.purpose,
            "task": context_packet.task,
            "nodes": [{"id": n.id, "label": n.label, "relevance": n.relevance_score} for n in context_packet.nodes],
            "evidence": [e.fact for e in context_packet.evidence],
            "assumptions": context_packet.assumptions,
            "uncertainties": context_packet.uncertainties,
            "agent_count": len(results),
        }

        return WindowPresentationPayload(
            window=window,
            window_name=window.value,
            l1_summary=l1,
            l2_details=l2,
            active_particles=particles,
            entangled_links=entangled,
            recommended_actions=actions[:5],
            metrics=metrics,
        )

    @classmethod
    def present_all_windows(
        cls,
        context_packet: ContextPacket,
        agent_results: Optional[List[AgentResult]] = None,
    ) -> Dict[PerspectiveWindow, WindowPresentationPayload]:
        """Generates presentation payloads for all 9 Omnipod windows."""
        return {
            window: cls.present_window(window, context_packet, agent_results)
            for window in PerspectiveWindow
        }
