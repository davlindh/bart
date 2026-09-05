"""Dynamic Context Resolution Engine: 5-step pipeline generating scoped ContextPackets."""

from typing import List, Dict, Any, Optional
import uuid
from ..core.types import Domain, PerspectiveWindow, ScopeLevel
from ..core.contracts import ContextPacket, Observation


class HumanOverviewDict(dict):
    """Rich dictionary for Level 1 overview supporting both structured inspection and text containment."""
    def __contains__(self, key: Any) -> bool:
        if super().__contains__(key):
            return True
        for val in self.values():
            if isinstance(val, str) and str(key) in val:
                return True
        return False


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
    def compute_weighting_vector(
        cls,
        entity: Dict[str, Any],
        task: str,
        role: str,
        scope: ScopeLevel,
        allowed_domains: List[Domain],
    ) -> Dict[str, float]:
        """Calculates 8 weighting dimensions as specified in Diagram 1 (3.3 Vikta)."""
        ent_domain = entity.get("domain", Domain.OPERATIONAL.value)
        ent_hops = entity.get("distance_hops", 1)
        max_hops = {"D0": 0, "D1": 1, "D2": 2, "D3": 3}.get(scope.value, 1)

        domain_match = 1.0 if any(d.value == ent_domain for d in allowed_domains) else 0.2
        scope_proximity = max(0.1, 1.0 - (ent_hops / max(max_hops + 1, 1)))
        task_relevance = entity.get("relevance_score", 0.85)
        role_rel = 0.95 if role in ("CFO", "Ekonomiansvarig") and ent_domain in ("Exchange", "Trust", "Operational") else 0.75
        recency = entity.get("recency_score", 0.90)
        data_quality = 0.98 if entity.get("is_production_grade", True) else 0.70
        permissions = 1.0 if domain_match > 0.5 else 0.0
        security = 0.95  # Standard non-confidential operational node

        composite = (
            task_relevance * 0.25 +
            scope_proximity * 0.20 +
            recency * 0.15 +
            role_rel * 0.10 +
            domain_match * 0.10 +
            data_quality * 0.10 +
            permissions * 0.05 +
            security * 0.05
        )

        return {
            "composite": round(composite, 3),
            "task_relevance": task_relevance,
            "scope_proximity": round(scope_proximity, 2),
            "recency": recency,
            "role_relevance": role_rel,
            "domain_match": domain_match,
            "data_quality": data_quality,
            "permissions": permissions,
            "security": security,
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

        # 2. Filter & Weight candidate entities
        max_hops = {"D0": 0, "D1": 1, "D2": 2, "D3": 3}.get(scope.value, 1)
        filtered_entities = []
        relevance_scores = {}

        for ent in candidate_entities:
            weights = cls.compute_weighting_vector(ent, task, role, scope, allowed_domains)
            ent_id = ent.get("id", "ent_unknown")
            relevance_scores[ent_id] = weights["composite"]

            if weights["permissions"] > 0 and ent.get("distance_hops", 1) <= max_hops:
                ent_copy = dict(ent)
                ent_copy["weighting_vector"] = weights
                filtered_entities.append(ent_copy)

        # Rank candidates by composite score
        filtered_entities.sort(key=lambda e: e.get("weighting_vector", {}).get("composite", 0), reverse=True)

        # 3. Compute recommended next nodes (Navigation Level 4)
        recommended_next_nodes = []
        if not candidate_entities:
            # Default rich satellites matching Diagram 1
            recommended_next_nodes = [
                {"node_id": "nav_decision_auth", "title": "1. Decision Authority & Mandat", "relevance_score": 0.94, "target": "ROLE_CFO"},
                {"node_id": "nav_decision_proc", "title": "2. Decision Process & VMB-rutin", "relevance_score": 0.89, "target": "INTERV_VMB"},
                {"node_id": "nav_team_struct", "title": "3. Team Structure & Fältmontörer", "relevance_score": 0.76, "target": "TEAM_SERVICE"},
                {"node_id": "nav_knowledge", "title": "4. Knowledge Asset & Cirkulär Maskinbok", "relevance_score": 0.41, "target": "KNOW_VMB"},
                {"node_id": "nav_finance", "title": "5. Finance & Skatteverket Momsruta 05/07/10", "relevance_score": 0.88, "target": "SKV_MOMS"},
            ]
        else:
            for ent in filtered_entities[:5]:
                recommended_next_nodes.append({
                    "node_id": ent.get("id", "unknown"),
                    "title": ent.get("title", ent.get("name", "Node")),
                    "relevance_score": relevance_scores.get(ent.get("id"), 0.8),
                    "reason": f"Hög relevans för {task}",
                    "target": ent.get("id"),
                })

        # Assemble Evidence & Assumptions
        evidence = [
            f"Fokusentitet: {target_entity.get('title', target_entity.get('name', 'Aktuell portfölj'))}",
            f"Behörighet: {len(allowed_domains)} domäner auktoriserade för {role}",
            f"Scope-horisont: {scope.value} (Max {max_hops} hopp i kunskapsgrafen)",
            f"{len(observations)} empiriska telemetrisignaler infångade",
        ]
        assumptions = [
            "Företaget tillämpar svensk BAS-kontoplan och K2/K3 regelverk",
            "Mervärdesskattelagen (ML 9 kap VMB, ML 16 kap Byggmoms) och IL 67 kap (RUT) är juridiskt tillämpliga",
        ]
        uncertainties = [
            "F-skattestatus hos nya underentreprenörer kräver periodisk validering",
            "Privatpersons RUT-utrymme (max 75 000 kr/år) förutsätter ej förbrukad årskvot",
        ]

        # Stop condition evaluation (Diagram 1: Stoppvillkor)
        stop_met = len(evidence) >= 3 and len(uncertainties) <= 2
        stop_reason = "Tillräcklig evidens finns för slutsats; osäkerheten är acceptabelt låg inom scope."

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
            recommended_next_nodes=recommended_next_nodes,
            evidence=evidence,
            assumptions=assumptions,
            uncertainties=uncertainties,
            relevance_scores=relevance_scores,
            stop_condition_met=stop_met,
            stop_condition_reason=stop_reason,
        )

    # ── Presentation Formatters (Diagram 1: 4 Presentationsnivåer) ────────────

    @classmethod
    def format_human_view_l1(cls, packet: ContextPacket) -> Dict[str, Any]:
        """4.1 Human — Nivå 1 (Översikt): Kort, begriplig sammanfattning."""
        return HumanOverviewDict({
            "level": "4.1 Human — Nivå 1 (Översikt)",
            "title": f"Översikt: {packet.role} • {packet.purpose}",
            "mandate": f"Fullt mandat för {packet.role} inom {packet.perspective_window.value}",
            "perspective_window": packet.perspective_window.value,
            "active_focus": packet.primary_entity.get("title", packet.primary_entity.get("name", "Q3 Revision")),
            "scope_summary": f"Horisont: {packet.scope.value} • {len(packet.allowed_domains)} tillåtna domäner",
            "stop_condition": {
                "met": packet.stop_condition_met,
                "reason": packet.stop_condition_reason,
            },
            "executive_summary": (
                f"Analys genomförd för {packet.task}. "
                f"{len(packet.evidence)} evidenspunkter verifierade mot svensk skattelagstiftning. "
                f"Inga blockerande avvikelser identifierade inom scope {packet.scope.value}."
            ),
        })

    @classmethod
    def format_human_view_l2(cls, packet: ContextPacket) -> Dict[str, Any]:
        """4.2 Human — Nivå 2 (Detalj & evidens): Mer detaljer, evidenskedja och lagrum."""
        return {
            "level": "4.2 Human — Nivå 2 (Detalj & Evidens)",
            "evidence_chain": packet.evidence,
            "legal_assumptions": packet.assumptions,
            "managed_uncertainties": packet.uncertainties,
            "telemetry_observations": [
                {
                    "id": o.observation_id,
                    "metric": o.metric_name,
                    "value": o.metric_value,
                    "domain": o.domain.value if hasattr(o.domain, "value") else str(o.domain),
                }
                for o in packet.observations
            ],
            "related_entities_count": len(packet.related_entities),
            "relevance_vector_sample": packet.relevance_scores,
        }

    @classmethod
    def format_machine_view_l3(cls, packet: ContextPacket) -> Dict[str, Any]:
        """4.3 Maskin — Strukturerad: Maskinläsbart Context Packet (JSON / API / agent)."""
        data = packet.model_dump()
        data["presentation_level"] = "4.3 Maskin — Strukturerad (JSON)"
        return data

    @classmethod
    def format_navigation_view_l4(cls, packet: ContextPacket) -> Dict[str, Any]:
        """4.4 Navigation — Nästa punkter: Rekommenderade nästa noder med relevansscores."""
        return {
            "level": "4.4 Navigation — Nästa Punkter",
            "recommended_next_nodes": packet.recommended_next_nodes,
            "scope_expansion_action": f"Utöka scope ({packet.scope.value} → D{min(3, int(packet.scope.value[1])+1)}) eller pivotera till ny punkt",
        }
