"""Integration test for BART HTTP & REST API endpoints."""

import json
from src.server import BARTRequestHandler, SCENARIOS
from src.context_engine.resolver import ContextResolver
from src.perspective_windows.financial_management import FinancialManagementWindow
from src.agents.tax_optimization_agent import TaxOptimizationAgent
from src.core.types import ScopeLevel, TaxRuleType


def test_scenarios_data_integrity():
    """Verify built-in scenarios have valid Swedish tax structures."""
    assert "mixed_q3" in SCENARIOS
    sc = SCENARIOS["mixed_q3"]
    assert len(sc["transactions"]) == 4
    assert sc["period"] == "2026-Q3"

    vmb_tx = sc["transactions"][0]
    assert vmb_tx["is_used_good"] is True
    assert vmb_tx["gross_amount"] == 16000.0


def test_graph_generator_scopes():
    """Verify dynamic graph generation expands nodes across D0, D1, D2, D3."""
    handler = BARTRequestHandler.__new__(BARTRequestHandler)
    
    # D0 Scope
    g_d0 = handler._generate_graph_data("mixed_q3", "D0", "CFO")
    assert g_d0["scope"] == "D0"
    assert g_d0["count"] == 5  # 1 batch + 4 txs

    # D1 Scope
    g_d1 = handler._generate_graph_data("mixed_q3", "D1", "CFO")
    assert g_d1["scope"] == "D1"
    assert g_d1["count"] > g_d0["count"]

    # D2 Scope
    g_d2 = handler._generate_graph_data("mixed_q3", "D2", "CFO")
    assert g_d2["scope"] == "D2"
    assert any(n["id"] == "win_5_financial" for n in g_d2["nodes"])
    assert any(n["id"] == "skv_moms_q3" for n in g_d2["nodes"])

    # D3 Scope
    g_d3 = handler._generate_graph_data("mixed_q3", "D3", "CFO")
    assert g_d3["scope"] == "D3"
    assert any(n["id"] == "meta_learning_agent" for n in g_d3["nodes"])
    assert any(n["id"] == "macro_skatteverket" for n in g_d3["nodes"])


def test_api_tax_rules_registry():
    """Verify rule registry endpoint returns metadata for all statutory rules."""
    from src.tax_engine.rule_library import ALL_TAX_RULES
    assert len(ALL_TAX_RULES) >= 8
    rule_types = [r.rule_type for r in ALL_TAX_RULES]
    assert TaxRuleType.VMB_MARGIN_TAX in rule_types
    assert TaxRuleType.RUT_DEDUCTION in rule_types
    assert TaxRuleType.ROT_DEDUCTION in rule_types
    assert TaxRuleType.GRON_TEKNIK in rule_types
    assert TaxRuleType.PERIODISERINGSFOND in rule_types
    assert TaxRuleType.K10_DIVIDEND_OPTIMAL in rule_types
    assert TaxRuleType.FOU_DEDUCTION in rule_types


def test_server_windows_and_fortnox_endpoints():
    """Verify internal server helper methods for perspective windows and Fortnox calculations."""
    handler = BARTRequestHandler.__new__(BARTRequestHandler)
    
    # Test windows W1 through W9
    for wid in ["W1", "W2", "W3", "W4", "W5", "W6", "W7", "W8", "W9"]:
        w_data = handler._get_window_data(wid)
        assert "window" in w_data

    # Test Fortnox live computation
    fn = handler._compute_fortnox_summary()
    assert "team_dynamics_metrics" in fn
    assert fn["team_dynamics_metrics"]["team_health_index"] > 50

    # Test Universal ERD graph
    erd = handler._get_erd_graph_data()
    assert erd["count"] >= 15
    assert len(erd["links"]) >= 10

    # Test Fortnox Customers API helper
    cust_data = handler._get_fortnox_customers_data()
    assert cust_data["count"] >= 4
    assert len(cust_data["customers"]) >= 4
    assert cust_data["total_potential_tax_savings_sek"] > 0
    assert any(c["rut_eligible"] for c in cust_data["customers"])


def test_export_endpoints_sie4_and_momsdeklaration():
    """Verify SIE-4 and Momsdeklaration export generation in server request handler."""
    handler = BARTRequestHandler.__new__(BARTRequestHandler)

    # Test SIE-4 export text
    sie_content = handler._generate_sie4_content()
    assert "#SIETYP 4" in sie_content
    assert "#FNAMN" in sie_content
    assert "#VER" in sie_content
    assert "#TRANS 1930" in sie_content
    assert "#TRANS 3051" in sie_content

    # Test Momsdeklaration export json
    moms_data = handler._generate_momsdeklaration_content()
    assert "falt_49_moms_att_betala_eller_fa_tillbaka" in moms_data
    assert moms_data["falt_49_moms_att_betala_eller_fa_tillbaka"] == 17600.0


def test_maskinochfritid_server_endpoints():
    """Verify maskinochfritid production computation and voucher handling on server handler."""
    handler = BARTRequestHandler.__new__(BARTRequestHandler)
    res = handler._compute_maskinochfritid_production()

    assert res["organization_name"] == "Maskin & Fritid i Skåne AB"
    assert res["summary"]["invoices_analyzed"] == 5
    assert res["voucher_telemetry"]["all_balanced"] is True
    assert res["voucher_telemetry"]["accounting_diff_sek"] == 0.0
    assert res["erd_graph"]["node_count"] > 15
    assert res["checkpoint"]["checkpoint_id"].startswith("chk_")
    assert len(res["checkpoint"]["checksum_sha256"]) == 64



