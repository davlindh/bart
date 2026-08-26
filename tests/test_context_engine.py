"""Tests for Dynamic Context Resolution Engine, 8D Weighting and Presentation Views."""

import pytest
from src.context_engine.presentation import PresentationFormatter
from src.context_engine.resolver import ContextResolutionEngine
from src.context_engine.scope_manager import ScopeManager
from src.core.contracts import ScopeContract
from src.core.types import ScopeDepth
from src.seeds.seed_loader import SeedDataLoader


def test_context_resolution_pipeline():
    """Verify end-to-end 5-step context resolution."""
    store = SeedDataLoader.load_seed_graph()
    engine = ContextResolutionEngine(graph_store=store)

    scope = ScopeContract(depth=ScopeDepth.D1, breadth_limit=5)
    packet = engine.resolve_context(
        role="Data Manager",
        purpose="Improve Data Quality",
        task="Identify why daily reporting is delayed",
        current_point="node:role:decision_owner_042",
        scope=scope,
    )

    assert packet.target_node == "node:role:decision_owner_042"
    assert len(packet.nodes) <= 5
    assert len(packet.evidence) >= 1
    assert "node:role:decision_owner_042" in packet.relevance_scores


def test_presentation_views():
    """Verify formatting of Human L1, L2, Machine JSON, and Navigation tiers."""
    store = SeedDataLoader.load_seed_graph()
    engine = ContextResolutionEngine(graph_store=store)
    packet = engine.resolve_context(
        role="Data Manager",
        purpose="Improve Data Quality",
        task="Identify why daily reporting is delayed",
        current_point="node:role:decision_owner_042",
    )

    l1_text = PresentationFormatter.format_human_l1_summary(packet)
    assert "Context Summary" in l1_text
    assert packet.target_node in l1_text

    l2_text = PresentationFormatter.format_human_l2_detailed(packet)
    assert "Detailed Context Brief" in l2_text

    machine_json = PresentationFormatter.format_machine_json(packet)
    assert "context_id" in machine_json

    nav_text = PresentationFormatter.format_navigation_view(packet)
    assert "Next Exploration Points" in nav_text


def test_scope_expansion():
    """Verify progressive scope depth expansion."""
    depth, expanded = ScopeManager.expand_depth(ScopeDepth.D0)
    assert depth == ScopeDepth.D1 and expanded

    depth, expanded = ScopeManager.expand_depth(ScopeDepth.D1)
    assert depth == ScopeDepth.D2 and expanded

    depth, expanded = ScopeManager.expand_depth(ScopeDepth.D3)
    assert depth == ScopeDepth.D3 and not expanded
