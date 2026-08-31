"""Base Agent lifecycle following the 6-function contract (observe -> evaluate)."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List
from ..core.types import AgentStatus
from ..core.contracts import ContextPacket, AgentResult, Observation, Diagnosis


class BaseAgent(ABC):
    """Abstract Base Agent implementing the universal 6-function lifecycle."""

    def __init__(self, name: str):
        self.name = name
        self.status = AgentStatus.PENDING

    @abstractmethod
    def observe(self, context: ContextPacket) -> List[Observation]:
        """Step 1: Gathers telemetry signals and facts from context."""
        pass

    @abstractmethod
    def analyze(self, observations: List[Observation]) -> Dict[str, Any]:
        """Step 2: Analyzes patterns, deviations, and suboptimal configurations."""
        pass

    @abstractmethod
    def identify(self, analysis: Dict[str, Any]) -> List[Diagnosis]:
        """Step 3: Pinpoints root causes, tax leakages, or structural frictions."""
        pass

    @abstractmethod
    def propose(self, diagnoses: List[Diagnosis]) -> List[str]:
        """Step 4: Generates actionable recommendations and tax optimizations."""
        pass

    @abstractmethod
    def act(self, recommendations: List[str]) -> List[str]:
        """Step 5: Executes changes, creates vouchers, or applies tags."""
        pass

    @abstractmethod
    def evaluate(self, actions: List[str]) -> Dict[str, Any]:
        """Step 6: Evaluates outcomes, cash savings, and net profit gain."""
        pass

    def run(self, context: ContextPacket) -> AgentResult:
        """Executes the standard 6-function lifecycle loop."""
        self.status = AgentStatus.OBSERVING
        observations = self.observe(context)

        self.status = AgentStatus.ANALYZING
        analysis = self.analyze(observations)

        self.status = AgentStatus.IDENTIFIED
        diagnoses = self.identify(analysis)

        self.status = AgentStatus.PROPOSED
        recommendations = self.propose(diagnoses)

        self.status = AgentStatus.ACTED
        actions = self.act(recommendations)

        self.status = AgentStatus.EVALUATED
        metrics = self.evaluate(actions)

        self.status = AgentStatus.COMPLETED
        return AgentResult(
            agent_name=self.name,
            status=self.status,
            observations=observations,
            diagnoses=diagnoses,
            recommendations=recommendations,
            actions_taken=actions,
            metrics_summary=metrics,
        )

    def run_step(self, step: str, context: ContextPacket) -> Dict[str, Any]:
        """Executes a single step in the lifecycle for interactive UI stepper."""
        step = step.lower()
        if step == "observe":
            self.status = AgentStatus.OBSERVING
            obs = self.observe(context)
            return {"step": "observe", "count": len(obs), "data": [o.model_dump() for o in obs], "output": f"Observerade {len(obs)} signaler"}
        elif step == "analyze":
            self.status = AgentStatus.ANALYZING
            obs = self.observe(context)
            ana = self.analyze(obs)
            return {"step": "analyze", "data": ana, "output": f"Analyserade mönster och data"}
        elif step == "identify":
            self.status = AgentStatus.IDENTIFIED
            obs = self.observe(context)
            diag = self.identify(self.analyze(obs))
            return {"step": "identify", "count": len(diag), "data": [d.model_dump() for d in diag], "output": f"Identifierade {len(diag)} diagnoser/flaskhalsar"}
        elif step == "propose":
            self.status = AgentStatus.PROPOSED
            obs = self.observe(context)
            diag = self.identify(self.analyze(obs))
            prop = self.propose(diag)
            return {"step": "propose", "count": len(prop), "data": prop, "output": f"Föreslog {len(prop)} åtgärder"}
        elif step == "act":
            self.status = AgentStatus.ACTED
            obs = self.observe(context)
            diag = self.identify(self.analyze(obs))
            prop = self.propose(diag)
            acted = self.act(prop)
            return {"step": "act", "count": len(acted), "data": acted, "output": f"Genomförde {len(acted)} åtgärder"}
        elif step == "evaluate":
            self.status = AgentStatus.EVALUATED
            obs = self.observe(context)
            diag = self.identify(self.analyze(obs))
            prop = self.propose(diag)
            acted = self.act(prop)
            ev = self.evaluate(acted)
            return {"step": "evaluate", "data": ev, "output": f"Utvärderade effekt"}
        return {"step": step, "error": f"Okänt steg: {step}"}
