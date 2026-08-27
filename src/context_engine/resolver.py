"""Dynamic Context Resolution Engine: 5-step pipeline generating scoped ContextPackets."""

from typing import List, Dict, Any, Optional
import uuid
from ..core.types import Domain, PerspectiveWindow, ScopeLevel
from ..core.contracts import ContextPacket, Observation


class ContextResolver:
    """Resolves dynamic context slices tailored to Role, Purpose, Task, and Scope (D0-D3)."""

    ROLE_PERMISSIONS: Dict[str, List[Domain]] = {
        "Ekonomiansvarig": [Domain.OPERATIONAL, Domain.EXCHANGE, Domain.TRUST, Domain.KNOWLEDGE],
        "CFO": [Domain.OPERATIONAL, Domain.EXCHANGE, Domain.TRUST, Domain.KNOWLEDGE, Domain.TOOLS],
        "Revisor": [Domain.OPERATIONAL, Domain.EXCHANGE, Domain.TRUST],
        "Säljare": [Domain.EXCHANGE, Domain.INTERACTIONAL, Domain.TOOLS],
        "Verkstadschef": [Domain.OPERATIONAL, Domain.TOOLS, Domain.INTERACTIONAL],
    }

    ROLE_PERSPECTIVES: Dict[str, PerspectiveWindow] = {
        "Ekonomiansvarig": PerspectiveWindow.W5_FINANCIAL_MANAGEMENT,
        "CFO": PerspectiveWindow.W5_FINANCIAL_MANAGEMENT,
        "Revisor": PerspectiveWindow.W3_EVALUATION,
        "Säljare": PerspectiveWindow.W2_MATCHING,
        "Verkstadschef": PerspectiveWindow.W4_RESOURCE_ALLOCATION,
    }

    @classmethod
    def resolve_context(
        cls,
        role: str,
        purpose: str,
        task: str,
        scope: ScopeLevel = ScopeLevel.D1_DIRECT,
        target_entity: Optional[Dict[str, Any]] = None,
        candidate_entities: Optional[List[Dict[str, Any]]] = None,
        observations: Optional[List[Observation]] = None,
    ) -> ContextPacket:
        """Executes the 5-step Context Resolution pipeline."""
        target_entity = target_entity or {}
        candidate_entities = candidate_entities or []
        observations = observations or []

        # 1. Determine allowed domains & perspective window by role
        allowed_domains = cls.ROLE_PERMISSIONS.get(role, [Domain.OPERATIONAL, Domain.EXCHANGE])
        window = cls.ROLE_PERSPECTIVES.get(role, PerspectiveWindow.W5_FINANCIAL_MANAGEMENT)

        # 2. Filter candidate entities by allowed domains & scope level
        filtered_entities = []
        max_hops = {"D0": 0, "D1": 1, "D2": 2, "D3": 3}.get(scope.value, 1)

        for ent in candidate_entities:
            ent_domain_str = ent.get("domain", Domain.OPERATIONAL.value)
            ent_hops = ent.get("distance_hops", 1)

            # Match domain permission
            domain_allowed = any(d.value == ent_domain_str for d in allowed_domains)
            hop_allowed = ent_hops <= max_hops

            if domain_allowed and hop_allowed:
                filtered_entities.append(ent)

        # 3. Compute recommended next nodes to explore (Navigation function)
        recommended_next_nodes = []
        for ent in filtered_entities:
            relevance = ent.get("relevance_score", 0.75)
            if relevance >= 0.70:
                recommended_next_nodes.append({
                    "node_id": ent.get("id", "unknown"),
                    "title": ent.get("title", ent.get("name", "Node")),
                    "relevance_score": relevance,
                    "reason": f"High relevance for task: {task}",
                })

        # Sort recommended next nodes by relevance
        recommended_next_nodes.sort(key=lambda x: x["relevance_score"], reverse=True)

        return ContextPacket(
            context_id=f"ctx_{uuid.uuid4().hex[:12]}",
            role=role,
            purpose=purpose,
            task=task,
            scope=scope,
            allowed_domains=allowed_domains,
            perspective_window=window,
            primary_entity=target_entity,
            related_entities=filtered_entities,
            observations=observations,
            recommended_next_nodes=recommended_next_nodes[:5],
        )

    @classmethod
    def format_human_view_l1(cls, packet: ContextPacket) -> str:
        """High-level executive summary view."""
        return (
            f"### Context View: {packet.role} | {packet.task}\n"
            f"**Window**: {packet.perspective_window.value} | **Scope**: {packet.scope.value}\n"
            f"**Primary Focus**: {packet.primary_entity.get('title', packet.primary_entity.get('name', 'N/A'))}\n"
            f"**Active Observations**: {len(packet.observations)} item(s) captured.\n"
            f"**Next Actionable Points**: {', '.join(n['title'] for n in packet.recommended_next_nodes[:3]) or 'None'}"
        )
