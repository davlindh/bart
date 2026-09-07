# Masterreferens: Samtliga Roller, Agenter och Personas

Denna manual dokumenterar samtliga aktörer i `bart`-ekosystemet: **12 Kärnagenter**, **8 Informationsspecialister** och **11 Operativa Personas / Mänskliga roller**.

---

## 1. De 12 Kärnagenterna (Team Dynamics Loop)

Samtliga agenter i denna loop ärver från [`BaseAgent`](file:///c:/Users/info/OneDrive/Dokument/GitHub/bart/src/agents/base.py) och följer 6-stegscykeln:
$$\text{observe}() \longrightarrow \text{analyze}() \longrightarrow \text{identify}() \longrightarrow \text{propose}() \longrightarrow \text{act}() \longrightarrow \text{evaluate}()$$

| # | Agent | Kärnfråga | Input | Output | Källkod |
|---|---|---|---|---|---|
| **1** | **Observer** | *Vad händer i teamet just nu?* | Råloggar, Jira, Fortnox, POS | Objektiv nulägesbild & telemetrisignaler | [`ObserverAgent`](file:///c:/Users/info/OneDrive/Dokument/GitHub/bart/src/agents/observer.py) |
| **2** | **Diagnostiker** | *Varför händer det?* | Nulägesbild & avvikelser | Hypoteser & identifierade rotorsaker | [`DiagnosticianAgent`](file:///c:/Users/info/OneDrive/Dokument/GitHub/bart/src/agents/diagnostician.py) |
| **3** | **Team Architect** | *Hur bör teamet vara utformat?* | Diagnos & verksamhetsmål | Strukturförslag, rollmandat, RACI | [`TeamArchitectAgent`](file:///c:/Users/info/OneDrive/Dokument/GitHub/bart/src/agents/team_architect.py) |
| **4** | **Role Transition** | *Hur tar vi oss från nu till önskat läge?* | Strukturförslag & förändringsbehov | Fasad övergångsplan & kommunikation | [`RoleTransitionAgent`](file:///c:/Users/info/OneDrive/Dokument/GitHub/bart/src/agents/role_transition.py) |
| **5** | **Collaboration** | *Hur kan vi samarbeta bättre?* | Teamstruktur & gränssnitt | Samarbetsinterventioner & verktygsflöden | [`CollaborationAgent`](file:///c:/Users/info/OneDrive/Dokument/GitHub/bart/src/agents/collaboration.py) |
| **6** | **Wellbeing** | *Hur mår teamet och vad behövs?* | Belastningssignaler, timmar | Hållbarhetsåtgärder & övertidstak | [`WellbeingAgent`](file:///c:/Users/info/OneDrive/Dokument/GitHub/bart/src/agents/wellbeing.py) |
| **7** | **AI Ethics** | *Är AI-användningen säker & etisk?* | Modeller, beslutsprocesser | Riskbedömning, safeguards, HITL-krav | [`AIEthicsAgent`](file:///c:/Users/info/OneDrive/Dokument/GitHub/bart/src/agents/ai_ethics.py) |
| **8** | **Experiment Agent** | *Hur testar vi hypotesen säkert?* | Åtgärdsförslag & hypoteser | Tidsbegränsad experimentplan & metriker | [`ExperimentAgent`](file:///c:/Users/info/OneDrive/Dokument/GitHub/bart/src/agents/experiment_agent.py) |
| **9** | **Measurement** | *Vad blev det faktiska resultatet?* | Experimentdata, baseline, ERP | Utfallsanalys & kvantifierat delta ($\Delta$) | [`MeasurementAgent`](file:///c:/Users/info/OneDrive/Dokument/GitHub/bart/src/agents/measurement.py) |
| **10**| **Learning** | *Vad har organisationen lärt sig?* | Utfallsanalys mot mål | Lärdomsobjekt & uppdaterade regler | [`LearningAgent`](file:///c:/Users/info/OneDrive/Dokument/GitHub/bart/src/agents/learning.py) |
| **11**| **Orchestrator** | *Vad ska göras härnäst & i vilken ordning?* | Samtliga agentresultat | Nästa actions, färdighetsdispatch & faser | [`OrchestratorAgent`](file:///c:/Users/info/OneDrive/Dokument/GitHub/bart/src/agents/orchestrator.py) |
| **12**| **Meta-Learning** | *Hur kan agentsystemet självt bli bättre?* | All agenttelemetri, avvikelser | Uppdaterade 8D-vikter, promptoptimering | [`MetaLearningAgent`](file:///c:/Users/info/OneDrive/Dokument/GitHub/bart/src/agents/meta_learning.py) |

---

## 2. De 8 Utökade Informationsspecialisterna (Graph & Cognitive Layer)

Dessa specialister kopplas in av Orchestratorn eller Context Resolvern när djupare ontologisk struktur krävs:

| Specialist | Syfte | Vad skapas? | Hur används det? |
|---|---|---|---|
| **Context Resolver** | Bestämma vad som är relevant just nu | `ContextPacket` | Filtrerar och skär ut delgraf för aktör och uppgift |
| **Scope Manager** | Begränsa djup, bredd och tokenkonsumtion | `ScopeContract` ($D_0-D_3$) | Hindrar okontrollerad graf-traversering |
| **Semantic Mapper** | Översätta språk till maskinlänkbar ontologi | Semantiska länkar & noder | Gör text till typade entiteter (`Ord → Nod → Relation`) |
| **Provenance Agent** | Säkerställa varför något anses sant | `EvidenceChain` & konfidens | Skiljer påståenden från evidens; spårbarhet |
| **Relationship Analyst** | Upptäcka dolda beroenden och samband | Relationssubgraf | Analyserar `causes`, `blocks`, `enables`, `depends_on` |
| **Decision Architect** | Strukturera val, trade-offs och risker | `DecisionObject` | Skapar underlag inför `FREEZE TAKE` och `Reality Gate` |
| **Action / Execution** | Översätta beslut till operativa arbetspaket | `ActionObject` & uppgifter | Skickar konkreta instruktioner till fält-/verkstadssystem |
| **Governance Agent** | Kontrollera juridik, skatteregler och behörighet | Guardrails & efterlevnadslogg | Spärrar otillåtna handlingar mot ML/IL-lagstiftning |

---

## 3. De 11 Operativa Rollerna & Personas (Human-in-the-Loop)

Roller representerar de funktionella perspektiv och behörighetsnivåer som människor eller systemaktörer intar:

| Roll / Persona | Funktionella Domäner | Perspektivfönster | Primärt Mandat & Användningsområde |
| :--- | :--- | :--- | :--- |
| **User A (Verifier & Creator)** | Trust, Knowledge | W1 / W3 | Kvalitetsgranskning, innehållsskapande, utbildningsmaterial |
| **User B (Data Manager & Logistics)**| Operational, Tools, Trust, Exchange | W4_RESOURCE_ALLOCATION | Processflöden, dataflöden, flaskhalsanalys och rapportering |
| **User C (Security & Infra Lead)** | Trust, Operational | W7 / W5 | Säkerhetspolicyer, infrastruktur, IT-drift och granskningsloggar |
| **User D (Curator & Data Steward)** | Knowledge, Operational | W9 / W1 | Datakataloger, ontologiska definitioner och metadatahygien |
| **CFO / Ekonomiansvarig** | Operational, Exchange, Trust, Knowledge, Tools | W5_FINANCIAL_MANAGEMENT | Månadsbokslut, VMB, momsdeklaration, likviditet |
| **Revisor** | Operational, Exchange, Trust | W3_EVALUATION | Skatterevision, regeltolkning, granskning av verifikationer |
| **Säljare** | Exchange, Interactional, Tools | W2_MATCHING | Kunddialog, offerter, inbytesvärdering av robotar |
| **Verkstadschef** | Operational, Tools, Interactional | W4_RESOURCE_ALLOCATION | Verkstadsplanering, reservdelslager, serviceflottor |
| **Innovationsledare** | Tools, Operational, Knowledge, Exchange | W8_INNOVATION_TECH | AI-assisterad diagnostik, teknikpiloter, FoU-avdrag |
| **Affärsutvecklare** | Exchange, Interactional, Tools, Operational | W2_MATCHING | Kommersiella abonnemangsmodeller, LTV, kundsegmentering |
| **Strategisk Ledare** | Trust, Knowledge, Operational, Exchange | W1_CONTEXTUALIZATION | Ekosystemkonvergens, företagsstrategi, säsongsanpassning |
