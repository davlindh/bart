"""Agent 1: Observer — Samlar signaler och skapar en objektiv nulägesbild.
Fråga: Vad händer i teamet just nu?
Output: Nulägesbild & signaler.
"""

from typing import List, Dict, Any
from .base import BaseAgent
from ..core.contracts import ContextPacket, Observation, Diagnosis
from ..core.types import Domain, PerspectiveWindow


class ObserverAgent(BaseAgent):
    """Gathers empirical signals across team communication, ERP, POS, and time logs."""

    def __init__(self):
        super().__init__("ObserverAgent")

    def observe(self, context: ContextPacket) -> List[Observation]:
        observations = list(context.observations)
        entity = context.primary_entity

        # Extract signals from context payload
        if "transactions" in entity:
            for tx in entity["transactions"]:
                obs = Observation(
                    observation_id=f"obs_tx_{tx.get('transaction_id', 'unknown')}",
                    source="FORTNOX_INVOICE",
                    domain=Domain.EXCHANGE,
                    window=PerspectiveWindow.W5_FINANCIAL_MANAGEMENT,
                    entity_id=tx.get("transaction_id", "unknown"),
                    metric_name="gross_amount",
                    metric_value=tx.get("gross_amount", 0.0),
                    confidence=1.0,
                    raw_payload=tx,
                )
                observations.append(obs)

        if "overtime_hours" in entity:
            observations.append(
                Observation(
                    observation_id="obs_team_overtime",
                    source="FORTNOX_TIMESHEET",
                    domain=Domain.OPERATIONAL,
                    window=PerspectiveWindow.W6_PERSONNEL_MANAGEMENT,
                    entity_id="team_workload",
                    metric_name="overtime_hours",
                    metric_value=entity.get("overtime_hours", 0.0),
                    confidence=0.95,
                )
            )

        if not observations:
            observations.append(
                Observation(
                    observation_id="obs_baseline",
                    source="SYSTEM_POLL",
                    domain=Domain.OPERATIONAL,
                    window=PerspectiveWindow.W1_CONTEXTUALIZATION,
                    entity_id="baseline_stream",
                    metric_name="status",
                    metric_value="active",
                    confidence=1.0,
                )
            )

        return observations

    def analyze(self, observations: List[Observation]) -> Dict[str, Any]:
        return {
            "signal_count": len(observations),
            "sources": list(set(o.source for o in observations)),
            "domains": list(set(o.domain.value for o in observations)),
            "high_variance_signals": [o.observation_id for o in observations if isinstance(o.metric_value, (int, float)) and o.metric_value > 15],
        }

    def identify(self, analysis: Dict[str, Any]) -> List[Diagnosis]:
        diagnoses = []
        if analysis["signal_count"] > 0:
            diagnoses.append(
                Diagnosis(
                    diagnosis_id="diag_obs_summary",
                    related_observations=analysis["high_variance_signals"],
                    issue_category="BASELINE_OBSERVED",
                    severity="low",
                    root_cause="Empirisk datainsamling slutförd utan avbrott",
                    description=f"Samlat in {analysis['signal_count']} objektiva signaler från källor: {', '.join(analysis['sources'])}.",
                )
            )
        return diagnoses

    def propose(self, diagnoses: List[Diagnosis]) -> List[str]:
        return ["Vidarebefordra objektiv nulägesbild till Diagnostikern för flaskhalsanalys."]

    def act(self, recommendations: List[str]) -> List[str]:
        return ["Nulägesbild och signaler indexerade i Universal ERD."]

    def evaluate(self, actions: List[str]) -> Dict[str, Any]:
        return {"objective_signals_collected": True, "status": "READY_FOR_DIAGNOSTICS"}
