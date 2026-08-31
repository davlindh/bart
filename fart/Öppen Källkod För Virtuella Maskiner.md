# **Systemarkitekturer för Självinitierad Exekvering och Isolering av A(S)GI-agenter och Service Workers**

Moderna AI-system, autonoma agenter och system för Artificiell Generell eller Specifik Intelligens (A(S)GI) ställer helt nya krav på exekveringsmiljöer1. I traditionell mjukvaruarkitektur är exekveringsmiljöer statiska: servrar, containers eller funktioner distribueras av utvecklare och väntar på definierade förfrågningar. I agentiska system genererar och utvärderar AI-modellen dynamisk kod, sätter samman verktyg och exekverar beräkningsflöden i realtid1. Detta kräver en arkitektur baserad på programmatisk självinitiering, där agenten eller styrsystemet på eget initiativ kan begära, konfigurera och starta isolerade virtuella maskiner eller sandlådor med förvalda programvarukomplex1.  
Säkerhetsutmaningen i detta område är påtaglig. Att exekvera godtycklig, AI-genererad kod direkt på värdsystemet eller i en standardiserad container skapar allvarliga sårbarheter för kodinjektion, nätverksintrång och resurserövring1. För att möjliggöra fri injektion och tolkning av A(S)GI-motorer, agentlogik eller mikrotjänster (service workers) krävs isoleringslager som förenar snabb kallstart med hårdvaruisolering på kärnnivå1.

## **Ekosystemet kring Hugging Face smolagents och E2B: Från Kodgenerering till MicroVM-sandlådor**

För att bygga ett komplett system för självinitierad exekvering kombineras ofta två skikt i mjukvarustacken: ett högnivåramverk för agentresonemang och kodinjektion samt ett lågnivåinfrastrukturlager för maskinvirtualisering2. Den mest framträdande kombinationen i det öppna källkodsekosystemet utgörs av Hugging Face-biblioteket smolagents (huggingface/smolagents) och sandlådeplattformen E2B (e2b-dev/e2b)2.

### **Hugging Face smolagents: Agentisk Kodinjektion och Tolkning**

Hugging Face smolagents är ett minimalistiskt öppen källkodsramverk utformat kring principen att agenter fungerar bäst när de "tänker i kod"2. Istället för att tvinga AI-modellen att producera strukturerade JSON-objekt för verktygsanrop (ToolCallingAgent), låter kärnkomponenten CodeAgent modellen generera rena Python-skript2. Koden sätter dynamiskt samman funktioner, importerar bibliotek, hanterar slingor och utvärderar villkor i ett enda sammanhängande steg2.  
Kodinjektionsmekanismen i smolagents styrs via en säkerhetsmodell där tillåtna importer explicit definieras via parametern additional\_authorized\_imports2. Ramverkets inbyggda lokala tolk (LocalPythonExecutor) tillämpar vissa begränsningar på abstrakt syntaxträd (AST) men saknar hårdvaru- och operativsystemsisolering5. Oberoende säkerhetsanalyser och identifierade sårbarheter (exempelvis CVE-2025-9959) understryker att den lokala tolken inte utgör en säkerhetsgräns och aldrig får användas för opålitlig kod i produktion5. För säkrare drift stöder smolagents nativ omkoppling av sin exekveringsmotor till isolerade sandlådor via parametern executor\_type, med direkt stöd för E2B, Docker, Modal och Blaxel5.

### **E2B Infrastructure: Firecracker-baserade MicroVM-sandlådor**

E2B utgör infrastrukturskiktet för att exekvera AI-genererad kod i cloud-native miljöer1. Till skillnad från traditionella Docker-containers, som delar värdsystemets Linux-kärna via namespaces och cgroups, kör varje E2B-sandlåda inuti en dedikerad Firecracker microVM1. Firecracker – samma virtualiseringsteknik som driver AWS Lambda och Fargate – ger hårdvaruisolering via KVM med en obetydlig överhängskostnad7.  
E2B initieras programmatiskt via JavaScript- eller Python-SDK:er3. En ny virtuell maskin startas på cirka 150 till 200 millisekunder3. Systemet har arkitektoniskt stöd för anpassade mallar (custom templates), vilket innebär att utvecklare kan definiera operativsystemsmiljöer via Dockerfiles som konverteras till microVM-rotfilsystem4. I dessa miljöer kan godtyckliga bibliotek, A(S)GI-beroenden eller service workers förinstalleras1.  
Utöver snabb start och hårdvarusäkerhet tillhandahåller E2B avancerad tillståndshantering genom funktioner för frysning och återupptagning (pause/resume) samt snapshot-skapande via createSnapshot()7. Detta gör det möjligt för en A(S)GI-motor att initiera en virtuell maskin, exekvera ett delsteg, ta en komplett minnes- och filsystemavbildning, stoppa maskinen för att spara resurser, och senare återuppta exekveringen i exakt samma tillstånd7.

## **Arkitektoniskt Flöde för Injicering av A(S)GI och Service Workers**

För att injicera och tolka ett eget A(S)GI-system eller dynamiska service workers i den valda infrastrukturen tillämpas en flerskiktad exekveringsmodell. Genom att kombinera resonemangslogiken i smolagents med exekveringsytan i E2B skapas ett deterministiskt flöde mellan orkestrering och isolerad maskinvarukod2.  
Inledningsvis utvärderar A(S)GI-motorn sitt nuvarande tillstånd och genererar källkod eller en beräkningsgraf2. Innan koden skickas till exekvering körs en valideringsfas2. I smolagents uppnås detta genom att kontrollera att kodens moduler och importanrop matchar de auktoriserade biblioteken som angivits i konfigurationen2. För ett A(S)GI-system innebär detta injektion av komplexa databehandlingsbibliotek som NumPy, PyTorch eller anpassade interna agentmoduler2.  
Därefter anropar agenten programmatiskt E2B SDK för att begära en ny sandbox-instans eller återuppta en befintlig instans4. Vid anropet specificeras vilken förkonfigurerad mall (template ID) som skall användas1. Mallen innehåller operativsystemsbilden, förinstallerade Python-paket, miljövariabler och eventuella bakgrundstjänster1.  
När microVM-instansen rapporterar färdigt tillstånd skickas koden över via ett säkert REST/gRPC-gränssnitt3. Till skillnad från enkla kommandoradsexekutorer upprätthåller E2B:s CodeInterpreter en ihållande REPL-session (Read-Eval-Print Loop)1. Detta gör att variabeltillstånd, laddade modeller och dataframes bevaras mellan upprepade kodeskaleringar utan att miljön behöver startas om1.  
När målet är att köra service workers snarare än linjära agentsteg fungerar sandlådan som en händelsedriven exekveringsnod1. Service workern injiceras som en ständigt lyssnande process i microVM-miljön, kapabel att ta emot inkommande HTTP-förfrågningar, bearbeta dataströmmar och interagera med nätverksresurser inom de gränser som definierats av E2B:s nätverkspolicyer1.

## **Jämförande Analys av Självhostade och Cloud-Native Isoleringsplattformar**

Medan E2B erbjuder en färdig hanterad plattform med goda möjligheter till självhosting via Terraform på AWS eller GCP4, kräver många enterprise-arkitekturer full kontroll över hårdvaran eller integration med befintliga Kubernetes-kluster18. För dessa fall utgör mjukvarusamlingarna Kata Containers och KubeVirt de primära öppna källkodsbyggstenarna19.

| Egenskap / Dimension | smolagents (Local Executor) | Docker Containers | E2B (Firecracker microVM) | Kata Containers (K8s) | WebAssembly (WasmEdge/WAMR) |
| :---- | :---- | :---- | :---- | :---- | :---- |
| **Isoleringsnivå** | Ingen (AST/Python-kodnivå)5 | Processnivå (Namespaces/cgroups)8 | Hårdvarunivå (KVM microVM)7 | Hårdvarunivå (MicroVM per Pod)19 | Sandlåda i bytekods-VM8 |
| **Kallstartstid** | \< 1 ms17 | 500 ms – 2 s8 | \~150 – 200 ms3 | 1 s – 3 s8 | \< 10 ms8 |
| **Kärn-arkitektur** | Delar värdens kärna och process6 | Delar värdens kärna14 | Dedikerad Linux-kärna per maskin7 | Dedikerad Linux-kärna per Pod20 | Ingen Linux-kärna (Wasm Runtime)8 |
| **Tillståndshantering** | Enhetsinternt Python-minne17 | Statiska volymer / bind mounts16 | Snapshots & Pause/Resume i minne7 | Kubernetes Persistent Volumes19 | Statisk Wasm-kontext22 |
| **Lämplighet för A(S)GI / Workers** | Endast lokal utvärdering5 | Standardiserad agentexekvering5 | Optimal för opålitlig kod & A(S)GI1 | Optimal för orkestrerad enterprise-K8s19 | Optimal för ultrahastighets Service Workers22 |

### **Kata Containers: Container-gränssnitt med MicroVM-isolering**

Kata Containers är ett öppen källkodsprojekt som implementerar OCI- (Open Container Initiative) och Kubernetes CRI-gränssnitten (Container Runtime Interface)19. Istället för att köra poddar som vanliga Linux-processer på värdkärnan, skapar Kata Containers en lättviktig virtuell maskin för varje Pod20. Som hypervisor kan Kata Containers använda QEMU, Cloud-Hypervisor eller Firecracker19.  
För en A(S)GI-arkitektur innebär detta att utvecklaren kan använda standardiserade Kubernetes-deklarationer (YAML) och K8s-orkestrering, samtidigt som exekveringen erhåller hårdvaruisolering på kärnnivå19. Detta möjliggör säker exekvering av opålitliga agent-workers direkt i ett delat Kubernetes-kluster19.

### **KubeVirt: Virtuella Maskiner som Kubernetes-resurser**

KubeVirt är en Kubernetes-operator som gör det möjligt att definiera, starta och hantera traditionella eller lätta virtuella maskiner sida vid sida med vanliga poddar19. Genom Custom Resource Definitions (CRD:er) kan ett A(S)GI-styrsystem programmatiskt initiera hela VM-instanser via Kubernetes API18. KubeVirt är särskilt användbart när A(S)GI-systemet kräver fullständiga operativsystem, komplexa kernellägen eller dedikerad GPU-pass-through som inte enkelt ryms i en förenklad microVM-miljö19.

### **WebAssembly som Alternativ för Ultralätta Service Workers**

När beräkningsenheterna utgörs av kortlivade, händelsedrivna service workers snarare än fullständiga Python-baserade A(S)GI-agenter, utgör WebAssembly-runtimes som WasmEdge eller WAMR (WebAssembly Micro Runtime) ett kraftfullt alternativ22.  
WebAssembly ger extremt snabb kallstart (ofta under 10 millisekunder) och ett minimalt minnesavtryck8. Eftersom Wasm-runtimes isolerar koden i en bytekodssandlåda på applikationsnivå krävs ingen hel Linux-kärna per worker8. Detta möjliggör hög packningstäthet på servrarna, men sätter begränsningar vad gäller kompatibilitet med vanliga C/Python-bibliotek för AI jämfört med Firecracker microVMs8.

## **Slutsatser och Strategiska Rekommendationer**

För att implementera ett system där en A(S)GI eller autonom agent fritt kan initiera, injicera och exekvera sin egen logik krävs en tydlig skiktning av mjukvarustacken1. Valet av källkodssamlingar styrs främst av kraven gällande kontroll, flexibilitet och infrastrukturinvestering:  
För snabb utveckling och direkt integrering med AI-modeller rekommenderas kombinationen av Hugging Face smolagents och E2B Sandbox2. smolagents tillhandahåller det minimalistiska kodgenererande agentgränssnittet, medan E2B levererar hårdvaruisolerade Firecracker microVMs med delsekundsnabb kallstart och tillståndspersistens via snapshots2.  
För cloud-native och självhostad storskalig infrastruktur är det mest robusata valet att implementera Kata Containers på ett Kubernetes-kluster19. Detta tillåter programmatisk pod-initiering via Kubernetes API med full isolation per microVM, utan beroende av externa molntjänster19.  
För ultrahastighets Service Workers bör händelsedrivna WebAssembly-miljöer (WasmEdge eller WAMR) utvärderas när beräkningarna består av enkla, deterministiska mikrotjänster med extrema krav på låg latens och hög packningstäthet22. Genom att isolera opålitlig kod i hårdvarubaserade microVMs eller bytekodssandlådor elimineras de fundamentala säkerhetsriskerna med dynamisk kodgenerering, samtidigt som A(S)GI-systemet ges full frihet att skapa, anpassa och köra sina egna exekveringsmiljöer1.

#### **Works cited**

> 1. E2B Review: AI Agent Sandbox Pricing, Code Interpreter, MCP, [https://aiidelist.com/ide/e2b](https://aiidelist.com/ide/e2b)  
> 2. SmolAgents by HuggingFace : AI Agents That Write Python Tools on, [https://medium.com/@speaktoharisudhan/smolagents-by-huggingface-ai-agents-that-executes-code-in-python-gemini-c97bc4bd3c87](https://medium.com/@speaktoharisudhan/smolagents-by-huggingface-ai-agents-that-executes-code-in-python-gemini-c97bc4bd3c87)  
> 3. GitHub \- api-evangelist/e2b, [https://github.com/api-evangelist/e2b](https://github.com/api-evangelist/e2b)  
> 4. GitHub \- e2b-dev/E2B: Open-source, secure environment with real, [https://github.com/e2b-dev/e2b](https://github.com/e2b-dev/e2b)  
> 5. smolagents (HuggingFace) \- SkillPack, [https://www.skillpack.co/solutions/smolagents](https://www.skillpack.co/solutions/smolagents)  
> 6. Security \- Overview · huggingface/smolagents \- GitHub, [https://github.com/huggingface/smolagents/security](https://github.com/huggingface/smolagents/security)  
> 7. E2B | Ry Walker Research, [https://rywalker.com/research/e2b](https://rywalker.com/research/e2b)  
> 8. GitHub \- restyler/awesome-sandbox, [https://github.com/restyler/awesome-sandbox](https://github.com/restyler/awesome-sandbox)  
> 9. E2B \- AI Agent Code Sandbox \- Wiki \- clawbot, [https://clawbot.ai/wiki/apis/e2b-ai-agent-code-sandbox.html](https://clawbot.ai/wiki/apis/e2b-ai-agent-code-sandbox.html)  
> 10. Smolagents (Hugging Face) \- Lightweight Agents \- Wiki \- clawbot, [https://clawbot.ai/wiki/apis/smolagents-lightweight-agents.html](https://clawbot.ai/wiki/apis/smolagents-lightweight-agents.html)  
> 11. smolagents: a barebones library for agents that think in code. \- GitHub, [https://github.com/huggingface/smolagents](https://github.com/huggingface/smolagents)  
> 12. Smolagents Cheat Sheet. Hugging Face's minimal library for… |, [https://medium.com/@deeptij2007/smolagents-cheat-sheet-b6cde206db58](https://medium.com/@deeptij2007/smolagents-cheat-sheet-b6cde206db58)  
> 13. smolagents \- Skill | Smithery, [https://smithery.ai/skills/svngoku/smolagents](https://smithery.ai/skills/svngoku/smolagents)  
> 14. E2B vs Daytona: Sandbox Comparison for Platform Engineers, [https://www.zenml.io/blog/e2b-vs-daytona](https://www.zenml.io/blog/e2b-vs-daytona)  
> 15. containers/e2b-sandbox/README.md · ar08/zzz at main, [https://huggingface.co/spaces/ar08/zzz/blob/main/containers/e2b-sandbox/README.md](https://huggingface.co/spaces/ar08/zzz/blob/main/containers/e2b-sandbox/README.md)  
> 16. Seeking secure Python code execution solutions for LLM output, [https://www.reddit.com/r/LLMDevs/comments/1ilhi0r/seeking\_secure\_python\_code\_execution\_solutions/](https://www.reddit.com/r/LLMDevs/comments/1ilhi0r/seeking_secure_python_code_execution_solutions/)  
> 17. Add exec-sandbox executor (self-hosted QEMU microVM sandbox), [https://github.com/huggingface/smolagents/issues/2000](https://github.com/huggingface/smolagents/issues/2000)  
> 18. e2b-alternative · GitHub Topics, [https://github.com/topics/e2b-alternative](https://github.com/topics/e2b-alternative)  
> 19. kata-containers · GitHub Topics, [https://github.com/topics/kata-containers](https://github.com/topics/kata-containers)  
> 20. Confidential Computing \- Akash Network, [https://akash.network/roadmap/aep-65/](https://akash.network/roadmap/aep-65/)  
> 21. veilair/cloud-native-development \- GitHub, [https://github.com/veilair/cloud-native-development](https://github.com/veilair/cloud-native-development)  
> 22. edge-computing · GitHub Topics, [https://github.com/topics/edge-computing](https://github.com/topics/edge-computing)  
> 23. 3W for In-Browser AI: WebLLM \+ WASM \+ WebWorkers, [https://blog.mozilla.ai/3w-for-in-browser-ai-webllm-wasm-webworkers/](https://blog.mozilla.ai/3w-for-in-browser-ai-webllm-wasm-webworkers/)  
> 24. KubeVirt \- GitHub, [https://github.com/kubevirt](https://github.com/kubevirt)  
> 25. Releases · wasm-micro-runtime/wasm-micro-runtime \- GitHub, [https://github.com/bytecodealliance/wasm-micro-runtime/releases](https://github.com/bytecodealliance/wasm-micro-runtime/releases)