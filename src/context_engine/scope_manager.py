"""Scope Manager controlling depth boundaries (D0..D3), breadth limits, and stop conditions."""

from typing import List, Tuple
from src.core.contracts import ScopeContract
from src.core.types import ScopeDepth


class ScopeManager:
    """Evaluates and bounds exploration scope, handling progressive expansion."""

    DEPTH_HOP_MAP = {
        ScopeDepth.D0: 0,
        ScopeDepth.D1: 1,
        ScopeDepth.D2: 2,
        ScopeDepth.D3: 3,
    }

    @classmethod
    def depth_to_hops(cls, depth: ScopeDepth) -> int:
        """Converts ScopeDepth enum to integer graph traversal hops."""
        return cls.DEPTH_HOP_MAP.get(depth, 1)

    @classmethod
    def expand_depth(cls, current_depth: ScopeDepth) -> Tuple[ScopeDepth, bool]:
        """Progressively expands depth: D0 -> D1 -> D2 -> D3."""
        progression = {
            ScopeDepth.D0: ScopeDepth.D1,
            ScopeDepth.D1: ScopeDepth.D2,
            ScopeDepth.D2: ScopeDepth.D3,
            ScopeDepth.D3: ScopeDepth.D3,
        }
        next_depth = progression.get(current_depth, current_depth)
        has_expanded = next_depth != current_depth
        return next_depth, has_expanded

    @classmethod
    def evaluate_stop_condition(
        cls,
        evidence_count: int,
        confidence_score: float,
        uncertainty_count: int,
        top_relevance: float,
    ) -> bool:
        """
        Determines whether the stop condition is fulfilled:
        1. High confidence (>= 0.85) and at least 1 verified evidence item.
        2. Zero remaining high-priority uncertainties.
        3. Top available relevance score is sufficient (>= 0.70).
        """
        if confidence_score >= 0.85 and evidence_count >= 1 and uncertainty_count == 0:
            return True
        if top_relevance < 0.30:  # Search is yielding irrelevant noise
            return True
        return False
