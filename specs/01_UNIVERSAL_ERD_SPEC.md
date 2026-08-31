# Universal ERD & Relational Knowledge Graph Specification
**Reference Diagram**: `Team Dynamics Optimizer_ Adaptivt agentsystem för team.png` & `Självförbättrande teamoptimering i ERD-loop.png`

---

## 1. Universal ERD Entity Schemas & Cardinalities

The Universal ERD represents the ground-truth relational foundation of the system. All organizations, teams, signals, diagnoses, experiments, and learnings are structured according to these 15 entities:

### 1.1 Organization & People Structure
- **Organization** (`organization_id`, `name`, `industry`, `size`, `region`, `created_at`): Top-level organizational unit.
  - Cardinality: `1` Organization `HAS` `N` Teams.
- **Team** (`team_id`, `organization_id`, `name`, `purpose`, `type`, `created_at`): Functional group.
  - Cardinality: `1` Team `INCLUDES` `N` Persons.
  - Cardinality: `1` Team `GENERATES` `N` Observations.
- **Person** (`person_id`, `team_id`, `name`, `role_title`, `seniority`, `employment_type`, `created_at`): Individual employee or collaborator.
  - Cardinality: `N` Persons `ASSIGNED_TO` `N` Roles (via Assignment).
- **Role** (`role_id`, `team_id`, `role_name`, `purpose`, `responsibilities`, `decision_rights`, `created_at`): Defined mandate and authority.
  - Cardinality: `1..N` Roles `REQUIRES` `N` Capabilities.
- **Capability** (`capability_id`, `name`, `description`, `category`, `created_at`): Skill, competence, or certification.
- **Assignment** (`assignment_id`, `person_id`, `role_id`, `start_date`, `end_date`, `allocation_pct`, `created_at`): Active role fulfillment linking Person to Role.

### 1.2 Observation & Diagnostic Pipeline
- **Observation** (`observation_id`, `team_id`, `source_type`, `source_ref`, `observed_at`, `data_json`, `created_by_agent_id`): Raw telemetry signal collected by Observer agent.
  - Cardinality: `1` Observation `GENERATES` `N` Diagnoses.
- **Diagnosis** (`diagnosis_id`, `observation_id`, `hypothesis`, `root_cause`, `confidence`, `created_by_agent_id`, `created_at`): Root-cause analysis by Diagnostician agent.
  - Cardinality: `1` Diagnosis `LEADS_TO` `N` Interventions.

### 1.3 Intervention, Experiment & Change Planning
- **Intervention** (`intervention_id`, `type`, `description`, `status`, `proposed_by_agent_id`, `created_at`): Action proposed by Team Architect, Role Transition, Collaboration, or Wellbeing agent.
  - Cardinality: `1` Intervention `DESIGNED_AS` `N` Experiments.
  - Cardinality: `1` Intervention `PLAN` `N` TransitionPlans.
- **TransitionPlan** (`transition_plan_id`, `intervention_id`, `from_state_json`, `to_state_json`, `steps_json`, `timeline`, `owner_id`, `status`): Role change and migration roadmap.
  - Cardinality: `1` TransitionPlan `INCLUDES` `N` Communications.
- **Communication** (`communication_id`, `transition_plan_id`, `audience`, `message`, `channel`, `sent_at`, `created_by`): Change announcement and alignment messaging.
- **Experiment** (`experiment_id`, `intervention_id`, `hypothesis`, `design`, `start_date`, `end_date`, `status`): Controlled test designed by Experiment Agent.
  - Cardinality: `1` Experiment `MEASURED_BY` `N` Measurements.

### 1.4 Measurement, Learning & Knowledge Synthesis
- **Measurement** (`measurement_id`, `experiment_id`, `metric_name`, `value_number`, `value_text`, `measured_at`): Metric gathered by Measurement Agent.
  - Cardinality: `1` Measurement `GENERATES` `N` Learnings.
- **Learning** (`learning_id`, `measurement_id`, `insight`, `impact`, `confidence`, `created_at`): Systematic deduction extracted by Learning Agent.
  - Cardinality: `N` Learnings `CREATES` `1` Knowledge.
- **Knowledge** (`knowledge_id`, `type`, `content`, `tags`, `source_learning_id`, `created_at`): Durable rule or heuristic added to the Knowledge base.

---

## 2. Declarations of Future Integration Points

- #TODO [Persistent Vector Index for Knowledge Entities](file:///c:/Users/info/OneDrive/Dokument/GitHub/bart/src/graph/universal_erd.py#L120): Connect in-memory knowledge graph to vector database (e.g. pgvector or Qdrant) for semantic similarity querying across historical experiments.
- #TODO [Decentralized Audit Trail for Knowledge Updates](file:///c:/Users/info/OneDrive/Dokument/GitHub/bart/src/graph/universal_erd.py#L210): Implement cryptographic hashing of Knowledge node mutations for immutable organizational compliance.
