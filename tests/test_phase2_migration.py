"""Tests for Phase 2 migrated components: Insight Agents, NavID, MPS Governance."""

import pytest
from src.agents.insight_agents import InsightIntegrationAgent, InsightSynthesizerAgent
from src.context_engine.resolver import ContextResolutionEngine
from src.core.contracts import ScopeContract
from src.core.governance import (
    ModificationProposalSystem,
    ProposalImpact,
    ProposalStatus,
)
from src.core.types import DomainType, ScopeDepth
from src.graph.graph_store import (
    KnowledgeGraphStore,
    generate_nav_id,
)
from src.seeds.seed_loader import SeedDataLoader


# ── Insight Agents Tests ────────────────────────────────────────────────


@pytest.fixture
def seeded_context_packet():
    """Create a context packet from seed data for insight agent testing."""
    store = SeedDataLoader.load_seed_graph()
    engine = ContextResolutionEngine(store)
    scope = ScopeContract(depth=ScopeDepth.D1, breadth_limit=6)
    return engine.resolve_context(
        role="Data Manager",
        purpose="Evaluate team dynamics",
        task="Identify pipeline bottlenecks",
        current_point="node:role:decision_owner_042",
        scope=scope,
    )


@pytest.mark.asyncio
async def test_integration_agent_lifecycle(seeded_context_packet):
    """InsightIntegrationAgent should complete full 6-function lifecycle."""
    agent = InsightIntegrationAgent()
    result = await agent.execute_cycle(seeded_context_packet)

    assert result.agent_name == "Insight Integration Agent"
    assert result.confidence > 0.5
    assert len(result.observations) > 0
    assert any("Scanning" in obs for obs in result.observations)
    assert result.metrics.get("active_window_count", 0) > 0
    assert result.metrics.get("total_windows") == 9


@pytest.mark.asyncio
async def test_synthesizer_agent_lifecycle(seeded_context_packet):
    """InsightSynthesizerAgent should complete full 6-function lifecycle."""
    agent = InsightSynthesizerAgent()
    result = await agent.execute_cycle(seeded_context_packet)

    assert result.agent_name == "Insight Synthesizer Agent"
    assert result.confidence > 0.5
    assert len(result.observations) > 0
    assert result.metrics.get("synthesis_depth") in ("comprehensive", "preliminary")


@pytest.mark.asyncio
async def test_integration_synthesizer_sequential_handoff(seeded_context_packet):
    """Integration agent should run before Synthesizer, with the Synthesizer
    consuming the same context enriched by Integration's analysis."""
    integration = InsightIntegrationAgent()
    synthesizer = InsightSynthesizerAgent()

    res_int = await integration.execute_cycle(seeded_context_packet)
    res_syn = await synthesizer.execute_cycle(seeded_context_packet)

    # Both should succeed
    assert res_int.confidence > 0.5
    assert res_syn.confidence > 0.5
    # Integration identifies coverage gaps or coherence status
    assert res_int.metrics.get("coverage_ratio") is not None
    # Synthesizer produces theme analysis
    assert res_syn.metrics.get("theme_count") is not None


# ── NavID System Tests ──────────────────────────────────────────────────


def test_navid_generation():
    """NavID should follow the DOMAIN-Type.Label format."""
    nav_id = generate_nav_id(DomainType.OPERATIONAL, "Process", "Data Pipeline Z")
    assert nav_id.startswith("OPS-")
    assert "Process" in nav_id
    assert "DataPipelineZ" in nav_id


def test_navid_auto_assigned_on_add():
    """Nodes should auto-generate NavIDs when none is provided."""
    store = KnowledgeGraphStore()
    node = store.add_node("test_1", "Role", DomainType.TRUST, "Security Lead")
    assert node.nav_id is not None
    assert node.nav_id.startswith("TRS-")


def test_navid_lookup():
    """Nodes should be retrievable by NavID."""
    store = KnowledgeGraphStore()
    node = store.add_node("test_2", "KPI", DomainType.DATA, "Revenue Metric")
    found = store.get_node_by_navid(node.nav_id)
    assert found is not None
    assert found.id == "test_2"


def test_navid_prefix_search():
    """Prefix search should return all nodes in a domain."""
    store = KnowledgeGraphStore()
    store.add_node("a1", "Process", DomainType.OPERATIONAL, "ETL Pipeline")
    store.add_node("a2", "Process", DomainType.OPERATIONAL, "Report Pipeline")
    store.add_node("b1", "User", DomainType.TRUST, "Admin User")

    ops_nodes = store.search_by_navid_prefix("OPS-")
    assert len(ops_nodes) == 2
    trust_nodes = store.search_by_navid_prefix("TRS-")
    assert len(trust_nodes) == 1


def test_navid_in_search():
    """search_nodes should also match against NavIDs."""
    store = KnowledgeGraphStore()
    store.add_node("test_3", "Process", DomainType.OPERATIONAL, "Pipeline Alpha")
    results = store.search_nodes("ops-process")
    assert len(results) >= 1


# ── MPS Governance Tests ────────────────────────────────────────────────


def test_mps_full_lifecycle():
    """Proposal should flow through DRAFT → PENDING → APPROVED → IMPLEMENTED."""
    mps = ModificationProposalSystem()
    proposal = mps.create_proposal(
        title="Add Tiered Approval System",
        summary="Implement 3-tier approval delegation for Pipeline Z decisions.",
        author="Team Architect",
        impact=ProposalImpact.HIGH,
        affected_components=["OPS-Role.DecisionOwner042"],
    )
    assert proposal.status == ProposalStatus.DRAFT
    assert proposal.proposal_id == "MPS-0001"

    # Submit for review
    mps.submit_for_review(proposal.proposal_id)
    assert proposal.status == ProposalStatus.PENDING

    # Agent approvals
    mps.add_agent_approval(proposal.proposal_id, "AI Ethics Agent", True, "No concerns")
    mps.add_agent_approval(proposal.proposal_id, "Security Agent", True, "Passes audit")

    # Finalize
    mps.finalize_review(proposal.proposal_id, required_approvals=2)
    assert proposal.status == ProposalStatus.APPROVED

    # Implement
    mps.mark_implemented(proposal.proposal_id)
    assert proposal.status == ProposalStatus.IMPLEMENTED

    # Verify immutable history
    assert len(proposal.status_history) == 4  # DRAFT → PENDING → APPROVED → IMPLEMENTED


def test_mps_rejection_on_any_rejection():
    """Any agent rejection should result in REJECTED status."""
    mps = ModificationProposalSystem()
    proposal = mps.create_proposal(
        title="Remove Audit Logging",
        summary="Proposal to disable audit logs for performance.",
        author="Dev",
    )
    mps.submit_for_review(proposal.proposal_id)
    mps.add_agent_approval(proposal.proposal_id, "AI Ethics Agent", False, "Violates compliance policy")
    mps.finalize_review(proposal.proposal_id)

    assert proposal.status == ProposalStatus.REJECTED


def test_mps_rollback():
    """Implemented proposals should support rollback with reason tracking."""
    mps = ModificationProposalSystem()
    proposal = mps.create_proposal(title="Experiment Config", summary="Change config", author="Exp Agent")
    mps.submit_for_review(proposal.proposal_id)
    mps.add_agent_approval(proposal.proposal_id, "Ethics", True)
    mps.finalize_review(proposal.proposal_id)
    mps.mark_implemented(proposal.proposal_id)

    mps.rollback(proposal.proposal_id, reason="Experiment results showed regression")
    assert proposal.status == ProposalStatus.ROLLED_BACK
    assert any("ROLLBACK" in c.content for c in proposal.comments)


def test_mps_commenting():
    """Comments should be appendable at any status."""
    mps = ModificationProposalSystem()
    proposal = mps.create_proposal(title="Test", summary="Test proposal", author="Bot")
    mps.add_comment(proposal.proposal_id, "Reviewer", "Need more details on impact")
    assert len(proposal.comments) == 1
    assert proposal.comments[0].author == "Reviewer"


def test_mps_listing_by_status():
    """Should filter proposals by status."""
    mps = ModificationProposalSystem()
    mps.create_proposal(title="A", summary="a", author="1")
    p2 = mps.create_proposal(title="B", summary="b", author="2")
    mps.submit_for_review(p2.proposal_id)

    drafts = mps.list_proposals(status=ProposalStatus.DRAFT)
    pending = mps.list_proposals(status=ProposalStatus.PENDING)

    assert len(drafts) == 1
    assert len(pending) == 1
