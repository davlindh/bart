"""Integration test for BART HTTP & REST API endpoints."""

import json
from src.server import BARTRequestHandler, SCENARIOS
from src.context_engine.resolver import ContextResolver
from src.perspective_windows.financial_management import FinancialManagementWindow
from src.agents.tax_optimization_agent import TaxOptimizationAgent
from src.core.types import ScopeLevel


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
