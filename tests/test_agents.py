"""Tests for Multi-Agent Lifecycle, Contract Enforcement and Orchestrator."""

import pytest
from src.agents.diagnostician import DiagnosticianAgent
from src.agents.observer import ObserverAgent
from src.agents.orchestrator import TeamDynamicsOrchestrator
from src.context_engine.resolver import ContextResolutionEngine
from src.core.contracts import AgentResult
from src.core.types import ScopeDepth
from src.seeds.seed_loader import SeedDataLoader


@pytest.mark.asyncio
async def test_agent_six_function_lifecycle():
    """Verify standard 6-function lifecycle execution and AgentResult structure."""
    store = SeedDataLoader.load_seed_graph()
    engine = ContextResolutionEngine(graph_store=store)
    packet = engine.resolve_context(
        role="Data Manager",
        purpose="Improve Data Quality",
        task="Identify why daily reporting is delayed",
        current_point="node:role:decision_owner_042",
    )

    observer = ObserverAgent()
    result = await observer.execute_cycle(packet)

    assert isinstance(result, AgentResult)
    assert result.agent_name == "Observer"
    assert len(result.observations) > 0
    assert len(result.identified_issues) > 0
    assert len(result.hypotheses) > 0
    assert len(result.actions) > 0
    assert result.confidence >= 0.8


@pytest.mark.asyncio
async def test_full_orchestrator_cycle():
    """Verify complete 12-agent optimization cycle."""
    store = SeedDataLoader.load_seed_graph()
    engine = ContextResolutionEngine(graph_store=store)
    orchestrator = TeamDynamicsOrchestrator(graph_store=store, context_engine=engine)

    cycle_output = await orchestrator.run_full_optimization_cycle(
        role="Data Manager",
        purpose="Improve Data Quality",
        task="Identify why daily reporting is delayed",
        current_point="node:role:decision_owner_042",
        initial_depth=ScopeDepth.D1,
    )

    assert "cycle_id" in cycle_output
    assert len(cycle_output["agent_results"]) == 13
    assert cycle_output["summary"]["measured_improvement"] == -65.0
    assert cycle_output["performance_model"].diagnostic_accuracy > 0.9
