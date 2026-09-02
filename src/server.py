"""FastAPI HTTP and Real-Time SSE Server for Omnipod & Team Dynamics Optimizer.

Exposes:
  - GET  /health               -> Service health & runtime telemetry
  - GET  /stream               -> Real-time Server-Sent Events (SSE) stream from StreamBridge
  - POST /api/cycle/run        -> Triggers full 12-agent optimization loop & broadcasts trace events
  - POST /api/context/resolve  -> Resolves dynamic task-specific sub-graph
  - POST /api/context/expand   -> Expands context depth (D1 -> D2 -> D3)
  - GET  /api/graph/nodes      -> Returns all active semantic graph nodes
  - GET  /api/graph/edges      -> Returns directed relationships
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from src.core.contracts import ScopeContract
from src.core.governance import GovernanceEngine
from src.core.types import DomainType, ScopeDepth
from src.graph.graph_store import KnowledgeGraphStore
from src.seeds.seed_loader import SeedDataLoader
from src.context_engine.resolver import ContextResolutionEngine
from src.context_engine.scope_manager import ScopeManager
from src.context_engine.presentation import PresentationFormatter
from src.agents.orchestrator import TeamDynamicsOrchestrator
from src.platform.stream_bridge import StreamBridge, EventType
from src.platform.omnipod_presenter import OmnipodPresenter

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("omnipod.server")

app = FastAPI(
    title="Omnipod & Team Dynamics Optimizer Server",
    description="Cognitive Multi-Agent Orchestration & Real-time Context Streaming API",
    version="1.0.0",
)

# Allow CORS for all local frontend dashboards
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global State Container
class SystemContainer:
    graph_store: KnowledgeGraphStore
    governance: GovernanceEngine
    context_engine: ContextResolutionEngine
    orchestrator: TeamDynamicsOrchestrator
    stream_bridge: StreamBridge

container = SystemContainer()

@app.on_event("startup")
async def startup_event():
    logger.info("Initializing Knowledge Graph from seed catalog...")
    container.graph_store = SeedDataLoader.load_seed_graph()
    container.governance = GovernanceEngine()
    container.context_engine = ContextResolutionEngine(
        graph_store=container.graph_store,
        governance_engine=container.governance,
    )
    container.orchestrator = TeamDynamicsOrchestrator(
        graph_store=container.graph_store,
        context_engine=container.context_engine,
    )
    container.stream_bridge = StreamBridge(max_buffer_size=500)
    logger.info(
        "Omnipod Engine started successfully with %d nodes and %d edges.",
        len(container.graph_store.get_all_nodes()),
        len(container.graph_store.get_all_edges()),
    )


# ── Health & Diagnostics ───────────────────────────────────────────────────

@app.get("/health")
async def health():
    nodes = container.graph_store.get_all_nodes() if hasattr(container, "graph_store") else []
    edges = container.graph_store.get_all_edges() if hasattr(container, "graph_store") else []
    return {
        "status": "healthy",
        "service": "bart-omnipod-orchestrator",
        "active_nodes": len(nodes),
        "active_edges": len(edges),
        "active_stream_subscribers": container.stream_bridge.active_connections if hasattr(container, "stream_bridge") else 0,
    }


# ── Real-time SSE Stream ────────────────────────────────────────────────────

@app.get("/stream")
async def stream_events(request: Request):
    """Server-Sent Events endpoint streaming real-time agent execution events to UI dashboards."""
    async def event_generator():
        async for frame in container.stream_bridge.client_stream(replay_history=True):
            if await request.is_disconnected():
                break
            yield {
                "event": frame.event_type.value,
                "id": frame.frame_id,
                "data": json.dumps({
                    "timestamp": frame.timestamp,
                    "event_type": frame.event_type.value,
                    "payload": frame.payload,
                }),
            }

    return EventSourceResponse(event_generator())


# ── Orchestrator Multi-Agent Cycle ─────────────────────────────────────────

class CycleRunRequest(BaseModel):
    role: str = Field(default="Ägare / VD", description="Requesting agent/persona role")
    purpose: str = Field(default="Marginaloptimering & Likviditetsstyrning", description="Operational focus purpose")
    task: str = Field(default="Analysera avvikelser i TB/TG samt förfallna kundfordringar", description="Actionable task trigger")
    current_point: str = Field(default="node:role:owner_ceo", description="Focal graph entity ID")
    initial_depth: str = Field(default="D1", description="Initial scope depth (D0..D3)")

@app.post("/api/cycle/run")
async def run_optimization_cycle(req: CycleRunRequest):
    """Executes a full 12-agent cycle and broadcasts each step to the SSE stream bridge."""
    try:
        depth = ScopeDepth(req.initial_depth)
    except ValueError:
        depth = ScopeDepth.D1

    # Broadcast cycle started
    await container.stream_bridge.broadcast(
        EventType.CYCLE_STARTED,
        {
            "role": req.role,
            "purpose": req.purpose,
            "task": req.task,
            "current_point": req.current_point,
            "depth": depth.value,
        }
    )

    try:
        results = await container.orchestrator.run_full_optimization_cycle(
            role=req.role,
            purpose=req.purpose,
            task=req.task,
            current_point=req.current_point,
            initial_depth=depth,
        )

        context_packet = results["context_packet"]
        agent_results = results["agent_results"]
        perf_model = results["performance_model"]

        # Present across 9 Omnipod windows
        windows_view = OmnipodPresenter.present_all_windows(context_packet, agent_results)
        windows_dict = {
            win.value: {
                "l1_summary": view.l1_summary,
                "active_particles": view.active_particles,
                "entangled_links": view.entangled_links,
            }
            for win, view in windows_view.items()
        }

        # Broadcast cycle completed with summarized findings
        await container.stream_bridge.broadcast(
            EventType.CYCLE_COMPLETED,
            {
                "measured_improvement": results.get("summary", {}).get("measured_improvement", 0),
                "codified_principle": results.get("summary", {}).get("codified_principle", ""),
                "diagnostic_accuracy": perf_model.diagnostic_accuracy,
                "agent_count": len(agent_results),
            }
        )

        return {
            "cycle_id": results.get("cycle_id"),
            "summary": results.get("summary"),
            "context_packet": context_packet.model_dump(),
            "performance_model": perf_model.model_dump(),
            "windows": windows_dict,
            "agent_count": len(agent_results),
        }
    except Exception as e:
        logger.exception("Error executing optimization cycle: %s", str(e))
        await container.stream_bridge.broadcast(
            EventType.ERROR_ALERT,
            {"error": str(e), "task": req.task}
        )
        raise HTTPException(status_code=500, detail=str(e))


# ── Context Resolution API ─────────────────────────────────────────────────

class ContextResolveRequest(BaseModel):
    role: str
    purpose: str
    task: str
    current_point: str
    depth: str = "D1"
    breadth_limit: int = 5
    allowed_domains: Optional[List[str]] = None

@app.post("/api/context/resolve")
async def resolve_context(req: ContextResolveRequest):
    domains = [DomainType(d) for d in req.allowed_domains] if req.allowed_domains else None
    scope = ScopeContract(
        depth=ScopeDepth(req.depth),
        breadth_limit=req.breadth_limit,
        allowed_domains=domains or [DomainType.OPERATIONAL, DomainType.DATA, DomainType.TOOLS],
    )
    packet = container.context_engine.resolve_context(
        role=req.role,
        purpose=req.purpose,
        task=req.task,
        current_point=req.current_point,
        scope=scope,
    )

    await container.stream_bridge.broadcast(
        EventType.CONTEXT_RESOLVED,
        {
            "context_id": packet.context_id,
            "target_node": packet.target_node,
            "nodes_count": len(packet.graph_nodes),
            "relations_count": len(packet.graph_relations),
        }
    )

    return packet.model_dump()


# ── Knowledge Graph Query Endpoints ────────────────────────────────────────

@app.get("/api/graph/nodes")
async def get_nodes(domain: Optional[str] = None):
    nodes = container.graph_store.get_all_nodes()
    if domain:
        nodes = [n for n in nodes if n.domain.value.lower() == domain.lower()]
    return [n.model_dump() for n in nodes]

@app.get("/api/graph/edges")
async def get_edges():
    edges = container.graph_store.get_all_edges()
    return [e.model_dump() for e in edges]
