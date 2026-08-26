"""Core protocol contracts, schema models, and data packet structures."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from src.core.types import (
    DomainType,
    ImpactLevel,
    PermissionLevel,
    ScopeDepth,
    SensitivityLevel,
    SeverityLevel,
)


class ScopeContract(BaseModel):
    """Specification of bounding constraints for context resolution."""
    depth: ScopeDepth = Field(default=ScopeDepth.D1, description="Traversal depth limit (D0..D3)")
    breadth_limit: int = Field(default=5, description="Maximum number of focal nodes returned")
    max_perspectives: int = Field(default=3, description="Maximum perspective windows allowed")
    allowed_domains: List[DomainType] = Field(
        default_factory=lambda: [DomainType.OPERATIONAL, DomainType.DATA, DomainType.TOOLS],
        description="Permitted domain boundaries",
    )
    time_horizon_days: int = Field(default=90, description="Recency boundary in days")
    permission_level: PermissionLevel = Field(default=PermissionLevel.TEAM, description="Required access clearance")
    sensitivity_ceiling: SensitivityLevel = Field(
        default=SensitivityLevel.STANDARD, description="Maximum data sensitivity allowed"
    )
    stop_on_sufficient_evidence: bool = Field(default=True, description="Halt expansion once evidence threshold met")


class EvidenceItem(BaseModel):
    """Attributable empirical fact supporting an observation or insight."""
    source_ref: str = Field(..., description="Unique source identifier, log URI, or record key")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Verification confidence score")
    fact: str = Field(..., description="Verifiable factual claim")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Record timestamp")


class RelevanceScoreItem(BaseModel):
    """Multi-dimensional relevance breakdown for a graph node."""
    node_id: str
    composite_score: float = Field(ge=0.0, le=1.0)
    dimension_scores: Dict[str, float] = Field(default_factory=dict)


class RecommendedNode(BaseModel):
    """Predictive next node for progressive exploration."""
    node_id: str
    label: str
    domain: DomainType
    relevance: float = Field(ge=0.0, le=1.0)
    rationale: Optional[str] = None


class GraphNodeSummary(BaseModel):
    """Node summary embedded inside a Context Packet."""
    id: str
    type: str
    domain: DomainType
    label: str
    relevance_score: float = Field(ge=0.0, le=1.0)
    properties: Dict[str, Any] = Field(default_factory=dict)


class GraphRelationSummary(BaseModel):
    """Relationship edge summary inside a Context Packet."""
    source: str
    target: str
    type: str
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    properties: Dict[str, Any] = Field(default_factory=dict)


class ContextPacket(BaseModel):
    """Standardized machine-linkable context packet produced by the Context Resolution Engine."""
    context_id: str = Field(..., description="Unique context packet identifier")
    target_node: str = Field(..., description="Focal graph entity ID")
    role: str = Field(..., description="Acting user/agent role persona")
    purpose: str = Field(..., description="High-level operational purpose")
    task: str = Field(..., description="Specific immediate task to execute")
    scope: ScopeContract = Field(default_factory=ScopeContract)
    nodes: List[GraphNodeSummary] = Field(default_factory=list)
    relations: List[GraphRelationSummary] = Field(default_factory=list)
    evidence: List[EvidenceItem] = Field(default_factory=list)
    assumptions: List[str] = Field(default_factory=list)
    uncertainties: List[str] = Field(default_factory=list)
    relevance_scores: Dict[str, float] = Field(default_factory=dict)
    permissions: List[str] = Field(default_factory=list)
    current_state: Dict[str, Any] = Field(default_factory=dict)
    recommended_next_nodes: List[RecommendedNode] = Field(default_factory=list)
    stop_condition_met: bool = Field(default=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class IdentifiedIssue(BaseModel):
    """Structural, behavioral, or technical issue diagnosed by agents."""
    issue_id: str
    severity: SeverityLevel
    description: str
    related_nodes: List[str] = Field(default_factory=list)


class HypothesisItem(BaseModel):
    """Falsifiable hypothesis regarding bottlenecks or causes."""
    hypothesis_id: str
    statement: str
    probability: float = Field(ge=0.0, le=1.0)
    root_cause: Optional[str] = None


class ActionItem(BaseModel):
    """Concrete operational action or task."""
    action_id: str
    type: str = Field(default="TASK")
    assignee: str
    description: str
    deadline: Optional[str] = None


class AgentResult(BaseModel):
    """Canonical standardized contract returned by every agent in the loop."""
    agent_name: str = Field(..., description="Identifier of the executing agent")
    iteration_id: str = Field(..., description="Execution loop iteration ID")
    observations: List[str] = Field(default_factory=list)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    identified_issues: List[IdentifiedIssue] = Field(default_factory=list)
    hypotheses: List[HypothesisItem] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    actions: List[ActionItem] = Field(default_factory=list)
    metrics: Dict[str, Any] = Field(default_factory=dict)
    risks: List[str] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)
    next_questions: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class DecisionOption(BaseModel):
    """Candidate option in a structured decision matrix."""
    option_id: str
    title: str
    description: str
    pros: List[str] = Field(default_factory=list)
    cons: List[str] = Field(default_factory=list)
    estimated_impact: ImpactLevel = Field(default=ImpactLevel.MEDIUM)
    confidence: float = Field(default=0.8)


class DecisionObject(BaseModel):
    """Structured decision matrix created by Decision Architect."""
    decision_id: str
    objective: str
    options: List[DecisionOption] = Field(default_factory=list)
    criteria: List[str] = Field(default_factory=list)
    tradeoffs: List[str] = Field(default_factory=list)
    risks: List[str] = Field(default_factory=list)
    recommended_option_id: Optional[str] = None
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    owner: str = Field(default="Team Lead")
    deadline: Optional[str] = None


class ExperimentPlan(BaseModel):
    """Testable hypothesis experiment blueprint."""
    experiment_id: str
    intervention_id: str
    hypothesis: str
    test_cohort: str
    control_cohort: str
    target_metric: str
    baseline_value: float
    expected_delta_pct: float
    duration_days: int = Field(default=14)
    success_criteria: List[str] = Field(default_factory=list)
    status: str = Field(default="SCHEDULED")


class LearningObject(BaseModel):
    """Extracted organizational principle or heuristic rule."""
    learning_id: str
    source_experiment_id: Optional[str] = None
    insight: str
    impact: ImpactLevel = Field(default=ImpactLevel.MEDIUM)
    confidence: float = Field(default=0.85, ge=0.0, le=1.0)
    updated_rules: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)


class AgentPerformanceModel(BaseModel):
    """Telemetry report assessing individual agent accuracy and system health."""
    agent_name: str
    evaluations_count: int = 0
    diagnostic_accuracy: float = Field(default=1.0, ge=0.0, le=1.0)
    false_positive_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    avg_confidence: float = Field(default=0.85, ge=0.0, le=1.0)
    scope_adequacy_score: float = Field(default=0.90, ge=0.0, le=1.0)
    recommended_prompt_updates: List[str] = Field(default_factory=list)
    recommended_weight_calibrations: Dict[str, float] = Field(default_factory=dict)


# ── Entity State Model (migrated from 3.7fmossmorph/entity_types.ts) ───


class VerificationLevel(str, Enum):
    """Trust verification levels for platform entities."""
    UNVERIFIED = "unverified"
    BASIC = "basic"
    VERIFIED = "verified"
    TRUSTED = "trusted"
    EXPERT = "expert"


class ExchangeStatus(str, Enum):
    """Status of an entity's exchange capabilities."""
    ACTIVE = "active"
    RESTRICTED = "restricted"
    SUSPENDED = "suspended"


class EntityVisibility(str, Enum):
    """Visibility scope for entity interactions."""
    PUBLIC = "public"
    LIMITED = "limited"
    PRIVATE = "private"


class LifecycleStage(str, Enum):
    """Temporal lifecycle stage for events."""
    ACTIVE = "active"
    DECAYING = "decaying"
    ARCHIVED = "archived"


class TrustState(BaseModel):
    """Trust-related state for a platform entity."""
    score: float = Field(default=50.0, ge=0.0, le=100.0, description="Trust score 0-100")
    verification_level: VerificationLevel = Field(default=VerificationLevel.BASIC)
    factors: Dict[str, Any] = Field(default_factory=dict, description="Trust factor breakdown")
    last_verified: Optional[datetime] = None


class ValueState(BaseModel):
    """Value contribution state for a platform entity."""
    intensity: float = Field(default=1.0, ge=0.0, description="Contribution intensity")
    confidence: float = Field(default=50.0, ge=0.0, le=100.0, description="Value confidence %")
    aggregate_weight: float = Field(default=1.0, description="Computed aggregate weight")
    context_weight: float = Field(default=1.0, description="Contextual multiplier")
    primary_context: Optional[str] = None
    secondary_contexts: List[str] = Field(default_factory=list)
    weight_last_computed: Optional[datetime] = None


class ExchangeState(BaseModel):
    """Exchange/transaction state for a platform entity."""
    status: ExchangeStatus = Field(default=ExchangeStatus.ACTIVE)
    contribution_count: int = Field(default=0, ge=0)
    receive_count: int = Field(default=0, ge=0)
    balance: float = Field(default=0.0)
    last_exchange: Optional[datetime] = None
    restriction_reason: Optional[str] = None
    promoted: bool = False


class InteractionState(BaseModel):
    """Interaction visibility and discovery state."""
    visibility: EntityVisibility = Field(default=EntityVisibility.PUBLIC)
    discovery_factor: float = Field(default=1.0, ge=0.0, description="Amplification factor for search/discovery")
    interaction_count: int = Field(default=0, ge=0)
    last_interaction: Optional[datetime] = None


class TemporalEvent(BaseModel):
    """A time-weighted event attached to an entity."""
    event_type: str
    event_data: Dict[str, Any] = Field(default_factory=dict)
    temporal_weight: float = Field(default=1.0, ge=0.0)
    lifecycle_stage: LifecycleStage = Field(default=LifecycleStage.ACTIVE)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class UserEntityState(BaseModel):
    """Composite entity state model capturing Trust, Value, Exchange, Interaction, and Temporal dimensions.

    Migrated from 3.7fmossmorph entity_types.ts EntityState.
    Complements the team-dynamics ERD models (Organization, Team, Person, etc.)
    by capturing the platform-level interaction state of any entity.
    """
    entity_id: str
    entity_type: str = Field(default="user", description="user | project | organization | resource")
    display_name: str = ""
    trust: TrustState = Field(default_factory=TrustState)
    value: ValueState = Field(default_factory=ValueState)
    exchange: ExchangeState = Field(default_factory=ExchangeState)
    interaction: InteractionState = Field(default_factory=InteractionState)
    temporal_events: List[TemporalEvent] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def apply_trust_cascades(self):
        """Apply trust-score-driven cascading state changes.

        Ported from 3.7fmossmorph DualPathProcessor.applyLocalStateChanges():
        - Low trust (<20): Restrict exchange, limit visibility, halve value weight
        - High trust (>50): Activate exchange, public visibility, boost value weight
        """
        if self.trust.score < 20:
            self.exchange.status = ExchangeStatus.RESTRICTED
            self.exchange.restriction_reason = "low_trust"
            self.interaction.visibility = EntityVisibility.LIMITED
            self.value.aggregate_weight *= 0.5
        elif self.trust.score > 50:
            self.exchange.status = ExchangeStatus.ACTIVE
            self.exchange.promoted = True
            self.interaction.visibility = EntityVisibility.PUBLIC
            self.value.aggregate_weight *= 1.2
        self.value.weight_last_computed = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)

    def recalculate_value_weight(self):
        """Recalculate aggregate weight from intensity, confidence, and context weight.

        Ported from 3.7fmossmorph DualPathProcessor value-change handler.
        """
        self.value.aggregate_weight = (
            (self.value.intensity * self.value.confidence / 100.0) * self.value.context_weight
        )
        # Update discovery factor based on weight
        if self.value.aggregate_weight > 5.0:
            self.interaction.discovery_factor = 1.5
        elif self.value.aggregate_weight > 2.0:
            self.interaction.discovery_factor = 1.2
        elif self.value.aggregate_weight < 0.5:
            self.interaction.discovery_factor = 0.7
        self.value.weight_last_computed = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)

