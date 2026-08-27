"""Core enums and foundational types for BART Omniframez & Tax Systems."""

from enum import Enum


class Domain(str, Enum):
    """The 6 Functional Domains of the Omnipod Architecture."""
    TRUST = "Trust"
    KNOWLEDGE = "Knowledge"
    TOOLS = "Tools"
    EXCHANGE = "Exchange"
    INTERACTIONAL = "Interactional Interface"
    OPERATIONAL = "Operational"


class PerspectiveWindow(str, Enum):
    """The 9 Omnipod Perspective Windows."""
    W1_CONTEXTUALIZATION = "Contextualization"
    W2_MATCHING = "Matching"
    W3_EVALUATION = "Evaluation"
    W4_RESOURCE_ALLOCATION = "Resource Allocation"
    W5_FINANCIAL_MANAGEMENT = "Financial Management"
    W6_PERSONNEL_MANAGEMENT = "Personnel Management"
    W7_COMMUNICATION = "Communication & Display"
    W8_INNOVATION_TECH = "Innovation & Technology"
    W9_ADAPTIVE_INSIGHTS = "Adaptive Insights"


class ScopeLevel(str, Enum):
    """Dynamic Context Scope bounding levels (D0..D3)."""
    D0_IMMEDIATE = "D0"     # Immediate target entity only
    D1_DIRECT = "D1"        # 1-hop direct neighbors and contracts
    D2_SYSTEMIC = "D2"      # 2-hop subsystem context, financial ledger & policies
    D3_EXPANDED = "D3"      # 3-hop macro organization, external tax codes & audits


class TaxRuleType(str, Enum):
    """Swedish Tax Rules and Special Regimes."""
    STANDARD_MOMS_25 = "MOMS_25"
    REDUCED_MOMS_12 = "MOMS_12"
    REDUCED_MOMS_6 = "MOMS_6"
    VMB_MARGIN_TAX = "VMB_MARGIN_TAX_ML9A"
    RUT_DEDUCTION = "RUT_ARBETSKOSTNAD_50"
    REVERSE_CHARGE_CONSTRUCTION = "OMVAND_BYGGMOMS_ML1_2"
    DIRECT_WRITE_OFF_MINOR_ASSET = "DIREKTAVSKRIVNING_PBB_HALF"
    PERIODISERINGSFOND = "PERIODISERINGSFOND_25"
    TAX_EXEMPT = "TAX_EXEMPT"


class AgentStatus(str, Enum):
    """Status lifecycle of an agent execution."""
    PENDING = "pending"
    OBSERVING = "observing"
    ANALYZING = "analyzing"
    IDENTIFIED = "identified"
    PROPOSED = "proposed"
    ACTED = "acted"
    EVALUATED = "evaluated"
    COMPLETED = "completed"
    FAILED = "failed"
