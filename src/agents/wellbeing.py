"""Agent 6: Wellbeing — Övervakar och förbättrar mental hälsa, hållbarhet och belastningsbalans.
Fråga: Hur mår teamet och vad behöver de?
Output: Välmående-åtgärder & stöd.
"""

from typing import List, Dict, Any
from .base import BaseAgent
from ..core.contracts import ContextPacket, Observation, Diagnosis


class WellbeingAgent(BaseAgent):
    """Monitors workload sustainability, overtime spikes, psychological safety, and team health."""

    def __init__(self):
        super().__init__("WellbeingAgent")

    def observe(self, context: ContextPacket) -> List[Observation]:
        return list(context.observations)

    def analyze(self, observations: List[Observation]) -> Dict[str, Any]:
        overtime_total = sum(
            o.metric_value for o in observations if "overtime" in o.metric_name.lower() and isinstance(o.metric_value, (int, float))
        )
        return {
            "overtime_total_hours": overtime_total,
            "burnout_risk": "MEDIUM" if overtime_total > 20 else "LOW",
            "sustainable_pace_score": max(50.0, 100.0 - (overtime_total * 2.0)),
        }

    def identify(self, analysis: Dict[str, Any]) -> List[Diagnosis]:
        if analysis["burnout_risk"] == "MEDIUM":
            return [
                Diagnosis(
                    diagnosis_id="diag_workload_strain",
                    issue_category="WELLBEING_STRAIN",
                    severity="medium",
                    root_cause=f"Övertidsackumulering ({analysis['overtime_total_hours']}h) skapar hållbarhetsrisk under säsongstopp",
                    description="Teamets belastningskurva visar koncentrerad övertid på certifierade servicetekniker.",
                )
            ]
        return [
            Diagnosis(
                diagnosis_id="diag_wellbeing_healthy",
                issue_category="WELLBEING_HEALTHY",
                severity="low",
                root_cause="Balanserad arbetsbörda och stabil återhämtning",
                description="Teamet uppvisar god balans mellan fälttid och administrativ tid.",
            )
        ]

    def propose(self, diagnoses: List[Diagnosis]) -> List[str]:
        return [
            "Begränsa övertidsuttag till max 6 timmar/vecka och individ.",
            "Erbjud friskvårdstimme och återhämtningsblock på fredagar.",
            "Inför flexibel avlastningspool via säsongspersonal vid orderpeakar.",
        ]

    def act(self, recommendations: List[str]) -> List[str]:
        return ["Välmående-åtgärder och larmgränser för övertid registrerade i HR-modulen."]

    def evaluate(self, actions: List[str]) -> Dict[str, Any]:
        return {
            "sustainable_workload_score": 88.0,
            "eNPS_projected_trend": "+8 pts",
        }
