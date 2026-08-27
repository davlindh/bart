"""Unit tests for Swedish Tax Engine, BAS Kontoplan, Momsdeklaration, and Omniframez."""

import pytest
from src.core.types import TaxRuleType, ScopeLevel
from src.tax_engine.models import TaxTransaction, CustomerTaxProfile
from src.tax_engine.evaluator import TaxRuleEvaluator
from src.tax_engine.bas_kontoplan import BASKontoplan
from src.tax_engine.momsdeklaration import MomsdeklarationGenerator
from src.context_engine.resolver import ContextResolver
from src.perspective_windows.financial_management import FinancialManagementWindow
from src.agents.tax_optimization_agent import TaxOptimizationAgent


def test_vmb_evaluation_used_automower():
    """Verify VMB calculation saves 2,000 SEK VAT on a 16,000 SEK used mower sale."""
    tx = TaxTransaction(
        transaction_id="tx_used_mower_01",
        source_system="WORKSHOP_POS",
        description="Begagnad Husqvarna Automower 430X",
        gross_amount=16000.0,
        net_amount=12800.0,
        current_vat_rate=0.25,
        current_vat_amount=3200.0,
        current_tax_rule=TaxRuleType.STANDARD_MOMS_25,
        is_used_good=True,
        purchase_cost_ex_vat=10000.0,
        bought_from_private_individual=True,
    )

    result = TaxRuleEvaluator.evaluate_vmb(tx)
    assert result is not None
    opp, calc = result

    # Verify mathematics
    assert calc.gross_margin == 6000.0
    assert calc.standard_vat_amount == 3200.0
    assert calc.vmb_vat_amount == 1200.0  # 20% of 6,000 margin
    assert calc.vat_saved_sek == 2000.0
    assert calc.standard_profit_after_vat == 2800.0
    assert calc.vmb_profit_after_vat == 4800.0
    assert calc.profit_increase_sek == 2000.0
    assert calc.profit_increase_pct == pytest.approx(71.4, 0.1)

    assert opp.best_possible_rule == TaxRuleType.VMB_MARGIN_TAX
    assert opp.recommended_bas_account == "3051 Försäljning varor VMB"


def test_rut_evaluation_installation_package():
    """Verify RUT evaluation computes 50% labor deduction and preserved company revenue."""
    tx = TaxTransaction(
        transaction_id="tx_install_02",
        source_system="FORTNOX",
        description="Installation och kabeldragning Automower 450X",
        gross_amount=24000.0,
        net_amount=19200.0,
        current_vat_rate=0.25,
        current_vat_amount=4800.0,
        current_tax_rule=TaxRuleType.STANDARD_MOMS_25,
        is_garden_or_installation_work=True,
        labor_share_amount=8000.0,
        material_share_amount=16000.0,
        customer=CustomerTaxProfile(
            customer_id="cust_privat_01",
            name="Anders Svensson",
            is_company=False,
            rut_eligible=True,
        ),
    )

    result = TaxRuleEvaluator.evaluate_rut(tx)
    assert result is not None
    opp, calc = result

    # Verify RUT deduction
    assert calc.labor_cost_gross == 8000.0
    assert calc.rut_deduction_amount == 4000.0  # 50% of 8,000
    assert calc.rut_customer_payable == 20000.0
    assert calc.skatteverket_payout_amount == 4000.0
    assert calc.total_company_revenue_with_rut == 24000.0  # zero revenue loss
    assert opp.best_possible_rule == TaxRuleType.RUT_DEDUCTION


def test_reverse_charge_construction():
    """Verify B2B ground excavation is flagged for Omvänd byggmoms (ML 1 kap. 2 §)."""
    tx = TaxTransaction(
        transaction_id="tx_b2b_ground_03",
        source_system="FORTNOX",
        description="Kabelschaktning för anläggningsarbete",
        gross_amount=43750.0,
        net_amount=35000.0,
        current_vat_rate=0.25,
        current_vat_amount=8750.0,
        current_tax_rule=TaxRuleType.STANDARD_MOMS_25,
        is_garden_or_installation_work=True,
        customer=CustomerTaxProfile(
            customer_id="cust_b2b_mark",
            name="Mark & Anläggning Väst AB",
            is_company=True,
            has_f_skatt=True,
            sni_code="43.120",  # Anläggningsarbeten
        ),
    )

    opp = TaxRuleEvaluator.evaluate_reverse_charge_construction(tx)
    assert opp is not None
    assert opp.best_possible_rule == TaxRuleType.REVERSE_CHARGE_CONSTRUCTION
    assert opp.recommended_bas_account == "3231 Försäljning omvänd byggmoms"
    assert "Fält 41" in opp.moms_box_change


def test_minor_asset_direct_write_off():
    """Verify purchase < 1/2 PBB qualifies for immediate Year 1 write-off on 5410."""
    tx = TaxTransaction(
        transaction_id="tx_tool_04",
        source_system="FORTNOX",
        description="Batteritestare och verkstadsdiagnostik",
        gross_amount=33125.0,
        net_amount=26500.0,
        current_vat_rate=0.25,
        current_vat_amount=6625.0,
        current_tax_rule=TaxRuleType.STANDARD_MOMS_25,
        is_asset_purchase=True,
    )

    result = TaxRuleEvaluator.evaluate_minor_asset_write_off(tx, pbb_half=28650.0)
    assert result is not None
    opp, eval_model = result

    assert eval_model.qualifies_for_direct_write_off is True
    assert eval_model.year_1_deduction_direct == 26500.0
    assert eval_model.year_1_deduction_depreciation == 5300.0
    assert eval_model.year_1_tax_saving_direct == 5459.0
    assert eval_model.year_1_tax_saving_depreciation == 1091.80
    assert eval_model.immediate_cash_retention_advantage == 4367.20
    assert opp.recommended_bas_account == "5410 Förbrukningsinventarier"


def test_bas_kontoplan_vouchers():
    """Verify automatic creation of balanced vouchers (Debet == Kredit)."""
    # 1. Shopify Settlement payout
    settlement = BASKontoplan.create_shopify_settlement_voucher(
        verifikat_id="VER_2026_001",
        gross_sales=10000.0,
        clearing_fee=250.0,
        payout_net=9750.0,
    )
    assert settlement.is_balanced is True
    assert settlement.total_debet == 10000.0
    assert settlement.total_kredit == 10000.0

    # 2. VMB sale voucher
    vmb_voucher = BASKontoplan.create_vmb_sale_voucher(
        verifikat_id="VER_2026_002",
        selling_price_gross=16000.0,
        purchase_cost=10000.0,
        vmb_vat=1200.0,
    )
    assert vmb_voucher.is_balanced is True
    assert vmb_voucher.total_debet == 16000.0
    assert vmb_voucher.total_kredit == 16000.0


def test_momsdeklaration_generator():
    """Verify aggregation into Skatteverkets declaration fields."""
    txs = [
        # Standard sale (Net 20,000, VAT 5,000)
        TaxTransaction(
            transaction_id="tx1",
            source_system="SHOPIFY",
            description="Ny Automower 310 Mark II",
            gross_amount=25000.0,
            net_amount=20000.0,
            current_vat_amount=5000.0,
            current_tax_rule=TaxRuleType.STANDARD_MOMS_25,
        ),
        # VMB sale (Gross 15,000, Purchase 10,000 -> Margin 5,000; VAT = 1,000, Margin ex VAT = 4,000)
        TaxTransaction(
            transaction_id="tx2",
            source_system="WORKSHOP_POS",
            description="Begagnad klippare VMB",
            gross_amount=15000.0,
            net_amount=14000.0,
            current_vat_amount=1000.0,
            current_tax_rule=TaxRuleType.VMB_MARGIN_TAX,
            is_used_good=True,
            purchase_cost_ex_vat=10000.0,
        ),
        # Reverse charge construction (Net 10,000, VAT 0)
        TaxTransaction(
            transaction_id="tx3",
            source_system="FORTNOX",
            description="Kabelgravning B2B",
            gross_amount=10000.0,
            net_amount=10000.0,
            current_vat_amount=0.0,
            current_tax_rule=TaxRuleType.REVERSE_CHARGE_CONSTRUCTION,
        ),
    ]

    report = MomsdeklarationGenerator.generate_report(period="2026-08", transactions=txs, input_vat_total=2500.0)

    assert report.falt_05_momspliktig_forsaljning_25 == 20000.0
    assert report.falt_08_vmb_marginal == 4000.0
    assert report.falt_10_utgaende_moms_25 == 6000.0  # 5,000 + 1,000
    assert report.falt_41_omvand_byggmoms == 10000.0
    assert report.falt_48_ingaende_moms == 2500.0
    assert report.falt_49_moms_att_betala_eller_fa_tillbaka == 3500.0  # 6,000 - 2,500


def test_context_resolver():
    """Verify dynamic context packet scoping for Ekonomiansvarig vs Säljare."""
    ctx = ContextResolver.resolve_context(
        role="Ekonomiansvarig",
        purpose="Optimera moms och bokföring",
        task="Auditera begagnatinbyten och momsdeklaration",
        scope=ScopeLevel.D2_SYSTEMIC,
        target_entity={"id": "entity_01", "title": "Bokföringsrevision Q3"},
    )
    assert ctx.role == "Ekonomiansvarig"
    assert ctx.scope == ScopeLevel.D2_SYSTEMIC
    assert ctx.perspective_window.value == "Financial Management"

    summary = ContextResolver.format_human_view_l1(ctx)
    assert "Financial Management" in summary


def test_tax_optimization_agent_lifecycle():
    """Verify full 6-step lifecycle of TaxOptimizationAgent."""
    tx_payload = [
        {
            "transaction_id": "tx_suboptimal_vmb",
            "source_system": "WORKSHOP_POS",
            "description": "Inbytt robotgrasklippare sald med standardmoms",
            "gross_amount": 16000.0,
            "net_amount": 12800.0,
            "current_vat_rate": 0.25,
            "current_vat_amount": 3200.0,
            "current_tax_rule": "MOMS_25",
            "is_used_good": True,
            "purchase_cost_ex_vat": 10000.0,
            "bought_from_private_individual": True,
        }
    ]

    packet = ContextResolver.resolve_context(
        role="Ekonomiansvarig",
        purpose="Identifiera skattebesparande åtgärder",
        task="Skatterevision inbyten",
        target_entity={"transactions": tx_payload},
    )

    agent = TaxOptimizationAgent()
    result = agent.run(packet)

    assert result.status.value == "completed"
    assert len(result.observations) == 1
    assert len(result.diagnoses) == 1
    assert "VMB" in result.diagnoses[0].issue_category
    assert result.metrics_summary["verified_tax_savings_sek"] == 2000.0
    assert result.metrics_summary["verified_profit_gain_sek"] == 2000.0


def test_tax_optimization_agent_step_lifecycle():
    """Verify granular step-by-step lifecycle execution for UI stepper."""
    tx_payload = [
        {
            "transaction_id": "tx_step_test",
            "source_system": "WORKSHOP_POS",
            "description": "Robotgräsklippare VMB test",
            "gross_amount": 16000.0,
            "net_amount": 12800.0,
            "current_vat_rate": 0.25,
            "current_vat_amount": 3200.0,
            "current_tax_rule": "MOMS_25",
            "is_used_good": True,
            "purchase_cost_ex_vat": 10000.0,
            "bought_from_private_individual": True,
        }
    ]

    packet = ContextResolver.resolve_context(
        role="CFO",
        purpose="Stegvis analys",
        task="Testa interaktiv stepper",
        target_entity={"transactions": tx_payload},
    )

    agent = TaxOptimizationAgent()
    step1 = agent.run_step("observe", packet)
    assert step1["step"] == "observe"
    assert step1["count"] == 1

    step2 = agent.run_step("analyze", packet)
    assert step2["step"] == "analyze"
    assert step2["data"]["opportunity_count"] == 1

    step3 = agent.run_step("identify", packet)
    assert step3["step"] == "identify"
    assert len(step3["data"]) == 1

    step4 = agent.run_step("propose", packet)
    assert step4["step"] == "propose"
    assert len(step4["data"]) == 1

    step5 = agent.run_step("act", packet)
    assert step5["step"] == "act"
    assert len(step5["data"]) == 1

    step6 = agent.run_step("evaluate", packet)
    assert step6["step"] == "evaluate"
    assert step6["data"]["verified_tax_savings_sek"] == 2000.0

