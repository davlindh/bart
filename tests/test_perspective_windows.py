"""Unit tests for all 9 Omnipod Perspective Windows."""

import pytest
from src.perspective_windows import (
    ContextualizationWindow,
    MatchingWindow,
    EvaluationWindow,
    ResourceAllocationWindow,
    FinancialManagementWindow,
    PersonnelManagementWindow,
    CommunicationWindow,
    InnovationWindow,
    AdaptiveInsightsWindow,
)
from src.tax_engine.models import TaxTransaction


def test_all_nine_perspective_windows():
    """Verify live data generation across all 9 Perspective Windows (W1..W9)."""
    # W1 Contextualization
    w1 = ContextualizationWindow.evaluate_context({})
    assert "active_trends" in w1
    assert w1["context_relevance_score"] > 0.8

    # W2 Matching
    w2 = MatchingWindow.match_quote_configuration("Robotklippare", 24000.0)
    assert len(w2["matched_packages"]) >= 1

    # W3 Evaluation
    w3 = EvaluationWindow.evaluate_performance({})
    assert w3["compliance_score"] >= 0.9

    # W4 Resource Allocation
    w4 = ResourceAllocationWindow.evaluate_allocations({})
    assert w4["capacity_utilization_pct"] > 50

    # W5 Financial Management
    txs = [TaxTransaction(transaction_id="T1", source_system="TEST", description="Mower", gross_amount=10000.0, net_amount=8000.0)]
    w5 = FinancialManagementWindow.audit_financial_stream(txs)
    assert "total_gross_turnover_sek" in w5

    # W6 Personnel Management
    w6 = PersonnelManagementWindow.evaluate_team_overview({})
    assert w6["active_team_members"] > 0
    assert w6["team_health_index"] > 80

    # W7 Communication
    w7 = CommunicationWindow.get_display_feed({})
    assert len(w7["active_channels"]) >= 3

    # W8 Innovation & Tech
    w8 = InnovationWindow.get_innovation_pipeline({})
    assert w8["active_pilots_count"] >= 1

    # W9 Adaptive Insights
    w9 = AdaptiveInsightsWindow.synthesize_insights({})
    assert w9["system_adaptivity_score"] > 90
