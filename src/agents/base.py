"""Base Agent class defining the standardized 6-function lifecycle for all agents."""

import uuid
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple
from src.core.contracts import (
    ActionItem,
    AgentResult,
    ContextPacket,
    HypothesisItem,
    IdentifiedIssue,
)


class BaseTeamDynamicsAgent(ABC):
    """
    Standardized Base Agent implementing the canonical 6-function loop:
    observe() -> analyze() -> identify() -> propose() -> act() -> evaluate()
    """

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    @abstractmethod
    async def observe(self, context_packet: ContextPacket) -> List[str]:
        """Gathers and normalizes raw observations from the bounded context."""
        pass

    @abstractmethod
    async def analyze(self, observations: List[str], context_packet: ContextPacket) -> Dict[str, Any]:
        """Analyzes observations to extract structured patterns and metrics."""
        pass

    @abstractmethod
    async def identify(self, analysis_result: Dict[str, Any]) -> List[IdentifiedIssue]:
        """Identifies specific bottlenecks, risks, or opportunities."""
        pass

    @abstractmethod
    async def propose(self, issues: List[IdentifiedIssue]) -> Tuple[List[HypothesisItem], List[str]]:
        """Formulates testable hypotheses and action recommendations."""
        pass

    @abstractmethod
    async def act(self, recommendations: List[str], context_packet: ContextPacket) -> List[ActionItem]:
        """Generates concrete operational actions or workflow tickets."""
        pass

    @abstractmethod
    async def evaluate(self, actions: List[ActionItem], metrics: Dict[str, Any]) -> float:
        """Evaluates overall confidence and execution readiness."""
        pass

    async def execute_cycle(self, context_packet: ContextPacket, iteration_id: Optional[str] = None) -> AgentResult:
        """Runs the complete 6-stage lifecycle, producing a strongly-typed AgentResult."""
        iter_id = iteration_id or f"iter_{uuid.uuid4().hex[:6]}"

        # 1. Observe
        observations = await self.observe(context_packet)

        # 2. Analyze
        analysis = await self.analyze(observations, context_packet)

        # 3. Identify
        issues = await self.identify(analysis)

        # 4. Propose
        hypotheses, recommendations = await self.propose(issues)

        # 5. Act
        actions = await self.act(recommendations, context_packet)

        # 6. Evaluate
        confidence = await self.evaluate(actions, analysis.get("metrics", {}))

        # Compile dependencies
        deps = [node.id for node in context_packet.nodes]

        return AgentResult(
            agent_name=self.name,
            iteration_id=iter_id,
            observations=observations,
            confidence=confidence,
            identified_issues=issues,
            hypotheses=hypotheses,
            recommendations=recommendations,
            actions=actions,
            metrics=analysis.get("metrics", {}),
            risks=analysis.get("risks", []),
            dependencies=deps,
            next_questions=analysis.get("next_questions", []),
        )
