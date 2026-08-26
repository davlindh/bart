"""Team Operations MCP Server providing tool handlers for observations, diagnoses, experiments, and learnings."""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from src.graph.models import (
    Diagnosis,
    Experiment,
    Intervention,
    Knowledge,
    Learning,
    Measurement,
    Observation,
)


class TeamOpsMcpServer:
    """MCP Server providing operational entity tracking, experiments, and learnings."""

    def __init__(self):
        self.observations: Dict[str, Observation] = {}
        self.diagnoses: Dict[str, Diagnosis] = {}
        self.interventions: Dict[str, Intervention] = {}
        self.experiments: Dict[str, Experiment] = {}
        self.measurements: Dict[str, Measurement] = {}
        self.learnings: Dict[str, Learning] = {}

    def log_observation(
        self,
        team_id: str,
        source_type: str,
        source_ref: str,
        data_json: Dict[str, Any],
        agent_id: str = "Observer",
    ) -> Dict[str, Any]:
        """Logs a raw telemetry observation."""
        obs_id = f"obs_{uuid.uuid4().hex[:8]}"
        obs = Observation(
            observation_id=obs_id,
            team_id=team_id,
            source_type=source_type,
            source_ref=source_ref,
            data_json=data_json,
            created_by_agent_id=agent_id,
        )
        self.observations[obs_id] = obs
        return obs.model_dump()

    def log_diagnosis(
        self,
        observation_id: str,
        hypothesis: str,
        root_cause: str,
        confidence: float = 0.85,
        agent_id: str = "Diagnostiker",
    ) -> Dict[str, Any]:
        """Logs an analytical diagnosis and root cause hypothesis."""
        diag_id = f"diag_{uuid.uuid4().hex[:8]}"
        diag = Diagnosis(
            diagnosis_id=diag_id,
            observation_id=observation_id,
            hypothesis=hypothesis,
            root_cause=root_cause,
            confidence=confidence,
            created_by_agent_id=agent_id,
        )
        self.diagnoses[diag_id] = diag
        return diag.model_dump()

    def register_experiment(
        self,
        intervention_id: str,
        hypothesis: str,
        design: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Registers a controlled experiment to validate an intervention."""
        exp_id = f"exp_{uuid.uuid4().hex[:8]}"
        exp = Experiment(
            experiment_id=exp_id,
            intervention_id=intervention_id,
            hypothesis=hypothesis,
            design=design,
        )
        self.experiments[exp_id] = exp
        return exp.model_dump()

    def record_measurement(
        self,
        experiment_id: str,
        metric_name: str,
        value_number: float,
        baseline_value: Optional[float] = None,
        delta_pct: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Records an empirical measurement outcome."""
        meas_id = f"meas_{uuid.uuid4().hex[:8]}"
        meas = Measurement(
            measurement_id=meas_id,
            experiment_id=experiment_id,
            metric_name=metric_name,
            value_number=value_number,
            baseline_value=baseline_value,
            delta_pct=delta_pct,
        )
        self.measurements[meas_id] = meas
        return meas.model_dump()

    def publish_learning(
        self,
        measurement_id: str,
        insight: str,
        confidence: float = 0.95,
    ) -> Dict[str, Any]:
        """Publishes verified institutional learning."""
        learn_id = f"learn_{uuid.uuid4().hex[:8]}"
        learning = Learning(
            learning_id=learn_id,
            measurement_id=measurement_id,
            insight=insight,
            confidence=confidence,
        )
        self.learnings[learn_id] = learning
        return learning.model_dump()
