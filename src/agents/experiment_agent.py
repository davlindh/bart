"""Agent 12: Experiment Agent — Omvandlar förslag till testbara experiment.
Fråga: Hur testar vi detta på ett säkert sätt?
Output: Experimentplan.
"""

from typing import List, Dict, Any
from .base import BaseAgent
from ..core.contracts import ContextPacket, Observation, Diagnosis


class ExperimentAgent(BaseAgent):
    """Designs controlled tests, hypotheses, success criteria, and pilot populations."""

    def __init__(self):
        super().__init__("ExperimentAgent")

    def observe(self, context: ContextPacket) -> List[Observation]:
        return list(context.observations)

    def analyze(self, observations: List[Observation]) -> Dict[str, Any]:
        return {
            "testable_interventions": 2,
            "pilot_population_size": 10,
            "duration_days": 14,
        }

    def identify(self, analysis: Dict[str, Any]) -> List[Diagnosis]:
        return [
            Diagnosis(
                diagnosis_id="diag_experiment_design",
                issue_category="PILOT_TESTING",
                severity="low",
                root_cause="Behov av att validera kunders acceptans av ny RUT-faktureringsmodell innan full utrullning",
                description="Experiment designat: 10 slumpmässigt utvalda privatkunder erhåller ny offert med tydliggjort 50% RUT-avdrag.",
            )
        ]

    def propose(self, diagnoses: List[Diagnosis]) -> List[str]:
        return [
            "Hypotes: RUT-tydlighet på offertens förstasida ökar signering från 42% till 65%.",
            "Mätmetod: Spåra konverteringsgrad och beslutstid under 14 dagar.",
            "Framgångskriterium: >20% ökning i snabbare kundacceptans.",
        ]

    def act(self, recommendations: List[str]) -> List[str]:
        return ["Experimentplan driftsatt: Pilotcohort aktiv i 14 dagar."]

    def evaluate(self, actions: List[str]) -> Dict[str, Any]:
        return {
            "experiment_status": "ACTIVE_PILOT",
            "sample_size": 10,
            "target_metric": "OFFER_CONVERSION_RATE",
        }
