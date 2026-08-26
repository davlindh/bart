# 01 Feature Specification: Omnipod & Team Dynamics Optimizer

## Executive Summary & Design Vision

The **Omnipod & Team Dynamics Optimizer** is an autonomous, self-improving, multi-agent cognitive architecture built on top of the **Google Antigravity SDK**, **Model Context Protocol (MCP)**, **Dynamic Context Resolution Engine**, and **Universal Entity-Relationship Knowledge Graph (ERD)**.

The framework bridges high-level strategic organizational perspectives with granular operational telemetry. Rather than treating information as static, monolithic text blocks, the system models all data as an **interconnected semantic knowledge graph of discrete entities and typed relationships**.

A core architectural principle of this system is:
> **The Information Graph is broad, rich, and relatively stable. The Context Layer is narrow, dynamic, and task-driven.**

By utilizing dynamic, task-oriented sub-graph extraction, agents and human stakeholders receive precisely calibrated context packets formatted across multiple presentation tiers (Human L1 summary, Human L2 detailed evidence, Machine JSON context packets, and Predictive Next-Node navigation).

---

## Architectural Taxonomy & The 8 Core Layers

The architecture synthesizes the 4 foundational system diagrams and conversational specifications into 8 synchronized layers:

```mermaid
graph TB
    subgraph L1["Layer 1: Perspective Windows (Omnipod Core)"]
        W1[Contextualization] --- W2[Matching] --- W3[Evaluation]
        W4[Resource Allocation] --- W5[Financial Mgt] --- W6[Personnel Mgt]
        W7[Communication] --- W8[Innovation & Tech] --- W9[Adaptive Insights]
    end

    subgraph L2["Layer 2: Functional Domains & Distance Topology"]
        D1[Trust Domain]
        D2[Knowledge Domain]
        D3[Tools Domain]
        D4[Exchange Domain]
        D5[Interactional Interface]
        D6[Operational Domain]
    end

    subgraph L3["Layer 3: Collaboration Structure & Persona Matrix"]
        P1[User A: Verifier & Creator]
        P2[User B: Data Manager & Logistics]
        P3[User C: Security & Infra]
        P4[User D: Curator & Data Steward]
    end

    subgraph L4["Layer 4: Information Catalogs & Data Lifecycle"]
        C1["/trust"]
        C2["/knowledge"]
        C3["/data"]
        C4["/operational"]
        LC[Ingest -> Categorize -> Store -> Share -> Use -> Feedback -> Improve]
    end

    subgraph L5["Layer 5: Dynamic Context Resolution Engine"]
        CR1[Candidate Fetcher] --> CR2[Relevance & Auth Filter]
        CR2 --> CR3[8D Relevance Weighter]
        CR3 --> CR4[Scope Bounding D0-D3]
        CR4 --> CR5[Context Packet Generator]
    end

    subgraph L6["Layer 6: Universal 12-Agent System & Extended Specialists"]
        AG1[Observer] --> AG2[Diagnostician]
        AG2 --> AG3[Team Architect]
        AG3 --> AG4[Role Transition]
        AG4 --> AG5[Collaboration]
        AG5 --> AG6[Wellbeing]
        AG6 --> AG7[AI Ethics]
        AG7 --> AG12[Experiment Agent]
        AG12 --> AG9[Measurement Agent]
        AG9 --> AG10[Learning Agent]
        AG10 --> AG11[Orchestrator]
        AG11 --> AG8[Meta-Learning Agent]
    end

    subgraph L7["Layer 7: Universal ERD Knowledge Graph"]
        ERD[(Universal ERD Schema: Org -> Team -> Person -> Role -> Capability -> Assignment -> Observation -> Diagnosis -> Intervention -> Experiment -> Measurement -> Learning -> Knowledge)]
    end

    subgraph L8["Layer 8: Dual Self-Improving Feedback Loops"]
        OperationalLoop[Team Dynamics Loop: Signal -> Diagnosis -> Intervention -> Measurement -> Learning -> New Signal]
        MetaLoop[Meta-Learning Loop: Agent Performance Telemetry -> Gap Analysis -> Prompt/Rule Calibration -> Model Weight Tuning]
    end

    L1 --> L5
    L2 --> L7
    L3 --> L5
    L4 --> L7
    L5 --> L6
    L6 --> L7
    L6 --> L8
```

---

## Omnipotent AI Configurations & Protocol Matrix

To ensure omnipotence and resilience, the agent layer is configured according to the **Google Antigravity SDK Protocol Standard**:

1. **Model Backbone**: Defaults to Gemini 3.7 Flash (`gemini-3.7-flash`) with optional Gemini Priority Inference (`service_tier=types.ServiceTier.PRIORITY`) for low-latency operational cycles.
2. **Behavioral Mode**: Agents operate in `AgentBehavior.AUTONOMOUS` mode for closed-loop analysis, transitioning dynamically to `AgentBehavior.INTERACTIVE` when user feedback, confirmation, or stakeholder sign-off is required.
3. **Multi-Agent Hierarchies**: Orchestrated using nested `SubagentConfig` hierarchies with strict `max_subagent_depth` controls and granular `allowed_subagents` allowlists.
4. **Structured Protocol Enforcements**: All agent-to-agent exchanges and tool invocations produce Pydantic-validated JSON payloads (`response_schema`), guaranteeing deterministic contract fulfillment.
5. **Tool & Context Decoupling**: Agents interact with the knowledge graph and external platforms exclusively via **Model Context Protocol (MCP)** servers (`graph_server`, `context_server`, `team_ops_server`).

---

## Standardized Agent Lifecycle: The 6-Function Contract

Every agent in the ecosystem implements the canonical six-function interface:

```python
class StandardAgentLifecycle:
    async def observe(self, context_packet: ContextPacket) -> list[Observation]: ...
    async def analyze(self, observations: list[Observation]) -> AnalysisResult: ...
    async def identify(self, analysis: AnalysisResult) -> list[IdentifiedIssue]: ...
    async def propose(self, issues: list[IdentifiedIssue]) -> list[Proposal]: ...
    async def act(self, proposals: list[Proposal]) -> list[Action]: ...
    async def evaluate(self, actions: list[Action]) -> EvaluationSummary: ...
```

---

## Feature Specifications by Functional Domain

### 1. Dynamic Context Engine
- **Task-Oriented Subgraph Extraction**: Resolves relevant subgraphs given `(Role, Purpose, Task, Current Node, Scope)`.
- **8-Dimensional Weighting**: Computes weighted scores across Task Relevance, Scope Distance, Recency, Role Alignment, Domain Matching, Data Quality, Permissions, and Security/Sensitivity.
- **Dynamic Scope Expansion**: Automatically evaluates stop conditions and supports progressive expansion from `D0` (focal point) to `D1` (direct neighbors), `D2` (extended context), and `D3` (cross-domain systemic context).

### 2. Team Dynamics & Organizational Optimization
- **Signal Aggregation**: Continuously monitors communication velocity, decision turnaround times, role ambiguities, sprint friction, workload distribution, and psychological safety.
- **Root-Cause Diagnostics**: Maps surface symptoms (e.g., "Reporting delay") to structural root causes (e.g., "Data pipeline failure + Unclear decision mandate").
- **Controlled Experimentation**: Automatically generates hypotheses, baseline metrics, test population cohorts, and timeboxes before full-scale rollouts.

### 3. Self-Improving Meta-Learning
- **Agent Performance Auditing**: Evaluates diagnostic accuracy, false positive rates, scope adequacy, and intervention efficacy across loop executions.
- **Adaptive Rule Generation**: Updates routing heuristics, relevance weights, and prompt strategies without human intervention.
