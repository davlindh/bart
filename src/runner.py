"""Interactive Runner demonstrating the complete Omnipod & Team Dynamics Multi-Agent Loop."""

import asyncio
import sys
from pathlib import Path

# Ensure project root is on sys.path and stdout handles UTF-8 on Windows
sys.path.insert(0, str(Path(__file__).parent.parent))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from src.context_engine.presentation import PresentationFormatter
from src.context_engine.resolver import ContextResolutionEngine
from src.core.governance import GovernanceEngine
from src.core.types import ScopeDepth
from src.graph.graph_store import KnowledgeGraphStore
from src.seeds.seed_loader import SeedDataLoader
from src.agents.orchestrator import TeamDynamicsOrchestrator


async def main():
    print("=" * 80)
    print("🚀 OMNIPOD & TEAM DYNAMICS OPTIMIZER — GOOGLE ANTIGRAVITY SDK ENGINE")
    print("=" * 80)

    # 1. Initialize Knowledge Graph Store from Seed Data
    print("\n📦 [1/4] Loading Seed Knowledge Graph & Domain Topologies...")
    graph_store = SeedDataLoader.load_seed_graph()
    nodes = graph_store.get_all_nodes()
    edges = graph_store.get_all_edges()
    print(f"✅ Loaded {len(nodes)} semantic nodes and {len(edges)} directed relationships.")

    # 2. Initialize Dynamic Context Resolution Engine
    print("\n🔍 [2/4] Initializing Dynamic Context Resolution Engine & Governance...")
    governance = GovernanceEngine()
    context_engine = ContextResolutionEngine(graph_store=graph_store, governance_engine=governance)
    orchestrator = TeamDynamicsOrchestrator(graph_store=graph_store, context_engine=context_engine)
    print("✅ Context Resolution Engine & 12-Agent Ecosystem Ready.")

    # 3. Define the Operational Scenario from the Conversation & Diagram
    role = "Data Manager"
    purpose = "Improve Data Quality & Report Delivery SLA"
    task = "Identify root causes of delayed daily SLA reporting (Pipeline Z / Decision Owner 042)"
    focal_point = "node:role:decision_owner_042"

    print("\n🎯 [3/4] Scenario Trigger:")
    print(f"   • Role        : {role}")
    print(f"   • Purpose     : {purpose}")
    print(f"   • Task        : {task}")
    print(f"   • Focal Point : {focal_point}")

    # 4. Run the Full Multi-Agent Optimization Loop
    print("\n🔄 [4/4] Executing Closed-Loop Multi-Agent Cycle (12 Agents + Dual Feedback Loops)...")
    results = await orchestrator.run_full_optimization_cycle(
        role=role,
        purpose=purpose,
        task=task,
        current_point=focal_point,
        initial_depth=ScopeDepth.D1,
    )

    context_packet = results["context_packet"]
    agent_results = results["agent_results"]
    perf_model = results["performance_model"]

    print("\n" + "=" * 80)
    print("📊 PRESENTATION TIER 1: HUMAN EXECUTIVE SUMMARY")
    print("=" * 80)
    print(PresentationFormatter.format_human_l1_summary(context_packet))

    print("\n" + "=" * 80)
    print("📋 PRESENTATION TIER 2: DETAILED EVIDENCE & DEPENDENCY GRAPH")
    print("=" * 80)
    print(PresentationFormatter.format_human_l2_detailed(context_packet))

    print("\n" + "=" * 80)
    print("🧭 PRESENTATION TIER 4: NAVIGATION & PREDICTIVE NEXT NODES")
    print("=" * 80)
    print(PresentationFormatter.format_navigation_view(context_packet))

    print("\n" + "=" * 80)
    print("🤖 MULTI-AGENT EXECUTION CYCLE TRACE (12 AGENTS)")
    print("=" * 80)
    for res in agent_results:
        print(f"\n🔹 Agent: [{res.agent_name}] (Confidence: {res.confidence})")
        if res.observations:
            print(f"   • Observation : {res.observations[0]}")
        if res.identified_issues:
            print(f"   • Issue       : [{res.identified_issues[0].severity.value}] {res.identified_issues[0].description}")
        if res.hypotheses:
            print(f"   • Hypothesis  : {res.hypotheses[0].statement}")
        if res.actions:
            print(f"   • Action      : [{res.actions[0].type}] {res.actions[0].description}")
        if res.metrics:
            print(f"   • Metrics     : {res.metrics}")

    print("\n" + "=" * 80)
    print("🧠 DUAL META-LEARNING & SELF-IMPROVEMENT REPORT")
    print("=" * 80)
    print(f"• System Health Accuracy Score : {perf_model.diagnostic_accuracy * 100:.1f}%")
    print(f"• Scope Adequacy Score         : {perf_model.scope_adequacy_score * 100:.1f}%")
    print(f"• Weight Calibrations Applied  : {perf_model.recommended_weight_calibrations}")
    print(f"• Measured Turnaround Delta    : {results['summary']['measured_improvement']}% improvement")
    print(f"• Codified Institutional Rule  : {results['summary']['codified_principle']}")

    # Phase 3 Platform Layer: 9-Window Omnipod Presenter
    from src.platform.omnipod_presenter import OmnipodPresenter
    print("\n" + "=" * 80)
    print("🪟 PLATFORM LAYER — 9 PERSPECTIVE WINDOWS CLIENT VIEWMODELS")
    print("=" * 80)
    window_payloads = OmnipodPresenter.present_all_windows(context_packet, agent_results)
    for win, payload in window_payloads.items():
        particle_names = [p["label"] for p in payload.active_particles]
        print(f"  [{win.value.upper()}]")
        print(f"    • L1 Summary    : {payload.l1_summary}")
        print(f"    • Particles ({len(particle_names)}): {', '.join(particle_names)}")
        if payload.entangled_links:
            print(f"    • Entanglements : {payload.entangled_links[0]}")

    print("\n" + "=" * 80)
    print("✨ CYCLE COMPLETE — Self-Improving Loop Successfully Concluded!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
