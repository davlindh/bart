"""Window Particle Decomposition Models — Components, Contextual Particles, and Entanglement Nodes.

Migrated from 3.7fmossmorph/meta-framework/layered_runner/Attach/
  - Component Layer and Contextual Particles Comprehension.txt
  - Insight Integration Agent.txt
  - Insight Synthesizer Agent.txt

Each of the 9 Perspective Windows is decomposed into:
  1. Components — the functional building blocks within the window
  2. Contextual Particles — the informational outputs the window produces
  3. Entanglement Nodes — cross-window linkages that create synchronized relevance
"""

from typing import Dict, List
from pydantic import BaseModel, Field
from src.core.types import PerspectiveWindow


class ContextualParticle(BaseModel):
    """A discrete unit of information produced by a window."""
    particle_id: str
    label: str
    description: str
    output_type: str = Field(default="text", description="text | metric | recommendation | report")


class WindowComponent(BaseModel):
    """A functional building block within a perspective window."""
    component_id: str
    label: str
    description: str
    particles: List[ContextualParticle] = Field(default_factory=list)


class EntanglementNode(BaseModel):
    """A cross-window linkage point where data synchronizes across domains."""
    node_id: str
    label: str
    linked_windows: List[PerspectiveWindow] = Field(min_length=2)
    description: str
    sync_mode: str = Field(default="bidirectional", description="bidirectional | source_to_target")


class WindowDecomposition(BaseModel):
    """Full decomposition of a single Perspective Window."""
    window: PerspectiveWindow
    components: List[WindowComponent] = Field(default_factory=list)
    entanglement_nodes: List[EntanglementNode] = Field(default_factory=list)


# ── Canonical Decomposition Registry ────────────────────────────────────

WINDOW_DECOMPOSITIONS: Dict[PerspectiveWindow, WindowDecomposition] = {

    PerspectiveWindow.CONTEXTUALIZATION: WindowDecomposition(
        window=PerspectiveWindow.CONTEXTUALIZATION,
        components=[
            WindowComponent(
                component_id="ctx_trend",
                label="Trend Analysis",
                description="Identifies and summarizes current project and organizational trends.",
                particles=[
                    ContextualParticle(particle_id="ctx_trend_insights", label="Trend Insights", description="Emerging trends relevant to user objectives", output_type="report"),
                ],
            ),
            WindowComponent(
                component_id="ctx_best",
                label="Best Practices Aggregator",
                description="Aggregates industry standards and historical operational data.",
                particles=[
                    ContextualParticle(particle_id="ctx_recommendations", label="Personalized Recommendations", description="Tailored insights based on user behavior and context", output_type="recommendation"),
                ],
            ),
        ],
        entanglement_nodes=[
            EntanglementNode(node_id="ent_trend_practice", label="Trends ↔ Best Practices", linked_windows=[PerspectiveWindow.CONTEXTUALIZATION, PerspectiveWindow.ADAPTIVE_INSIGHTS], description="Trends interact with adaptive insights to provide landscape understanding"),
        ],
    ),

    PerspectiveWindow.MATCHING: WindowDecomposition(
        window=PerspectiveWindow.MATCHING,
        components=[
            WindowComponent(
                component_id="match_db",
                label="Resource Database",
                description="Information on available resources, skills, and capacities.",
                particles=[
                    ContextualParticle(particle_id="match_suggestions", label="Match Suggestions", description="Potential resource and personnel matches", output_type="recommendation"),
                ],
            ),
            WindowComponent(
                component_id="match_algo",
                label="Matching Algorithms",
                description="Tools to align resources with project needs based on compatibility.",
                particles=[
                    ContextualParticle(particle_id="match_analysis", label="Compatibility Analysis", description="Rationale and scoring for resource matches", output_type="metric"),
                ],
            ),
        ],
        entanglement_nodes=[
            EntanglementNode(node_id="ent_resource_compat", label="Resources ↔ Compatibility", linked_windows=[PerspectiveWindow.MATCHING, PerspectiveWindow.RESOURCE_ALLOCATION], description="Matched resources synchronize with allocation planning"),
        ],
    ),

    PerspectiveWindow.EVALUATION: WindowDecomposition(
        window=PerspectiveWindow.EVALUATION,
        components=[
            WindowComponent(
                component_id="eval_metrics",
                label="Performance Metrics",
                description="Quantitative data from past and current performance.",
                particles=[
                    ContextualParticle(particle_id="eval_reports", label="Performance Reports", description="Summarized outcomes and key metrics", output_type="report"),
                ],
            ),
            WindowComponent(
                component_id="eval_feedback",
                label="Feedback Integration",
                description="Continuous analysis of qualitative feedback.",
                particles=[
                    ContextualParticle(particle_id="eval_improvements", label="Improvement Recommendations", description="Areas identified for enhancement", output_type="recommendation"),
                ],
            ),
        ],
        entanglement_nodes=[
            EntanglementNode(node_id="ent_perf_feedback", label="Performance ↔ Feedback", linked_windows=[PerspectiveWindow.EVALUATION, PerspectiveWindow.ADAPTIVE_INSIGHTS], description="Historical performance interconnects with real-time feedback"),
        ],
    ),

    PerspectiveWindow.RESOURCE_ALLOCATION: WindowDecomposition(
        window=PerspectiveWindow.RESOURCE_ALLOCATION,
        components=[
            WindowComponent(
                component_id="res_mgmt",
                label="Resource Management Tools",
                description="Systems for tracking and allocating time, budget, and materials.",
                particles=[
                    ContextualParticle(particle_id="res_plans", label="Resource Plans", description="Detailed strategies for resource allocation", output_type="recommendation"),
                ],
            ),
            WindowComponent(
                component_id="res_optim",
                label="Optimization Algorithms",
                description="Methods for efficient resource utilization.",
                particles=[
                    ContextualParticle(particle_id="res_forecasts", label="Budget Forecasts", description="Financial projections for resource distribution", output_type="metric"),
                ],
            ),
        ],
        entanglement_nodes=[
            EntanglementNode(node_id="ent_res_optim", label="Resources ↔ Optimization", linked_windows=[PerspectiveWindow.RESOURCE_ALLOCATION, PerspectiveWindow.FINANCIAL_MANAGEMENT], description="Resource plans synchronize with financial management"),
        ],
    ),

    PerspectiveWindow.FINANCIAL_MANAGEMENT: WindowDecomposition(
        window=PerspectiveWindow.FINANCIAL_MANAGEMENT,
        components=[
            WindowComponent(
                component_id="fin_models",
                label="Financial Models",
                description="Tools for budgeting, forecasting, and scenario planning.",
                particles=[
                    ContextualParticle(particle_id="fin_budget", label="Budget Reports", description="Detailed financial summaries", output_type="report"),
                ],
            ),
            WindowComponent(
                component_id="fin_accountability",
                label="Accountability Frameworks",
                description="Systems for transparent financial management.",
                particles=[
                    ContextualParticle(particle_id="fin_strategies", label="Funding Strategies", description="Plans for resource acquisition and distribution", output_type="recommendation"),
                ],
            ),
        ],
        entanglement_nodes=[
            EntanglementNode(node_id="ent_budget_account", label="Budget ↔ Accountability", linked_windows=[PerspectiveWindow.FINANCIAL_MANAGEMENT, PerspectiveWindow.EVALUATION], description="Financial strategies synchronized with transparent evaluation outcomes"),
        ],
    ),

    PerspectiveWindow.PERSONNEL_MANAGEMENT: WindowDecomposition(
        window=PerspectiveWindow.PERSONNEL_MANAGEMENT,
        components=[
            WindowComponent(
                component_id="pers_analysis",
                label="Team Analysis Tools",
                description="Systems for evaluating team dynamics and composition.",
                particles=[
                    ContextualParticle(particle_id="pers_charts", label="Team Charts", description="Visual representation of team structure", output_type="report"),
                ],
            ),
            WindowComponent(
                component_id="pers_roles",
                label="Role Management Systems",
                description="Tools for role assignment, adjustment, and transition planning.",
                particles=[
                    ContextualParticle(particle_id="pers_descriptions", label="Role Descriptions", description="Detailed definitions and mandates for each role", output_type="text"),
                ],
            ),
        ],
        entanglement_nodes=[
            EntanglementNode(node_id="ent_team_roles", label="Team Dynamics ↔ Roles", linked_windows=[PerspectiveWindow.PERSONNEL_MANAGEMENT, PerspectiveWindow.MATCHING], description="Team composition synchronizes with skill matching"),
        ],
    ),

    PerspectiveWindow.COMMUNICATION_PRESENTATION: WindowDecomposition(
        window=PerspectiveWindow.COMMUNICATION_PRESENTATION,
        components=[
            WindowComponent(
                component_id="comm_platforms",
                label="Interactive Platforms",
                description="Systems for real-time updates and stakeholder communication.",
                particles=[
                    ContextualParticle(particle_id="comm_announcements", label="Announcements", description="Key updates and operational news", output_type="text"),
                ],
            ),
            WindowComponent(
                component_id="comm_engagement",
                label="Engagement Tools",
                description="Resources for stakeholder interaction and feedback collection.",
                particles=[
                    ContextualParticle(particle_id="comm_metrics", label="Engagement Metrics", description="Data on interaction levels and reach", output_type="metric"),
                ],
            ),
        ],
        entanglement_nodes=[
            EntanglementNode(node_id="ent_comm_engage", label="Communication ↔ Engagement", linked_windows=[PerspectiveWindow.COMMUNICATION_PRESENTATION, PerspectiveWindow.ADAPTIVE_INSIGHTS], description="Communication flow synchronizes with engagement feedback"),
        ],
    ),

    PerspectiveWindow.INNOVATION_TECHNOLOGY: WindowDecomposition(
        window=PerspectiveWindow.INNOVATION_TECHNOLOGY,
        components=[
            WindowComponent(
                component_id="innov_scout",
                label="Technology Scouting Tools",
                description="Systems for identifying and evaluating new technologies.",
                particles=[
                    ContextualParticle(particle_id="innov_reports", label="Tech Reports", description="Insights into emerging technologies and applicability", output_type="report"),
                ],
            ),
            WindowComponent(
                component_id="innov_strategy",
                label="Innovation Strategies",
                description="Plans for integrating new technology into operations.",
                particles=[
                    ContextualParticle(particle_id="innov_plans", label="Adoption Plans", description="Strategies for technology integration and rollout", output_type="recommendation"),
                ],
            ),
        ],
        entanglement_nodes=[
            EntanglementNode(node_id="ent_tech_innov", label="Technology ↔ Innovation", linked_windows=[PerspectiveWindow.INNOVATION_TECHNOLOGY, PerspectiveWindow.RESOURCE_ALLOCATION], description="Technology evaluation synchronizes with resource planning"),
        ],
    ),

    PerspectiveWindow.ADAPTIVE_INSIGHTS: WindowDecomposition(
        window=PerspectiveWindow.ADAPTIVE_INSIGHTS,
        components=[
            WindowComponent(
                component_id="adapt_sentiment",
                label="Sentiment Analysis Tools",
                description="Systems for analyzing qualitative feedback and team morale.",
                particles=[
                    ContextualParticle(particle_id="adapt_sentiment_reports", label="Sentiment Reports", description="Analysis of feedback and emotional signals", output_type="report"),
                ],
            ),
            WindowComponent(
                component_id="adapt_patterns",
                label="Pattern Recognition Systems",
                description="Tools for identifying trends and evolving needs.",
                particles=[
                    ContextualParticle(particle_id="adapt_trends", label="Trend Analysis", description="Insights into evolving community needs", output_type="report"),
                ],
            ),
        ],
        entanglement_nodes=[
            EntanglementNode(node_id="ent_sentiment_trends", label="Sentiment ↔ Trends", linked_windows=[PerspectiveWindow.ADAPTIVE_INSIGHTS, PerspectiveWindow.CONTEXTUALIZATION], description="Feedback and trends continuously analyzed to adapt strategies"),
        ],
    ),
}


def get_all_entanglement_nodes() -> List[EntanglementNode]:
    """Returns all cross-window entanglement nodes from the full decomposition."""
    nodes: List[EntanglementNode] = []
    for decomp in WINDOW_DECOMPOSITIONS.values():
        nodes.extend(decomp.entanglement_nodes)
    return nodes


def get_all_particles() -> List[ContextualParticle]:
    """Returns all contextual particles across all windows."""
    particles: List[ContextualParticle] = []
    for decomp in WINDOW_DECOMPOSITIONS.values():
        for comp in decomp.components:
            particles.extend(comp.particles)
    return particles
