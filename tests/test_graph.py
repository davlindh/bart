"""Tests for Knowledge Graph Store and Universal ERD Models."""

import pytest
from src.core.types import DomainType
from src.graph.graph_store import KnowledgeGraphStore
from src.graph.models import Organization, Person, Role, Team
from src.seeds.seed_loader import SeedDataLoader


def test_seed_data_loader():
    """Verify that seed loader correctly populates the graph store with nodes and edges."""
    store = SeedDataLoader.load_seed_graph()
    nodes = store.get_all_nodes()
    edges = store.get_all_edges()

    assert len(nodes) >= 15
    assert len(edges) >= 8

    decision_owner = store.get_node("node:role:decision_owner_042")
    assert decision_owner is not None
    assert decision_owner.label == "Decision Owner (Reporting SLA)"
    assert decision_owner.properties["turnaround_days"] == 12


def test_graph_traversal():
    """Verify multi-hop graph traversal outwards from focal node."""
    store = SeedDataLoader.load_seed_graph()
    nodes_d1, edges_d1, distances_d1 = store.traverse_subgraph("node:role:decision_owner_042", depth=1)

    node_ids_d1 = {n.id for n in nodes_d1}
    assert "node:role:decision_owner_042" in node_ids_d1
    assert "node:process:data_pipeline_z" in node_ids_d1
    assert "node:kpi:decision_time" in node_ids_d1
    assert distances_d1["node:role:decision_owner_042"] == 0
    assert distances_d1["node:process:data_pipeline_z"] == 1


def test_erd_model_instantiation():
    """Verify Pydantic Universal ERD model instantiation."""
    org = Organization(organization_id="org_test", name="Test Org")
    assert org.size == "ENTERPRISE"

    team = Team(team_id="team_test", organization_id=org.organization_id, name="Test Squad", purpose="Testing")
    assert team.type == "CROSS_FUNCTIONAL"

    person = Person(person_id="p_test", team_id=team.team_id, name="Alice", role_title="Lead Architect")
    assert person.seniority == "SENIOR"
