"""10-Dimensional Relevance Scoring Engine for Graph Nodes.

Extended from 8D to 10D by incorporating two additional meta-attributes
migrated from 3.7fmossmorph/Contextual Layer.txt:
  - Emotional Tone: sentiment alignment of the node with current operational mood
  - Interaction Phase: lifecycle alignment (onboarding, deep engagement, mastery, contribution)
"""

import math
import time
from typing import Dict, Optional
from src.core.contracts import ScopeContract
from src.core.types import DomainType
from src.graph.graph_store import GraphNode


class RelevanceWeightMatrix:
    """Weights across the 10 scoring dimensions, normalized to sum to 1.0."""

    def __init__(
        self,
        task_relevance: float = 0.22,
        scope_distance: float = 0.18,
        recency: float = 0.08,
        role_relevance: float = 0.13,
        domain_matching: float = 0.09,
        data_quality: float = 0.08,
        permissions: float = 0.04,
        security_sensitivity: float = 0.04,
        emotional_tone: float = 0.07,
        interaction_phase: float = 0.07,
    ):
        raw_weights = {
            "task_relevance": task_relevance,
            "scope_distance": scope_distance,
            "recency": recency,
            "role_relevance": role_relevance,
            "domain_matching": domain_matching,
            "data_quality": data_quality,
            "permissions": permissions,
            "security_sensitivity": security_sensitivity,
            "emotional_tone": emotional_tone,
            "interaction_phase": interaction_phase,
        }
        total = sum(raw_weights.values()) or 1.0
        self.weights = {k: v / total for k, v in raw_weights.items()}

    def update_weights(self, calibrations: Dict[str, float]):
        """Dynamically adjusts dimensional weights (e.g., via Meta-Learning loop)."""
        for k, v in calibrations.items():
            if k in self.weights:
                self.weights[k] = v
        total = sum(self.weights.values()) or 1.0
        self.weights = {k: v / total for k, v in self.weights.items()}


class RelevanceWeighter:
    """Computes multi-dimensional relevance scores for candidate nodes."""

    def __init__(self, weight_matrix: Optional[RelevanceWeightMatrix] = None):
        self.matrix = weight_matrix or RelevanceWeightMatrix()

    def score_node(
        self,
        node: GraphNode,
        distance: int,
        task_text: str,
        role_persona: str,
        scope: ScopeContract,
    ) -> tuple[float, Dict[str, float]]:
        """Calculates normalized composite score and dimensional breakdown."""
        dim_scores: Dict[str, float] = {}

        # 1. Task Relevance (keyword overlap & semantic heuristic)
        task_tokens = set(task_text.lower().split())
        node_text = f"{node.id} {node.label} {node.type} {' '.join(str(v) for v in node.properties.values())}".lower()
        matched_tokens = sum(1 for t in task_tokens if len(t) > 3 and t in node_text)
        task_score = min(1.0, 0.4 + 0.2 * matched_tokens) if matched_tokens > 0 else 0.3
        dim_scores["task_relevance"] = task_score

        # 2. Scope Distance Proximity (exponential decay)
        dim_scores["scope_distance"] = math.exp(-0.4 * distance)

        # 3. Recency (temporal decay)
        current_time = time.time()
        age_days = max(0.0, (current_time - node.last_updated) / (24 * 3600)) if node.last_updated > 0 else 10.0
        dim_scores["recency"] = max(0.2, 1.0 - (age_days / max(1, scope.time_horizon_days)))

        # 4. Role Relevance
        role_lower = role_persona.lower()
        node_domain_str = node.domain.value.lower()
        role_score = 0.5
        if ("data" in role_lower and ("data" in node_domain_str or "operational" in node_domain_str)) or \
           ("security" in role_lower and "trust" in node_domain_str) or \
           ("architect" in role_lower and ("operational" in node_domain_str or "tools" in node_domain_str)):
            role_score = 0.95
        dim_scores["role_relevance"] = role_score

        # 5. Domain Matching
        dim_scores["domain_matching"] = 1.0 if node.domain in scope.allowed_domains else 0.2

        # 6. Data Quality & Completeness
        dim_scores["data_quality"] = node.verification_level

        # 7. Permissions & Authority
        dim_scores["permissions"] = 1.0

        # 8. Security & Sensitivity
        sens_penalty = 0.0
        if node.sensitivity_level.value == "Highly Sensitive":
            sens_penalty = 0.3
        dim_scores["security_sensitivity"] = max(0.1, 1.0 - sens_penalty)

        # 9. Emotional Tone (sentiment alignment heuristic)
        # Nodes with positive operational signals score higher; stress/risk indicators lower
        emotional_score = 0.6  # Neutral baseline
        props_text = " ".join(str(v).lower() for v in node.properties.values())
        positive_signals = ["success", "improvement", "resolved", "growth", "healthy", "stable"]
        negative_signals = ["failure", "risk", "burnout", "overload", "critical", "decline"]
        pos_count = sum(1 for s in positive_signals if s in props_text)
        neg_count = sum(1 for s in negative_signals if s in props_text)
        if pos_count > neg_count:
            emotional_score = min(1.0, 0.6 + 0.15 * pos_count)
        elif neg_count > pos_count:
            # Negative signals still have high relevance (problems need attention)
            emotional_score = min(1.0, 0.5 + 0.2 * neg_count)
        dim_scores["emotional_tone"] = emotional_score

        # 10. Interaction Phase (lifecycle alignment)
        # Nodes closer to the active operational phase score highest
        phase_score = 0.5
        node_type_lower = node.type.lower()
        if node_type_lower in ("measurement", "experiment", "kpi", "observation"):
            phase_score = 0.95  # Deep engagement / mastery phase
        elif node_type_lower in ("role", "person", "team", "assignment"):
            phase_score = 0.80  # Active contribution phase
        elif node_type_lower in ("knowledge", "learning"):
            phase_score = 0.70  # Mastery/codification phase
        elif node_type_lower in ("organization",):
            phase_score = 0.40  # Onboarding/structural context
        dim_scores["interaction_phase"] = phase_score

        # Compute weighted sum
        composite = sum(self.matrix.weights[k] * dim_scores[k] for k in self.matrix.weights)
        composite = max(0.0, min(1.0, composite))
        return composite, dim_scores

