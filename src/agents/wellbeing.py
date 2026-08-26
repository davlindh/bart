"""Wellbeing Agent (Agent 6) - Cognitive Load, Friction & Psychological Safety."""

from typing import Any, Dict, List, Tuple
from src.agents.base import BaseTeamDynamicsAgent
from src.core.contracts import (
    ActionItem,
    ContextPacket,
    HypothesisItem,
    IdentifiedIssue,
)
from src.core.types import SeverityLevel


class WellbeingAgent(BaseTeamDynamicsAgent):
    """Monitors cognitive load, burnout risks, friction, and promotes psychological safety."""

    def __init__(self):
        super().__init__(
            name="Wellbeing Agent",
            description="Identifies cognitive load, on-call friction, burnout risks, and fosters psychological safety.",
        )

    async def observe(self, context_packet: ContextPacket) -> List[str]:
        return [
            "Assessing workload concentration and off-hours alerting load on Decision Owner and On-Call Engineers.",
            "Evaluating sprint friction signals and overtime logs.",
        ]

    async def analyze(self, observations: List[str], context_packet: ContextPacket) -> Dict[str, Any]:
        return {
            "metrics": {
                "team_health_index": 72.0,  # 0-100 scale
                "cognitive_load_score": 82.0,  # 0-100 scale (high)
                "burnout_risk_indicator": "ELEVATED",
            },
            "risks": [
                "Decision Owner 042 experiencing decision fatigue due to repeated urgent signoff requests during degraded pipeline events."
            ],
            "next_questions": ["Can on-call rotation be distributed across 3 qualified engineers?"],
        }

    async def identify(self, analysis_result: Dict[str, Any]) -> List[IdentifiedIssue]:
        return [
            IdentifiedIssue(
                issue_id="wellbeing_issue_001",
                severity=SeverityLevel.HIGH,
                description="Cognitive overload & burnout risk: Decision Owner is the sole escalation target for 100% of daily approvals.",
                related_nodes=["person:user_b", "node:role:decision_owner_042"],
            )
        ]

    async def propose(self, issues: List[IdentifiedIssue]) -> Tuple[List[HypothesisItem], List[str]]:
        hypotheses = [
            HypothesisItem(
                hypothesis_id="wellbeing_hypo_001",
                statement="Distributing approval load reduces cognitive load index from 82 to < 50 and improves decision quality.",
                probability=0.91,
                root_cause="Over-concentration of operational responsibility",
            )
        ]
        recommendations = [
            "Establish on-call rotation and secondary backup approver.",
            "Implement automated health and rest periods following high-severity incident weeks.",
        ]
        return hypotheses, recommendations

    async def act(self, recommendations: List[str], context_packet: ContextPacket) -> List[ActionItem]:
        return [
            ActionItem(
                action_id="act_wellbeing_01",
                type="POLICY_UPDATE",
                assignee="Team Lead",
                description="Enact secondary approver rotation to mitigate individual burnout risk.",
            )
        ]

    async def evaluate(self, actions: List[ActionItem], metrics: Dict[str, Any]) -> float:
        return 0.95
