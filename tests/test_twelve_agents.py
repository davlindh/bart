"""Unit tests for all 12 Core Team Dynamics Agents and their execution lifecycle."""

import pytest
from src.core.contracts import ContextPacket
from src.core.types import ScopeLevel, PerspectiveWindow
from src.agents import (
    TWELVE_CORE_AGENTS,
    ObserverAgent,
    DiagnosticianAgent,
    TeamArchitectAgent,
    RoleTransitionAgent,
    CollaborationAgent,
    WellbeingAgent,
    AIEthicsAgent,
    MetaLearningAgent,
    MeasurementAgent,
    LearningAgent,
    OrchestratorAgent,
    ExperimentAgent,
)


def test_twelve_core_agents_registry():
    """Verify exactly 12 core agents are registered in the loop."""
    assert len(TWELVE_CORE_AGENTS) == 12


def test_full_12_agent_lifecycle_execution():
    """Verify sequential execution of all 12 agents on a shared context packet."""
    context = ContextPacket(
        context_id="ctx_12_loop_test",
        role="CFO",
        purpose="12-Agent Test",
        task="Testa sekventiell loop",
        scope=ScopeLevel.D1_DIRECT,
        perspective_window=PerspectiveWindow.W6_PERSONNEL_MANAGEMENT,
        primary_entity={"overtime_hours": 14.5, "team_name": "Fältteam"},
    )

    results = []
    for AgentCls in TWELVE_CORE_AGENTS:
        agent = AgentCls()
        # Verify 6-step methods exist
        assert hasattr(agent, "observe")
        assert hasattr(agent, "analyze")
        assert hasattr(agent, "identify")
        assert hasattr(agent, "propose")
        assert hasattr(agent, "act")
        assert hasattr(agent, "evaluate")
        assert hasattr(agent, "run_step")

        # Test single step execution
        step_res = agent.run_step("observe", context)
        assert step_res["step"] == "observe"

        # Test full lifecycle run
        result = agent.run(context)
        assert result.status.value == "completed"
        results.append(result)

    assert len(results) == 12
    # Verify MetaLearning updated weights
    meta_res = [r for r in results if r.agent_name == "MetaLearningAgent"][0]
    assert "active_weights" in meta_res.metrics_summary
