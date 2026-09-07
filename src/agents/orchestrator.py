"""Agent 11: Pre-Cognitive Master Orchestrator — Bestämmer nästa steg och orkestrerar agenterna.
Fråga: Vad ska göras härnäst och i vilken ordning baserat på intentional förhandskognition?
Output: Nästa actions, förutsagda färdighetsbehov & pre-emptiva prioriteringar.
"""

from typing import List, Dict, Any, Optional
from .base import BaseAgent
from ..core.types import PerspectiveWindow, Domain
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

    @classmethod
    def generate_next_evolutionary_phase(
        cls,
        current_window: PerspectiveWindow,
        previous_outcome: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Generates the next evolutionary phase when the current phase has converged.
        Creates continuous self-generating phases following the Omnipod & Omniframez lifecycle:
        W5/W6 (Friction Mitigation & Financial Order)
          -> W8 (Innovation & Technology Pilots)
          -> W2 (Matching & Commercial Offering)
          -> W4 (Resource Allocation & Scaling)
          -> W1 (Contextualization & Strategic Expansion)
          -> W9 (Adaptive Insights & Continuous Meta-Evolution)
          -> (Loop back to W8/W2 for next generative cycle)
        """
        previous_outcome = previous_outcome or {}

        if current_window in (PerspectiveWindow.W5_FINANCIAL_MANAGEMENT, PerspectiveWindow.W6_PERSONNEL_MANAGEMENT):
            return {
                "phase_id": "phase_w8_growth_innovation",
                "phase_number": 3,
                "window": PerspectiveWindow.W8_INNOVATION_TECH,
                "role": "Innovationsledare",
                "purpose": "Aktivera frigjord kapacitet i nya teknik- och tillväxtinitiativ",
                "task": "Pilotera AI-assisterad kabeldiagnostik och smart cirkulärt robotabonnemang",
                "target_node_id": "pilot:ai_cable_diagnostic_fleet",
                "target_entity": {
                    "id": "pilot:ai_cable_diagnostic_fleet",
                    "name": "AI-Assisterad Kabeldiagnostik & Smart Flottabonnemang",
                    "domain": "Tools",
                    "type": "PilotProject",
                    "stage": "PILOT",
                    "budget_allocated_sek": 18000.0,
                    "target_fault_detection_minutes": 25,
                },
                "observations": [
                    Observation(
                        observation_id="obs_rd_capacity",
                        source="Orchestrator Telemetry",
                        domain=Domain.OPERATIONAL,
                        window=PerspectiveWindow.W8_INNOVATION_TECH,
                        entity_id="pilot:ai_cable_diagnostic_fleet",
                        metric_name="available_weekly_hours",
                        metric_value=13.5,
                        confidence=0.98,
                    ),
                    Observation(
                        observation_id="obs_cable_fault_frequency",
                        source="Support Ticket Logs",
                        domain=Domain.TOOLS,
                        window=PerspectiveWindow.W8_INNOVATION_TECH,
                        entity_id="pilot:ai_cable_diagnostic_fleet",
                        metric_name="cable_fault_ticket_share_pct",
                        metric_value=45.0,
                        confidence=0.95,
                    ),
                ],
                "recommended_actions": [
                    "Designa 21-dagars fältpilot med 15 nyckelkunder för AI-kabeldiagnostik",
                    "Integrera fältapp med realtidsavkänning av slingkabelns resistans och brottspunkt",
                    "Tillämpa FoU-forskningsavdrag (FOU_FORSKNINGSAVDRAG) för mjukvaruutveckling",
                ],
            }
        elif current_window == PerspectiveWindow.W8_INNOVATION_TECH:
            return {
                "phase_id": "phase_w2_commercial_matching",
                "phase_number": 4,
                "window": PerspectiveWindow.W2_MATCHING,
                "role": "Affärsutvecklare",
                "purpose": "Matcha verifierad AI-innovation mot prioriterade kundsegment",
                "task": "Paketera cirkulärt VMB+RUT robotabonnemang för privat- och företagskunder",
                "target_node_id": "offering:circular_robot_subscription",
                "target_entity": {
                    "id": "offering:circular_robot_subscription",
                    "name": "Cirkulärt Robotabonnemang 'Grön Robotkomfort'",
                    "domain": "Exchange",
                    "type": "CommercialProduct",
                    "subscription_price_sek_month": 495.0,
                    "target_conversion_rate_pct": 35.0,
                },
                "observations": [
                    Observation(
                        observation_id="obs_customer_readiness",
                        source="CRM / Fortnox Customer",
                        domain=Domain.EXCHANGE,
                        window=PerspectiveWindow.W2_MATCHING,
                        entity_id="offering:circular_robot_subscription",
                        metric_name="high_affinity_customers_count",
                        metric_value=38,
                        confidence=0.94,
                    ),
                    Observation(
                        observation_id="obs_vmb_inventory_ready",
                        source="Fortnox Inbyteslager",
                        domain=Domain.OPERATIONAL,
                        window=PerspectiveWindow.W2_MATCHING,
                        entity_id="offering:circular_robot_subscription",
                        metric_name="serviced_inbytes_mowers",
                        metric_value=12,
                        confidence=0.99,
                    ),
                ],
                "recommended_actions": [
                    "A/B-testa månadsabonnemang (495 kr/mån inkl service) mot engångsköp",
                    "Aktivera automatisk RUT-beräkning (50% på arbetskostnad) i iPad-kassan",
                    "Rikta inbyteserbjudande till kunder med maskiner äldre än 4 år",
                ],
            }
        elif current_window == PerspectiveWindow.W2_MATCHING:
            return {
                "phase_id": "phase_w4_fleet_scaling",
                "phase_number": 5,
                "window": PerspectiveWindow.W4_RESOURCE_ALLOCATION,
                "role": "Verkstadschef",
                "purpose": "Skala fält- och verkstadskapacitet efter hög abonnemangsefterfrågan",
                "task": "Allokera scheman, fordon och reservdelslager för 100+ aktiva robotabonnemang",
                "target_node_id": "alloc:field_fleet_expansion",
                "target_entity": {
                    "id": "alloc:field_fleet_expansion",
                    "name": "Kapacitetsallokering: Fältflotta 100+ Robotar",
                    "domain": "Operational",
                    "type": "ResourcePlan",
                    "active_contracts": 42,
                    "pipeline_demand": 85,
                },
                "observations": [
                    Observation(
                        observation_id="obs_conversion_rate",
                        source="MeasurementAgent",
                        domain=Domain.EXCHANGE,
                        window=PerspectiveWindow.W4_RESOURCE_ALLOCATION,
                        entity_id="alloc:field_fleet_expansion",
                        metric_name="subscription_conversion_pct",
                        metric_value=41.2,
                        confidence=0.97,
                    ),
                ],
                "recommended_actions": [
                    "Allokera 1 fältservicetekniker dedikerad till abonnemangsförebyggande service",
                    "Optimera ruttplanering för kabeldiagnostik via spatial klusteranalys",
                ],
            }
        else:
            cycle_num = previous_outcome.get("cycle_number", 2) + 1
            return {
                "phase_id": f"phase_w8_nextgen_cycle_{cycle_num}",
                "phase_number": 6,
                "window": PerspectiveWindow.W8_INNOVATION_TECH,
                "role": "Innovationsledare",
                "purpose": f"Initiera Cykel {cycle_num}: Autonom flotthantering och prediktivt underhåll",
                "task": "Integrera maskininlärningsmodell för batteridegradering och tidig inbytesoffert",
                "target_node_id": f"pilot:predictive_battery_telemetry_{cycle_num}",
                "target_entity": {
                    "id": f"pilot:predictive_battery_telemetry_{cycle_num}",
                    "name": f"Prediktiv Batteritelemetri & Cykel {cycle_num}",
                    "domain": "Tools",
                    "type": "NextGenPilot",
                },
                "observations": [
                    Observation(
                        observation_id=f"obs_cycle_{cycle_num}_trigger",
                        source="AdaptiveInsightsWindow",
                        domain=Domain.OPERATIONAL,
                        window=PerspectiveWindow.W9_ADAPTIVE_INSIGHTS,
                        entity_id=f"pilot:predictive_battery_telemetry_{cycle_num}",
                        metric_name="ecosystem_convergence_index",
                        metric_value=98.5,
                        confidence=0.99,
                    ),
                ],
                "recommended_actions": [
                    f"Starta Cykel {cycle_num} med fokus på autonom maskintelemetri",
                    "Utvärdera API-integration mot Husqvarna Fleet Services",
                ],
            }
