"""Dynamic Pre-Cognition Engine: Intent-driven trajectory projection and proactive skill dispatch."""

import uuid
from typing import Any, Dict, List, Optional, Tuple

from ..core.types import Domain, PerspectiveWindow, ScopeLevel
from ..core.contracts import ContextPacket, Observation
from ..core.precognition import (
    ProjectIntent,
    PreCognitionTrajectory,
    TrajectoryNode,
    PredictedSkillNeed,
    AnticipatedFriction,
    RiskSeverity,
)
from ..graph.universal_erd import UniversalERDGraph
from .resolver import ContextResolver


class PreCognitiveEngine:
    """Computes intentional trajectory projections, pre-fetches context packets, and predicts skill needs."""

    # Pre-cognitive skill mapping registry
    SKILL_INTENT_MAP: Dict[str, Dict[str, Any]] = {
        "disk-persistence": {
            "keywords": ["persist", "checkpoint", "save", "restore", "state", "restart", "recover"],
            "domains": [Domain.OPERATIONAL, Domain.TRUST],
            "tools": ["persist_sandbox", "restore_sandbox_disk", "manage_snapshot", "list_persisted_sandboxes"],
            "description": "Persist and restore sandbox REPL sessions and state vectors across restarts."
        },
        "tax-optimization": {
            "keywords": ["tax", "moms", "vmb", "rut", "rot", "skatt", "voucher", "bokföring"],
            "domains": [Domain.EXCHANGE, Domain.TRUST],
            "tools": ["audit_financial_stream", "evaluate_tax_rule", "create_vmb_sale_voucher"],
            "description": "Evaluate Swedish tax regimes, optimize gross margin, and generate balanced vouchers."
        },
        "role-transition": {
            "keywords": ["role", "responsibility", "transition", "mandate", "handover", "authority"],
            "domains": [Domain.OPERATIONAL, Domain.KNOWLEDGE],
            "tools": ["create_transition_plan", "assess_role_overlap", "dispatch_communication"],
            "description": "Plan and manage organizational role migrations and mitigate transition risks."
        },
        "sandbox-execution": {
            "keywords": ["execute", "code", "run", "simulation", "python", "model", "inference"],
            "domains": [Domain.TOOLS, Domain.OPERATIONAL],
            "tools": ["create_sandbox", "execute_code", "destroy_sandbox"],
            "description": "Isolated microVM / local execution of scripts, REPL turns, and data science notebooks."
        },
        "worker-orchestration": {
            "keywords": ["schedule", "cron", "timer", "background", "daemon", "worker"],
            "domains": [Domain.OPERATIONAL, Domain.TOOLS],
            "tools": ["spawn_worker", "inspect_worker_health", "cancel_worker"],
            "description": "Orchestrate recurring background daemon tasks and asynchronous health telemetry."
        }
    }

    @classmethod
    def project_trajectory(
        cls,
        intent: ProjectIntent,
        current_node_id: str,
        graph: UniversalERDGraph,
        role: str = "CFO",
        observations: Optional[List[Observation]] = None,
    ) -> PreCognitionTrajectory:
        """Projects the multi-step cognitive path towards the intended goal state."""
        trajectory_id = f"traj_{uuid.uuid4().hex[:10]}"
        horizon = max(1, min(intent.horizon_steps, 5))
        observations = observations or []

        # 1. Trajectory projection via goal-oriented graph exploration
        predicted_nodes: List[TrajectoryNode] = []
        visited = {current_node_id}
        curr_id = current_node_id

        graph_dict = graph.to_dict()
        nodes_by_id = {n["id"]: n for n in graph_dict.get("nodes", [])}
        edges = graph_dict.get("edges", [])

        for step in range(1, horizon + 1):
            next_node_info = cls._predict_next_node(
                current_id=curr_id,
                visited=visited,
                nodes_by_id=nodes_by_id,
                edges=edges,
                intent=intent,
                step_offset=step
            )

            if next_node_info:
                predicted_nodes.append(next_node_info)
                visited.add(next_node_info.node_id)
                curr_id = next_node_info.node_id
            else:
                # Synthesize goal convergence step if no direct edge
                synth_node = TrajectoryNode(
                    step_offset=step,
                    node_id=f"synth_goal_step_{step}",
                    title=f"Intent Convergence: {intent.mandate[:30]}",
                    domain=intent.allowed_domains[0] if intent.allowed_domains else Domain.OPERATIONAL,
                    perspective_window=PerspectiveWindow.W9_ADAPTIVE_INSIGHTS,
                    transition_probability=round(max(0.40, 0.95 - (step * 0.12)), 2),
                    expected_transformation=f"Måluppfyllelse: {intent.mandate}",
                    driving_factors=["Intent Direct Path", "Goal Constraint Matching"]
                )
                predicted_nodes.append(synth_node)
                break

        # 2. Predict skill needs based on projected trajectory and intent
        predicted_skills = cls._predict_skill_needs(intent, predicted_nodes)

        # 3. Detect anticipated friction / anomalies along the path
        anticipated_frictions = cls._detect_anticipated_frictions(intent, predicted_nodes, observations)

        # 4. Pre-fetch Context Packets for the projected steps
        prefetched_packets: List[ContextPacket] = []
        for p_node in predicted_nodes[:2]:  # pre-fetch top 2 steps
            target_entity = nodes_by_id.get(p_node.node_id, {"id": p_node.node_id, "title": p_node.title})
            pkt = ContextResolver.resolve_context(
                role=role,
                purpose=f"Pre-Cognitive Preparation: {p_node.title}",
                task=f"Anticipated task for {p_node.title}",
                scope=ScopeLevel.D1_DIRECT,
                target_entity=target_entity,
                candidate_entities=list(nodes_by_id.values())[:10],
                observations=observations,
            )
            prefetched_packets.append(pkt)

        # 5. Formulate proactive recommended actions
        recommended_actions = [
            f"Pre-dispatch '{s.skill_name}' with lead-time {s.lead_time_steps} steps ({s.reasoning})"
            for s in predicted_skills
        ]
        if anticipated_frictions:
            for f in anticipated_frictions:
                recommended_actions.append(f"Pre-emptive countermeasure: {f.preventive_action}")

        return PreCognitionTrajectory(
            trajectory_id=trajectory_id,
            project_intent=intent,
            current_point_id=current_node_id,
            horizon_steps=horizon,
            predicted_nodes=predicted_nodes,
            predicted_skills=predicted_skills,
            anticipated_frictions=anticipated_frictions,
            prefetched_context_packets=prefetched_packets,
            recommended_proactive_actions=recommended_actions,
            confidence_score=0.92
        )

    @classmethod
    def _predict_next_node(
        cls,
        current_id: str,
        visited: set,
        nodes_by_id: Dict[str, Any],
        edges: List[Dict[str, Any]],
        intent: ProjectIntent,
        step_offset: int
    ) -> Optional[TrajectoryNode]:
        """Finds highest scoring neighbor node aligned with the intent."""
        candidates = []
        for e in edges:
            target_id = None
            if e.get("source") == current_id and e.get("target") not in visited:
                target_id = e.get("target")
            elif e.get("target") == current_id and e.get("source") not in visited:
                target_id = e.get("source")

            if target_id and target_id in nodes_by_id:
                target_node = nodes_by_id[target_id]
                score = cls._score_node_alignment(target_node, intent)
                candidates.append((target_node, score, e.get("relation", "RELATES_TO")))

        if not candidates:
            return None

        candidates.sort(key=lambda x: x[1], reverse=True)
        best_node, best_score, relation = candidates[0]

        domain_str = best_node.get("domain", Domain.OPERATIONAL.value)
        try:
            domain = Domain(domain_str)
        except Exception:
            domain = Domain.OPERATIONAL

        return TrajectoryNode(
            step_offset=step_offset,
            node_id=best_node.get("id", "unknown"),
            title=best_node.get("label", best_node.get("name", "Node")),
            domain=domain,
            perspective_window=PerspectiveWindow.W1_CONTEXTUALIZATION,
            transition_probability=round(min(0.98, best_score), 2),
            expected_transformation=f"Transitions via {relation} towards {intent.mandate[:25]}",
            driving_factors=[f"Edge relation: {relation}", f"Intent alignment score: {best_score:.2f}"]
        )

    @classmethod
    def _score_node_alignment(cls, node: Dict[str, Any], intent: ProjectIntent) -> float:
        """Calculates cognitive alignment score between candidate node and Project Intent."""
        score = 0.50
        node_text = f"{node.get('label', '')} {node.get('type', '')} {node.get('domain', '')}".lower()
        mandate_words = intent.mandate.lower().split()

        matches = sum(1 for w in mandate_words if len(w) > 3 and w in node_text)
        score += min(0.35, matches * 0.10)

        # Domain match bonus
        node_domain = node.get("domain", "")
        if any(d.value.lower() == node_domain.lower() for d in intent.allowed_domains):
            score += 0.15

        return min(0.99, score)

    @classmethod
    def _predict_skill_needs(
        cls,
        intent: ProjectIntent,
        predicted_nodes: List[TrajectoryNode]
    ) -> List[PredictedSkillNeed]:
        """Proactively identifies required Antigravity skills along the predicted trajectory."""
        needs = []
        combined_text = f"{intent.mandate} {' '.join(n.title for n in predicted_nodes)}".lower()

        for skill_name, meta in cls.SKILL_INTENT_MAP.items():
            keyword_matches = [kw for kw in meta["keywords"] if kw in combined_text]
            if keyword_matches:
                needs.append(PredictedSkillNeed(
                    skill_name=skill_name,
                    trigger_condition=f"Trajectory steps match keywords: {', '.join(keyword_matches)}",
                    confidence=round(min(0.99, 0.70 + (len(keyword_matches) * 0.10)), 2),
                    lead_time_steps=1,
                    reasoning=f"Anticipated requirement for {skill_name}: {meta['description']}",
                    tool_suggestions=meta["tools"]
                ))

        # Always ensure disk-persistence is suggested for complex projects to safeguard state
        if not any(n.skill_name == "disk-persistence" for n in needs) and len(predicted_nodes) >= 2:
            needs.append(PredictedSkillNeed(
                skill_name="disk-persistence",
                trigger_condition="Multi-step state trajectory checkpointing",
                confidence=0.85,
                lead_time_steps=2,
                reasoning="Self-preservation: persist ERD state and variables before complex transitions.",
                tool_suggestions=["persist_sandbox", "manage_snapshot"]
            ))

        return needs

    @classmethod
    def _detect_anticipated_frictions(
        cls,
        intent: ProjectIntent,
        predicted_nodes: List[TrajectoryNode],
        observations: List[Observation]
    ) -> List[AnticipatedFriction]:
        """Predicts operational, financial, or ethical friction points in advance."""
        frictions = []

        # Check for overtime/burnout trajectory
        has_overtime_obs = any("overtime" in o.metric_name.lower() or o.metric_value > 10 for o in observations if isinstance(o.metric_value, (int, float)))
        if has_overtime_obs:
            frictions.append(AnticipatedFriction(
                friction_id=f"fric_{uuid.uuid4().hex[:8]}",
                domain=Domain.TRUST,
                severity=RiskSeverity.HIGH,
                lead_time_steps=1,
                predicted_issue="Kritiskt personalberoende och risk för fördröjning pga övertidsbelastning",
                root_factor="Historiska tidrapporter indikerar ojämn arbetsfördelning",
                preventive_action="Aktivera WellbeingAgent och initiera omfördelning av uppgifter före nästa sprint.",
                confidence=0.88
            ))

        # Check for authority / role transition ambiguity
        role_nodes = [n for n in predicted_nodes if "role" in n.title.lower() or n.domain == Domain.KNOWLEDGE]
        if len(role_nodes) >= 2:
            frictions.append(AnticipatedFriction(
                friction_id=f"fric_{uuid.uuid4().hex[:8]}",
                domain=Domain.OPERATIONAL,
                severity=RiskSeverity.MEDIUM,
                lead_time_steps=2,
                predicted_issue="Mandatglapp eller rollöverlappning vid strukturell förändring",
                root_factor="Flera angränsande rollnoder i samma beslutskedja",
                preventive_action="Generera en TransitionPlan med tydlig ansvarsmatris (RACI).",
                confidence=0.82
            ))

        return frictions

    @classmethod
    def evaluate_intent_convergence(
        cls,
        intent: ProjectIntent,
        trajectory: Optional['PreCognitionTrajectory'] = None,
        current_metrics: Optional[Dict[str, Any]] = None,
        current_state: Optional[Dict[str, Any]] = None,
    ) -> 'IntentStatus':
        """Evaluates how close the project is to achieving the declared intent.

        Returns:
            - ACHIEVED: All target KPIs are met.
            - CONVERGING: ≥2 of 3 target KPIs (or ≥50% of goals) are within 10% of desired values.
            - BLOCKED: Any HIGH/CRITICAL friction persists at lead_time_steps ≤ 0.
            - ACTIVE: Default — progress is being made but goals not yet met.
        """
        from ..core.precognition import IntentStatus

        # Check for blocking frictions first (highest priority)
        if trajectory and trajectory.anticipated_frictions:
            for f in trajectory.anticipated_frictions:
                sev = getattr(f, "severity", None)
                sev_str = str(getattr(sev, "value", sev)).lower()
                lead = getattr(f, "lead_time_steps", 0)
                if sev_str in ("high", "critical") and lead <= 0:
                    return IntentStatus.BLOCKED

        metrics = current_metrics or current_state or {}

        # Combine target_kpis and desired_state goals
        goals: Dict[str, Any] = {}
        if intent.target_kpis:
            goals.update(intent.target_kpis)
        if intent.desired_state:
            goals.update(intent.desired_state)

        if not goals or not metrics:
            # Without KPIs, check trajectory confidence
            if trajectory and trajectory.confidence_score >= 0.90:
                return IntentStatus.CONVERGING
            return IntentStatus.ACTIVE

        met_count = 0
        near_count = 0
        evaluated_keys = 0

        for k, target in goals.items():
            if k not in metrics:
                continue
            actual = metrics[k]
            evaluated_keys += 1

            if isinstance(target, (int, float)) and isinstance(actual, (int, float)):
                if target == 0:
                    if actual == 0:
                        met_count += 1
                    continue
                ratio = actual / target if target != 0 else 0
                if ratio >= 1.0:
                    met_count += 1
                elif ratio >= 0.90:
                    near_count += 1
            else:
                # Exact match check (e.g. "PASSED")
                if str(actual).strip().upper() == str(target).strip().upper():
                    met_count += 1

        total = evaluated_keys if evaluated_keys > 0 else len(goals)

        if met_count >= total and total > 0:
            return IntentStatus.ACHIEVED

        if (met_count + near_count) >= max(1, total // 2):
            return IntentStatus.CONVERGING

        return IntentStatus.ACTIVE

