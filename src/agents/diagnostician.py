"""Agent 2: Diagnostiker — Analyserar mönster, identifierar problem och flaskhalsar.
Fråga: Varför händer det?
Output: Hypoteser & rotorsaker.
"""

from typing import List, Dict, Any
from .base import BaseAgent
from ..core.contracts import ContextPacket, Observation, Diagnosis


class DiagnosticianAgent(BaseAgent):
    """Analyzes empirical observations, identifies bottlenecks, and isolates root causes."""

    def __init__(self):
        super().__init__("DiagnosticianAgent")

    def observe(self, context: ContextPacket) -> List[Observation]:
        return list(context.observations)

    def analyze(self, observations: List[Observation]) -> Dict[str, Any]:
        bottlenecks = []
        overtime_flags = []
        for o in observations:
            if "overtime" in o.metric_name.lower() and isinstance(o.metric_value, (int, float)) and o.metric_value > 10:
                overtime_flags.append(o)
            if o.source == "FORTNOX_INVOICE" and isinstance(o.raw_payload, dict):
                # Check for tax or margin suboptimalities
                payload = o.raw_payload
                if payload.get("is_used_good") and payload.get("current_tax_rule") == "MOMS_25":
                    bottlenecks.append({"type": "VMB_MISCLASSIFICATION", "ref": o.entity_id})
                if payload.get("is_garden_or_installation_work") and payload.get("current_tax_rule") == "MOMS_25":
                    bottlenecks.append({"type": "RUT_UNUSED", "ref": o.entity_id})

        return {
            "total_observed": len(observations),
            "overtime_flags": overtime_flags,
            "bottlenecks": bottlenecks,
        }

    def identify(self, analysis: Dict[str, Any]) -> List[Diagnosis]:
        diagnoses = []
        for b in analysis.get("bottlenecks", []):
            diagnoses.append(
                Diagnosis(
                    diagnosis_id=f"diag_{b['type']}_{b['ref']}",
                    issue_category=b["type"],
                    severity="high" if "VMB" in b["type"] else "medium",
                    root_cause=f"Suboptimal skatte-/processkonfiguration i transaktionsflödet för {b['ref']}",
                    financial_impact_sek=2000.0,
                    description=f"Flaskhals upptäckt ({b['type']}): Suboptimal redovisningsmetod tillämpas på {b['ref']}.",
                )
            )

        if analysis.get("overtime_flags"):
            diagnoses.append(
                Diagnosis(
                    diagnosis_id="diag_overtime_bottleneck",
                    issue_category="WORKLOAD_OVERLOAD",
                    severity="high",
                    root_cause="Obalanserad resursallokering mellan installation och service",
                    financial_impact_sek=15000.0,
                    description="Övertidstimmar överstiger tröskelvärde (10h/vecka), vilket indikerar operativ flaskhals i fältteamet.",
                )
            )

        if not diagnoses:
            diagnoses.append(
                Diagnosis(
                    diagnosis_id="diag_stable_baseline",
                    issue_category="HEALTHY_BASELINE",
                    severity="low",
                    root_cause="Inga kritiska friktioner eller flaskhalsar detekterade",
                    description="Systemet opererar inom normala parametrar för drift och regelefterlevnad.",
                )
            )

        return diagnoses

    def propose(self, diagnoses: List[Diagnosis]) -> List[str]:
        proposals = []
        for d in diagnoses:
            if d.issue_category == "WORKLOAD_OVERLOAD":
                proposals.append("Team Architect bör omfördela arbetsmandat och allokera extra installationskapacitet.")
            elif "VMB" in d.issue_category or "RUT" in d.issue_category:
                proposals.append(f"Justera skattestrategi för {d.diagnosis_id} via VMB/RUT-omklassificering.")
        return proposals or ["Fortsätt övervakning enligt standardrutin."]

    def act(self, recommendations: List[str]) -> List[str]:
        return [f"Hypoteser och rotorsaker överförda till Team Architect och Role Transition ({len(recommendations)} åtgärder initierade)."]

    def evaluate(self, actions: List[str]) -> Dict[str, Any]:
        return {"diagnostic_certainty": 0.92, "handoff_ready": True}
