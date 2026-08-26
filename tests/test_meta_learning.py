"""Tests for Meta-Learning Feedback Loop and Relevance Weight Updates."""

import pytest
from src.agents.meta_learning import MetaLearningAgent
from src.context_engine.resolver import ContextResolutionEngine
from src.context_engine.weighting import RelevanceWeightMatrix
from src.core.contracts import AgentResult, AgentPerformanceModel
from src.seeds.seed_loader import SeedDataLoader


def test_relevance_weight_matrix_calibration():
    """Verify dynamic weight normalization and updating."""
    matrix = RelevanceWeightMatrix()
    initial_task_w = matrix.weights["task_relevance"]

    matrix.update_weights({"task_relevance": 0.50, "recency": 0.05})
    assert matrix.weights["task_relevance"] > initial_task_w
    assert abs(sum(matrix.weights.values()) - 1.0) < 1e-5


@pytest.mark.asyncio
async def test_meta_learning_agent_evaluation():
    """Verify meta-learning report generation and calibration proposals."""
    store = SeedDataLoader.load_seed_graph()
    engine = ContextResolutionEngine(graph_store=store)
    packet = engine.resolve_context(
        role="Data Manager",
        purpose="Improve Data Quality",
        task="Identify why daily reporting is delayed",
        current_point="node:role:decision_owner_042",
    )

    meta_agent = MetaLearningAgent()
    res = await meta_agent.execute_cycle(packet)
    assert res.agent_name == "Meta-Learning Agent"

    sample_results = [
        AgentResult(
            agent_name="Observer",
            iteration_id="test_iter",
            observations=["Telemetry normal."],
            confidence=0.95,
        ),
        AgentResult(
            agent_name="Diagnostiker",
            iteration_id="test_iter",
            hypotheses=[],
            confidence=0.90,
        ),
    ]

    model = meta_agent.generate_performance_model(sample_results)
    assert isinstance(model, AgentPerformanceModel)
    assert model.diagnostic_accuracy >= 0.90
    assert "task_relevance" in model.recommended_weight_calibrations
