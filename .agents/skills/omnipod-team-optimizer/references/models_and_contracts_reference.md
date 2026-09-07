# Masterreferens: Samtliga Modeller, Kontrakt & Entiteter

Denna manual dokumenterar samtliga datastrukturer, Pydantic-kontrakt och ERD-entiteter som utgör informationslagret i `bart`.

---

## 1. De 15 Universal ERD-Entiteterna (Kunskapsgrafen)

Modellerna är definierade i [`src/graph/models.py`](file:///c:/Users/info/OneDrive/Dokument/GitHub/bart/src/graph/models.py) och instansieras i [`UniversalERDGraph`](file:///c:/Users/info/OneDrive/Dokument/GitHub/bart/src/graph/universal_erd.py):

| # | Entitetsnamn | Primärnyckel | Beskrivning & Nyckelfält | Relationer |
|---|---|---|---|---|
| **1** | **Organization** | `org_id` | Juridisk enhet (namn, orgnr, momsregistrerad, skattestatus) | Äger Teams, Kunder, Tillgångar |
| **2** | **Team** | `team_id` | Avdelning eller funktionell grupp (namn, avdelning, budget) | Tillhör Org; innehåller Personer & Roller |
| **3** | **Person** | `person_id` | Anställd eller konsult (namn, e-post, lön, kapacitetstimmar) | Tillhör Team; har Roller & Capabilities |
| **4** | **Role** | `role_id` | Formell funktion (titel, ansvarsområde, mandatgräns SEK) | Tilldelad till Person; definierar Mandat |
| **5** | **Capability** | `cap_id` | Verifierad kompetens (namn, certifiering, giltighetsdatum) | Besitts av Person; krävs av Roll |
| **6** | **Assignment** | `assignment_id` | Uppdragskoppling (person, roll, projekt, allokerad tid) | Länkar Person, Roll och Uppgift |
| **7** | **Observation** | `observation_id` | Empirisk telemetri eller signal (metrik, värde, enhet, konfidens) | Skapas av Observer; refererar Entiteter |
| **8** | **Diagnosis** | `diagnosis_id` | Identifierad avvikelse eller flaskhals (kategori, rotorsak, allvarlighetsgrad)| Skapas av Diagnostiker från Observationer |
| **9** | **Intervention** | `intervention_id` | Föreslagen förändring (titel, mekanism, förväntad effekt) | Svarar mot Diagnos; föreslås av Architect |
| **10**| **TransitionPlan** | `plan_id` | Tidsplan för struktur-/rollbyte (faser, milstolpar, risker) | Skapas av RoleTransition; styr Uppdrag |
| **11**| **Communication** | `comm_id` | Loggad interaktion eller notifiering (avsändare, kanal, payload) | Skapas av Collaboration/Orchestrator |
| **12**| **Experiment** | `experiment_id` | Testbar hypotes (hypotes, kontrollgrupp, mätpunkter, tidsram) | Skapas av ExperimentAgent; testar Intervention |
| **13**| **Measurement** | `measurement_id` | Kvantifierat utfall (metrik, delta $\Delta$, baseline, konfidens) | Skapas av MeasurementAgent; utvärderar Experiment |
| **14**| **Learning** | `learning_id` | Validerad insikt (lärdom, konfidens, uppdaterade regler) | Skapas av LearningAgent; uppdaterar Knowledge |
| **15**| **Knowledge** | `knowledge_id` | Beständig kunskapstillgång i `/knowledge` (titel, innehåll, domän) | Konsumeras av samtliga fönster och agenter |

---

## 2. Kärnkontrakt & Maskinprotokoll

Dessa kontrakt styr datautbytet mellan motor, agenter och gränssnitt:

### A. `ContextPacket` ([`src/core/contracts.py`](file:///c:/Users/info/OneDrive/Dokument/GitHub/bart/src/core/contracts.py#L58))
Det dynamiska informationspaketet som genereras av `ContextResolver`:
```python
class ContextPacket(BaseModel):
    context_id: str
    role: str
    purpose: str
    task: str
    scope: ScopeLevel = ScopeLevel.D1_DIRECT
    allowed_domains: List[Domain]
    perspective_window: PerspectiveWindow
    primary_entity: Dict[str, Any]
    related_entities: List[Dict[str, Any]]
    observations: List[Observation]
    recommended_next_nodes: List[Dict[str, Any]]
    evidence: List[str]
    assumptions: List[str]
    uncertainties: List[str]
    relevance_scores: Dict[str, float]
    stop_condition_met: bool = False
    stop_condition_reason: str
```

### B. `AgentResult` ([`src/core/contracts.py`](file:///c:/Users/info/OneDrive/Dokument/GitHub/bart/src/core/contracts.py#L79))
Det obligatoriska returformatet från samtliga 12 optimeringsagenter:
```python
class AgentResult(BaseModel):
    agent_name: str
    status: AgentStatus = AgentStatus.COMPLETED
    observations: List[Observation]
    diagnoses: List[Diagnosis]
    tax_opportunities: List[TaxOptimizationOpportunity]
    recommendations: List[str]
    actions_taken: List[str]
    next_questions: List[str]
    metrics_summary: Dict[str, Any]
```

### C. `ScopeContract` & `ScopeLevel`
Styr sökhorisonten och hindrar okontrollerad tokenexpansion:
- `D0_IMMEDIATE`: Endast målnod (0 hopp).
- `D1_DIRECT`: 1-hopps grannar och direkta beroenden.
- `D2_SYSTEMIC`: 2-hopps delsystem, relaterade processer och finansiella ledtrådar.
- `D3_EXPANDED`: 3-hopps makroorganisation, externa skatteregler och myndigheter.

### D. `ProjectIntent` ([`src/core/precognition.py`](file:///c:/Users/info/OneDrive/Dokument/GitHub/bart/src/core/precognition.py))
Avsiktsförklaring för intentional framåtblick och pre-kognition:
```python
class ProjectIntent(BaseModel):
    intent_id: str
    project_id: str
    mandate: str
    desired_state: Dict[str, Any]
    target_kpis: Dict[str, float]
    allowed_domains: List[Domain]
    horizon_steps: int = 3
    status: IntentStatus = IntentStatus.ACTIVE
```

### E. `Take` (Omniframez Utvecklingsprimitiv)
Ett oföränderligt (immutable) snapshot av det kollektiva tänkandet vid en specifik tidpunkt:
- Fält: `take_id`, `parent_take_id`, `branch_id`, `active_goal`, `active_context`, `domains`, `claims`, `evidence`, `bottlenecks`, `decisions`, `integrity_hash`.
- Operationer: `FREEZE TAKE`, `BRANCH`, `MERGE`.

---

## 3. Svenska Skatte- & Affärsmodeller

Definierade i [`src/core/types.py`](file:///c:/Users/info/OneDrive/Dokument/GitHub/bart/src/core/types.py) och [`src/tax_engine/`](file:///c:/Users/info/OneDrive/Dokument/GitHub/bart/src/tax_engine):

| Skattemodell / Regel | Juridisk Grund | Tillämpning i Bart |
| :--- | :--- | :--- |
| `VMB_MARGIN_TAX_ML9A` | ML 9a kap (Vinstmarginalbeskattning) | Begagnade maskiner/inbyten: moms endast på vinstmarginalen |
| `RUT_ARBETSKOSTNAD_50`| IL 67 kap (RUT-avdrag) | Installation & reparation: 50% skattereduktion på arbete |
| `ROT_ARBETSKOSTNAD_30`| IL 67 kap (ROT-avdrag) | Bygg- och markarbeten: 30% skattereduktion på arbete |
| `GRON_TEKNIK_SKATTEREDUKTION` | Lag (2020:1066) | Solceller, batterilager och laddboxar (19.4% till 48.5%) |
| `OMVAND_BYGGMOMS_ML1_2`| ML 1 kap 2 § andra stycket | Omvänd skattskyldighet för bygg- och entreprenadtjänster |
| `FOU_FORSKNINGSAVDRAG`| Lag (2013:948) om FoU-avdrag | Nedsättning av arbetsgivaravgifter för mjukvaruutveckling |
| `K10_UTDELNING_3_12` | IL 57 kap (3:12-reglerna) | Utdelningsoptimering: schablonbelopp vs lönebaserat utrymme |

### Svensk BAS-kontoplan som genereras:
- `1510`: Kundfordringar
- `1930`: Företagskonto / Bank
- `2440`: Leverantörsskulder
- `2611`: Utgående moms 25%
- `2641`: Ingående moms
- `3001`: Försäljning varor 25% moms
- `3051`: Försäljning tjänster 25% moms
- `3211`: Försäljning VMB (positiv/negativ marginal)
