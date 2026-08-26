"""Google Antigravity SDK Configuration Helper and System Environment Settings."""

import os
from typing import Optional, List
from pydantic import BaseModel, Field


class AntigravitySystemConfig(BaseModel):
    """Global system configuration for Google Antigravity SDK execution."""
    default_model: str = Field(default="gemini-3.7-flash", description="Default reasoning foundation model")
    image_model: str = Field(default="gemini-3.1-flash-lite-image", description="Default diagram/image generator model")
    api_key: Optional[str] = Field(default=None, description="Gemini API Key from environment or explicit config")
    max_subagent_depth: int = Field(default=3, description="Hierarchical subagent recursion ceiling")
    enable_subagents: bool = Field(default=True, description="Enable multi-agent delegation")
    max_model_calls: int = Field(default=50, description="Session budget limit for model requests")
    max_tool_calls: int = Field(default=100, description="Session budget limit for tool executions")
    max_total_tokens: int = Field(default=500_000, description="Session total token budget ceiling")
    app_data_dir: Optional[str] = Field(default=None, description="Custom directory for artifacts and scratch files")

    @classmethod
    def load_from_env(cls) -> "AntigravitySystemConfig":
        """Instantiates system config with environment variables fallback."""
        return cls(
            default_model=os.environ.get("ANTIGRAVITY_MODEL", "gemini-3.7-flash"),
            api_key=os.environ.get("GEMINI_API_KEY", None),
            max_subagent_depth=int(os.environ.get("MAX_SUBAGENT_DEPTH", "3")),
            app_data_dir=os.environ.get("ANTIGRAVITY_APP_DATA_DIR", None),
        )


def get_allowed_core_subagents() -> List[str]:
    """Returns the comprehensive allowlist of registered subagent names."""
    return [
        "observer",
        "diagnostician",
        "team_architect",
        "role_transition",
        "collaboration",
        "wellbeing",
        "ai_ethics",
        "experiment_agent",
        "measurement_agent",
        "learning_agent",
        "meta_learning_agent",
        "context_resolver",
        "scope_manager",
        "semantic_mapper",
        "provenance_agent",
        "relationship_analyst",
        "decision_architect",
    ]
