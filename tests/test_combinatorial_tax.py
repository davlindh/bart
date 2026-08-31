"""Unit and integration tests for Extended Tax Cuts, Financial Verification Engine, and Combinatorial Tax Engine."""

import pytest
from src.core.types import TaxRuleType
from src.tax_engine.models import (
    TaxTransaction,
    CustomerTaxProfile,
    MomsdeklarationReport,
)
from src.tax_engine.evaluator import TaxRuleEvaluator
from src.tax_engine.rule_library import (
    ROTRule,
    GronTeknikRule,
    PeriodiseringsfondRule,
    K10DividendRule,
    FoUDeductionRule,
)
from src.tax_engine.verification_engine import FinancialVerificationEngine
from src.tax_engine.combinatorial_engine import CombinatorialTaxEngine


def test_rot_evaluation():
    """Verify 30% ROT-avdrag evaluation on repair work for private customer."""
    tx = TaxTransaction(
        transaction_id="tx_rot_repair",
        source_system="FORTNOX",
        description="Reparation och renovering av maskinhall",
        gross_amount=30000.0,
        net_amount=24000.0,
        current_vat_rate=0.25,
        current_vat_amount=6000.0,
        current_tax_rule=TaxRuleType.STANDARD_MOMS_25,
        is_garden_or_installation_work=True,
        labor_share_amount=20000.0,
        material_share_amount=10000.0,
        customer=CustomerTaxProfile(
            customer_id="cust_priv_01",
            name="Helena Berg",
            is_company=False,
            rut_eligible=True,
        ),
    )

    res = TaxRuleEvaluator.evaluate_rot(tx)
    assert res is not None
    opp, calc = res

    assert calc.labor_cost_gross == 20000.0
    assert calc.rot_deduction_amount == 6000.0  # 30% of 20,000
    assert calc.rot_customer_payable == 24000.0  # 30,000 - 6,000
    assert opp.best_possible_rule == TaxRuleType.ROT_DEDUCTION
    assert opp.recommended_bas_account == "3003 Försäljning arbetskostnad ROT"


def test_gron_teknik_battery_evaluation():
    """Verify 50% Grön Teknik deduction on solar battery storage installation."""
    tx = TaxTransaction(
        transaction_id="tx_green_battery",
        source_system="FORTNOX",
        description="Installation av solcellsbatteri 10kWh för energilagring",
        gross_amount=60000.0,
        net_amount=48000.0,
        current_vat_rate=0.25,
        current_vat_amount=12000.0,
        current_tax_rule=TaxRuleType.STANDARD_MOMS_25,
        customer=CustomerTaxProfile(
            customer_id="cust_priv_green",
            name="Lars Gustafsson",
            is_company=False,
        ),
    )

    res = TaxRuleEvaluator.evaluate_gron_teknik(tx)
    assert res is not None
    opp, calc = res

    assert calc.installation_type == "BATTERY_STORAGE"
    assert calc.deduction_rate == 0.50
    assert calc.deduction_amount == 30000.0  # 50% of 60,000
    assert calc.customer_payable == 30000.0
    assert opp.best_possible_rule == TaxRuleType.GRON_TEKNIK


def test_periodiseringsfond_allocation():
    """Verify Periodiseringsfond (IL 30 kap.) defers 25% of taxable profit."""
    taxable_profit = 800000.0  # 800k SEK taxable profit before allocation
    res = TaxRuleEvaluator.evaluate_periodiseringsfond(taxable_profit)
    assert res is not None
    opp, calc = res

    assert calc.max_allocation_amount == 200000.0  # 25% of 800k
    assert calc.tax_deferral_benefit_sek == 41200.0  # 20.6% of 200k
    assert calc.max_deferral_years == 6
    assert opp.best_possible_rule == TaxRuleType.PERIODISERINGSFOND
    assert opp.net_tax_saved_sek == 41200.0


def test_k10_dividend_optimization():
    """Verify K10 wage-based rule (50% of total wages) beats standard schablon for qualifying owners."""
    total_wages = 1200000.0  # 1.2M total salaries paid in company
    owner_wage = 600000.0    # Owner wage qualifies (> min salary requirement)

    opp, calc = TaxRuleEvaluator.evaluate_k10_dividend(total_wages, owner_wage)
    assert calc.qualifies_for_wage_rule is True
    assert calc.wage_based_space == 600000.0  # 50% of 1.2M
    assert calc.optimal_rule == "LONEBASERAT"
    assert calc.optimal_gransbelopp == 600000.0
    assert calc.tax_at_20_pct == 120000.0  # 20% of 600,000
    assert opp.net_tax_saved_sek == 180000.0  # 30% savings vs standard salary taxation


def test_fou_social_fees_deduction():
    """Verify FoU R&D deduction reduces employer social fees."""
    rd_salaries = 100000.0  # 100k SEK monthly gross salaries for tech team
    res = TaxRuleEvaluator.evaluate_fou_deduction(rd_salaries)
    assert res is not None
    opp, calc = res

    assert calc.monthly_saving_sek == 19590.0  # 100,000 * 0.1959
    assert calc.annual_saving_sek == 235080.0
    assert opp.best_possible_rule == TaxRuleType.FOU_DEDUCTION


def test_financial_verification_engine_detects_all_issues():
    """Verify FinancialVerificationEngine flags BFL missing specs, VAT mismatches, unverified VIES, and unbalanced ledgers."""
    flawed_txs = [
        # Missing description / underlag
        TaxTransaction(
            transaction_id="tx_flawed_1",
            source_system="",
            description="",
            gross_amount=10000.0,
            net_amount=8000.0,
            current_vat_amount=2000.0,
        ),
        # Company missing Org.nr
        TaxTransaction(
            transaction_id="tx_flawed_2",
            source_system="FORTNOX",
            description="Leverans maskindelar",
            gross_amount=50000.0,
            net_amount=40000.0,
            current_vat_amount=10000.0,
            customer=CustomerTaxProfile(
                customer_id="",
                name="Okänt AB",
                is_company=True,
                org_nr=None,
            ),
        ),
        # EU B2B customer missing VIES VAT number
        TaxTransaction(
            transaction_id="tx_flawed_3",
            source_system="SHOPIFY",
            description="EU export mower parts",
            gross_amount=12000.0,
            net_amount=12000.0,
            current_vat_rate=0.0,
            current_vat_amount=0.0,
            customer=CustomerTaxProfile(
                customer_id="cust_eu_1",
                name="Garten Technik GmbH",
                is_company=True,
                is_eu_business=True,
                eu_vat_nr=None,  # Missing!
            ),
        ),
    ]

    flawed_moms = MomsdeklarationReport(
        period="2026-Q3",
        falt_05_momspliktig_forsaljning_25=100000.0,
        falt_10_utgaende_moms_25=15000.0,  # Flawed! Should be 25,000 SEK
        falt_48_ingaende_moms=5000.0,
        falt_49_moms_att_betala_eller_fa_tillbaka=20000.0,  # Flawed! 15k - 5k = 10k, not 20k
    )

    unbalanced_vouchers = [
        {
            "voucher": {
                "verifikat_id": "VER_BAD_01",
                "rows": [
                    {"account": "1930", "debet": 10000.0, "kredit": 0.0},
                    {"account": "3001", "debet": 0.0, "kredit": 8000.0},  # Imbalance 2,000 SEK!
                ],
            }
        }
    ]

    report = FinancialVerificationEngine.verify_transaction_batch(
        transactions=flawed_txs,
        momsdeklaration=flawed_moms,
        booked_vouchers=unbalanced_vouchers,
    )

    assert report.verification_score < 1.0
    assert report.balanced_ledger_verified is False
    assert report.reconciliations["moms_falt_10_reconciliation"] is False
    assert report.reconciliations["moms_falt_49_net_reconciliation"] is False

    issue_codes = [i.code for i in report.issues]
    assert "BFL_MISSING_SPECIFICATION" in issue_codes
    assert "BFL_MISSING_COUNTERPARTY_ORGNR" in issue_codes
    assert "ML_EU_VIES_UNVERIFIED" in issue_codes
    assert "ML_MOMS_FALT10_MISMATCH" in issue_codes
    assert "ML_MOMS_FALT49_NET_ERROR" in issue_codes
    assert "BFL_UNBALANCED_VOUCHER" in issue_codes


def test_combinatorial_tax_engine_synergy_and_conflict_resolution():
    """Verify CombinatorialTaxEngine resolves conflicts and bundles synergies."""
    txs = [
        # VMB Trade-in
        TaxTransaction(
            transaction_id="TX-COMB-1",
            source_system="WORKSHOP_POS",
            description="Inbytt Automower 430X VMB",
            gross_amount=16000.0,
            net_amount=12800.0,
            current_vat_rate=0.25,
            current_vat_amount=3200.0,
            current_tax_rule=TaxRuleType.STANDARD_MOMS_25,
            is_used_good=True,
            purchase_cost_ex_vat=10000.0,
            bought_from_private_individual=True,
        ),
        # RUT installation
        TaxTransaction(
            transaction_id="TX-COMB-2",
            source_system="FORTNOX",
            description="Installation & kabeldragning robotgräsklippare",
            gross_amount=24000.0,
            net_amount=19200.0,
            current_vat_rate=0.25,
            current_vat_amount=4800.0,
            current_tax_rule=TaxRuleType.STANDARD_MOMS_25,
            is_garden_or_installation_work=True,
            labor_share_amount=10000.0,
            material_share_amount=14000.0,
            customer=CustomerTaxProfile(
                customer_id="cust_p",
                name="Sven Larsson",
                is_company=False,
                rut_eligible=True,
            ),
        ),
    ]

    combo_eval = CombinatorialTaxEngine.analyze_combinatorial_opportunities(
        transactions=txs,
        annual_taxable_profit=500000.0,
        total_salaries_paid=1000000.0,
        owner_salary=600000.0,
        monthly_rd_salaries=50000.0,
    )

    assert combo_eval.evaluated_strategies_count >= 4
    assert len(combo_eval.optimal_bundles) == 2  # Operational Bundle + Strategic Wealth Bundle
    assert any("Begagnat Inbyte + Nyckelfärdig RUT-Installation" in s for s in combo_eval.synergy_opportunities)
    assert any("Optimal Ägar- och Bolagsskatteallokering" in s for s in combo_eval.synergy_opportunities)
    assert combo_eval.max_combined_savings_sek > 100000.0
