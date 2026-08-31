"""Universal ERD Data Models: Pydantic schemas for the 15 Universal Entities in the Team Dynamics & Omnipod Framework.
Reference: 'Självförbättrande teamoptimering i ERD-loop.png'
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class OrganizationEntity(BaseModel):
    """Top-level organizational entity."""
    organization_id: str
    name: str
    industry: str
    size: str  # e.g., '10-50', 'SMB'
    region: str = "Sverige"
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class TeamEntity(BaseModel):
    """Functional team or organizational group."""
    team_id: str
    organization_id: str
    name: str
    purpose: str
    type: str  # e.g., 'Core', 'Operational', 'Engineering', 'Sales'
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class PersonEntity(BaseModel):
    """Individual team member, collaborator, or leader."""
    person_id: str
    team_id: str
    name: str
    role_title: str
    seniority: str = "Mid"  # Junior, Mid, Senior, Lead
    employment_type: str = "Full-time"  # Full-time, Part-time, Consultant
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class RoleEntity(BaseModel):
    """Defined organizational role with mandates and decision rights."""
    role_id: str
    team_id: str
    role_name: str
    purpose: str
    responsibilities: List[str] = Field(default_factory=list)
    decision_rights: List[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class CapabilityEntity(BaseModel):
    """Competence, skill, or credential required by roles."""
    capability_id: str
    name: str
    description: str
    category: str  # 'Technical', 'Financial', 'Domain', 'Leadership'
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class AssignmentEntity(BaseModel):
    """Fulfillment relationship between a Person and a Role."""
    assignment_id: str
    person_id: str
    role_id: str
    start_date: str = Field(default_factory=lambda: datetime.utcnow().strftime("%Y-%m-%d"))
    end_date: Optional[str] = None
    allocation_pct: float = 100.0
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class ObservationEntity(BaseModel):
    """Empirical signal collected by Observer agent from logs, Fortnox, or POS."""
    observation_id: str
    team_id: str
    source_type: str  # 'FORTNOX', 'TIMESHEET', 'POS', 'USER_FEEDBACK'
    source_ref: str
    observed_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    data_json: Dict[str, Any] = Field(default_factory=dict)
    created_by_agent_id: str = "ObserverAgent"


class DiagnosisEntity(BaseModel):
    """Diagnostic hypothesis produced by Diagnostician agent."""
    diagnosis_id: str
    observation_id: str
    hypothesis: str
    root_cause: str
    confidence: float = 0.85
    created_by_agent_id: str = "DiagnosticianAgent"
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class InterventionEntity(BaseModel):
    """Actionable intervention designed to resolve a diagnosis."""
    intervention_id: str
    type: str  # 'ROLE_CHANGE', 'COLLABORATION', 'WELLBEING', 'TAX_OPTIMIZATION'
    description: str
    status: str = "PROPOSED"  # PROPOSED, APPROVED, IN_PROGRESS, COMPLETED
    proposed_by_agent_id: str
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class TransitionPlanEntity(BaseModel):
    """Roadmap detailing how a role or process change is enacted."""
    transition_plan_id: str
    intervention_id: str
    from_state_json: Dict[str, Any] = Field(default_factory=dict)
    to_state_json: Dict[str, Any] = Field(default_factory=dict)
    steps_json: List[Dict[str, Any]] = Field(default_factory=list)
    timeline: str = "2 weeks"
    owner_id: str
    status: str = "DRAFT"  # DRAFT, ACTIVE, COMPLETED


class CommunicationEntity(BaseModel):
    """Alignment communication broadcast to team or stakeholders."""
    communication_id: str
    transition_plan_id: str
    audience: str
    message: str
    channel: str = "SLACK"  # SLACK, EMAIL, HUD_NOTIFICATION
    sent_at: Optional[str] = None
    created_by: str


class ExperimentEntity(BaseModel):
    """Controlled organizational test designed by Experiment Agent."""
    experiment_id: str
    intervention_id: str
    hypothesis: str
    design: str
    start_date: str = Field(default_factory=lambda: datetime.utcnow().strftime("%Y-%m-%d"))
    end_date: Optional[str] = None
    status: str = "RUNNING"  # DRAFT, RUNNING, MEASURED, COMPLETED


class MeasurementEntity(BaseModel):
    """Empirical metric captured during or after an experiment."""
    measurement_id: str
    experiment_id: str
    metric_name: str
    value_number: float
    value_text: str = ""
    measured_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class LearningEntity(BaseModel):
    """Durable insight extracted by Learning Agent from measurements."""
    learning_id: str
    measurement_id: str
    insight: str
    impact: str
    confidence: float = 0.90
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class KnowledgeEntity(BaseModel):
    """System-level rule, heuristic, or capability added to the organizational knowledge base."""
    knowledge_id: str
    type: str  # 'HEURISTIC', 'TAX_RULE', 'WORKFLOW_POLICY', 'ROLE_GUIDE'
    content: str
    tags: List[str] = Field(default_factory=list)
    source_learning_id: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
