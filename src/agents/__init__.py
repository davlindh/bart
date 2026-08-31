"""The 12 Core Team Dynamics Agents & Specialist Agents for the Omnipod Framework."""

from .base import BaseAgent
from .observer import ObserverAgent
from .diagnostician import DiagnosticianAgent
from .team_architect import TeamArchitectAgent
from .role_transition import RoleTransitionAgent
from .collaboration import CollaborationAgent
from .wellbeing import WellbeingAgent
from .ai_ethics import AIEthicsAgent
from .meta_learning import MetaLearningAgent
from .measurement import MeasurementAgent
from .learning import LearningAgent
from .orchestrator import OrchestratorAgent
from .experiment_agent import ExperimentAgent
from .tax_optimization_agent import TaxOptimizationAgent

# Complete 12 Core Agents registry in loop order
TWELVE_CORE_AGENTS = [
    ObserverAgent,       # 1. Observer
    DiagnosticianAgent,  # 2. Diagnostiker
    TeamArchitectAgent,  # 3. Team Architect
    RoleTransitionAgent, # 4. Role Transition
    CollaborationAgent,  # 5. Collaboration
    WellbeingAgent,      # 6. Wellbeing
    AIEthicsAgent,       # 7. AI Ethics
    ExperimentAgent,     # 12. Experiment Agent
    MeasurementAgent,    # 9. Measurement
    LearningAgent,       # 10. Learning
    OrchestratorAgent,   # 11. Orchestrator
    MetaLearningAgent,   # 8. Meta-Learning
]

__all__ = [
    "BaseAgent",
    "ObserverAgent",
    "DiagnosticianAgent",
    "TeamArchitectAgent",
    "RoleTransitionAgent",
    "CollaborationAgent",
    "WellbeingAgent",
    "AIEthicsAgent",
    "MetaLearningAgent",
    "MeasurementAgent",
    "LearningAgent",
    "OrchestratorAgent",
    "ExperimentAgent",
    "TaxOptimizationAgent",
    "TWELVE_CORE_AGENTS",
]
