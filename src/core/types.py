"""Core enumerations and typing primitives for the Omnipod & Team Dynamics Framework."""

from enum import Enum


class DomainType(str, Enum):
    """The 6 fundamental functional domains plus cross-cutting data domain."""
    TRUST = "Trust"
    KNOWLEDGE = "Knowledge"
    TOOLS = "Tools"
    EXCHANGE = "Exchange"
    INTERACTIONAL_INTERFACE = "Interactional Interface"
    OPERATIONAL = "Operational"
    DATA = "Data"


class PerspectiveWindow(str, Enum):
    """The 9 Omnipod Core perspective windows."""
    CONTEXTUALIZATION = "Kontextualisering"
    MATCHING = "Matchning"
    EVALUATION = "Utvärdering"
    RESOURCE_ALLOCATION = "Resursallokering"
    FINANCIAL_MANAGEMENT = "Finansiell hantering"
    PERSONNEL_MANAGEMENT = "Personalhantering"
    COMMUNICATION_PRESENTATION = "Kommunikation & Visning"
    INNOVATION_TECHNOLOGY = "Innovation & Teknologi"
    ADAPTIVE_INSIGHTS = "Adaptiva Insikter"


class ScopeDepth(str, Enum):
    """Scope depth boundaries."""
    D0 = "D0"  # Focal node only
    D1 = "D1"  # 1-hop direct neighbors
    D2 = "D2"  # 2-hop extended neighborhood
    D3 = "D3"  # Cross-domain systemic topology


class AgentBehavior(str, Enum):
    """Agent operational execution behavior mode."""
    AUTONOMOUS = "AUTONOMOUS"
    INTERACTIVE = "INTERACTIVE"


class SeverityLevel(str, Enum):
    """Issue and risk severity levels."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class InterventionStatus(str, Enum):
    """Lifecycle status of organizational interventions."""
    PROPOSED = "PROPOSED"
    APPROVED = "APPROVED"
    IN_EXPERIMENT = "IN_EXPERIMENT"
    DEPLOYED = "DEPLOYED"
    REJECTED = "REJECTED"


class ExperimentStatus(str, Enum):
    """Lifecycle status of controlled experiments."""
    SCHEDULED = "SCHEDULED"
    RUNNING = "RUNNING"
    CONCLUDED = "CONCLUDED"
    ABORTED = "ABORTED"


class TransitionStatus(str, Enum):
    """Status of role and team transition roadmaps."""
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"


class ImpactLevel(str, Enum):
    """Impact magnitude classifications."""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class PermissionLevel(str, Enum):
    """Access authorization levels."""
    PUBLIC = "Public"
    TEAM = "Team"
    CONFIDENTIAL = "Confidential"
    RESTRICTED = "Restricted"


class SensitivityLevel(str, Enum):
    """Data sensitivity classifications."""
    STANDARD = "Standard"
    SENSITIVE = "Sensitive"
    HIGHLY_SENSITIVE = "Highly Sensitive"


class PresentationTier(str, Enum):
    """Multi-level presentation output tiers."""
    HUMAN_L1_SUMMARY = "HUMAN_L1_SUMMARY"
    HUMAN_L2_DETAIL = "HUMAN_L2_DETAIL"
    MACHINE_JSON = "MACHINE_JSON"
    NAVIGATION_NEXT_NODES = "NAVIGATION_NEXT_NODES"
