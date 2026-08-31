"""Agent 3: Team Architect — Designar optimal teamstruktur, roller och mandat.
Fråga: Hur bör teamet vara utformat?
Output: Strukturförslag & scenarier.
"""

from typing import List, Dict, Any
from .base import BaseAgent
from ..core.contracts import ContextPacket, Observation, Diagnosis


class TeamArchitectAgent(BaseAgent):
    """Designs organizational structures, aligns mandates, and configures role topologies."""

    def __init__(self):
        super().__init__("TeamArchitectAgent")

    def observe(self, context: ContextPacket) -> List[Observation]:
        return list(context.observations)

    def analyze(self, observations: List[Observation]) -> Dict[str, Any]:
        return {
            "current_mandates_analyzed": True,
            "span_of_control_balanced": True,
            "role_confusion_index": 0.15,
        }

    def identify(self, analysis: Dict[str, Any]) -> List[Diagnosis]:
        return [
            Diagnosis(
                diagnosis_id="diag_structure_design",
                issue_category="STRUCTURE_OPTIMIZATION",
                severity="low",
                root_cause="Behov av renodlade beslutsmandat mellan sälj, installation och eftermarknad",
                description="Designad struktur särskiljer VMB-inbytesverifiering (Ekonomi) från teknisk RUT-installation (Fältteam).",
            )
        ]

    def propose(self, diagnoses: List[Diagnosis]) -> List[str]:
        return [
            "Inrätta formellt mandat för 'Inbytesansvarig' med direkt attest för VMB-kalkylering.",
            "Delegera RUT-beräkning direkt till fältsäljare vid offertkonstruktion.",
            "Allokera 10% buffertkapacitet till serviceverkstad för att absorbera övertidstoppar.",
        ]

    def act(self, recommendations: List[str]) -> List[str]:
        return [f"Strukturförslag och rollscenarier ({len(recommendations)} st) formaliserade i Universal ERD."]

    def evaluate(self, actions: List[str]) -> Dict[str, Any]:
        return {
            "structural_cohesion_score": 92.0,
            "projected_friction_reduction_pct": 28.5,
        }
