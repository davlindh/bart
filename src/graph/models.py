"""Universal ERD Entity Models implemented as Pydantic models."""

from datetime import datetime, timezone, date
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from src.core.types import (
    DomainType,
    ExperimentStatus,
    ImpactLevel,
    InterventionStatus,
    PermissionLevel,
    SensitivityLevel,
    TransitionStatus,
)


class Organization(BaseModel):
    """Organization entity representing the enterprise or business umbrella."""
    organization_id: str = Field(..., description="Unique organization ID")
    name: str = Field(..., description="Organization name")
    industry: str = Field(default="Technology")
    size: str = Field(default="ENTERPRISE", description="SMALL | MEDIUM | ENTERPRISE")
    region: str = Field(default="Nordics")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Team(BaseModel):
    """Team entity representing a cross-functional or operational unit."""
    team_id: str = Field(..., description="Unique team ID")
    organization_id: str = Field(..., description="Foreign key to Organization")
    name: str = Field(..., description="Team name")
    purpose: str = Field(..., description="Mission/purpose statement")
    type: str = Field(default="CROSS_FUNCTIONAL", description="CROSS_FUNCTIONAL | FUNCTIONAL | PLATFORM")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Person(BaseModel):
    """Person entity representing a team member or stakeholder."""
    person_id: str = Field(..., description="Unique person ID")
    team_id: str = Field(..., description="Foreign key to Team")
    name: str = Field(..., description="Full name")
    role_title: str = Field(..., description="Official job title")
    seniority: str = Field(default="SENIOR", description="JUNIOR | MID | SENIOR | LEAD | PRINCIPAL")
    employment_type: str = Field(default="FULL_TIME", description="FULL_TIME | CONTRACTOR | PART_TIME")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Role(BaseModel):
    """Role entity defining functional archetypes, responsibilities, and mandates."""
    role_id: str = Field(..., description="Unique role ID")
    team_id: str = Field(..., description="Foreign key to Team")
    role_name: str = Field(..., description="Functional role name")
    domain: DomainType = Field(default=DomainType.OPERATIONAL)
    purpose: str = Field(..., description="Role charter and objective")
    responsibilities: List[str] = Field(default_factory=list)
    decision_rights: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Capability(BaseModel):
    """Capability entity representing required competencies."""
    capability_id: str = Field(..., description="Unique capability ID")
    name: str = Field(..., description="Competency name")
    description: str = Field(..., description="Competency description")
    category: str = Field(default="TECHNICAL", description="TECHNICAL | DOMAIN | LEADERSHIP | PROCESS")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Assignment(BaseModel):
    """Assignment connecting a person to a role with allocation fraction."""
    assignment_id: str = Field(..., description="Unique assignment ID")
    person_id: str = Field(..., description="Foreign key to Person")
    role_id: str = Field(..., description="Foreign key to Role")
    start_date: date = Field(default_factory=date.today)
    end_date: Optional[date] = None
    allocation_pct: float = Field(default=100.0, ge=0.0, le=100.0)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Observation(BaseModel):
    """Observation entity storing raw/aggregated signals captured by Observer."""
    observation_id: str = Field(..., description="Unique observation ID")
    team_id: str = Field(..., description="Foreign key to Team")
    source_type: str = Field(..., description="JIRA | SLACK | GIT | HRIS | SURVEY | TELEMETRY")
    source_ref: str = Field(..., description="Reference log URI or tracking ticket")
    observed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    data_json: Dict[str, Any] = Field(default_factory=dict)
    created_by_agent_id: str = Field(default="Observer")


class Diagnosis(BaseModel):
    """Diagnosis entity storing analyzed hypotheses and root causes."""
    diagnosis_id: str = Field(..., description="Unique diagnosis ID")
    observation_id: str = Field(..., description="Foreign key to Observation")
    hypothesis: str = Field(..., description="Formulated hypothesis")
    root_cause: str = Field(..., description="Identified root cause")
    confidence: float = Field(default=0.85, ge=0.0, le=1.0)
    created_by_agent_id: str = Field(default="Diagnostiker")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Intervention(BaseModel):
    """Intervention entity representing proposed solutions and changes."""
    intervention_id: str = Field(..., description="Unique intervention ID")
    diagnosis_id: Optional[str] = Field(default=None, description="Foreign key to Diagnosis")
    type: str = Field(..., description="ROLE_CHANGE | PROCESS_OPTIMIZATION | TOOLING | WELLBEING_POLICY")
    description: str = Field(..., description="Intervention details")
    status: InterventionStatus = Field(default=InterventionStatus.PROPOSED)
    proposed_by_agent_id: str = Field(default="Team Architect")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class TransitionPlan(BaseModel):
    """TransitionPlan entity outlining step-by-step organizational change."""
    transition_plan_id: str = Field(..., description="Unique transition plan ID")
    intervention_id: str = Field(..., description="Foreign key to Intervention")
    from_state_json: Dict[str, Any] = Field(default_factory=dict)
    to_state_json: Dict[str, Any] = Field(default_factory=dict)
    steps_json: List[Dict[str, Any]] = Field(default_factory=list)
    timeline: str = Field(default="4 weeks")
    owner_id: str = Field(..., description="Foreign key to Person")
    status: TransitionStatus = Field(default=TransitionStatus.DRAFT)


class Communication(BaseModel):
    """Communication entity representing change messaging broadcasts."""
    communication_id: str = Field(..., description="Unique communication ID")
    transition_plan_id: str = Field(..., description="Foreign key to TransitionPlan")
    audience: str = Field(..., description="Target audience group")
    message: str = Field(..., description="Message text")
    channel: str = Field(default="SLACK", description="SLACK | EMAIL | IN_APP | TOWN_HALL")
    sent_at: Optional[datetime] = None
    created_by: str = Field(default="Role Transition Agent")


class Experiment(BaseModel):
    """Experiment entity representing a controlled validation test."""
    experiment_id: str = Field(..., description="Unique experiment ID")
    intervention_id: str = Field(..., description="Foreign key to Intervention")
    hypothesis: str = Field(..., description="Specific falsifiable hypothesis")
    design: Dict[str, Any] = Field(default_factory=dict)
    start_date: date = Field(default_factory=date.today)
    end_date: Optional[date] = None
    status: ExperimentStatus = Field(default=ExperimentStatus.SCHEDULED)


class Measurement(BaseModel):
    """Measurement entity capturing empirical outcomes."""
    measurement_id: str = Field(..., description="Unique measurement ID")
    experiment_id: str = Field(..., description="Foreign key to Experiment")
    metric_name: str = Field(..., description="Metric label")
    value_number: Optional[float] = None
    value_text: Optional[str] = None
    baseline_value: Optional[float] = None
    delta_pct: Optional[float] = None
    measured_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Learning(BaseModel):
    """Learning entity storing verified insights from experiments."""
    learning_id: str = Field(..., description="Unique learning ID")
    measurement_id: str = Field(..., description="Foreign key to Measurement")
    insight: str = Field(..., description="Extracted learning statement")
    impact: ImpactLevel = Field(default=ImpactLevel.HIGH)
    confidence: float = Field(default=0.90, ge=0.0, le=1.0)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Knowledge(BaseModel):
    """Knowledge entity codified in the long-term semantic knowledge graph."""
    knowledge_id: str = Field(..., description="Unique knowledge node ID")
    type: str = Field(default="PRINCIPLE", description="PRINCIPLE | POLICY | HEURISTIC | PLAYBOOK")
    domain: DomainType = Field(default=DomainType.KNOWLEDGE)
    content: str = Field(..., description="Knowledge content")
    tags: List[str] = Field(default_factory=list)
    source_learning_id: Optional[str] = Field(default=None, description="Foreign key to Learning")
    permission_level: PermissionLevel = Field(default=PermissionLevel.PUBLIC)
    sensitivity_level: SensitivityLevel = Field(default=SensitivityLevel.STANDARD)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
