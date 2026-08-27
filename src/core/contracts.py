"""Core contracts and data structures for BART Omniframez."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from .types import Domain, PerspectiveWindow, ScopeLevel, TaxRuleType, AgentStatus


class Observation(BaseModel):
    """Telemetry signal or fact observed in the environment."""
    observation_id: str
    source: str
    domain: Domain = Domain.OPERATIONAL
    window: PerspectiveWindow = PerspectiveWindow.W5_FINANCIAL_MANAGEMENT
    entity_id: str
    metric_name: str
    metric_value: Any
    confidence: float = 1.0
    timestamp: Optional[str] = None
    raw_payload: Dict[str, Any] = Field(default_factory=dict)


class Diagnosis(BaseModel):
    """Analysis of root causes, friction points, or tax misallocations."""
    diagnosis_id: str
    related_observations: List[str] = Field(default_factory=list)
    issue_category: str
    severity: str = "medium"  # low, medium, high, critical
    root_cause: str
    financial_impact_sek: float = 0.0
    description: str


class TaxOptimizationOpportunity(BaseModel):
    """Concrete tax optimization recommendation comparing applied vs best possible."""
    opportunity_id: str
    transaction_id: str
    applied_rule: TaxRuleType
    best_possible_rule: TaxRuleType
    applied_tax_sek: float
    best_possible_tax_sek: float
    net_tax_saved_sek: float
    net_profit_delta_sek: float
    legal_basis: str
    recommended_bas_account: str
    moms_box_change: str
    explanation: str


class TaxEvaluationResult(BaseModel):
    """Full evaluation of a transaction or batch of transactions."""
    total_evaluated_count: int = 0
    total_potential_savings_sek: float = 0.0
    total_profit_gain_sek: float = 0.0
    opportunities: List[TaxOptimizationOpportunity] = Field(default_factory=list)
    compliance_risks_detected: List[str] = Field(default_factory=list)


class ContextPacket(BaseModel):
    """The machine-consumable dynamic context slice passed to agents or UI views."""
    context_id: str
    role: str
    purpose: str
    task: str
    scope: ScopeLevel = ScopeLevel.D1_DIRECT
    allowed_domains: List[Domain] = Field(default_factory=list)
    perspective_window: PerspectiveWindow = PerspectiveWindow.W5_FINANCIAL_MANAGEMENT
    primary_entity: Dict[str, Any] = Field(default_factory=dict)
    related_entities: List[Dict[str, Any]] = Field(default_factory=list)
    observations: List[Observation] = Field(default_factory=list)
    recommended_next_nodes: List[Dict[str, Any]] = Field(default_factory=list)


class AgentResult(BaseModel):
    """Standard contract returned by any agent in the 12-agent system loop."""
    agent_name: str
    status: AgentStatus = AgentStatus.COMPLETED
    observations: List[Observation] = Field(default_factory=list)
    diagnoses: List[Diagnosis] = Field(default_factory=list)
    tax_opportunities: List[TaxOptimizationOpportunity] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    actions_taken: List[str] = Field(default_factory=list)
    next_questions: List[str] = Field(default_factory=list)
    metrics_summary: Dict[str, Any] = Field(default_factory=dict)
