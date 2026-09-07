# OMNIFRAMEZ COLLECTIVE

## Contextual Operating System for Shared Intelligence

**Whitepaper / Product Constitution v0.1**

---

# 0. Product Declaration

**Product name:** Omniframez Collective  
**Category:** Contextual Decision & Collective Intelligence System  
**Core primitive:** Context  
**Core navigation primitive:** Portal  
**Core organizational primitive:** Cognitive Bottleneck  
**Core epistemic primitive:** Claim ↔ Evidence  
**Core developmental primitive:** Take → Branch → Merge  
**Core action primitive:** Cognitive Action  
**Core learning primitive:** Outcome → Belief Update

## Product thesis

Organizations do not primarily suffer from a lack of tasks, documents, messages or AI-generated answers.

They frequently suffer because:

- the active goal is unclear,
- different people operate from different contexts,
- assumptions remain implicit,
- uncertainty is not assigned,
- downstream work begins before upstream uncertainty is resolved,
- evidence is disconnected from decisions,
- decisions lose their rationale over time,
- learning disappears when people, tools or projects change.

Omniframez Collective makes these relationships explicit.

The system transforms:

**Conversation → Context → Problem Frame → Bottleneck → Evidence → Decision → Action → Outcome → Learning**

and makes the transformation collaboratively observable.

---

# 1. Fundamental Product Principle

The platform shall not primarily organize files or tasks.

It shall organize:

**what matters, why it matters, what is uncertain, what blocks progress, who can resolve it, what evidence is required and what becomes possible when it is resolved.**

The canonical organizational chain is:

**Goal  
→ Shared Context  
→ Decision  
→ Problem Frame  
→ Cognitive Bottleneck  
→ Cognitive Action  
→ Evidence  
→ Resolution  
→ Decision Readiness  
→ World Action  
→ Outcome  
→ Learning  
→ New Context**

Tasks remain supported, but exist underneath this semantic layer.

---

# 2. Source-Derived Foundations

The existing Omniframez material establishes several principles that become normative in Collective.

## 2.1 Specialized domains

Contextualization, Matching, Evaluation, Resource Allocation, Financial Management, Personnel Management, Communication, Innovation and Adaptive Insights each have distinct purposes and outputs.

Collective therefore does not collapse all reasoning into one universal agent.

It provides a shared context layer through which specialized domains operate.

## 2.2 Adaptive contextualization

Information is not permanently equally relevant.

Meta-attributes, user intent, temporal relevance, domain specificity and interaction state affect how information is interpreted.

Therefore:

**Stored Information ≠ Active Context**

## 2.3 Modular domains

Domains must consist of reusable components whose configuration can vary by need and abstraction level.

Therefore:

**Component definitions are reusable.  
Contextual instances are local.**

## 2.4 Integration before synthesis

Information from different windows is first integrated into a coherent context.

Only afterwards should the system synthesize recommendations.

Therefore:

**Integration ≠ Recommendation**

This separation becomes a hard architectural principle.

---

# 3. New Product Decisions

The following are additions introduced by Omniframez Collective rather than specifications already present in the source material:

- immutable Takes,
- branching and merging,
- contribution provenance,
- Utility Ledger,
- Cognitive Action Selection,
- Cognitive Bottleneck management,
- Decision Readiness,
- Reality Gate,
- component protocol,
- interoperability layer,
- team orchestration.

---

# 4. Product Vocabulary

## Workspace

A shared organizational environment.

Examples:

- company,
- product initiative,
- customer engagement,
- R&D programme.

## Context

The currently relevant configuration of:

- actor,
- goal,
- time,
- scope,
- constraints,
- evidence,
- relationships.

## Domain

A reusable semantic perspective with a defined purpose.

Examples:

- Need,
- Capability,
- Evidence,
- Finance,
- Negotiation,
- R&D.

## Contextual Particle

An information object currently interpreted inside a Domain.

Any sufficiently important particle may be zoomed into and become a new local Domain.

## Portal

A contextual observational interface into a Domain or Particle.

## Entanglement

A context-dependent semantic relation.

It is a graph relation, not a claim of physical quantum computation.

## Take

An immutable snapshot of the relevant state of collective reasoning at a particular moment.

## Branch

A new development path originating from a Take.

## Merge

An explicit reconciliation of compatible contributions from multiple Branches.

## Cognitive Bottleneck

A constraint preventing meaningful progress in understanding, decision or action.

## Cognitive Action

An operation intended to improve understanding or decision readiness.

Examples:

ASK, VERIFY, REFRAME, COMPARE, EXPERIMENT, DECIDE.

---

# 5. The Take — Collective's Development Primitive

The user must be able to press:

**FREEZE TAKE**

This creates an immutable object.

```text
Take
├── take_id
├── workspace_id
├── parent_take_id?
├── branch_id
├── created_by
├── created_at
├── active_goal
├── active_context
├── problem_frame
├── domains[]
├── contextual_particles[]
├── relations[]
├── claims[]
├── evidence[]
├── assumptions[]
├── unknowns[]
├── bottlenecks[]
├── alternatives[]
├── decisions[]
├── cognitive_actions[]
├── contribution_records[]
├── model_versions[]
├── policy_versions[]
└── integrity_hash
```

A Take means:

> This was the collective state we were prepared to stand behind at this point in time.

It must never silently mutate.

---

# 6. Branching

Any permitted user may create:

**Branch from Take**

Example:

```text
Take 42
│
├── Branch A
│   └── "Automation-first"
│
├── Branch B
│   └── "Human augmentation"
│
└── Branch C
    └── "Process change without new technology"
```

Each branch preserves:

- origin,
- contribution lineage,
- changed assumptions,
- changed claims,
- changed relations,
- changed components,
- evidence introduced,
- decisions produced.

This enables alternative futures to coexist without destroying the previous state.

---

# 7. Merge

Branches shall not overwrite each other.

A Merge creates a new Take.

```text
Take 42
├── Branch A
└── Branch B
       ↓
    Merge Review
       ↓
    Take 43
```

Merge must expose:

- agreements,
- semantic conflicts,
- incompatible assumptions,
- evidence differences,
- object additions,
- object deletions,
- changed weights,
- unresolved disagreements.

No material contradiction may disappear automatically.

---

# 8. Contribution & Utility Ledger

The system shall attribute contributions.

It must **not automatically equate contribution attribution with legal equity ownership**.

Legal ownership, shares, compensation, IP transfer or securities rights require explicit contracts outside the inference engine.

The platform can, however, maintain a rigorous ledger of contribution and realized utility.

## Contribution

```text
Contribution
├── contribution_id
├── actor_id
├── take_id
├── branch_id
├── contribution_type
├── target_object
├── before_state
├── after_state
├── submitted_at
├── accepted_at?
├── accepted_by?
├── provenance
└── status
```

Contribution types:

- new evidence,
- domain definition,
- contextual relation,
- problem reframing,
- claim,
- counter-claim,
- experiment,
- implementation,
- correction,
- synthesis,
- decision,
- reusable component.

---

# 9. Utility Attribution

Utility shall preferably be attributed after observable outcomes, not merely at submission time.

Conceptually:

**AttributedUtility = Contribution × CausalRelevance × Reuse × OutcomeImpact × Confidence**

Possible dimensions:

- direct contribution,
- information gain,
- decision improvement,
- downstream work unlocked,
- component reuse,
- avoided cost,
- realized commercial value,
- learning value.

The ledger may issue:

**Utility Credits**

as accounting units.

They may be used for:

- reputation,
- recognition,
- internal rewards,
- contributor ranking,
- contractual revenue-sharing calculations,
- governance rights where separately agreed.

They are not automatically financial securities or legal ownership.

---

# 10. Utility Graph

Utility is not only attached to the final implementation.

Example:

```text
Observation
   ↓
Problem Reframe
   ↓
Critical Experiment
   ↓
Rejected Feature
   ↓
€500k avoided investment
```

The person who identified the reframing may have created more utility than someone who wrote code that was never needed.

Collective shall therefore preserve upstream causal contribution.

---

# 11. Reuse Multiplier

Reusable components create value beyond their original context.

```text
ReusableComponent
├── component_id
├── originating_contribution
├── original_domain
├── reuse_count
├── reuse_contexts[]
├── downstream_outcomes[]
└── attributed_utility
```

Conceptually:

**UtilityContribution increases when independently useful reuse occurs.**

This creates an incentive to build:

- reusable schemas,
- prompts,
- domain components,
- evidence adapters,
- reasoning protocols,

rather than one-off artifacts.

---

# 12. Domain Contract

Every reusable Domain must satisfy a standard contract.

```text
DomainDefinition
├── domain_id
├── name
├── purpose
├── activation_conditions
├── required_context
├── contextual_components[]
├── contextual_particle_types[]
├── allowed_relations[]
├── input_contract
├── output_contract
├── cognitive_actions[]
├── evidence_requirements[]
├── governance_rules[]
├── exit_conditions[]
└── version
```

A domain therefore always explains:

**WHY it exists.  
WHAT it receives.  
HOW it interprets.  
WHAT it produces.  
WHEN it should activate.  
WHEN it should stop.**

---

# 13. Component Contract

```text
ComponentDefinition
├── component_id
├── name
├── semantic_type
├── purpose
├── schema
├── dependencies[]
├── compatible_domains[]
├── input_types[]
├── output_types[]
├── version
└── provenance
```

Components must be reusable across domains wherever their meaning remains invariant.

Example:

`EvidenceRail`

can support:

- Commercial,
- R&D,
- Legal,
- Investment,
- Negotiation.

The visual component is reused.

Its contextual projection changes.

---

# 14. The Canonical Data Model

## Identity

```text
Organization
Actor
Identity
Role
Authority
Workspace
```

## Context

```text
Goal
Context
ContextCandidate
ContextMembership
ContextStack
Scope
Domain
Portal
ContextualParticle
Relation
RelationContextWeight
```

## Epistemic

```text
Observation
DerivedFeature
Evidence
Provenance
Claim
ClaimDependency
EvidenceClaimLink
Assumption
Unknown
InformationGap
ConfidenceState
VerificationRequirement
```

## Reasoning

```text
ReasoningSession
ReasoningState
ProblemFrame
ProblemFrameVersion
CognitiveBottleneck
CognitiveAction
Alternative
AlternativeAssessment
CounterAnalysis
RealityGate
StopAssessment
```

## Decision

```text
Decision
DecisionAlternative
DecisionCriterion
DecisionStakeholder
DecisionGate
Recommendation
Commitment
Action
OutcomeObservation
LearningEvent
```

## Collective development

```text
Take
Branch
Merge
Contribution
ContributionRelation
UtilityAttribution
UtilityCredit
ComponentDefinition
DomainDefinition
```

## Commercial

```text
Customer
Need
Gap
Capability
SolutionPattern
OfferableUnit
Offering
ValueProposition
Signal
PerceptionState
Transaction
Delivery
Outcome
ValueRealization
```

## R&D

```text
Friction
NeedCluster
InnovationSignal
FutureCapability
R&DThesis
Hypothesis
Experiment
ExperimentResult
InvestmentGate
R&DProject
```

## Portfolio / Futures

```text
CapabilityPortfolio
StrategicOption
CapitalTranche
FutureDriver
DriverInteraction
FutureContext
FutureNeed
FutureRequiredCapability
FutureTrigger
ScenarioCapabilityAssessment
```

---

# 15. Canonical Relation Model

All graph-compatible objects may participate in:

```text
REQUIRES
ENABLES
SUPPORTS
CONTRADICTS
CAUSES
AMPLIFIES
REDUCES
DEPENDS_ON
CONSTRAINS
PRECEDES
FOLLOWS
SUBSTITUTES_FOR
ALTERNATIVE_TO
ADDRESSES
PRODUCES
RESOLVES
TRIGGERS
SUPERSEDES
DERIVED_FROM
BRANCHED_FROM
MERGED_FROM
CONTRIBUTED_BY
VALIDATED_BY
```

Every relation may contain:

```text
context_id
weight
confidence
provenance
valid_from
valid_to
```

Therefore:

**Relation(A,B) ≠ Relation(A,B | Context)**

---

# 16. Epistemic Types

Every meaningful information object must be classifiable as:

```text
OBSERVED
DECLARED
DERIVED
INFERRED
DECIDED
SIMULATED
```

This is mandatory.

A simulation must never silently become observed fact.

An inference must never overwrite an observation.

---

# 17. System Architecture

```text
┌─────────────────────────────────────────────────────┐
│ EXPERIENCE LAYER                                    │
│ Context Bar • Portal Canvas • Bottleneck Board      │
│ Evidence Rail • Branch/Take • Decision Workspace    │
└─────────────────────────┬───────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────┐
│ COLLECTIVE ORCHESTRATION                            │
│ Shared Context • Ownership • Cognitive Actions      │
│ Decision Readiness • Reality Gate                   │
└─────────────────────────┬───────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────┐
│ METACOGNITIVE EXECUTION KERNEL                      │
│ Orient • Understand • Challenge • Clarify • Frame   │
│ Generate • Analyze • Counter • Verify • Decide      │
│ Observe • Learn                                     │
└─────────────────────────┬───────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────┐
│ CONTEXT ENGINE                                      │
│ Domains • Components • Particles • Relations        │
│ Context weights • Portal selection                  │
└───────────────┬───────────────────────┬─────────────┘
                │                       │
┌───────────────▼──────────┐ ┌──────────▼─────────────┐
│ EPISTEMIC ENGINE         │ │ DOMAIN MODULES         │
│ Claims • Evidence        │ │ Commercial • R&D       │
│ Confidence • Provenance  │ │ Finance • Legal etc.   │
└───────────────┬──────────┘ └──────────┬─────────────┘
                │                       │
┌───────────────▼───────────────────────▼─────────────┐
│ TAKE / BRANCH / CONTRIBUTION GRAPH                  │
│ Versioning • Attribution • Utility • Audit          │
└─────────────────────────┬───────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────┐
│ DATA & EVENT LAYER                                  │
│ Relational DB • Graph • Event Store • Analytics     │
└─────────────────────────┬───────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────┐
│ CONNECTORS                                           │
│ Documents • CRM • ERP • Analytics • APIs • Agents   │
└─────────────────────────────────────────────────────┘
```

---

# 18. Storage Architecture

## Relational store

Authoritative objects:

- identities,
- permissions,
- decisions,
- transactions,
- contributions,
- Takes,
- contracts,
- governance.

## Graph projection

Used for:

- Context relationships,
- claim dependencies,
- bottleneck dependencies,
- capability graphs,
- contribution lineage.

## Append-only event store

Used for:

- state transitions,
- reasoning events,
- Take creation,
- contribution history,
- auditability.

## Analytical store

Used for:

- patterns,
- historical outcomes,
- utility measurement,
- portfolio analysis.

---

# 19. Compatibility Layer

The original material describes modularity and integration but does not prescribe concrete wire protocols.

Collective therefore proposes an open compatibility layer.

## Data interchange

- JSON
- JSON Schema
- CSV where tabular interchange is sufficient
- JSON-LD where semantic graph portability is required

## APIs

- HTTPS
- REST
- OpenAPI-described interfaces
- GraphQL optionally for contextual graph queries
- Webhooks for asynchronous integration

## Events

- CloudEvents-compatible event envelopes
- immutable event IDs
- UTC/ISO-8601 timestamps
- idempotency keys

## Identity / access

- OAuth 2-style delegated authorization
- OpenID Connect-style identity federation
- SAML where enterprise federation requires it
- SCIM-style provisioning where appropriate

Exact versions must be selected and verified at implementation time.

## Provenance

Use a W3C-PROV-inspired structure:

**Entity ← Activity ← Agent**

for contribution and evidence lineage.

## Observability

OpenTelemetry-compatible:

- traces,
- metrics,
- logs.

## Semantic export

Where interoperability requires it:

- RDF-compatible triples,
- JSON-LD contexts,
- explicit schemas and vocabulary versioning.

## Agent interface

Agents shall consume and produce structured envelopes rather than rely exclusively on free text.

Vendor-specific agent protocols may be connected through adapters rather than becoming the canonical internal representation.

---

# 20. Integration Principle

No external system becomes the Omniframez model.

Instead:

```text
External Source
      ↓
Adapter
      ↓
Canonical Event / Entity / Evidence
      ↓
Context Engine
```

This protects the architecture from vendor lock-in.

---

# 21. Functional Requirements

## FR-001 Context

The system SHALL allow a user or agent to establish an Active Context.

## FR-002 Context Candidates

The system SHALL support several competing Context Candidates simultaneously.

## FR-003 Domain Activation

The system SHALL activate specialized Domains according to context and purpose.

## FR-004 Zoom

Any qualifying Contextual Particle SHALL be capable of becoming a new local Domain.

## FR-005 Bottlenecks

The system SHALL represent Cognitive Bottlenecks as first-class entities.

## FR-006 Ownership

Each material Bottleneck SHALL support accountable owner, resolution owner, evidence owner and decision owner.

## FR-007 Cognitive Actions

The system SHALL distinguish Cognitive Actions from World Actions.

## FR-008 Evidence

Every material inference SHALL support evidence, provenance and confidence.

## FR-009 Contradictions

Contradictory evidence SHALL remain visible.

## FR-010 Takes

Users SHALL be able to freeze immutable Takes.

## FR-011 Branch

Users SHALL be able to branch from any authorized Take.

## FR-012 Diff

The system SHALL display semantic differences between Takes and Branches.

## FR-013 Merge

Users SHALL be able to merge compatible contributions while retaining unresolved conflicts.

## FR-014 Attribution

Every accepted contribution SHALL preserve authorship and lineage.

## FR-015 Utility

The system SHALL support post-outcome utility attribution.

## FR-016 Reuse

Reusable Domains and Components SHALL preserve origin and reuse attribution.

## FR-017 Decision Readiness

The system SHALL represent whether a Decision is epistemically and operationally ready.

## FR-018 Reality Gate

The system SHALL be capable of recommending external observation rather than continued reasoning.

## FR-019 Learning

Outcome observations SHALL be able to update Claims, Context Weights and Bottleneck States.

## FR-020 Export

Users SHALL be able to export their canonical objects and provenance through documented formats.

---

# 22. Non-functional Requirements

## NFR-001 Traceability

Every consequential system-generated recommendation must be reconstructable.

## NFR-002 Versionability

Schemas, prompts, policies and models must be versioned.

## NFR-003 Idempotency

Repeated integration events must not silently duplicate canonical state.

## NFR-004 Portability

Canonical data must not depend on one AI provider.

## NFR-005 Explainability

Users must be able to inspect:

**Why this context?  
Why this bottleneck?  
Why this action?  
Why this recommendation?**

## NFR-006 Security

Workspace and object access must support least privilege.

## NFR-007 Temporal correctness

Historical Takes must remain interpretable using their original versions.

## NFR-008 Human override

Authorized humans must be able to reject, reframe or supersede AI-generated interpretations.

## NFR-009 Graceful incompleteness

The system must operate with partial information.

Unknown must remain a valid state.

## NFR-010 Reusability

A reusable component must not depend on one specific UI surface.

---

# 23. Canonical Prompt Envelope

All specialized prompts shall receive a standard contextual envelope.

```text
CONTEXT
- Actor
- Goal
- Active Context
- Time
- Scope
- Constraints

EPISTEMIC STATE
- Known
- Declared
- Assumed
- Unknown
- Needs Verification
- Contradictions

CURRENT REASONING STATE
- ORIENT / UNDERSTAND / ...

ACTIVE BOTTLENECK
- type
- severity
- decision impact

AVAILABLE DOMAINS
- relevant reusable domains

GOVERNANCE
- permissions
- autonomy
- review requirements

TASK
- cognitive operation to perform

OUTPUT CONTRACT
- structured objects to create/update

WHY
- decision or uncertainty this operation is intended to improve
```

---

# 24. Prompt Sequence — ORIENT

**Expression**

> Determine the minimum context required to interpret the input. Identify actor, goal candidates, temporal scope, relevant constraints and candidate domains. Do not solve the presented question yet. Preserve ambiguity where multiple contexts remain plausible.

**What:** establishes Context.

**How:** generates weighted Context Candidates.

**Why:** prevents premature interpretation.

**Output**

```text
OrientationState
ContextCandidates[]
CriticalMissingContext[]
```

---

# 25. UNDERSTAND

> Separate the explicit request from the underlying goal, candidate decision and desired outcome. Do not assume they are identical. Preserve multiple plausible interpretations where evidence does not discriminate between them.

**Why:** Query ≠ Goal ≠ Decision.

---

# 26. CHALLENGE

> Inspect the current frame for hidden assumptions, premature solutions, false dichotomies, missing variables, symptom-as-problem errors and competing causal explanations. Challenge only premises that materially affect the goal or decision.

**Why:** avoid optimizing inside the wrong problem.

---

# 27. CLARIFY

> Classify relevant information as Observed, Declared, Verified, Derived, Assumed, Unknown or Needs Verification. Rank missing information by expected impact on the decision. Ask the user only when the user is the best available source and the information is decision-relevant.

**Why:** reduce unnecessary questioning.

---

# 28. FRAME

> Construct the smallest Problem Frame sufficient for meaningful analysis. Include goal, actor, decision, current state, target state, scope, constraints, time horizon, critical assumptions, unknowns and success criteria.

**Why:** analysis becomes meaningful only after the problem is sufficiently defined.

---

# 29. GENERATE

> Generate genuinely different mechanisms for reaching the desired outcome. Include status quo where relevant. Do not treat different vendors or implementations of the same mechanism as fundamentally different alternatives.

**Why:** avoid solution lock-in.

---

# 30. ANALYZE

> Evaluate each eligible alternative across expected benefit, cost, risk, dependencies, reversibility, time-to-value, opportunity cost, evidence strength and downside if wrong. Keep dimensions separate unless the decision explicitly defines weights.

**Why:** avoid false precision.

---

# 31. COUNTER

> Identify the strongest argument against the currently leading alternative. Find the weakest critical assumption, contradictory evidence and strongest alternative explanation. Revise confidence if warranted.

**Why:** fight premature convergence.

---

# 32. VERIFY

> Determine which facts, assumptions or claims require reality-based verification given uncertainty, consequence, irreversibility and exposure. Select the cheapest valid verification method capable of changing the decision.

**Why:** reasoning must eventually meet reality.

---

# 33. BOTTLENECK

> Identify the smallest unresolved constraint currently limiting progress toward the active goal or decision. Distinguish root bottleneck from downstream symptoms. Estimate unblock value and identify the actor or capability required to resolve it.

**Why:** organize work around what unlocks progress.

---

# 34. COGNITIVE ACTION

> Generate eligible Cognitive Actions for the active bottleneck. Exclude actions whose prerequisites are not met. Prefer the action with the greatest combined information gain, context improvement and decision value relative to cost, delay and risk.

**Possible output**

```text
ASK
VERIFY
REFRAME
GENERATE
COMPARE
COUNTER
EXPERIMENT
OPEN_PORTAL
ACTIVATE_MODULE
DECIDE
ESCALATE
STOP
```

---

# 35. REALITY GATE

> Compare the expected value of additional reasoning against external evidence. If measurement, experiment, document inspection, customer observation or expert review is more likely to change the decision than further inference, stop expanding the reasoning and recommend the appropriate reality action.

---

# 36. DECIDE

> Determine whether the decision is sufficiently ready. State the recommended alternative, accepted trade-offs, critical assumptions, residual uncertainty, what could change the decision and any verification still required. Do not imply higher certainty than the evidence supports.

---

# 37. ACT

> Translate the approved decision into the smallest concrete World Action consistent with governance, authority and reversibility requirements. Preserve the relationship to the decision and expected outcome.

---

# 38. OBSERVE

> Compare expected and observed outcomes. Keep delivery, adoption, capability change, outcome and value realization distinct.

---

# 39. LEARN

> Identify which prior assumption or claim made the observed outcome expected. Localize prediction error before updating beliefs. Update locally before generalizing globally. Preserve contradictory evidence and provenance.

---

# 40. FREEZE TAKE Prompt

> Freeze the current collective state without rewriting it. Include the active context, problem frame, unresolved assumptions, claims, evidence, bottlenecks, decisions, domain versions, prompt versions and contribution lineage. Produce an immutable Take identifier.

---

# 41. BRANCH Prompt

> Create a new Branch from Take X. Preserve all inherited objects and identify every proposed change as a delta. Do not mutate the parent Take. Record new assumptions, removed assumptions, modified relations and contributor provenance.

---

# 42. MERGE Prompt

> Compare Branch A and Branch B relative to their common ancestor. Classify changes as compatible, complementary, semantically conflicting or evidence-conflicting. Merge only compatible changes automatically. Preserve unresolved conflicts as explicit objects.

---

# 43. UTILITY ATTRIBUTION Prompt

> Given an observed outcome, trace the causal contribution graph backward. Identify contributions that materially enabled, improved, accelerated or prevented waste associated with the outcome. Separate direct causal contribution, enabling contribution, reusable contribution and speculative attribution. Assign confidence to each attribution.

---

# 44. User Journey — Freeze and Develop

```text
Explore Context
      ↓
Work collaboratively
      ↓
Problem Frame stabilizes
      ↓
FREEZE TAKE
      ↓
Take #17 becomes immutable
      ↓
User A branches
User B branches
AI explores alternative branch
      ↓
Evidence accumulates
      ↓
Compare Branches
      ↓
Merge Review
      ↓
Take #18
      ↓
Outcome
      ↓
Utility Attribution
```

The user becomes part of product development through preserved causal contribution rather than comments disappearing into chat history.

---

# 45. Minimum Product Philosophy

We shall not create a disposable MVP.

We shall create a:

## Minimum Coherent Kernel

The smallest implementation using the **same canonical primitives required by the complete system**.

The first product exposes only:

```text
Workspace
Actor
Goal
Context
ProblemFrame
Decision
CognitiveBottleneck
CognitiveAction
Claim
Evidence
Take
Branch
Contribution
Outcome
```

But those objects already use the final:

- IDs,
- provenance,
- context relations,
- event architecture,
- versioning,
- APIs.

Therefore later capabilities extend the system rather than replace it.

---

# 46. Minimum Product UX

Only five main surfaces are required initially.

## 1. Context Workspace

Shows:

Goal  
Problem Frame  
Decision

## 2. Bottleneck Board

Shows:

what blocks progress, owner, dependencies, unblock value.

## 3. Evidence Rail

Shows:

claims, support, contradiction, uncertainty.

## 4. Take / Branch

Shows:

freeze, branch, semantic diff, merge.

## 5. Decision View

Shows:

alternatives, trade-offs, readiness, decision trace.

Everything else may initially appear through these surfaces.

---

# 47. First End-to-End Use Case

## Product investment decision

**Goal**

Determine whether capability X deserves investment.

**Input**

- one project brief,
- involved people,
- current evidence,
- proposed decision.

**Collective produces**

```text
ProblemFrame
BottleneckGraph
ClaimGraph
EvidenceGaps
CognitiveActions
Take #1
```

Team performs reality test.

Evidence is added.

A new Take is frozen.

Decision Readiness changes.

Investment decision is made.

Outcome is measured.

Contribution and utility are attributed.

This single vertical slice exercises nearly the entire kernel.

---

# 48. Component Reuse Strategy

A component may be:

**semantic**, **reasoning**, **visual**, **integration**, or **governance**.

Example:

```text
EvidenceComponent
```

can be reused inside:

```text
Commercial Domain
Negotiation Domain
R&D Domain
Legal Domain
Investment Domain
Future Context Domain
```

The component does not know why the entire system exists.

It only knows:

- its own purpose,
- required inputs,
- outputs,
- valid relations,
- constraints.

This is essential.

---

# 49. Domain Composition

A higher-order domain should be composed rather than reinvented.

Example:

```text
R&D Investment Domain
=
Need
+ Capability
+ Evidence
+ Experiment
+ Finance
+ Decision
+ Portfolio
```

Each retains its own semantics.

The new domain contributes context and composition.

---

# 50. Domain Registry

Collective requires a registry.

```text
DomainRegistry
├── domain
├── version
├── purpose
├── maintainer
├── schemas
├── compatible_components[]
├── dependencies[]
├── activation_rules
├── test_suite
├── deprecated_by?
└── provenance
```

This becomes the reuse marketplace inside the architecture.

---

# 51. Compatibility Rule

A reusable Domain or Component must be portable whenever:

1. its semantic contract is preserved,
2. required context is available,
3. schemas are compatible,
4. governance permits reuse.

No component should require knowledge of unrelated domains.

---

# 52. Cost-of-Boundary Principle

Every boundary has a cost.

Too few boundaries produce:

- semantic collision,
- coupling,
- difficult reuse.

Too many produce:

- orchestration overhead,
- duplicated context,
- integration cost.

Therefore boundaries shall be justified by:

**independent purpose + meaningful semantic invariance + reuse potential.**

Do not create a domain merely because an organizational department exists.

---

# 53. Investment Architecture

The investment sequence follows evidence maturity.

## Investment A — Method

Prove that teams benefit from explicit:

Goal → Decision → Bottleneck → Evidence.

## Investment B — Kernel

Implement canonical objects and Take/Branch.

## Investment C — Collaboration

Shared workspace, attribution and merge.

## Investment D — Integrations

Connect operational sources.

## Investment E — Cognitive Selection

Automate cognitive-action recommendations.

## Investment F — Utility Ledger

Measure reusable and realized contribution.

## Investment G — Dynamic Orchestration

Route bottlenecks between humans and agents.

## Investment H — Adaptive Organization

Allocate capabilities and resources according to high-unblock-value contexts.

Each tranche must purchase new evidence, capability or strategic optionality.

---

# 54. Investment Gates

Do not ask:

> Have we already invested too much to stop?

Ask:

> What evidence does the next investment buy?

### Gate 1

Can humans use the model effectively?

### Gate 2

Does shared contextual state improve decisions?

### Gate 3

Does Take/Branch preserve useful development lineage?

### Gate 4

Can contribution attribution be meaningfully reconstructed?

### Gate 5

Can integrations reduce manual context maintenance?

### Gate 6

Does Cognitive Action Selection outperform simple human selection?

### Gate 7

Can automated orchestration reduce decision latency without unacceptable coordination cost?

---

# 55. Core Metrics

The system should initially optimize measurable organizational outcomes, not engagement.

Primary metrics:

```text
DecisionLeadTime
BottleneckResolutionTime
PrematureWorkAvoided
EvidenceCoverage
DecisionReversalRate
UnownedBottleneckRate
ContextAlignment
RealityTransitionTime
ReusableComponentRate
ContributionReuse
```

Later:

```text
RealizedUtility
UtilityPerInvestment
PortfolioOptionValue
```

---

# 56. Anti-metrics

Do not optimize by default for:

- messages sent,
- time in application,
- number of AI responses,
- number of tasks created,
- number of insights produced.

More activity is not necessarily more value.

---

# 57. Product Governance

Every material automated action must answer:

**Can infer?  
Can use?  
Can act?**

Separate:

- relevance,
- confidence,
- permission,
- authority.

A high-confidence inference may still be prohibited from automated action.

---

# 58. Contribution Governance

The system must protect against gaming.

Utility must not simply equal:

- number of edits,
- number of prompts,
- volume of text,
- number of branches.

Useful contribution requires downstream effect.

Negative contributions may still have positive value if they falsify expensive wrong paths.

Example:

**“This will not work; here is decisive evidence.”**

may deserve large utility attribution.

---

# 59. Constitutional Invariants

1. Query ≠ Goal.
2. Goal ≠ Problem.
3. Problem ≠ Solution.
4. Observation ≠ Inference.
5. Claim ≠ Evidence.
6. Need ≠ Capability.
7. Capability ≠ Offering.
8. Intention ≠ Commitment.
9. Transaction ≠ Outcome.
10. Simulation ≠ Reality.
11. Task completion ≠ Bottleneck resolution.
12. AI recommendation ≠ human accountability.
13. Contribution ≠ automatic legal ownership.
14. High activity ≠ high utility.
15. A Take is immutable.
16. A Branch never mutates its parent.
17. Contradictions survive until explicitly resolved.
18. Reuse preserves provenance.
19. Context governs relevance.
20. Reality may override any model.

---

# 60. Product's Deepest Operating Loop

```text
USER / WORLD INPUT
        ↓
ORIENT
        ↓
CONTEXT CANDIDATES
        ↓
UNDERSTAND
        ↓
CHALLENGE
        ↓
CLARIFY
        ↓
PROBLEM FRAME
        ↓
COGNITIVE BOTTLENECK
        ↓
COGNITIVE ACTION
        ↓
EVIDENCE / REALITY
        ↓
DECISION
        ↓
WORLD ACTION
        ↓
OUTCOME
        ↓
LEARNING
        ↓
TAKE
        ↓
NEW CONTEXT
```

At any stable point:

**FREEZE TAKE**

At any useful divergence:

**BRANCH**

When compatible development should converge:

**MERGE**

When reality creates measurable value:

**ATTRIBUTE UTILITY**

---

# 61. Product Vision

Omniframez Collective should ultimately allow an organization to ask:

> What are we actually trying to accomplish?

> Which decisions matter now?

> Which uncertainty blocks each decision?

> Which evidence would change it?

> Who is best positioned to obtain that evidence?

> Which downstream work should wait?

> Which components can be reused?

> Which ideas or contributions actually created value?

> What did we believe when we made the decision?

> What did reality teach us?

> Which context should govern us now?

The product therefore evolves from:

**AI collaboration**

to:

**collective cognitive infrastructure**

and ultimately toward:

**an observable, versionable and learning organizational intelligence system.**

---

# 62. Whitepaper Claim

The core proposition to test is:

> Organizations can improve decision quality, reduce premature work and accumulate reusable institutional intelligence when goals, contexts, bottlenecks, claims, evidence, contributions and outcomes are represented as explicit, versioned and interoperable objects rather than remaining implicit inside conversations, meetings and documents.

This claim must remain falsifiable.

If teams do not make better or faster decisions with the kernel, more automation is not justified.

---

# 63. Final Product Principle

**Do not build the future as one giant application.**

Build a small set of semantically stable primitives from which the entire future can be composed.

The minimum product is therefore not a temporary simplification of the idea.

It is the **minimum complete kernel of the full idea**.

And the long-term architecture follows one rule:

**Every useful context may become a Domain.  
Every Domain must have its own purpose.  
Every Domain is composed of reusable Components.  
Every Component creates contextual Particles.  
Every Particle may become the next Portal.  
Every meaningful contribution preserves lineage.  
Every stable state may be frozen as a Take.  
Every Take may become the origin of a new future.**