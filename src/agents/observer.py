"""Observer Agent (Agent 1) - Telemetry, Behavioral Signal & Context Gathering."""

from typing import Any, Dict, List, Tuple
from src.agents.base import BaseTeamDynamicsAgent
from src.core.contracts import (
    ActionItem,
    ContextPacket,
    HypothesisItem,
    IdentifiedIssue,
)
from src.core.types import SeverityLevel


class ObserverAgent(BaseTeamDynamicsAgent):
    """Gathers raw signals, logs, and telemetry to formulate objective baseline status."""

    def __init__(self):
        super().__init__(
            name="Observer",
            description="Collects and normalizes team signals, sprint metrics, and operational context.",
        )

    async def observe(self, context_packet: ContextPacket) -> List[str]:
        obs = []
        for node in context_packet.nodes:
            props = node.properties
            if "turnaround_days" in props:
                obs.append(f"Entity '{node.label}' current decision turnaround is {props['turnaround_days']} days (target: {props.get('target_turnaround_days', 5)} days).")
            if "failure_rate" in props:
                obs.append(f"Pipeline '{node.label}' reports failure rate of {props['failure_rate']} with {props.get('incidents', 0)} incidents.")
            if "avg_queue_days" in props:
                obs.append(f"Process '{node.label}' queue latency is {props['avg_queue_days']} days.")
        if not obs:
            obs.append(f"Observed {len(context_packet.nodes)} nodes anchored at {context_packet.target_node}.")
        return obs

    async def analyze(self, observations: List[str], context_packet: ContextPacket) -> Dict[str, Any]:
        metrics = {
            "node_count": len(context_packet.nodes),
            "relation_count": len(context_packet.relations),
            "evidence_count": len(context_packet.evidence),
        }
        for node in context_packet.nodes:
            for k, v in node.properties.items():
                if isinstance(v, (int, float)):
                    metrics[f"{node.id}_{k}"] = v

        return {
            "metrics": metrics,
            "risks": ["Potential reporting delay SLA breach", "Upstream data dependency instability"],
            "next_questions": ["What is the root cause of the 8% pipeline failure rate?", "Is the decision owner over-allocated?"],
        }

    async def identify(self, analysis_result: Dict[str, Any]) -> List[IdentifiedIssue]:
        return [
            IdentifiedIssue(
                issue_id="obs_issue_001",
                severity=SeverityLevel.HIGH,
                description="High turnaround time (12 days) exceeding target SLA threshold (5 days).",
                related_nodes=["node:role:decision_owner_042", "node:kpi:decision_time"],
            )
        ]

    async def propose(self, issues: List[IdentifiedIssue]) -> Tuple[List[HypothesisItem], List[str]]:
        hypotheses = [
            HypothesisItem(
                hypothesis_id="obs_hypo_001",
                statement="Signoff delays stem from upstream pipeline instability and unoptimized verification queues.",
                probability=0.85,
                root_cause="Process dependency delays",
            )
        ]
        recommendations = [
            "Initiate diagnostic analysis on Data Pipeline Z and Process Y.",
            "Review Decision Owner mandate delegation and capacity allocation.",
        ]
        return hypotheses, recommendations

    async def act(self, recommendations: List[str], context_packet: ContextPacket) -> List[ActionItem]:
        return [
            ActionItem(
                action_id="act_obs_01",
                type="TELEMETRY_DIGEST",
                assignee="Diagnostiker",
                description="Forward baseline telemetry snapshot and identified issues to Diagnostiker agent.",
            )
        ]

    async def evaluate(self, actions: List[ActionItem], metrics: Dict[str, Any]) -> float:
        return 0.95
