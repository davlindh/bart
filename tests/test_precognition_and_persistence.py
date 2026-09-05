"""Comprehensive tests for Self-Preservation and Intentional Contextual Pre-Cognition."""

import os
import tempfile
import pytest
from pathlib import Path

from src.core.types import Domain, PerspectiveWindow, ScopeLevel
from src.core.contracts import ContextPacket, Observation
from src.core.precognition import (
    ProjectIntent,
    PreCognitionTrajectory,
    TrajectoryNode,
    PredictedSkillNeed,
    ProjectCheckpoint,
    IntentStatus,
)
from src.graph.universal_erd import UniversalERDGraph
from src.graph.models import OrganizationEntity, TeamEntity, PersonEntity, RoleEntity
from src.graph.persistence_bridge import GraphPersistenceBridge
from src.context_engine.precognition import PreCognitiveEngine
from src.agents.orchestrator import OrchestratorAgent


@pytest.fixture
def sample_graph():
    """Builds a representative sample Universal ERD graph."""
    graph = UniversalERDGraph()
    org = OrganizationEntity(organization_id="ORG_TEST", name="Nordic Tech Solutions AB", industry="SaaS", size="50 anställda")
    graph.add_organization(org)

    team1 = TeamEntity(team_id="TEAM_DEV", organization_id="ORG_TEST", name="Utveckling & Arkitektur", purpose="Utveckla mjukvara", type="Engineering")
    team2 = TeamEntity(team_id="TEAM_FIN", organization_id="ORG_TEST", name="Ekonomi & Skatt", purpose="Finansiell styrning", type="Operational")
    graph.add_team(team1)
    graph.add_team(team2)

    emp1 = PersonEntity(person_id="EMP_01", team_id="TEAM_FIN", name="Anna Lind", role_title="CFO")
    graph.add_person(emp1)

    role1 = RoleEntity(role_id="ROLE_CFO", team_id="TEAM_FIN", role_name="CFO", purpose="Ekonomiskt ledarskap")
    graph.add_role(role1)

    # Add custom nodes and edges for navigation
    graph.add_node("node_vmb_audit", "VMB Skatterevision", "Task", "Exchange")
    graph.add_node("node_sandbox_sim", "Simulering av K10-utdelning", "Simulation", "Tools")
    graph.add_node("node_role_realign", "Omstrukturering av Roller", "Governance", "Operational")

    graph.add_edge("ORG_TEST", "TEAM_FIN", "HAS")
    graph.add_edge("TEAM_FIN", "node_vmb_audit", "EXECUTES")
    graph.add_edge("node_vmb_audit", "node_sandbox_sim", "VALIDATES_WITH")
    graph.add_edge("node_vmb_audit", "node_role_realign", "TRIGGERS")

    return graph


@pytest.fixture
def sample_intent():
    """Builds an explicit Project Intent."""
    return ProjectIntent(
        intent_id="intent_q3_optimization",
        project_id="PRJ_Q3_AUDIT",
        mandate="Optimera VMB och säkra projekttillstånd i sandlåda före bokslut",
        desired_state={"target_savings_sek": 45000.0, "compliance_audit": "PASSED"},
        target_kpis={"gross_margin_boost_pct": 12.5},
        allowed_domains=[Domain.EXCHANGE, Domain.OPERATIONAL, Domain.TRUST],
        horizon_steps=3,
        status=IntentStatus.ACTIVE,
    )


# =========================================================================
# 1. Tests for GraphPersistenceBridge (Self-Preservation)
# =========================================================================

def test_persistence_bridge_save_and_restore(sample_graph, sample_intent):
    """Verifies atomic snapshot save and exact state restoration via SQLite WAL."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = os.path.join(tmp_dir, "test_persistence.db")
        bridge = GraphPersistenceBridge(db_path=db_path)

        agent_states = {
            "TaxOptimizationAgent": {"last_savings_found": 3200.0},
            "ObserverAgent": {"signals_captured": 5},
        }

        # Save checkpoint
        checkpoint = bridge.save_checkpoint(
            project_id="PRJ_Q3_AUDIT",
            erd_graph=sample_graph,
            intent=sample_intent,
            agent_states=agent_states,
        )

        assert checkpoint.checkpoint_id.startswith("chk_PRJ_Q3_AUDIT_")
        assert checkpoint.node_count > 0
        assert checkpoint.edge_count > 0
        assert len(checkpoint.checksum_sha256) == 64

        # List checkpoints
        checkpoints_list = bridge.list_checkpoints(project_id="PRJ_Q3_AUDIT")
        assert len(checkpoints_list) == 1
        assert checkpoints_list[0]["checkpoint_id"] == checkpoint.checkpoint_id

        # Restore checkpoint
        restored = bridge.restore_checkpoint(checkpoint_id=checkpoint.checkpoint_id)
        assert restored is not None
        assert restored["project_id"] == "PRJ_Q3_AUDIT"
        assert restored["intent"].mandate == sample_intent.mandate
        assert restored["agent_states"]["TaxOptimizationAgent"]["last_savings_found"] == 3200.0
        assert restored["checksum_sha256"] == checkpoint.checksum_sha256

        # Check restored graph integrity
        restored_graph = restored["erd_graph"]
        assert len(restored_graph.nodes) == len(sample_graph.nodes)


def test_persistence_agent_memory(sample_intent):
    """Verifies granular key-value memory persistence for individual agents."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = os.path.join(tmp_dir, "test_mem.db")
        bridge = GraphPersistenceBridge(db_path=db_path)

        bridge.save_agent_memory("MetaLearningAgent", "PRJ_01", "heuristic_weights", {"D1": 0.85, "D2": 0.55})
        val = bridge.get_agent_memory("MetaLearningAgent", "PRJ_01", "heuristic_weights")

        assert val is not None
        assert val["D1"] == 0.85
        assert val["D2"] == 0.55


# =========================================================================
# 2. Tests for PreCognitiveEngine (Intentional Pre-Cognition)
# =========================================================================

def test_precognition_trajectory_projection(sample_graph, sample_intent):
    """Verifies trajectory projection, proactive skill matching, and context pre-fetching."""
    trajectory = PreCognitiveEngine.project_trajectory(
        intent=sample_intent,
        current_node_id="TEAM_FIN",
        graph=sample_graph,
        role="CFO",
    )

    assert isinstance(trajectory, PreCognitionTrajectory)
    assert len(trajectory.predicted_nodes) > 0
    assert trajectory.confidence_score > 0.80

    # Verify skill predictions
    skill_names = [s.skill_name for s in trajectory.predicted_skills]
    assert "disk-persistence" in skill_names or "tax-optimization" in skill_names

    # Verify pre-fetched context packets
    assert len(trajectory.prefetched_context_packets) > 0
    pkt = trajectory.prefetched_context_packets[0]
    assert pkt.role == "CFO"
    assert pkt.scope == ScopeLevel.D1_DIRECT


def test_precognition_friction_detection(sample_graph, sample_intent):
    """Verifies proactive detection of friction when telemetry signals overtime."""
    obs = [
        Observation(
            observation_id="obs_ot_1",
            source="FORTNOX_TIME",
            entity_id="EMP_01",
            metric_name="overtime_hours",
            metric_value=14.5,
        )
    ]

    trajectory = PreCognitiveEngine.project_trajectory(
        intent=sample_intent,
        current_node_id="TEAM_FIN",
        graph=sample_graph,
        role="CFO",
        observations=obs,
    )

    # Should detect anticipated friction due to overtime
    assert len(trajectory.anticipated_frictions) > 0
    friction = trajectory.anticipated_frictions[0]
    assert friction.domain == Domain.TRUST
    assert "övertid" in friction.predicted_issue.lower()


# =========================================================================
# 3. Tests for Upgraded Pre-Cognitive Orchestrator
# =========================================================================

def test_orchestrator_pre_cognitive_execution(sample_graph, sample_intent):
    """Verifies OrchestratorAgent utilizes pre-cognition for proactive sequencing."""
    orchestrator = OrchestratorAgent()

    context = ContextPacket(
        context_id="ctx_orch_test",
        role="CFO",
        purpose="Helhetsrevision",
        task="Orkestrera nästa steg",
        scope=ScopeLevel.D1_DIRECT,
        allowed_domains=[Domain.OPERATIONAL, Domain.EXCHANGE],
        perspective_window=PerspectiveWindow.W5_FINANCIAL_MANAGEMENT,
    )

    result = orchestrator.orchestrate_project(
        intent=sample_intent,
        current_node_id="TEAM_FIN",
        graph=sample_graph,
        context=context,
    )

    assert result["orchestrator_status"] == "completed"
    assert "trajectory_id" in result
    assert len(result["predicted_nodes"]) > 0
    assert len(result["recommendations"]) > 0
    assert any("disk-persistence" in r for r in result["recommendations"])


# =========================================================================
# 4. Tests for Server Endpoints
# =========================================================================

def test_server_precognition_and_checkpoint_handlers():
    """Verifies server handler logic for precognition and checkpoint endpoints."""
    from src.server import BARTRequestHandler

    handler = BARTRequestHandler.__new__(BARTRequestHandler)
    erd_data = handler._get_erd_graph_data()
    assert "nodes" in erd_data
    assert len(erd_data["nodes"]) >= 16

    # Test persistence bridge listing
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = os.path.join(tmp_dir, "test_server_chk.db")
        bridge = GraphPersistenceBridge(db_path=db_path)
        chks = bridge.list_checkpoints()
        assert isinstance(chks, list)


# =========================================================================
# 5. Tests for Contextual Pre-Cognition Further Development Features
# =========================================================================

def test_auto_checkpoint_pruning(sample_graph, sample_intent):
    """Verifies that prune_checkpoints retains exactly keep_last checkpoints and deletes older ones."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = os.path.join(tmp_dir, "test_pruning.db")
        bridge = GraphPersistenceBridge(db_path=db_path)

        # Save 8 checkpoints
        for i in range(8):
            bridge.save_checkpoint(
                project_id="PRJ_PRUNE",
                erd_graph=sample_graph,
                intent=sample_intent,
                trigger_source=f"step_{i}"
            )

        all_chks = bridge.list_checkpoints(project_id="PRJ_PRUNE")
        assert len(all_chks) == 8

        # Prune to keep only the 3 newest
        pruned_count = bridge.prune_checkpoints(project_id="PRJ_PRUNE", keep_last=3)
        assert pruned_count == 5

        remaining = bridge.list_checkpoints(project_id="PRJ_PRUNE")
        assert len(remaining) == 3


def test_checkpoint_diffing(sample_graph, sample_intent):
    """Verifies structural diff between two checkpoints returns correct added/removed counts."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = os.path.join(tmp_dir, "test_diff.db")
        bridge = GraphPersistenceBridge(db_path=db_path)

        # Snapshot A: initial graph
        chk_a = bridge.save_checkpoint(
            project_id="PRJ_DIFF",
            erd_graph=sample_graph,
            intent=sample_intent,
            trigger_source="initial"
        )

        # Modify graph: add a node, remove one node
        sample_graph.add_node("node_extra_tax", "Extra Skattekonto", "Account", "Exchange")
        del sample_graph.nodes["node_sandbox_sim"]

        # Intent drift
        drifted_intent = ProjectIntent(
            intent_id="intent_drifted",
            project_id="PRJ_DIFF",
            mandate="Ny reviderad inriktning: Säkra momsdeklaration och likviditetsbuffert",
            target_kpis={"gross_margin_boost_pct": 18.0},
            horizon_steps=4,
            status=IntentStatus.CONVERGING
        )

        # Snapshot B: modified graph
        chk_b = bridge.save_checkpoint(
            project_id="PRJ_DIFF",
            erd_graph=sample_graph,
            intent=drifted_intent,
            trigger_source="drifted"
        )

        # Compute diff
        diff = bridge.diff_checkpoints(chk_a.checkpoint_id, chk_b.checkpoint_id)

        assert "error" not in diff
        assert "node_extra_tax" in diff["nodes_added"]
        assert "node_sandbox_sim" in diff["nodes_removed"]
        assert diff["intent_drift"] is not None
        assert "momsdeklaration" in diff["intent_drift"]


def test_intent_convergence_evaluation(sample_intent):
    """Verifies status transitions for ACTIVE -> CONVERGING -> ACHIEVED and BLOCKED scenarios."""
    from src.core.precognition import AnticipatedFriction

    # Scenario 1: Initial state -> ACTIVE
    status_active = PreCognitiveEngine.evaluate_intent_convergence(
        intent=sample_intent,
        trajectory=None,
        current_state={"target_savings_sek": 10000.0}
    )
    assert status_active == IntentStatus.ACTIVE

    # Scenario 2: Close to desired state -> CONVERGING
    # Target savings is 45000, current state is 43000 (within 10%)
    status_converging = PreCognitiveEngine.evaluate_intent_convergence(
        intent=sample_intent,
        trajectory=None,
        current_state={"target_savings_sek": 43000.0, "compliance_audit": "IN_REVIEW"}
    )
    assert status_converging == IntentStatus.CONVERGING

    # Scenario 3: All KPIs achieved -> ACHIEVED
    status_achieved = PreCognitiveEngine.evaluate_intent_convergence(
        intent=sample_intent,
        trajectory=None,
        current_state={"target_savings_sek": 46000.0, "compliance_audit": "PASSED"}
    )
    assert status_achieved == IntentStatus.ACHIEVED

    # Scenario 4: Critical blocking friction present -> BLOCKED
    traj_with_critical = PreCognitionTrajectory(
        trajectory_id="traj_blocked",
        project_intent=sample_intent,
        current_point_id="TEAM_FIN",
        confidence_score=0.9,
        anticipated_frictions=[
            AnticipatedFriction(
                friction_id="fric_crit",
                domain=Domain.TRUST,
                predicted_issue="Kritiskt skattebrottshinder",
                root_factor="Saknat underlag",
                lead_time_steps=0,
                preventive_action="Stoppa omedelbart",
                severity="critical"
            )
        ]
    )
    status_blocked = PreCognitiveEngine.evaluate_intent_convergence(
        intent=sample_intent,
        trajectory=traj_with_critical,
        current_state={"target_savings_sek": 20000.0}
    )
    assert status_blocked == IntentStatus.BLOCKED


def test_trajectory_persistence_in_checkpoint(sample_graph, sample_intent):
    """Verifies that pre-cognitive trajectory snapshots roundtrip cleanly through SQLite WAL checkpoints."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = os.path.join(tmp_dir, "test_traj_persist.db")
        bridge = GraphPersistenceBridge(db_path=db_path)

        # Generate a real trajectory
        traj = PreCognitiveEngine.project_trajectory(
            intent=sample_intent,
            current_node_id="TEAM_FIN",
            graph=sample_graph,
            role="CFO",
        )

        # Save checkpoint with trajectory
        chk = bridge.save_checkpoint(
            project_id="PRJ_TRAJ_PERSIST",
            erd_graph=sample_graph,
            intent=sample_intent,
            trajectory=traj,
            trigger_source="pre_cognitive_evaluation"
        )

        assert chk.has_trajectory is True

        # List checkpoints and verify has_trajectory metadata
        chks = bridge.list_checkpoints(project_id="PRJ_TRAJ_PERSIST")
        assert len(chks) == 1
        assert chks[0]["has_trajectory"] is True
        assert chks[0]["trigger_source"] == "pre_cognitive_evaluation"
        assert chks[0]["trajectory_snapshot"] is not None
        assert len(chks[0]["trajectory_snapshot"]["predicted_nodes"]) > 0

        # Restore checkpoint and check trajectory
        restored = bridge.restore_checkpoint(chk.checkpoint_id)
        assert restored is not None
        assert restored["trajectory"].trajectory_id == traj.trajectory_id


