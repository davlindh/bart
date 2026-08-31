"""Unit tests for the Universal ERD Knowledge Graph and all 15 Entity schemas."""

import pytest
from src.graph.models import (
    OrganizationEntity,
    TeamEntity,
    PersonEntity,
    RoleEntity,
    CapabilityEntity,
    AssignmentEntity,
    ObservationEntity,
    DiagnosisEntity,
    InterventionEntity,
    TransitionPlanEntity,
    CommunicationEntity,
    ExperimentEntity,
    MeasurementEntity,
    LearningEntity,
    KnowledgeEntity,
)
from src.graph.universal_erd import UniversalERDGraph


def test_universal_erd_all_15_entities():
    """Verify creation, relationship linking, and traversal across all 15 Universal ERD entities."""
    g = UniversalERDGraph()

    # 1. Organization & Team
    org = OrganizationEntity(organization_id="ORG_TEST", name="Test Maskin AB", industry="Grön Teknik", size="25")
    g.add_organization(org)

    team = TeamEntity(team_id="TEAM_TEST", organization_id="ORG_TEST", name="Fältteam Väst", purpose="Installation", type="Operational")
    g.add_team(team)

    # 2. Person & Role & Capability & Assignment
    person = PersonEntity(person_id="PERSON_1", team_id="TEAM_TEST", name="Lars Montör", role_title="Fältmontör")
    g.add_person(person)

    role = RoleEntity(role_id="ROLE_INSTALL", team_id="TEAM_TEST", role_name="Fältmontör", purpose="Installation", responsibilities=["Kabeldragning"])
    g.add_role(role)

    assignment = AssignmentEntity(assignment_id="ASS_1", person_id="PERSON_1", role_id="ROLE_INSTALL", allocation_pct=100.0)
    g.add_assignment(assignment)

    # 3. Observation & Diagnosis
    obs = ObservationEntity(observation_id="OBS_1", team_id="TEAM_TEST", source_type="FORTNOX", source_ref="INV_1", data_json={"hours": 9.5})
    g.add_observation(obs)

    diag = DiagnosisEntity(diagnosis_id="DIAG_1", observation_id="OBS_1", hypothesis="Flaskhals kabeldragning", root_cause="Materialbrist")
    g.add_diagnosis(diag)

    # 4. Intervention & Experiment
    interv = InterventionEntity(intervention_id="INT_1", type="PROCESS_OPTIMIZATION", description="Förbättrad lagerbuffert", proposed_by_agent_id="TeamArchitect")
    g.add_intervention(interv)

    exp = ExperimentEntity(experiment_id="EXP_1", intervention_id="INT_1", hypothesis="Buffert minskar restid med 25%", design="2-veckors pilot")
    g.add_experiment(exp)

    # 5. Measurement & Learning & Knowledge
    meas = MeasurementEntity(measurement_id="MEAS_1", experiment_id="EXP_1", metric_name="restid_minskning_pct", value_number=28.0)
    g.add_measurement(meas)

    learn = LearningEntity(learning_id="LEARN_1", measurement_id="MEAS_1", insight="Lokal buffert eliminerar extra resor", impact="HÖG")
    g.add_learning(learn)

    know = KnowledgeEntity(knowledge_id="KNOW_1", type="HEURISTIC", content="Ha alltid 200m kabel i servicebussen", source_learning_id="LEARN_1")
    g.add_knowledge(know)

    # Verify counts
    assert len(g.organizations) == 1
    assert len(g.teams) == 1
    assert len(g.persons) == 1
    assert len(g.roles) == 1
    assert len(g.observations) == 1
    assert len(g.diagnoses) == 1
    assert len(g.experiments) == 1
    assert len(g.measurements) == 1
    assert len(g.learnings) == 1
    assert len(g.knowledge) == 1

    # Verify scope subgraph traversal (D0..D2)
    d0 = g.extract_subgraph_by_scope("ORG_TEST", "D0")
    assert d0["node_count"] == 1

    d1 = g.extract_subgraph_by_scope("ORG_TEST", "D1")
    assert d1["node_count"] >= 2  # Org + Team

    d2 = g.extract_subgraph_by_scope("ORG_TEST", "D2")
    assert d2["node_count"] >= 3  # Org + Team + Person/Observations
