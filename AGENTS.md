# Workspace Rules & Architecture Guidelines: bart (Omnipod & Omniframez)

Välkommen till repositoryt **bart**. Detta projekt implementerar en självförbättrande, distribuerad multi-agentarkitektur baserad på **Omniframez Collective**, **Omnipod Framework**, **Dynamic Context Resolution** och **Team Dynamics Optimization**.

## Aktiva Regler & Guardrails
Samtliga agenter och utvecklare som opererar i detta workspace lyder under följande regler:

1. **Epistemisk separation**:
   - `Stored Information ≠ Active Context`: All data i kunskapsgrafen/ERD är inte relevant samtidigt. Kontext måste lösas dynamiskt genom `Role + Purpose + Task + Current Point + Scope`.
   - `Integration ≠ Recommendation`: Samla och integrera evidens över domäner innan syntes eller rekommendationer skapas.
   - `Cognitive Bottlenecks`: Identifiera flaskhalsen innan kognitiva handlingar (`ASK`, `VERIFY`, `REFRAME`, `COMPARE`, `EXPERIMENT`, `DECIDE`) väljs.
2. **Standardiserat Agentkontrakt**:
   - Alla optimeringsagenter följer 6-stegscykeln: `observe() → analyze() → identify() → propose() → act() → evaluate()`.
   - Resultat returneras alltid enligt datamodellen `AgentResult`.
3. **Begränsat Sökdjup (Bounded Scope)**:
   - All traversering styrs av `ScopeContract` med nivåerna $D_0$ (0 hopp), $D_1$ (1 hopp), $D_2$ (2 hopp) och $D_3$ (3 hopp).
4. **Slutna Dubbla Loopar**:
   - **Teamloop**: `Signal → Diagnos → Intervention → Experiment → Mätning → Lärdom`.
   - **Meta-Learning Loop**: Analyserar agentprestanda och kalibrerar heuristiska 8D-vikter och regler.
5. **Kontinuerlig Evolutionär Progression**:
   - Ett konvergerat tillstånd är aldrig slutpunkten. Frigjord kapacitet styrs automatiskt mot W8 Innovation, W2 Matchning, W4 Skalning och nya cykler.

För fullständig regeldefinition, se [`.agents/rules/omnipod-invariants.md`](file:///c:/Users/info/OneDrive/Dokument/GitHub/bart/.agents/rules/omnipod-invariants.md).

## Tillgängliga Skills
- [`omnipod-team-optimizer`](file:///c:/Users/info/OneDrive/Dokument/GitHub/bart/.agents/skills/omnipod-team-optimizer/SKILL.md): 5-stegs dynamisk kontextupplösning, orkestrering av 12-agentsteamet, experiment och meta-learning.
- [`contextual-precognition`](file:///c:/Users/info/OneDrive/Dokument/GitHub/bart/.agents/skills/contextual-precognition/SKILL.md): Trajektorieprojektion, förebyggande friktionsskydd och SQLite WAL-persistens.
