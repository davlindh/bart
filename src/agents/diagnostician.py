"""Diagnostiker Agent (Agent 2) - Bottleneck Detection & Root-Cause Hypotheses."""

from typing import Any, Dict, List, Tuple
from src.agents.base import BaseTeamDynamicsAgent
from src.core.contracts import (
    ActionItem,
    ContextPacket,
    HypothesisItem,
    IdentifiedIssue,
)
from src.core.types import SeverityLevel


class DiagnosticianAgent(BaseTeamDynamicsAgent):
    """Analyzes telemetry patterns, isolates bottlenecks, and formulates causal hypotheses."""

    def __init__(self):
        super().__init__(
            name="Diagnostiker",
            description="Isolates organizational bottlenecks, dependency deadlocks, and root causes.",
        )

    async def observe(self, context_packet: ContextPacket) -> List[str]:
        return [
            f"Diagnostiker received context packet '{context_packet.context_id}' with {len(context_packet.nodes)} nodes and {len(context_packet.evidence)} evidence items.",
            "Analyzing multi-hop dependencies around focal point.",
        ]

    async def analyze(self, observations: List[str], context_packet: ContextPacket) -> Dict[str, Any]:
        has_pipeline_failure = any("failure_rate" in n.properties for n in context_packet.nodes)
        has_queue_bottleneck = any("avg_queue_days" in n.properties for n in context_packet.nodes)

        return {
            "metrics": {
                "bottleneck_factor": 0.88,
                "dependency_depth": len(context_packet.relations),
                "pipeline_impact": 0.75 if has_pipeline_failure else 0.2,
                "queue_impact": 0.65 if has_queue_bottleneck else 0.1,
            },
            "risks": [
                "Cascading downstream dispatch delays causing customer SLA penalties",
                "Cognitive overload on decision owner due to manual pipeline recovery checks",
            ],
            "next_questions": [
                "Can Decision Owner mandate be partially automated with confidence thresholds?",
                "Can Pipeline Z be equipped with automated self-healing retries?",
            ],
        }

    async def identify(self, analysis_result: Dict[str, Any]) -> List[IdentifiedIssue]:
        return [
            IdentifiedIssue(
                issue_id="diag_issue_001",
                severity=SeverityLevel.HIGH,
                description="Root cause: Decision Owner 042 is serial-blocked waiting for manual validation of unstable Pipeline Z morning runs.",
                related_nodes=["node:role:decision_owner_042", "node:process:data_pipeline_z"],
            ),
            IdentifiedIssue(
                issue_id="diag_issue_002",
                severity=SeverityLevel.MEDIUM,
                description="Process Y validation queue introduces 4.2 days of latency due to lack of parallel delegation.",
                related_nodes=["node:process:queue_process_y"],
            ),
        ]

    async def propose(self, issues: List[IdentifiedIssue]) -> Tuple[List[HypothesisItem], List[str]]:
        hypotheses = [
            HypothesisItem(
                hypothesis_id="diag_hypo_001",
                statement="Automating Pipeline Z idempotency and delegating low-risk dispatch approvals will reduce decision turnaround from 12 days to < 5 days.",
                probability=0.90,
                root_cause="Unclear delegation threshold + pipeline unreliability",
            )
        ]
        recommendations = [
            "Redesign Decision Owner role charter to introduce stratified approval thresholds.",
            "Hand over structural role recommendations to Team Architect.",
        ]
        return hypotheses, recommendations

    async def act(self, recommendations: List[str], context_packet: ContextPacket) -> List[ActionItem]:
        return [
            ActionItem(
                action_id="act_diag_01",
                type="DISPATCH_TO_ARCHITECT",
                assignee="Team Architect",
                description="Request structural role & delegation redesign from Team Architect.",
            )
        ]

    async def evaluate(self, actions: List[ActionItem], metrics: Dict[str, Any]) -> float:
        return 0.92
