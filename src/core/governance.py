"""Governance, Ethical AI guardrails, Privacy masking, and Audit Logging."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from src.core.types import PermissionLevel, SensitivityLevel


class GovernancePolicy(BaseModel):
    """Enforceable governance, compliance, and ethical safeguard policy."""
    policy_id: str
    name: str
    description: str
    min_permission_level: PermissionLevel = Field(default=PermissionLevel.TEAM)
    max_sensitivity_allowed: SensitivityLevel = Field(default=SensitivityLevel.STANDARD)
    require_human_in_the_loop: bool = Field(default=False)
    audit_required: bool = Field(default=True)
    disparate_impact_threshold: float = Field(default=0.80)


class AuditLogEntry(BaseModel):
    """Immutable audit trail entry recording agent decisions and context accesses."""
    log_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    actor_id: str
    action_type: str
    target_node: str
    scope_depth: str
    governance_approved: bool
    rationale: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class GovernanceEngine:
    """Validates actions, checks permissions, filters sensitive fields, and logs audit events."""

    def __init__(self):
        self._audit_logs: List[AuditLogEntry] = []

    def validate_access(
        self,
        actor_role: str,
        node_permission: PermissionLevel,
        node_sensitivity: SensitivityLevel,
        scope_permission: PermissionLevel,
        scope_sensitivity: SensitivityLevel,
    ) -> bool:
        """Determines if the actor and scope constraints permit accessing the target node."""
        perm_hierarchy = {
            PermissionLevel.PUBLIC: 0,
            PermissionLevel.TEAM: 1,
            PermissionLevel.CONFIDENTIAL: 2,
            PermissionLevel.RESTRICTED: 3,
        }
        sens_hierarchy = {
            SensitivityLevel.STANDARD: 0,
            SensitivityLevel.SENSITIVE: 1,
            SensitivityLevel.HIGHLY_SENSITIVE: 2,
        }

        # Check if the requested node's required permission exceeds what the scope allows
        if perm_hierarchy[node_permission] > perm_hierarchy[scope_permission]:
            return False

        # Check if the requested node's sensitivity exceeds the scope ceiling
        if sens_hierarchy[node_sensitivity] > sens_hierarchy[scope_sensitivity]:
            return False

        return True

    def sanitize_payload(self, data: Dict[str, Any], max_sensitivity: SensitivityLevel) -> Dict[str, Any]:
        """Redacts or masks fields flagged above the maximum allowed sensitivity."""
        sanitized = dict(data)
        if max_sensitivity == SensitivityLevel.STANDARD:
            # Mask PII and restricted identifiers if present
            for sensitive_key in ["ssn", "salary", "personal_email", "auth_token", "private_key"]:
                if sensitive_key in sanitized:
                    sanitized[sensitive_key] = "[REDACTED_BY_GOVERNANCE]"
        return sanitized

    def log_event(
        self,
        actor_id: str,
        action_type: str,
        target_node: str,
        scope_depth: str,
        governance_approved: bool,
        rationale: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AuditLogEntry:
        """Appends an entry to the immutable audit log."""
        entry = AuditLogEntry(
            log_id=f"audit_{len(self._audit_logs) + 1}_{int(datetime.now(timezone.utc).timestamp())}",
            actor_id=actor_id,
            action_type=action_type,
            target_node=target_node,
            scope_depth=scope_depth,
            governance_approved=governance_approved,
            rationale=rationale,
            metadata=metadata or {},
        )
        self._audit_logs.append(entry)
        return entry

    def get_audit_logs(self) -> List[AuditLogEntry]:
        """Returns all recorded audit logs."""
        return list(self._audit_logs)


# ── Modification Proposal System (MPS) ──────────────────────────────────
# Migrated from 3.7fmossmorph/meta-framework/meta_manager.py
# Provides a formal proposal → approval → execution lifecycle for
# governed changes to the agent loop, knowledge graph, or system config.


class ProposalStatus(str, Enum):
    """Lifecycle status of a Modification Proposal."""
    DRAFT = "DRAFT"
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    IMPLEMENTED = "IMPLEMENTED"
    ROLLED_BACK = "ROLLED_BACK"


class ProposalImpact(str, Enum):
    """Expected impact level of a proposal."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AgentApproval(BaseModel):
    """An individual agent's approval or rejection of a proposal."""
    agent_name: str
    status: ProposalStatus = Field(default=ProposalStatus.PENDING)
    comments: str = ""
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ProposalComment(BaseModel):
    """A discussion comment on a proposal."""
    author: str
    content: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ModificationProposal(BaseModel):
    """A governed change request for the agent loop, graph, or system configuration.

    Follows the MPS lifecycle: DRAFT → PENDING → APPROVED/REJECTED → IMPLEMENTED → (ROLLED_BACK)
    """
    proposal_id: str
    title: str
    summary: str
    author: str
    status: ProposalStatus = Field(default=ProposalStatus.DRAFT)
    impact: ProposalImpact = Field(default=ProposalImpact.MEDIUM)
    affected_components: List[str] = Field(default_factory=list, description="NavIDs or component names affected")
    agent_approvals: List[AgentApproval] = Field(default_factory=list)
    comments: List[ProposalComment] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status_history: List[Dict[str, Any]] = Field(default_factory=list, description="Immutable status transition log")


class ModificationProposalSystem:
    """Manages the lifecycle of Modification Proposals (MPS).

    Ported from 3.7fmossmorph meta_manager.py proposal management.
    Supports creation, agent approval/rejection, status transitions,
    commenting, and immutable history tracking.
    """

    def __init__(self):
        self._proposals: Dict[str, ModificationProposal] = {}
        self._id_counter: int = 0

    def create_proposal(
        self,
        title: str,
        summary: str,
        author: str,
        impact: ProposalImpact = ProposalImpact.MEDIUM,
        affected_components: Optional[List[str]] = None,
    ) -> ModificationProposal:
        """Create a new modification proposal in DRAFT status."""
        self._id_counter += 1
        proposal_id = f"MPS-{self._id_counter:04d}"
        proposal = ModificationProposal(
            proposal_id=proposal_id,
            title=title,
            summary=summary,
            author=author,
            impact=impact,
            affected_components=affected_components or [],
        )
        proposal.status_history.append({
            "from": None,
            "to": ProposalStatus.DRAFT,
            "timestamp": proposal.created_at.isoformat(),
            "actor": author,
        })
        self._proposals[proposal_id] = proposal
        return proposal

    def submit_for_review(self, proposal_id: str) -> ModificationProposal:
        """Transition a DRAFT proposal to PENDING review."""
        proposal = self._get_proposal(proposal_id)
        if proposal.status != ProposalStatus.DRAFT:
            raise ValueError(f"Cannot submit: proposal {proposal_id} is in {proposal.status} status")
        return self._transition(proposal, ProposalStatus.PENDING, "system")

    def add_agent_approval(
        self,
        proposal_id: str,
        agent_name: str,
        approved: bool,
        comments: str = "",
    ) -> ModificationProposal:
        """Record an individual agent's approval or rejection."""
        proposal = self._get_proposal(proposal_id)
        if proposal.status != ProposalStatus.PENDING:
            raise ValueError(f"Cannot approve: proposal {proposal_id} is in {proposal.status} status")

        approval = AgentApproval(
            agent_name=agent_name,
            status=ProposalStatus.APPROVED if approved else ProposalStatus.REJECTED,
            comments=comments,
        )
        proposal.agent_approvals.append(approval)
        proposal.updated_at = datetime.now(timezone.utc)
        return proposal

    def finalize_review(self, proposal_id: str, required_approvals: int = 1) -> ModificationProposal:
        """Check approvals and transition to APPROVED or REJECTED."""
        proposal = self._get_proposal(proposal_id)
        if proposal.status != ProposalStatus.PENDING:
            raise ValueError(f"Cannot finalize: proposal {proposal_id} is in {proposal.status} status")

        approved_count = sum(1 for a in proposal.agent_approvals if a.status == ProposalStatus.APPROVED)
        rejected_count = sum(1 for a in proposal.agent_approvals if a.status == ProposalStatus.REJECTED)

        if approved_count >= required_approvals and rejected_count == 0:
            return self._transition(proposal, ProposalStatus.APPROVED, "system")
        elif rejected_count > 0:
            return self._transition(proposal, ProposalStatus.REJECTED, "system")
        else:
            # Not enough approvals yet; stay PENDING
            return proposal

    def mark_implemented(self, proposal_id: str) -> ModificationProposal:
        """Mark an approved proposal as implemented."""
        proposal = self._get_proposal(proposal_id)
        if proposal.status != ProposalStatus.APPROVED:
            raise ValueError(f"Cannot implement: proposal {proposal_id} is in {proposal.status} status")
        return self._transition(proposal, ProposalStatus.IMPLEMENTED, "system")

    def rollback(self, proposal_id: str, reason: str = "") -> ModificationProposal:
        """Roll back an implemented proposal."""
        proposal = self._get_proposal(proposal_id)
        if proposal.status != ProposalStatus.IMPLEMENTED:
            raise ValueError(f"Cannot rollback: proposal {proposal_id} is in {proposal.status} status")
        proposal.comments.append(ProposalComment(author="system", content=f"ROLLBACK: {reason}"))
        return self._transition(proposal, ProposalStatus.ROLLED_BACK, "system")

    def add_comment(self, proposal_id: str, author: str, content: str) -> ModificationProposal:
        """Add a discussion comment to a proposal."""
        proposal = self._get_proposal(proposal_id)
        proposal.comments.append(ProposalComment(author=author, content=content))
        proposal.updated_at = datetime.now(timezone.utc)
        return proposal

    def list_proposals(self, status: Optional[ProposalStatus] = None) -> List[ModificationProposal]:
        """List all proposals, optionally filtered by status."""
        proposals = list(self._proposals.values())
        if status:
            proposals = [p for p in proposals if p.status == status]
        return proposals

    def get_proposal(self, proposal_id: str) -> Optional[ModificationProposal]:
        """Retrieve a proposal by ID."""
        return self._proposals.get(proposal_id)

    def _get_proposal(self, proposal_id: str) -> ModificationProposal:
        proposal = self._proposals.get(proposal_id)
        if not proposal:
            raise KeyError(f"Proposal not found: {proposal_id}")
        return proposal

    def _transition(self, proposal: ModificationProposal, new_status: ProposalStatus, actor: str) -> ModificationProposal:
        """Apply an immutable status transition."""
        old_status = proposal.status
        proposal.status_history.append({
            "from": old_status,
            "to": new_status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "actor": actor,
        })
        proposal.status = new_status
        proposal.updated_at = datetime.now(timezone.utc)
        return proposal

