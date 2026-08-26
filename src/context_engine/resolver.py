"""Dynamic Context Resolution Engine executing the 5-Step Resolution Pipeline."""

import time
import uuid
from typing import Dict, List, Optional
from src.core.contracts import (
    ContextPacket,
    EvidenceItem,
    GraphNodeSummary,
    GraphRelationSummary,
    RecommendedNode,
    ScopeContract,
)
from src.core.governance import GovernanceEngine
from src.core.types import ScopeDepth
from src.context_engine.scope_manager import ScopeManager
from src.context_engine.weighting import RelevanceWeighter
from src.graph.graph_store import GraphEdge, GraphNode, KnowledgeGraphStore


class ContextResolutionEngine:
    """Core engine extracting and packaging targeted subgraphs into Context Packets."""

    def __init__(
        self,
        graph_store: KnowledgeGraphStore,
        governance_engine: Optional[GovernanceEngine] = None,
        weighter: Optional[RelevanceWeighter] = None,
    ):
        self.store = graph_store
        self.governance = governance_engine or GovernanceEngine()
        self.weighter = weighter or RelevanceWeighter()

    def resolve_context(
        self,
        role: str,
        purpose: str,
        task: str,
        current_point: str,
        scope: Optional[ScopeContract] = None,
    ) -> ContextPacket:
        """
        Executes the 5-step Context Resolution Pipeline:
        1. Fetch candidates within depth hops.
        2. Filter unauthorized / out-of-domain nodes.
        3. Score candidates with 8-dimensional relevance algorithm.
        4. Rank and bound to breadth limit.
        5. Package into strongly typed ContextPacket.
        """
        scope_contract = scope or ScopeContract()
        hops = ScopeManager.depth_to_hops(scope_contract.depth)

        # 3.1 Candidate Fetching
        candidate_nodes, candidate_edges, distances = self.store.traverse_subgraph(
            focal_node_id=current_point,
            depth=hops,
            allowed_domains=scope_contract.allowed_domains,
        )

        # 3.2 Filtering & Governance Check
        filtered_nodes: List[GraphNode] = []
        for node in candidate_nodes:
            is_authorized = self.governance.validate_access(
                actor_role=role,
                node_permission=node.permission_level,
                node_sensitivity=node.sensitivity_level,
                scope_permission=scope_contract.permission_level,
                scope_sensitivity=scope_contract.sensitivity_ceiling,
            )
            if is_authorized:
                filtered_nodes.append(node)

        # 3.3 8-Dimensional Relevance Scoring
        scored_nodes: List[tuple[float, GraphNode]] = []
        relevance_score_map: Dict[str, float] = {}

        for node in filtered_nodes:
            dist = distances.get(node.id, 1)
            score, _ = self.weighter.score_node(
                node=node,
                distance=dist,
                task_text=task,
                role_persona=role,
                scope=scope_contract,
            )
            scored_nodes.append((score, node))
            relevance_score_map[node.id] = round(score, 3)

        # 3.4 Ranking & Scope Bounding
        scored_nodes.sort(key=lambda x: x[0], reverse=True)
        selected_nodes = scored_nodes[: scope_contract.breadth_limit]
        selected_node_ids = {node.id for _, node in selected_nodes}

        # Select relevant relations between bounded nodes
        bounded_relations: List[GraphRelationSummary] = []
        for edge in candidate_edges:
            if edge.source in selected_node_ids and edge.target in selected_node_ids:
                bounded_relations.append(
                    GraphRelationSummary(
                        source=edge.source,
                        target=edge.target,
                        type=edge.rel_type,
                        confidence=edge.confidence,
                        properties=edge.properties,
                    )
                )

        # Build Node Summaries
        bounded_node_summaries: List[GraphNodeSummary] = []
        for score, node in selected_nodes:
            sanitized_props = self.governance.sanitize_payload(
                node.properties, scope_contract.sensitivity_ceiling
            )
            bounded_node_summaries.append(
                GraphNodeSummary(
                    id=node.id,
                    type=node.type,
                    domain=node.domain,
                    label=node.label,
                    relevance_score=round(score, 3),
                    properties=sanitized_props,
                )
            )

        # Identify next candidate nodes beyond current selection for navigation
        recommended_next: List[RecommendedNode] = []
        remaining_candidates = scored_nodes[scope_contract.breadth_limit :]
        for score, node in remaining_candidates[:5]:
            recommended_next.append(
                RecommendedNode(
                    node_id=node.id,
                    label=node.label,
                    domain=node.domain,
                    relevance=round(score, 3),
                    rationale=f"Adjacent entity in {node.domain.value} domain (hop distance: {distances.get(node.id, 2)})",
                )
            )

        # Extract Evidence, Assumptions, Uncertainties from node properties
        evidence_list: List[EvidenceItem] = []
        assumptions: List[str] = []
        uncertainties: List[str] = []

        for score, node in selected_nodes:
            if "incidents" in node.properties:
                evidence_list.append(
                    EvidenceItem(
                        source_ref=f"log:{node.id}:incidents",
                        confidence=0.95,
                        fact=f"Node '{node.label}' has {node.properties['incidents']} recorded operational incidents.",
                    )
                )
            if "failure_rate" in node.properties:
                evidence_list.append(
                    EvidenceItem(
                        source_ref=f"metric:{node.id}:failure_rate",
                        confidence=0.92,
                        fact=f"Node '{node.label}' reports an active failure rate of {node.properties['failure_rate']}.",
                    )
                )
            if "turnaround_days" in node.properties:
                evidence_list.append(
                    EvidenceItem(
                        source_ref=f"kpi:{node.id}:turnaround",
                        confidence=1.0,
                        fact=f"Node '{node.label}' current decision turnaround is {node.properties['turnaround_days']} days.",
                    )
                )

        if not assumptions:
            assumptions.append(f"Task '{task}' requires operational integrity across bounded dependencies.")

        # Check Stop Condition
        top_rel = selected_nodes[0][0] if selected_nodes else 0.0
        stop_met = ScopeManager.evaluate_stop_condition(
            evidence_count=len(evidence_list),
            confidence_score=top_rel,
            uncertainty_count=len(uncertainties),
            top_relevance=top_rel,
        )

        context_id = f"ctx_{int(time.time())}_{uuid.uuid4().hex[:6]}"

        packet = ContextPacket(
            context_id=context_id,
            target_node=current_point,
            role=role,
            purpose=purpose,
            task=task,
            scope=scope_contract,
            nodes=bounded_node_summaries,
            relations=bounded_relations,
            evidence=evidence_list,
            assumptions=assumptions,
            uncertainties=uncertainties,
            relevance_scores=relevance_score_map,
            permissions=[scope_contract.permission_level.value],
            current_state={"focal_node": current_point, "bounded_node_count": len(selected_nodes)},
            recommended_next_nodes=recommended_next,
            stop_condition_met=stop_met,
        )

        # Log audit entry
        self.governance.log_event(
            actor_id=role,
            action_type="CONTEXT_RESOLUTION",
            target_node=current_point,
            scope_depth=scope_contract.depth.value,
            governance_approved=True,
            rationale=f"Resolved {len(selected_nodes)} nodes for task: {task}",
        )

        return packet
