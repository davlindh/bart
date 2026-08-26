"""Context MCP Server exposing tools for Dynamic Context Resolution and Multi-tier views."""

from typing import Any, Dict, List, Optional
from src.context_engine.presentation import PresentationFormatter
from src.context_engine.resolver import ContextResolutionEngine
from src.context_engine.scope_manager import ScopeManager
from src.core.contracts import ContextPacket, ScopeContract
from src.core.types import DomainType, PresentationTier, ScopeDepth


class ContextMcpServer:
    """MCP Server providing tool handlers for Dynamic Context Engine."""

    def __init__(self, context_engine: ContextResolutionEngine):
        self.context_engine = context_engine
        self._cached_packets: Dict[str, ContextPacket] = {}

    def resolve_context(
        self,
        role: str,
        purpose: str,
        task: str,
        current_point: str,
        depth: str = "D1",
        breadth_limit: int = 5,
        allowed_domains: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Resolves task-specific subgraph and returns a strongly-typed ContextPacket dictionary."""
        domains = [DomainType(d) for d in allowed_domains] if allowed_domains else None
        scope = ScopeContract(
            depth=ScopeDepth(depth),
            breadth_limit=breadth_limit,
            allowed_domains=domains or [DomainType.OPERATIONAL, DomainType.DATA, DomainType.TOOLS],
        )
        packet = self.context_engine.resolve_context(
            role=role,
            purpose=purpose,
            task=task,
            current_point=current_point,
            scope=scope,
        )
        self._cached_packets[packet.context_id] = packet
        return packet.model_dump()

    def expand_scope(self, context_id: str) -> Dict[str, Any]:
        """Progressively expands context depth (e.g. D1 -> D2) for an existing context session."""
        cached = self._cached_packets.get(context_id)
        if not cached:
            return {"error": f"Context ID '{context_id}' not found."}

        next_depth, has_expanded = ScopeManager.expand_depth(cached.scope.depth)
        if not has_expanded:
            return {"message": "Maximum depth D3 already reached.", "packet": cached.model_dump()}

        new_scope = cached.scope.copy(update={"depth": next_depth, "breadth_limit": cached.scope.breadth_limit + 3})
        new_packet = self.context_engine.resolve_context(
            role=cached.role,
            purpose=cached.purpose,
            task=cached.task,
            current_point=cached.target_node,
            scope=new_scope,
        )
        self._cached_packets[new_packet.context_id] = new_packet
        return new_packet.model_dump()

    def get_presentation_view(self, context_id: str, tier: str = "HUMAN_L1_SUMMARY") -> str:
        """Renders presentation views (HUMAN_L1_SUMMARY, HUMAN_L2_DETAIL, MACHINE_JSON, NAVIGATION_NEXT_NODES)."""
        cached = self._cached_packets.get(context_id)
        if not cached:
            return f"Error: Context ID '{context_id}' not found."

        tier_enum = PresentationTier(tier)
        if tier_enum == PresentationTier.HUMAN_L1_SUMMARY:
            return PresentationFormatter.format_human_l1_summary(cached)
        elif tier_enum == PresentationTier.HUMAN_L2_DETAIL:
            return PresentationFormatter.format_human_l2_detailed(cached)
        elif tier_enum == PresentationTier.MACHINE_JSON:
            return PresentationFormatter.format_machine_json(cached)
        elif tier_enum == PresentationTier.NAVIGATION_NEXT_NODES:
            return PresentationFormatter.format_navigation_view(cached)
        return PresentationFormatter.format_human_l1_summary(cached)
