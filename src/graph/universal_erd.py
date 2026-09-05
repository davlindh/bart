"""Universal ERD Knowledge Graph Store: Manages entities, bidirectional relationships, and scope-based subgraph queries."""

from typing import Dict, List, Any, Optional, Set, Tuple
from collections import defaultdict
from .models import (
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


class UniversalERDGraph:
    """In-memory bidirectional relational graph store implementing the Universal ERD schema."""

    def __init__(self):
        # Entity collections indexed by ID
        self.organizations: Dict[str, OrganizationEntity] = {}
        self.teams: Dict[str, TeamEntity] = {}
        self.persons: Dict[str, PersonEntity] = {}
        self.roles: Dict[str, RoleEntity] = {}
        self.capabilities: Dict[str, CapabilityEntity] = {}
        self.assignments: Dict[str, AssignmentEntity] = {}
        self.observations: Dict[str, ObservationEntity] = {}
        self.diagnoses: Dict[str, DiagnosisEntity] = {}
        self.interventions: Dict[str, InterventionEntity] = {}
        self.transition_plans: Dict[str, TransitionPlanEntity] = {}
        self.communications: Dict[str, CommunicationEntity] = {}
        self.experiments: Dict[str, ExperimentEntity] = {}
        self.measurements: Dict[str, MeasurementEntity] = {}
        self.learnings: Dict[str, LearningEntity] = {}
        self.knowledge: Dict[str, KnowledgeEntity] = {}

        # Generic node registry
        self.nodes: Dict[str, Dict[str, Any]] = {}
        # Adjacency maps for bidirectional graph traversal
        self.outgoing_edges: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.incoming_edges: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

    def add_node(self, node_id: str, label: str, node_type: str, domain: str = "Operational", metadata: Optional[Dict[str, Any]] = None):
        """Registers a node in the generic graph store."""
        self.nodes[node_id] = {
            "id": node_id,
            "label": label,
            "type": node_type,
            "domain": domain,
            "metadata": metadata or {},
        }

    def add_edge(self, source_id: str, target_id: str, relation: str, weight: float = 1.0):
        """Adds a directed relationship between two nodes."""
        edge = {"source": source_id, "target": target_id, "relation": relation, "weight": weight}
        self.outgoing_edges[source_id].append(edge)
        self.incoming_edges[target_id].append(edge)

    # ── Entity Insertion Helpers ──────────────────────────────────────────────

    def add_organization(self, org: OrganizationEntity):
        self.organizations[org.organization_id] = org
        self.add_node(org.organization_id, org.name, "Organization", "Trust", org.model_dump())

    def add_team(self, team: TeamEntity):
        self.teams[team.team_id] = team
        self.add_node(team.team_id, team.name, "Team", "Operational", team.model_dump())
        self.add_edge(team.organization_id, team.team_id, "HAS")

    def add_person(self, person: PersonEntity):
        self.persons[person.person_id] = person
        self.add_node(person.person_id, person.name, "Person", "Interactional Interface", person.model_dump())
        self.add_edge(person.team_id, person.person_id, "INCLUDES")

    def add_role(self, role: RoleEntity):
        self.roles[role.role_id] = role
        self.add_node(role.role_id, role.role_name, "Role", "Operational", role.model_dump())
        self.add_edge(role.team_id, role.role_id, "DEFINES")

    def add_capability(self, cap: CapabilityEntity, role_id: Optional[str] = None):
        self.capabilities[cap.capability_id] = cap
        self.add_node(cap.capability_id, cap.name, "Capability", "Knowledge", cap.model_dump())
        if role_id:
            self.add_edge(role_id, cap.capability_id, "REQUIRES")

    def add_assignment(self, assignment: AssignmentEntity):
        self.assignments[assignment.assignment_id] = assignment
        self.add_node(assignment.assignment_id, f"Assignment:{assignment.person_id}->{assignment.role_id}", "Assignment", "Operational", assignment.model_dump())
        self.add_edge(assignment.person_id, assignment.assignment_id, "HAS")
        self.add_edge(assignment.assignment_id, assignment.role_id, "FILLED_BY")
        self.add_edge(assignment.person_id, assignment.role_id, "ASSIGNED_TO")

    def add_observation(self, obs: ObservationEntity):
        self.observations[obs.observation_id] = obs
        self.add_node(obs.observation_id, f"Observation:{obs.source_type}", "Observation", "Operational", obs.model_dump())
        self.add_edge(obs.team_id, obs.observation_id, "GENERATES")

    def add_diagnosis(self, diag: DiagnosisEntity):
        self.diagnoses[diag.diagnosis_id] = diag
        self.add_node(diag.diagnosis_id, f"Diagnosis:{diag.root_cause[:20]}", "Diagnosis", "Knowledge", diag.model_dump())
        self.add_edge(diag.observation_id, diag.diagnosis_id, "GENERATES")

    def add_intervention(self, interv: InterventionEntity):
        self.interventions[interv.intervention_id] = interv
        self.add_node(interv.intervention_id, f"Intervention:{interv.type}", "Intervention", "Tools", interv.model_dump())

    def add_transition_plan(self, plan: TransitionPlanEntity):
        self.transition_plans[plan.transition_plan_id] = plan
        self.add_node(plan.transition_plan_id, f"TransitionPlan:{plan.timeline}", "TransitionPlan", "Tools", plan.model_dump())
        self.add_edge(plan.intervention_id, plan.transition_plan_id, "PLAN")

    def add_communication(self, comm: CommunicationEntity):
        self.communications[comm.communication_id] = comm
        self.add_node(comm.communication_id, f"Comm:{comm.channel} ({comm.audience[:15]})", "Communication", "Interactional Interface", comm.model_dump())
        self.add_edge(comm.transition_plan_id, comm.communication_id, "INCLUDES")

    def add_experiment(self, exp: ExperimentEntity):
        self.experiments[exp.experiment_id] = exp
        self.add_node(exp.experiment_id, f"Experiment:{exp.hypothesis[:20]}", "Experiment", "Innovation & Tech", exp.model_dump())
        self.add_edge(exp.intervention_id, exp.experiment_id, "DESIGNED_AS")

    def add_measurement(self, meas: MeasurementEntity):
        self.measurements[meas.measurement_id] = meas
        self.add_node(meas.measurement_id, f"{meas.metric_name}: {meas.value_number}", "Measurement", "Evaluation", meas.model_dump())
        self.add_edge(meas.experiment_id, meas.measurement_id, "MEASURED_BY")

    def add_learning(self, learn: LearningEntity):
        self.learnings[learn.learning_id] = learn
        self.add_node(learn.learning_id, f"Learning:{learn.insight[:20]}", "Learning", "Knowledge", learn.model_dump())
        self.add_edge(learn.measurement_id, learn.learning_id, "GENERATES")

    def add_knowledge(self, kn: KnowledgeEntity):
        self.knowledge[kn.knowledge_id] = kn
        self.add_node(kn.knowledge_id, f"Knowledge:{kn.type}", "Knowledge", "Knowledge", kn.model_dump())
        if kn.source_learning_id:
            self.add_edge(kn.source_learning_id, kn.knowledge_id, "CREATES")

    # ── Traversal & Scope Subgraph Resolution ────────────────────────────────

    def get_neighbors(self, node_id: str, direction: str = "both") -> List[Tuple[str, str, float]]:
        """Returns adjacent nodes with relation and weight: [(target_id, relation, weight)]."""
        results = []
        if direction in ("out", "both"):
            for e in self.outgoing_edges.get(node_id, []):
                results.append((e["target"], e["relation"], e["weight"]))
        if direction in ("in", "both"):
            for e in self.incoming_edges.get(node_id, []):
                results.append((e["source"], f"REV_{e['relation']}", e["weight"]))
        return results

    def extract_subgraph_by_scope(self, focal_node_id: str, scope: str = "D1") -> Dict[str, Any]:
        """Extracts a bounded subgraph around focal_node_id based on scope (D0, D1, D2, D3)."""
        max_depth = 0 if scope == "D0" else (1 if scope == "D1" else (2 if scope == "D2" else 3))

        visited_nodes: Set[str] = {focal_node_id}
        frontier: Set[str] = {focal_node_id}
        collected_edges: List[Dict[str, Any]] = []

        for _ in range(max_depth):
            next_frontier: Set[str] = set()
            for current in frontier:
                for neighbor_id, rel, weight in self.get_neighbors(current, "both"):
                    collected_edges.append({"source": current, "target": neighbor_id, "relation": rel, "weight": weight})
                    if neighbor_id not in visited_nodes:
                        visited_nodes.add(neighbor_id)
                        next_frontier.add(neighbor_id)
            frontier = next_frontier

        # Assemble node representations
        subgraph_nodes = []
        for n_id in visited_nodes:
            n_data = self.nodes.get(n_id, {"id": n_id, "label": n_id, "type": "Generic", "domain": "Operational"})
            subgraph_nodes.append(n_data)

        return {
            "focal_node_id": focal_node_id,
            "scope": scope,
            "max_depth": max_depth,
            "nodes": subgraph_nodes,
            "links": collected_edges,
            "node_count": len(subgraph_nodes),
            "edge_count": len(collected_edges),
        }

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the entire in-memory graph to a dictionary."""
        all_edges = []
        seen_edges = set()
        for src, edges in self.outgoing_edges.items():
            for e in edges:
                key = (e["source"], e["target"], e.get("relation", "RELATES_TO"))
                if key not in seen_edges:
                    seen_edges.add(key)
                    all_edges.append(e)

        return {
            "nodes": list(self.nodes.values()),
            "edges": all_edges,
            "node_count": len(self.nodes),
            "edge_count": len(all_edges),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UniversalERDGraph":
        """Reconstructs a UniversalERDGraph from a serialized dictionary."""
        graph = cls()
        for node in data.get("nodes", []):
            graph.add_node(
                node_id=node.get("id"),
                label=node.get("label", node.get("name", "")),
                node_type=node.get("type", "Generic"),
                domain=node.get("domain", "Operational"),
                metadata=node.get("metadata", {})
            )
        for edge in data.get("edges", []):
            graph.add_edge(
                source_id=edge.get("source"),
                target_id=edge.get("target"),
                relation=edge.get("relation", "RELATES_TO"),
                weight=edge.get("weight", 1.0)
            )
        return graph
