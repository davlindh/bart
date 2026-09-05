---
name: contextual-precognition
description: Intentional trajectory projection, proactive skill dispatch, pre-emptive friction shielding, and durable SQLite WAL self-preservation across project sessions and process boundaries. Use when declaring project goals, predicting multi-step actions, pre-fetching scoped context packets, or checkpointing Universal ERD state.
---

# Contextual Pre-Cognition & Self-Preservation Skill

## Overview
The `contextual-precognition` skill elevates autonomous agents from reactive event handlers to proactive, goal-directed systems. Powered by `PreCognitiveEngine` and `GraphPersistenceBridge`, this subsystem calculates multi-step forward trajectories ($\tau = [N_{t+1}, N_{t+2}, \dots]$) along the Universal ERD graph, pre-fetches scoped `ContextPacket` slices, anticipates operational/financial bottlenecks, and checkpoints project states into crash-resilient SQLite WAL storage.

---

## Tool Reference & Capabilities

| Capability / Action | Primary Purpose | Required Parameters | Optional Parameters |
| :--- | :--- | :--- | :--- |
| `project_trajectory` | Compute lookahead trajectory & proactive skill needs | `intent`, `current_node_id`, `graph` | `role`, `observations`, `horizon_steps` |
| `save_checkpoint` | Atomically persist full project state & ERD to SQLite WAL | `project_id`, `erd_graph` | `intent`, `agent_states`, `checkpoint_id` |
| `restore_checkpoint` | Rehydrate project, ERD topology, and intent into active session | `checkpoint_id` or `project_id` | None |
| `list_checkpoints` | Catalog all persisted state checkpoints with SHA-256 checksums | None | `project_id` |
| `detect_friction` | Pre-emptively flag overtime, role gaps, or tax discrepancies | `observations`, `predicted_nodes` | `thresholds` |

---

## Standard Step-by-Step Workflow

### Step 1: Declare Intentional Mandate
Define an explicit `ProjectIntent` with desired outcomes and constraints rather than raw prompts:

```python
from src.core.precognition import ProjectIntent, IntentStatus
from src.core.types import Domain

intent = ProjectIntent(
    intent_id="intent_vmb_q3",
    project_id="PRJ-101",
    mandate="Optimera VMB-marginaler och säkra projekttillstånd i sandlåda före revision",
    desired_state={"target_savings_sek": 45000.0, "compliance_audit": "PASSED"},
    target_kpis={"gross_margin_boost_pct": 12.5},
    allowed_domains=[Domain.EXCHANGE, Domain.OPERATIONAL, Domain.TRUST],
    horizon_steps=3,
    status=IntentStatus.ACTIVE,
)
```

---

### Step 2: Project Cognitive Trajectory & Pre-fetch Context
Execute forward lookahead along the Universal ERD to predict future steps and pre-dispatch required skills:

```python
from src.context_engine.precognition import PreCognitiveEngine

trajectory = PreCognitiveEngine.project_trajectory(
    intent=intent,
    current_node_id="cust_1",
    graph=erd_graph,
    role="CFO"
)

# Inspect proactive skill dispatches
for skill in trajectory.predicted_skills:
    print(f"PRE-DISPATCH: {skill.skill_name} (lead time: {skill.lead_time_steps} steps)")
    print(f"  Reason: {skill.reasoning}")

# Inspect pre-fetched context packets
for pkt in trajectory.prefetched_context_packets:
    print(f"READY PACKET: {pkt.role} -> {pkt.task} (Scope: {pkt.scope.value})")
```

---

### Step 3: Pre-empt Friction and Bottlenecks
Shield the team or process from predicted anomalies before they impact delivery:

```python
for friction in trajectory.anticipated_frictions:
    print(f"ALERT [{friction.severity.value}]: {friction.predicted_issue}")
    print(f"  Root Factor: {friction.root_factor}")
    print(f"  Countermeasure: {friction.preventive_action}")
```

---

### Step 4: Self-Preservation & Checkpoint Persistence
Atomically commit project state to SQLite WAL storage with SHA-256 integrity verification:

```python
from src.graph.persistence_bridge import GraphPersistenceBridge

bridge = GraphPersistenceBridge()
checkpoint = bridge.save_checkpoint(
    project_id="PRJ-101",
    erd_graph=erd_graph,
    intent=intent,
    agent_states={"TaxOptimizationAgent": {"last_savings_found": 3200.0}}
)

print(f"CHECKPOINT SAVED: {checkpoint.checkpoint_id} (SHA256: {checkpoint.checksum_sha256[:12]}...)")
```

---

### Step 5: Process Boundary Crossing & Recovery
Rehydrate project state in a new process, agent thread, or following a restart:

```python
restored = bridge.restore_checkpoint(project_id="PRJ-101")
active_erd = restored["erd_graph"]
active_intent = restored["intent"]
print(f"REHYDRATED: {len(active_erd.nodes)} nodes recovered with zero data loss.")
```

---

## Proactive Skill Matrix

* **`disk-persistence`**: Dispatched whenever multi-step state transitions or session branching are anticipated.
* **`tax-optimization`**: Dispatched when invoice lines, used goods (VMB), or RUT labor cost opportunities appear on the path.
* **`role-transition`**: Dispatched when organizational mandates, decision owners, or RACI changes occur.
* **`sandbox-execution`**: Dispatched when complex calculations, Python simulations, or ML tensors need execution.
* **`worker-orchestration`**: Dispatched when background monitoring, periodic audit loops, or cron schedules are planned.
