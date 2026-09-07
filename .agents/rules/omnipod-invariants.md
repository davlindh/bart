# Omnipod & Omniframez Invariants

När du analyserar, designar eller modifierar kod, agenter, domäner eller kontext i detta repository ska följande arkitektoniska grundsatser och invarianta guardrails alltid upprätthållas:

## 1. Epistemiska Grundseparationer (Separation of Concerns)
- **Stored Information ≠ Active Context**: All tillgänglig data i informationsgrafen/ERD är inte relevant samtidigt. Att dumpa rådata eller hela kunskapsgrafen i en agents kontextfönster är strikt förbjudet. Kontext måste alltid härledas dynamiskt utifrån:
  $$\text{Context} = \text{Role} + \text{Purpose} + \text{Task} + \text{Current Point} + \text{Scope}$$
- **Integration ≠ Recommendation**: Informationsfusion över domäner och perspektivfönster måste alltid slutföras och verifieras innan syntes och rekommendationer genereras. Rå observationer får aldrig skickas direkt till beslutsmodeller utan kontextuell resolution.
- **Component Definitions are Reusable, Contextual Instances are Local**: Nod- och domändefinitioner ska vara universella och återanvändbara, medan instanser och relationer alltid är lokalt kontextbundna.
- **Cognitive Action Selection**: Varje agenthandling ska utgå från att identifiera en `Cognitive Bottleneck` (vad som hindrar förståelse, beslut eller framdrift) och välja rätt operation (`ASK`, `VERIFY`, `REFRAME`, `COMPARE`, `EXPERIMENT`, `DECIDE`).

## 2. Standardiserad 6-Stegs Agentlivscykel
Alla agenter i teamoptimeringsloopen måste implementera eller ansluta till samma standardiserade livscykel:
$$\text{observe}() \longrightarrow \text{analyze}() \longrightarrow \text{identify}() \longrightarrow \text{propose}() \longrightarrow \text{act}() \longrightarrow \text{evaluate}()$$

Varje agent producerar ett standardiserat `AgentResult` med följande struktur:
```python
AgentResult(
    observations=...,       # Faktiska observerade signaler och mätpunkter
    confidence=...,         # 0.0 - 1.0 konfidensgrad
    identified_issues=...,  # Konkreta friktioner, flaskhalsar eller avvikelser
    hypotheses=...,         # Diagnostiska hypoteser och rotorsaker
    recommendations=...,    # Prioriterade rekommendationer
    actions=...,            # Konkreta handlingsbara actions
    metrics=...,            # Kvantifierbara KPI:er för utvärdering
    risks=...,              # Identifierade risker och safeguards
    dependencies=...,       # Beroenden till andra roller/agenter/processer
    next_questions=...      # Rekommenderade frågor eller nästa noder
)
```

## 3. Begränsat Scope (Bounded Horizon D0-D3)
All navigation och sökning i kunskapsgrafen/ERD måste styras av ett explicit `ScopeContract`:
- **$D_0$ (Immediate)**: Omedelbar målnod (0 hopp).
- **$D_1$ (Direct)**: Direkt grannskap och närmaste beroenden (1 hopp).
- **$D_2$ (Systemic)**: Systemiskt delsystem, relaterade processer och finansiell ledning (2 hopp).
- **$D_3$ (Expanded)**: Makroorganisation, externa myndigheter och historiska mönster (3 hopp).

**Stoppvillkor**: Expansion från $D_n$ till $D_{n+1}$ sker endast om evidensen i $D_n$ är otillräcklig för att uppfylla konfidensmålet. Informationsöverflöd och okontrollerad traversering är otillåten.

## 4. Slutna Dubbla Lärloopar (Dual Feedback Loops)
- **Operativ Teamloop**:
  $$\text{Signal} \longrightarrow \text{Diagnos} \longrightarrow \text{Intervention} \longrightarrow \text{Experiment} \longrightarrow \text{Mätning} \longrightarrow \text{Lärdom} \longrightarrow \text{Ny Signal}$$
  Ingen förändring får implementeras permanent utan att formuleras som ett testbart experiment och följas upp med kvantifierbar effektmätning.
- **Arkitektonisk Meta-Lärandeloop**:
  Meta-learning analyserar *inte* teamet direkt, utan analyserar *hur väl agentsystemet självt fungerar*:
  - Vilka agenter aktiverades och gav önskad effekt?
  - Förekom feldiagnoser eller blindspots?
  - Var de valda scope-nivåerna adekvata?
  - Uppdatera heuristiska vikter, promptmallar och aktiveringsregler för nästa cykel.

## 5. Kontinuerlig Evolutionär Fas-Progression (Autonomous Progression)
Ett konvergerat systemtillstånd får aldrig innebära att agentprocessen avstannar i en återvändsgränd:
- **Frigjord Kapacitet ska Återinvesteras**: När en flaskhals elimineras (t.ex. -72% ledtid, normaliserad övertid, realiserad skattevinst) ska systemet automatiskt syntetisera och initiera nästa fas via `OrchestratorAgent.generate_next_evolutionary_phase()`.
- **Kanonisk Utvecklingstrajektoria över Perspektivfönstren**:
  $$\text{W5/W6 (Stabilitet)} \longrightarrow \text{W8 (Innovation & Pilot)} \longrightarrow \text{W2 (Matchning & Kommersialisering)} \longrightarrow \text{W4 (Resursskalning)} \longrightarrow \text{W9 (Adaptiv Konvergens)} \longrightarrow \text{Cykel } N+1$$
- **Evig Självförnyelse**: När en fullständig omgång av perspektivfönster genomlöpts genereras en ny generation ($N+1$) med djupare prediktiv horisont, maskintelemetri och autonom ekosystemutveckling.
