"""Core Tax Rule Evaluator comparing Applied vs Best Possible Swedish Tax Treatments."""

from typing import List, Optional, Tuple, Dict, Any
from .models import (
    TaxTransaction,
    VMBCalculation,
    RUTCalculation,
    ROTCalculation,
    GronTeknikCalculation,
    PeriodiseringsfondCalculation,
    K10Calculation,
    FoUCalculation,
    AssetDepreciationEvaluation,
    CombinationEvaluation,
    FinancialVerificationReport,
    MomsdeklarationReport,
)
from ..core.types import TaxRuleType
from ..core.contracts import TaxOptimizationOpportunity, TaxEvaluationResult
from .rule_library import (
    VMBRule,
    RUTRule,
    ROTRule,
    GronTeknikRule,
    ReverseChargeConstructionRule,
    MinorAssetWriteOffRule,
    PeriodiseringsfondRule,
    K10DividendRule,
    FoUDeductionRule,
)
from .combinatorial_engine import CombinatorialTaxEngine
from .verification_engine import FinancialVerificationEngine


class TaxRuleEvaluator:
    """Evaluates applied tax treatments against legally compliant optimal alternatives."""

    DEFAULT_PBB_HALF: float = 28650.0  # 1/2 of Prisbasbelopp (2024: 57,300, 2025: 58,800)
    CORPORATE_TAX_RATE: float = 0.206   # 20.6% standard Swedish corporate income tax

    @classmethod
    def evaluate_vmb(cls, tx: TaxTransaction) -> Optional[Tuple[TaxOptimizationOpportunity, VMBCalculation]]:
        """Evaluates whether a used trade-in machine should use VMB (ML 9a kap.) instead of 25% VAT."""
        return VMBRule.evaluate(tx)

    @classmethod
    def evaluate_rut(cls, tx: TaxTransaction) -> Optional[Tuple[TaxOptimizationOpportunity, RUTCalculation]]:
        """Evaluates whether an installation/service package qualifies for 50% RUT-avdrag."""
        return RUTRule.evaluate(tx)

    @classmethod
    def evaluate_rot(cls, tx: TaxTransaction) -> Optional[Tuple[TaxOptimizationOpportunity, ROTCalculation]]:
        """Evaluates whether a repair/renovation package qualifies for 30% ROT-avdrag."""
        return ROTRule.evaluate(tx)

    @classmethod
    def evaluate_gron_teknik(cls, tx: TaxTransaction) -> Optional[Tuple[TaxOptimizationOpportunity, GronTeknikCalculation]]:
        """Evaluates whether solar, battery storage, or EV charging qualifies for Grön Teknik deduction."""
        return GronTeknikRule.evaluate(tx)

    @classmethod
    def evaluate_reverse_charge_construction(cls, tx: TaxTransaction) -> Optional[TaxOptimizationOpportunity]:
        """Evaluates whether ground/cabling work for a construction company requires Reverse Charge VAT."""
        return ReverseChargeConstructionRule.evaluate(tx)

    @classmethod
    def evaluate_minor_asset_write_off(
        cls, tx: TaxTransaction, pbb_half: float = DEFAULT_PBB_HALF
    ) -> Optional[Tuple[TaxOptimizationOpportunity, AssetDepreciationEvaluation]]:
        """Evaluates whether equipment purchase qualifies for 100% direct write-off in Year 1."""
        return MinorAssetWriteOffRule.evaluate(tx, pbb_half=pbb_half)

    @classmethod
    def evaluate_periodiseringsfond(cls, taxable_profit_sek: float) -> Optional[Tuple[TaxOptimizationOpportunity, PeriodiseringsfondCalculation]]:
        """Evaluates Periodiseringsfond (IL 30 kap.) deferral on corporate profits."""
        return PeriodiseringsfondRule.evaluate_company_profit(taxable_profit_sek)

    @classmethod
    def evaluate_k10_dividend(cls, total_salaries: float, owner_salary: float) -> Tuple[TaxOptimizationOpportunity, K10Calculation]:
        """Evaluates optimal 3:12 K10 dividend headroom for 20% capital taxation."""
        return K10DividendRule.evaluate_dividend_space(total_salaries, owner_salary)

    @classmethod
    def evaluate_fou_deduction(cls, rd_salaries: float) -> Optional[Tuple[TaxOptimizationOpportunity, FoUCalculation]]:
        """Evaluates R&D employer social fee reduction."""
        return FoUDeductionRule.evaluate_rd_team(rd_salaries)

    @classmethod
    def evaluate_combinatorial_strategies(
        cls,
        transactions: List[TaxTransaction],
        annual_taxable_profit: Optional[float] = None,
        total_salaries_paid: Optional[float] = None,
        owner_salary: Optional[float] = None,
        monthly_rd_salaries: Optional[float] = None,
    ) -> CombinationEvaluation:
        """Finds the most potent, conflict-free combination of tax cuts and strategy bundles."""
        return CombinatorialTaxEngine.analyze_combinatorial_opportunities(
            transactions=transactions,
            annual_taxable_profit=annual_taxable_profit,
            total_salaries_paid=total_salaries_paid,
            owner_salary=owner_salary,
            monthly_rd_salaries=monthly_rd_salaries,
        )

    @classmethod
    def verify_financial_integrity(
        cls,
        transactions: List[TaxTransaction],
        momsdeklaration: Optional[MomsdeklarationReport] = None,
        bank_balance_sek: Optional[float] = None,
        skattekonto_balance_sek: Optional[float] = None,
        booked_vouchers: Optional[List[Dict[str, Any]]] = None,
    ) -> FinancialVerificationReport:
        """Performs comprehensive Swedish accounting (BFL, ML, SFL) verification and checks for missing source documents."""
        return FinancialVerificationEngine.verify_transaction_batch(
            transactions=transactions,
            momsdeklaration=momsdeklaration,
            bank_balance_sek=bank_balance_sek,
            skattekonto_balance_sek=skattekonto_balance_sek,
            booked_vouchers=booked_vouchers,
        )

    @classmethod
    def evaluate_batch(cls, transactions: List[TaxTransaction]) -> TaxEvaluationResult:
        """Evaluates a batch of transactions and compiles an optimization report."""
        result = TaxEvaluationResult(total_evaluated_count=len(transactions))

        for tx in transactions:
            # 1. VMB Check
            vmb_res = cls.evaluate_vmb(tx)
            if vmb_res:
                opp, _ = vmb_res
                result.opportunities.append(opp)
                result.total_potential_savings_sek += opp.net_tax_saved_sek
                result.total_profit_gain_sek += opp.net_profit_delta_sek

            # 2. RUT Check
            rut_res = cls.evaluate_rut(tx)
            if rut_res:
                opp, _ = rut_res
                result.opportunities.append(opp)
                result.total_profit_gain_sek += opp.net_profit_delta_sek

            # 3. ROT Check
            rot_res = cls.evaluate_rot(tx)
            if rot_res:
                opp, _ = rot_res
                result.opportunities.append(opp)
                result.total_profit_gain_sek += opp.net_profit_delta_sek

            # 4. Grön Teknik Check
            gron_res = cls.evaluate_gron_teknik(tx)
            if gron_res:
                opp, _ = gron_res
                result.opportunities.append(opp)
                result.total_profit_gain_sek += opp.net_profit_delta_sek

            # 5. Reverse charge construction Check
            rev_opp = cls.evaluate_reverse_charge_construction(tx)
            if rev_opp:
                result.opportunities.append(rev_opp)
                result.compliance_risks_detected.append(
                    f"Tx {tx.transaction_id}: Construction buyer charged 25% VAT incorrectly. Reverse charge required."
                )

            # 6. Asset minor write-off Check
            asset_res = cls.evaluate_minor_asset_write_off(tx)
            if asset_res:
                opp, _ = asset_res
                result.opportunities.append(opp)
                result.total_potential_savings_sek += opp.net_tax_saved_sek
                result.total_profit_gain_sek += opp.net_profit_delta_sek

        result.total_potential_savings_sek = round(result.total_potential_savings_sek, 2)
        result.total_profit_gain_sek = round(result.total_profit_gain_sek, 2)
        return result
