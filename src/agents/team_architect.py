"""Team Architect Agent (Agent 3) - Structural Role Design, Mandates & Scenarios."""

from typing import Any, Dict, List, Tuple
from src.agents.base import BaseTeamDynamicsAgent
from src.core.contracts import (
    ActionItem,
    ContextPacket,
    HypothesisItem,
    IdentifiedIssue,
)
from src.core.types import SeverityLevel


class TeamArchitectAgent(BaseTeamDynamicsAgent):
    """Designs organizational topologies, role charters, authority matrices, and structural scenarios."""

    def __init__(self):
        super().__init__(
            name="Team Architect",
            description="Designs optimal team structures, role charters, decision rights, and structural scenarios.",
        )

    async def observe(self, context_packet: ContextPacket) -> List[str]:
        return [
            f"Reviewing role charters and authority nodes connected to '{context_packet.target_node}'.",
            "Evaluating decision rights distribution vs operational bottleneck nodes.",
        ]

    async def analyze(self, observations: List[str], context_packet: ContextPacket) -> Dict[str, Any]:
        return {
            "metrics": {
                "role_clarity_score": 0.65,
                "mandate_centralization_index": 0.85,
                "structural_friction_level": 0.70,
            },
            "risks": [
                "Single point of failure on Decision Owner 042 for all dispatch approvals.",
                "Cognitive overload causing decision latency.",
            ],
            "next_questions": [
                "Which categories of Decision X can be safely delegated to automated checks or peer review?",
            ],
        }

    async def identify(self, analysis_result: Dict[str, Any]) -> List[IdentifiedIssue]:
        return [
            IdentifiedIssue(
                issue_id="arch_issue_001",
                severity=SeverityLevel.HIGH,
                description="Overly centralized decision rights: Decision Owner 042 holds 100% manual signoff without tiered delegation.",
                related_nodes=["node:role:decision_owner_042", "node:decision:decision_x"],
            )
        ]

    async def propose(self, issues: List[IdentifiedIssue]) -> Tuple[List[HypothesisItem], List[str]]:
        hypotheses = [
            HypothesisItem(
                hypothesis_id="arch_hypo_001",
                statement="Implementing a Tiered Mandate Model (Tier 1: automated pass for standard telemetry, Tier 2: peer review, Tier 3: lead signoff) reduces queue load by 60%.",
                probability=0.92,
                root_cause="Monolithic decision authority",
            )
        ]
        recommendations = [
            "Create 'Role Transition Blueprint: Tiered Dispatch Mandate'.",
            "Define clear boundary conditions for automated vs manual approvals.",
            "Pass structural plan to Role Transition Agent and Experiment Agent.",
        ]
        return hypotheses, recommendations

    async def act(self, recommendations: List[str], context_packet: ContextPacket) -> List[ActionItem]:
        return [
            ActionItem(
                action_id="act_arch_01",
                type="ROLE_REDESIGN_SPEC",
                assignee="Role Transition Agent",
                description="Deliver updated role charter with Tiered Mandate structure for Decision Owner 042.",
            )
        ]

    async def evaluate(self, actions: List[ActionItem], metrics: Dict[str, Any]) -> float:
        return 0.94
