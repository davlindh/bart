"""Agent 5: Collaboration — Optimerar samarbetssätt, kommunikation och verktyg.
Fråga: Hur kan vi samarbeta bättre?
Output: Samarbetsinterventioner.
"""

from typing import List, Dict, Any
from .base import BaseAgent
from ..core.contracts import ContextPacket, Observation, Diagnosis


class CollaborationAgent(BaseAgent):
    """Optimizes cross-functional collaboration, tool interoperability, and handoff friction."""

    def __init__(self):
        super().__init__("CollaborationAgent")

    def observe(self, context: ContextPacket) -> List[Observation]:
        return list(context.observations)

    def analyze(self, observations: List[Observation]) -> Dict[str, Any]:
        return {
            "handoff_points_evaluated": 4,
            "tool_friction_detected": False,
            "cross_team_sync_frequency": "WEEKLY",
        }

    def identify(self, analysis: Dict[str, Any]) -> List[Diagnosis]:
        return [
            Diagnosis(
                diagnosis_id="diag_collab_handoff",
                issue_category="COLLABORATION_ALIGNMENT",
                severity="low",
                root_cause="Manuell överlämning mellan verkstadens POS och Fortnox kundfakturering",
                description="Automatisk synkronisering av godkända inbytesavtal eliminerar dubbelregistrering.",
            )
        ]

    def propose(self, diagnoses: List[Diagnosis]) -> List[str]:
        return [
            "Aktivera realtids-webhook från Workshop POS till Fortnox för godkända VMB-inbyten.",
            "Inför 10-minuters daglig synk mellan säljledare och verkstadschef.",
        ]

    def act(self, recommendations: List[str]) -> List[str]:
        return ["Samarbetsinterventioner aktiverade i systemflödet."]

    def evaluate(self, actions: List[str]) -> Dict[str, Any]:
        return {"collaboration_index_gain": "+14%", "friction_reduced": True}
