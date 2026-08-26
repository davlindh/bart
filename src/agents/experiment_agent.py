"""Experiment Agent (Agent 12), Measurement Agent (Agent 9) & Learning Agent (Agent 10)."""

from typing import Any, Dict, List, Tuple
from src.agents.base import BaseTeamDynamicsAgent
from src.core.contracts import (
    ActionItem,
    ContextPacket,
    ExperimentPlan,
    HypothesisItem,
    IdentifiedIssue,
    LearningObject,
)
from src.core.types import ImpactLevel, SeverityLevel


class ExperimentAgent(BaseTeamDynamicsAgent):
    """Converts proposed interventions into rigorous, falsifiable hypothesis experiments."""

    def __init__(self):
        super().__init__(
            name="Experiment Agent",
            description="Designs testable experiments, cohorts, metrics, and guardrails to validate interventions.",
        )

    async def observe(self, context_packet: ContextPacket) -> List[str]:
        return [
            "Synthesizing recommendations from Diagnostiker, Team Architect, and AI Ethics.",
            "Formulating empirical experiment specification.",
        ]

    async def analyze(self, observations: List[str], context_packet: ContextPacket) -> Dict[str, Any]:
        return {
            "metrics": {
                "target_metric": "KPI: Decision Turnaround Time (days)",
                "baseline": 12.0,
                "target": 4.5,
                "test_duration_days": 14,
            },
            "risks": ["Unexpected edge cases in automated Tier 1 rule evaluation."],
            "next_questions": ["What is the fallback path if Tier 1 auto-approval detects anomalous inputs?"],
        }

    async def identify(self, analysis_result: Dict[str, Any]) -> List[IdentifiedIssue]:
        return [
            IdentifiedIssue(
                issue_id="exp_issue_001",
                severity=SeverityLevel.LOW,
                description="Need for clear rollback triggers if test cohort experiences false-positive auto-approvals.",
                related_nodes=["node:decision:decision_x"],
            )
        ]

    async def propose(self, issues: List[IdentifiedIssue]) -> Tuple[List[HypothesisItem], List[str]]:
        hypotheses = [
            HypothesisItem(
                hypothesis_id="exp_hypo_001",
                statement="Deploying Tiered Approvals for a 14-day A/B experiment will reduce turnaround time by >= 50% with zero regulatory breaches.",
                probability=0.91,
                root_cause="Validation experiment design",
            )
        ]
        recommendations = [
            "Launch 14-day Experiment 'EXP_TIERED_APPROVAL_001' on 50% of daily dispatches.",
            "Set rollback threshold: any false-positive trigger immediately reverts to manual signoff.",
        ]
        return hypotheses, recommendations

    async def act(self, recommendations: List[str], context_packet: ContextPacket) -> List[ActionItem]:
        return [
            ActionItem(
                action_id="act_exp_01",
                type="LAUNCH_EXPERIMENT",
                assignee="Measurement Agent",
                description="Deploy Experiment 'EXP_TIERED_APPROVAL_001' and notify Measurement Agent to begin metric tracking.",
            )
        ]

    async def evaluate(self, actions: List[ActionItem], metrics: Dict[str, Any]) -> float:
        return 0.94


class MeasurementAgent(BaseTeamDynamicsAgent):
    """Quantifies outcome impact and computes delta changes against baselines."""

    def __init__(self):
        super().__init__(
            name="Measurement Agent",
            description="Collects post-intervention telemetry, computes metric deltas, and validates experiment success.",
        )

    async def observe(self, context_packet: ContextPacket) -> List[str]:
        return [
            "Sampling post-experiment telemetry for Decision Turnaround Time and Pipeline Reliability.",
            "Comparing observed values against pre-intervention baseline (12.0 days).",
        ]

    async def analyze(self, observations: List[str], context_packet: ContextPacket) -> Dict[str, Any]:
        baseline = 12.0
        observed_value = 4.2  # Delta improvement result
        delta_pct = round(((observed_value - baseline) / baseline) * 100, 1)

        return {
            "metrics": {
                "metric_name": "decision_turnaround_days",
                "baseline_value": baseline,
                "measured_value": observed_value,
                "delta_pct": delta_pct,  # -65.0%
                "pipeline_z_failure_rate": "1.2%",  # down from 8.0%
                "goal_achieved": True,
            },
            "risks": [],
            "next_questions": ["Is this improvement sustained during peak quarter-end volume?"],
        }

    async def identify(self, analysis_result: Dict[str, Any]) -> List[IdentifiedIssue]:
        return []

    async def propose(self, issues: List[IdentifiedIssue]) -> Tuple[List[HypothesisItem], List[str]]:
        hypotheses = [
            HypothesisItem(
                hypothesis_id="meas_hypo_001",
                statement="Tiered approval architecture successfully reduced decision latency by 65.0% without error introduction.",
                probability=0.98,
                root_cause="Validated intervention",
            )
        ]
        recommendations = [
            "Confirm permanent adoption of Tiered Mandate Model across all dispatch workflows.",
            "Deliver validated measurement findings to Learning Agent.",
        ]
        return hypotheses, recommendations

    async def act(self, recommendations: List[str], context_packet: ContextPacket) -> List[ActionItem]:
        return [
            ActionItem(
                action_id="act_meas_01",
                type="HANDOVER_TO_LEARNING",
                assignee="Learning Agent",
                description="Deliver verified -65.0% decision latency reduction findings to Learning Agent for codification.",
            )
        ]

    async def evaluate(self, actions: List[ActionItem], metrics: Dict[str, Any]) -> float:
        return 0.98


class LearningAgent(BaseTeamDynamicsAgent):
    """Extracts generalizable organizational principles and codifies updated knowledge rules."""

    def __init__(self):
        super().__init__(
            name="Learning Agent",
            description="Extracts institutional learnings, updates knowledge nodes, and codifies new heuristics.",
        )

    async def observe(self, context_packet: ContextPacket) -> List[str]:
        return [
            "Synthesizing measured results from Experiment 'EXP_TIERED_APPROVAL_001'.",
            "Extracting generalizable architectural and organizational principles.",
        ]

    async def analyze(self, observations: List[str], context_packet: ContextPacket) -> Dict[str, Any]:
        return {
            "metrics": {
                "learning_confidence": 0.96,
                "generalizability_score": 0.90,
            },
            "risks": [],
            "next_questions": ["Which other operational queues could benefit from Tiered Mandates?"],
        }

    async def identify(self, analysis_result: Dict[str, Any]) -> List[IdentifiedIssue]:
        return []

    async def propose(self, issues: List[IdentifiedIssue]) -> Tuple[List[HypothesisItem], List[str]]:
        hypotheses = [
            HypothesisItem(
                hypothesis_id="learn_hypo_001",
                statement="Stratified authority structures consistently yield > 50% turnaround improvements in serial operational approval queues.",
                probability=0.96,
                root_cause="Generalizable organizational principle",
            )
        ]
        recommendations = [
            "Codify Principle 'KNOW_PRINCIPLE_TIERED_APPROVALS' in long-term knowledge graph.",
            "Forward performance signals to Meta-Learning Agent.",
        ]
        return hypotheses, recommendations

    async def act(self, recommendations: List[str], context_packet: ContextPacket) -> List[ActionItem]:
        return [
            ActionItem(
                action_id="act_learn_01",
                type="KNOWLEDGE_UPDATE",
                assignee="Knowledge Graph",
                description="Publish Knowledge Node 'Stratified Decision Delegation Pattern' to /knowledge directory.",
            )
        ]

    async def evaluate(self, actions: List[ActionItem], metrics: Dict[str, Any]) -> float:
        return 0.97
