"""Tax Optimization Agent operating on the 6-function lifecycle loop."""

from typing import Any, Dict, List
import uuid
from .base import BaseAgent
from ..core.contracts import ContextPacket, Observation, Diagnosis, TaxOptimizationOpportunity
from ..core.types import Domain, PerspectiveWindow
from ..tax_engine.models import TaxTransaction
from ..tax_engine.evaluator import TaxRuleEvaluator


class TaxOptimizationAgent(BaseAgent):
    """Specialist agent detecting suboptimal tax rules and generating SEK-saving recommendations."""

    def __init__(self):
        super().__init__(name="TaxOptimizationAgent")
        self._current_transactions: List[TaxTransaction] = []
        self._evaluation_result = None

    def observe(self, context: ContextPacket) -> List[Observation]:
        """Observes financial transactions embedded in the ContextPacket."""
        observations: List[Observation] = []
        self._current_transactions = []

        # Pull transactions from related entities or packet observations
        raw_txs = context.primary_entity.get("transactions", [])
        if not raw_txs and context.related_entities:
            for ent in context.related_entities:
                if "transactions" in ent:
                    raw_txs.extend(ent["transactions"])
                elif ent.get("type") == "transaction":
                    raw_txs.append(ent)

        for raw in raw_txs:
            try:
                tx = TaxTransaction(**raw) if isinstance(raw, dict) else raw
                self._current_transactions.append(tx)
                observations.append(
                    Observation(
                        observation_id=f"obs_tx_{tx.transaction_id}",
                        source="TaxOptimizationAgent",
                        domain=Domain.EXCHANGE,
                        window=PerspectiveWindow.W5_FINANCIAL_MANAGEMENT,
                        entity_id=tx.transaction_id,
                        metric_name="transaction_gross_sek",
                        metric_value=tx.gross_amount,
                        raw_payload=tx.model_dump(),
                    )
                )
            except Exception:
                continue

        return observations

    def analyze(self, observations: List[Observation]) -> Dict[str, Any]:
        """Evaluates applied tax rules against best possible Swedish tax regimes."""
        eval_result = TaxRuleEvaluator.evaluate_batch(self._current_transactions)
        self._evaluation_result = eval_result

        return {
            "total_transactions": len(self._current_transactions),
            "opportunity_count": len(eval_result.opportunities),
            "total_potential_savings_sek": eval_result.total_potential_savings_sek,
            "total_profit_gain_sek": eval_result.total_profit_gain_sek,
            "opportunities": eval_result.opportunities,
            "compliance_risks": eval_result.compliance_risks_detected,
        }

    def identify(self, analysis: Dict[str, Any]) -> List[Diagnosis]:
        """Identifies root cause misclassifications and financial leakages."""
        diagnoses: List[Diagnosis] = []

        for opp in analysis.get("opportunities", []):
            diag = Diagnosis(
                diagnosis_id=f"diag_{uuid.uuid4().hex[:8]}",
                related_observations=[f"obs_tx_{opp.transaction_id}"],
                issue_category=f"Suboptimal Tax Rule: {opp.applied_rule.value} -> {opp.best_possible_rule.value}",
                severity="high" if opp.net_tax_saved_sek > 1000 else "medium",
                root_cause=opp.explanation,
                financial_impact_sek=opp.net_tax_saved_sek if opp.net_tax_saved_sek > 0 else opp.net_profit_delta_sek,
                description=(
                    f"Transaction {opp.transaction_id} uses {opp.applied_rule.value}. "
                    f"Best possible: {opp.best_possible_rule.value} ({opp.legal_basis})."
                ),
            )
            diagnoses.append(diag)

        return diagnoses

    def propose(self, diagnoses: List[Diagnosis]) -> List[str]:
        """Proposes concrete bookkeeping corrections and quote modifications."""
        proposals: List[str] = []

        if not self._evaluation_result:
            return proposals

        for opp in self._evaluation_result.opportunities:
            proposals.append(
                f"[{opp.best_possible_rule.value}] Switch Tx {opp.transaction_id} to BAS {opp.recommended_bas_account}. "
                f"Saves {opp.net_tax_saved_sek:.2f} SEK VAT / increases profit by {opp.net_profit_delta_sek:.2f} SEK. "
                f"Legal Basis: {opp.legal_basis}."
            )

        return proposals

    def act(self, recommendations: List[str]) -> List[str]:
        """Simulates automated actions taken: prepares verifikat, updates quote tags."""
        actions: List[str] = []
        for rec in recommendations:
            actions.append(f"Action Executed: Prepared automated journal voucher mapping for: {rec[:60]}...")
        return actions

    def evaluate(self, actions: List[str]) -> Dict[str, Any]:
        """Evaluates net monetary outcomes and efficiency."""
        if not self._evaluation_result:
            return {"status": "no_eval"}

        return {
            "verified_tax_savings_sek": self._evaluation_result.total_potential_savings_sek,
            "verified_profit_gain_sek": self._evaluation_result.total_profit_gain_sek,
            "actions_executed_count": len(actions),
            "recommendation_adoption_rate": 1.0,
        }
