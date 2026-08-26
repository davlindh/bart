"""Dynamic Context Resolution Engine package initialization."""

from src.context_engine.presentation import PresentationFormatter
from src.context_engine.resolver import ContextResolutionEngine
from src.context_engine.scope_manager import ScopeManager
from src.context_engine.weighting import RelevanceWeighter, RelevanceWeightMatrix

__all__ = [
    "ContextResolutionEngine",
    "ScopeManager",
    "RelevanceWeighter",
    "RelevanceWeightMatrix",
    "PresentationFormatter",
]
