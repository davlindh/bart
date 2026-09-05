"""Agent 11: Pre-Cognitive Master Orchestrator — Bestämmer nästa steg och orkestrerar agenterna.
Fråga: Vad ska göras härnäst och i vilken ordning baserat på intentional förhandskognition?
Output: Nästa actions, förutsagda färdighetsbehov & pre-emptiva prioriteringar.
"""

from typing import List, Dict, Any, Optional
from .base import BaseAgent
from ..core.contracts import ContextPacket, Observation, Diagnosis
from ..core.precognition import ProjectIntent, PreCognitionTrajectory, PredictedSkillNeed
from ..graph.universal_erd import UniversalERDGraph
from ..context_engine.precognition import PreCognitiveEngine


class OrchestratorAgent(BaseAgent):
    """Pre-cognitive master orchestrator scheduling agent activations and proactive skill dispatch."""

    def __init__(self):
        super().__init__("OrchestratorAgent")
        self.last_trajectory: Optional[PreCognitionTrajectory] = None

    def observe(self, context: ContextPacket) -> List[Observation]:
        return list(context.observations)

    def analyze(self, observations: List[Observation]) -> Dict[str, Any]:
        has_bottlenecks = any("overtime" in o.metric_name.lower() or "friction" in o.metric_name.lower() for o in observations)
        return {
            "active_agents_ready": 12,
            "next_critical_phase": "PRE_COGNITIVE_PROJECTION" if not has_bottlenecks else "FRICTION_PREVENTION",
            "priority_domain": "OPERATIONAL_FINANCIAL",
            "has_bottlenecks": has_bottlenecks,
            "observations_count": len(observations),
        }

    def identify(self, analysis: Dict[str, Any]) -> List[Diagnosis]:
        diagnoses = [
            Diagnosis(
                diagnosis_id="diag_orchestration_plan",
                issue_category="ORCHESTRATION_FLOW",
                severity="low" if not analysis.get("has_bottlenecks") else "medium",
                root_cause="Behov av målstyrd sekvens mellan diagnos, färdighetsdispatch och självbevarande",
                description="Orkestratorn har synkroniserat agentkedjan med intentional förhandskognition.",
            )
        ]
        if analysis.get("has_bottlenecks"):
            diagnoses.append(Diagnosis(
                diagnosis_id="diag_friction_detected",
                issue_category="WORKFLOW_BOTTLENECK",
                severity="high",
                root_cause="Identifierad operativ friktion eller övertidsbelastning i observerad telemetri",
                description="Pre-kognitiv avvikelsehantering kräver förebyggande åtgärder innan eskalering.",
            ))
        return diagnoses

    def propose(self, diagnoses: List[Diagnosis]) -> List[str]:
        proposals = [
            "Aktivera 'disk-persistence' för att säkra pågående projekttillstånd i SQLite WAL.",
            "Lås resurser i Window 5 (Ekonomihantering) och pre-fetcha skattekalkyler.",
            "Trigger Meta-Learning loop efter avslutad mätning för självförbättrande heuristik.",
        ]
        if any(d.severity == "high" for d in diagnoses):
            proposals.insert(0, "Aktivera WellbeingAgent och initiera förebyggande resursomfördelning.")
        return proposals

    def act(self, recommendations: List[str]) -> List[str]:
        return [
            f"Orkestreringsorder utfärdad: {r}" for r in recommendations
        ]

    def evaluate(self, actions: List[str]) -> Dict[str, Any]:
        return {
            "orchestration_efficiency": "OPTIMAL",
            "pipeline_status": "CONVERGED",
            "precognition_mode": "ACTIVE",
            "actions_dispatched": len(actions),
        }

    def orchestrate_project(
        self,
        intent: ProjectIntent,
        current_node_id: str,
        graph: UniversalERDGraph,
        context: ContextPacket,
    ) -> Dict[str, Any]:
        """Executes goal-directed intentional orchestration with dynamic trajectory pre-cognition."""
        trajectory = PreCognitiveEngine.project_trajectory(
            intent=intent,
            current_node_id=current_node_id,
            graph=graph,
            role=context.role,
            observations=context.observations,
        )
        self.last_trajectory = trajectory

        # Run standard 6-step loop with pre-cognitive insight
        base_result = self.run(context)

        # Merge pre-cognitive recommendations
        enhanced_recommendations = list(base_result.recommendations)
        enhanced_recommendations.extend(trajectory.recommended_proactive_actions)

        return {
            "orchestrator_status": base_result.status.value,
            "trajectory_id": trajectory.trajectory_id,
            "predicted_nodes": [n.model_dump() for n in trajectory.predicted_nodes],
            "predicted_skills": [s.model_dump() for s in trajectory.predicted_skills],
            "anticipated_frictions": [f.model_dump() for f in trajectory.anticipated_frictions],
            "recommendations": enhanced_recommendations,
            "prefetched_context_count": len(trajectory.prefetched_context_packets),
            "confidence_score": trajectory.confidence_score,
        }
