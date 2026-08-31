"""Agent 4: Role Transition — Planerar och genomför smidiga rollförändringar.
Fråga: Hur tar vi oss från nuläge till önskat läge?
Output: Övergångsplan & kommunikation.
"""

from typing import List, Dict, Any
from .base import BaseAgent
from ..core.contracts import ContextPacket, Observation, Diagnosis


class RoleTransitionAgent(BaseAgent):
    """Plans transition roadmaps, manages change risk, and aligns team communication."""

    def __init__(self):
        super().__init__("RoleTransitionAgent")

    def observe(self, context: ContextPacket) -> List[Observation]:
        return list(context.observations)

    def analyze(self, observations: List[Observation]) -> Dict[str, Any]:
        return {
            "transition_complexity": "LOW_TO_MEDIUM",
            "competency_gaps": ["RUT_SKATTEVERKET_PORTAL", "VMB_MARGINALBOKFORING"],
            "stakeholders_affected": ["Ekonomiansvarig", "Verkstadsledare", "Fältsäljare"],
        }

    def identify(self, analysis: Dict[str, Any]) -> List[Diagnosis]:
        return [
            Diagnosis(
                diagnosis_id="diag_transition_readiness",
                issue_category="TRANSITION_READINESS",
                severity="low",
                root_cause="Kompetensgap rörande digital inbytesmall och RUT-ansökan",
                description="Övergångsrisk minimeras genom en 14-dagars parallellfas med digitala checklistor.",
            )
        ]

    def propose(self, diagnoses: List[Diagnosis]) -> List[str]:
        return [
            "Fas 1 (Vecka 1): Briefing och lansering av digital inbytesmall i POS.",
            "Fas 2 (Vecka 2): Pilot med 5 transaktioner och dubbelkoll av BAS-konton.",
            "Fas 3 (Vecka 3): Full implementering och överlämning till ordinarie attest.",
        ]

    def act(self, recommendations: List[str]) -> List[str]:
        return [
            "Övergångsplan skapad: 3 faser över 14 dagar.",
            "Kommunikationsnotis förberedd för Slack #ekonomi-och-salj.",
        ]

    def evaluate(self, actions: List[str]) -> Dict[str, Any]:
        return {
            "transition_plan_status": "READY_FOR_COMMUNICATION",
            "adoption_risk_level": "LOW",
        }
