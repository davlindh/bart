"""Core data contracts for Intentional Contextual Pre-Cognition and Self-Preservation."""

from typing import Any, Dict, List, Optional
from enum import Enum
from pydantic import BaseModel, Field
from .types import Domain, PerspectiveWindow, ScopeLevel
from .contracts import ContextPacket, Observation


class IntentStatus(str, Enum):
    """Lifecycle status of a project intent."""
    DECLARED = "declared"
    ACTIVE = "active"
    CONVERGING = "converging"
    ACHIEVED = "achieved"
    BLOCKED = "blocked"


class RiskSeverity(str, Enum):
    """Severity of anticipated friction or anomalies."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ProjectIntent(BaseModel):
    """Explicit intentional mandate defining desired state, boundaries, and goals."""
    intent_id: str
    project_id: str
    mandate: str
    desired_state: Dict[str, Any] = Field(default_factory=dict)
    current_state_summary: Optional[str] = None
    target_kpis: Dict[str, float] = Field(default_factory=dict)
    allowed_domains: List[Domain] = Field(default_factory=lambda: [Domain.OPERATIONAL, Domain.EXCHANGE, Domain.TRUST])
    horizon_steps: int = 3
    status: IntentStatus = IntentStatus.DECLARED
    constraints: List[str] = Field(default_factory=list)


class TrajectoryNode(BaseModel):
    """Anticipated future state or action node in the cognitive trajectory."""
    step_offset: int  # +1, +2, +3
    node_id: str
    title: str
    domain: Domain
    perspective_window: PerspectiveWindow
    transition_probability: float  # P(N_{t+k} | N_t, Intent) [0.0 - 1.0]
    expected_transformation: str
    driving_factors: List[str] = Field(default_factory=list)


class PredictedSkillNeed(BaseModel):
    """Proactive prediction of an Antigravity skill or tool required in the future."""
    skill_name: str
    trigger_condition: str
    confidence: float = 1.0
    lead_time_steps: int = 1
    reasoning: str
    tool_suggestions: List[str] = Field(default_factory=list)
    prefetched_context: Optional[ContextPacket] = None


class AnticipatedFriction(BaseModel):
    """Pre-cognitive detection of potential operational, ethical, or financial friction."""
    friction_id: str
    domain: Domain
    severity: RiskSeverity
    lead_time_steps: int = 1
    predicted_issue: str
    root_factor: str
    preventive_action: str
    confidence: float = 0.85


class PreCognitionTrajectory(BaseModel):
    """Complete multi-step trajectory projection with skill needs and friction shielding."""
    trajectory_id: str
    project_intent: ProjectIntent
    current_point_id: str
    horizon_steps: int = 3
    predicted_nodes: List[TrajectoryNode] = Field(default_factory=list)
    predicted_skills: List[PredictedSkillNeed] = Field(default_factory=list)
    anticipated_frictions: List[AnticipatedFriction] = Field(default_factory=list)
    prefetched_context_packets: List[ContextPacket] = Field(default_factory=list)
    recommended_proactive_actions: List[str] = Field(default_factory=list)
    confidence_score: float = 0.90


class ProjectCheckpoint(BaseModel):
    """Durable state snapshot for self-preservation across process boundaries."""
    checkpoint_id: str
    project_id: str
    timestamp: str
    intent: Optional[ProjectIntent] = None
    node_count: int = 0
    edge_count: int = 0
    variable_count: int = 0
    agent_states: Dict[str, Any] = Field(default_factory=dict)
    erd_snapshot: Dict[str, Any] = Field(default_factory=dict)
    trajectory_snapshot: Optional[PreCognitionTrajectory] = None
    checksum_sha256: str = ""
    has_trajectory: bool = False
    trigger_source: str = "manual"
