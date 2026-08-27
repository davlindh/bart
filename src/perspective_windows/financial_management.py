"""Omnipod Perspective Window 5: Financial Management & Tax Governance."""

from typing import List, Dict, Any
from ..core.types import PerspectiveWindow, Domain
from ..core.contracts import Observation, TaxEvaluationResult
from ..tax_engine.models import TaxTransaction, MomsdeklarationReport
from ..tax_engine.evaluator import TaxRuleEvaluator
from ..tax_engine.momsdeklaration import MomsdeklarationGenerator


class FinancialManagementWindow:
    """Window 5: Monitors financial health, true margins (TB1/TB2), BAS accuracy, and tax rules."""

    WINDOW_TYPE = PerspectiveWindow.W5_FINANCIAL_MANAGEMENT

    @classmethod
    def audit_financial_stream(
        cls,
        transactions: List[TaxTransaction],
        input_vat_total: float = 0.0,
        period: str = "2026-Q3"
    ) -> Dict[str, Any]:
        """Comprehensive audit through the Financial Management Perspective Window."""
        # 1. Tax rule evaluation (Applied vs Best Possible)
        tax_eval: TaxEvaluationResult = TaxRuleEvaluator.evaluate_batch(transactions)

        # 2. Momsdeklaration generation
        moms_report: MomsdeklarationReport = MomsdeklarationGenerator.generate_report(
            period=period,
            transactions=transactions,
            input_vat_total=input_vat_total
        )

        # 3. Margin & Turnover Metrics
        total_gross = sum(t.gross_amount for t in transactions)
        total_net = sum(t.net_amount for t in transactions)

        # Compute tax efficiency rating
        # Efficiency = 1.0 - (Suboptimal Tax Paid / Total Turnover)
        tax_efficiency_rating = 1.0
        if total_gross > 0 and tax_eval.total_potential_savings_sek > 0:
            tax_efficiency_rating = round(1.0 - (tax_eval.total_potential_savings_sek / total_gross), 4)

        # 4. Generate Telemetry Observations
        observations: List[Observation] = [
            Observation(
                observation_id=f"obs_turnover_{period}",
                source="FinancialManagementWindow",
                domain=Domain.OPERATIONAL,
                window=cls.WINDOW_TYPE,
                entity_id=f"financial_summary_{period}",
                metric_name="total_gross_turnover",
                metric_value=total_gross,
            ),
            Observation(
                observation_id=f"obs_tax_savings_{period}",
                source="FinancialManagementWindow",
                domain=Domain.TRUST,
                window=cls.WINDOW_TYPE,
                entity_id=f"tax_optimization_{period}",
                metric_name="potential_tax_savings_sek",
                metric_value=tax_eval.total_potential_savings_sek,
            ),
            Observation(
                observation_id=f"obs_tax_efficiency_{period}",
                source="FinancialManagementWindow",
                domain=Domain.TRUST,
                window=cls.WINDOW_TYPE,
                entity_id=f"tax_efficiency_{period}",
                metric_name="tax_efficiency_score",
                metric_value=tax_efficiency_rating,
            ),
        ]

        return {
            "window": cls.WINDOW_TYPE.value,
            "period": period,
            "total_gross_turnover_sek": round(total_gross, 2),
            "total_net_turnover_sek": round(total_net, 2),
            "tax_efficiency_score": tax_efficiency_rating,
            "tax_evaluation": tax_eval.model_dump(),
            "momsdeklaration": moms_report.model_dump(),
            "observations": [obs.model_dump() for obs in observations],
            "actionable_tax_opportunities_count": len(tax_eval.opportunities),
        }
