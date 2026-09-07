---
name: omnipod-team-optimizer
description: Execute dynamic context resolution, bounded scope traversal (D0-D3), 12-agent closed-loop team dynamics optimization, and self-improving meta-learning feedback loops. Use when querying the Universal ERD, resolving task-specific context packets, addressing team friction/bottlenecks, or updating system heuristics.
---

# Omnipod Team Optimizer & Dynamic Context Skill

## Overview
Denna skill ger handlingsbara arbetsflöden, körexempel och verktygskedjor för att operera och optimera systemet i `bart`. Den förenar **Dynamic Context Resolution Engine** (som begränsar och anpassar informationsflödet) med **12-Agent Closed Loop** för teamoptimering och självförbättring.

---

## Snabböversikt över Arbetsflöden

| Uppgift | Metod / Verktyg | Primär Output |
| :--- | :--- | :--- |
| **Generera Kontextpaket** | `DynamicContextResolver.resolve(...)` | `ContextPacket` (L1, L2, Machine, Next Nodes) |
| **Avgränsa Utforskning** | `ScopeContract(depth=ScopeLevel.D0..D3)` | Begränsat sökdjup och token-skydd |
| **Köra Teamloopen** | `OrchestratorAgent.run_cycle(...)` | Diagnos, strukturförslag, åtgärder |
| **Skapa & Köra Experiment**| `ExperimentAgent.design_experiment(...)` | Testbar hypotes och mätplan |
| **Mäta & Extrahera Lärdom** | `MeasurementAgent` + `LearningAgent` | $\Delta$-utfall och uppdaterade kunskapsnoder |
| **Självförbättrande Meta-Loop**| `MetaLearningAgent.calibrate(...)` | Uppdaterade 8D-vikter och regler |

---

## Arbetsflöde 1: Dynamisk Kontextupplösning (5 Steg)

Använd detta arbetsflöde när en agent eller användare behöver ett precist informationsutsnitt från kunskapsgrafen istället för hela grafen:

```python
from src.context_engine.resolver import DynamicContextResolver
from src.core.contracts import ScopeContract
from src.core.types import ScopeLevel, Domain
from src.graph.universal_erd import UniversalERDGraph

# 1. Initiera grafen (eller hämta från checkpoint)
graph = UniversalERDGraph()

# 2. Definiera ScopeContract för att förhindra informationsöverflöd
scope = ScopeContract(
    depth=ScopeLevel.D1,             # D0: Målnod, D1: 1 hopp, D2: 2 hopp, D3: 3 hopp
    max_nodes=12,
    allowed_domains=[Domain.OPERATIONAL, Domain.TOOLS, Domain.TRUST],
    confidence_threshold=0.80
)

# 3. Kör kontextupplösning med Actor-nyckeln (Roll + Ändamål + Uppgift)
packet = DynamicContextResolver.resolve(
    target_node_id="role:decision-owner-042",
    role="Data Manager",
    purpose="Identifiera förseningsorsaker i rapportering",
    task="Kartlägg beroenden och mandatkonflikter",
    scope=scope,
    graph=graph
)

# 4. Konsumera i relevant vy
print("=== HUMAN L1 ===")
print(packet.human_l1_view)

print("\n=== MACHINE VIEW (JSON) ===")
print(packet.machine_view)

print("\n=== NÄSTA REKOMMENDERADE NODER ===")
for next_node in packet.recommended_next_nodes:
    print(f"-> {next_node.label} (Relevans: {next_node.score:.2f})")
```

---

## Arbetsflöde 2: Den 12-Agentiga Teamoptimeringsloopen

När en teamfriktion, rollkonflikt eller flaskhals identifierats:

1. **ObserverAgent** aktiveras för att extrahera signaler och generera en objektiv nulägesbild.
2. **DiagnosticianAgent** jämför nulägesbilden med historiska mönster och formulerar rotorsakshypoteser.
3. **TeamArchitectAgent** utvärderar rollmandat, RACI och föreslår nödvändiga strukturjusteringar.
4. **Specialiserade Agenter** kallas in baserat på problemets natur:
   - Vid otydliga ansvarsgränser: `RoleTransitionAgent`
   - Vid samarbets- och kommunikationsproblem: `CollaborationAgent`
   - Vid hög arbetsbelastning eller stress: `WellbeingAgent`
   - Vid automatiserade processer eller AI-beslut: `AIEthicsAgent`
5. **ExperimentAgent** omvandlar rekommendationen till ett kontrollerat experiment:
   - Formulerar testbar hypotes (t.ex. *"Om mandat för godkännande flyttas till Roll A minskar beslutstiden med minst 30%"*).
   - Etablerar tidsfönster (t.ex. 14 dagar) och kontrollgrupp/mätpunkter.
6. **MeasurementAgent** loggar baseline vs testutfall och beräknar nettoeffekt.
7. **LearningAgent** skapar ett `LearningObject` och uppdaterar systemets kunskapsbas och regelverk.

---

## Arbetsflöde 3: Meta-Learning & Systemoptimering

Körs cykliskt för att systemet ska förbättra sin egen precision över tid:

```python
from src.agents.meta_learning import MetaLearningAgent

meta_agent = MetaLearningAgent()

# Utvärdera alla agentresultat från senaste iterationscykeln
evaluation = meta_agent.evaluate_system_performance(
    iteration_history=history,
    telemetry=system_telemetry
)

# Kontrollera kalibreringsbehov:
# 1. False positive diagnoser -> justera tröskelvärden för Diagnostiker
# 2. Onödigt djupa scopes -> sänk standard-djup från D2 till D1 för snabbare svar
# 3. Vikter i 8D-modellen -> förstärk rollmatchning om felaktiga noder hämtades

if evaluation.requires_calibration:
    meta_agent.apply_calibrations(evaluation.updated_weights)
```

---

## Arbetsflöde 4: Kontinuerlig Evolutionär Fas-Progression (Självgenererande Faser)

När en fas når konvergens (friktion löst, hypotes verifierad) ska systemet automatiskt syntetisera och exekvera nästa fas i trajektorian:

```python
from src.agents.orchestrator import OrchestratorAgent
from src.context_engine.resolver import ContextResolver
from src.core.types import PerspectiveWindow, ScopeLevel
from src.agents import TWELVE_CORE_AGENTS

# 1. Be OrchestratorAgent syntetisera nästa evolutionära fas
next_phase = OrchestratorAgent.generate_next_evolutionary_phase(
    current_window=PerspectiveWindow.W8_INNOVATION_TECH,
    previous_outcome={"pilot_status": "VALIDATED", "lead_time_minutes": 25}
)

print(f"-> Nästa Fas #{next_phase['phase_number']}: {next_phase['phase_id']}")
print(f"-> Fönster: {next_phase['window'].value} | Roll: {next_phase['role']}")

# 2. Lös kontexten för den nya fasen med roll och målnod
context = ContextResolver.resolve_context(
    role=next_phase["role"],
    purpose=next_phase["purpose"],
    task=next_phase["task"],
    scope=ScopeLevel.D1_DIRECT,
    target_entity=next_phase["target_entity"],
    observations=next_phase["observations"],
    window=next_phase["window"],  # Explicit fönsterstyrning
)

# 3. Exekvera 12-agent loopen för att driva fasen i mål
for AgentCls in TWELVE_CORE_AGENTS:
    res = AgentCls().run(context)
    print(f"[{res.agent_name}] Status: {res.status.value}")
```

---

## Fördjupande Referenser
- För fullständig dokumentation av 8D-viktningsformeln, fönstren W1-W9 och de 6 domänerna, se [Kontextmotor & Domänreferens](./references/context_engine_reference.md).
- För specifikation av alla agenter, specialister och kontraktet `AgentResult`, se [12-Agent Systemet & Meta-Lärande](./references/twelve_agents_reference.md).

