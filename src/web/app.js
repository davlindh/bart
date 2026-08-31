/**
 * BART Omnipod Application Controller v3.0
 * Reactive state, pivot-navigation, animated counters, breadcrumbs,
 * keyboard shortcuts, window routing, REST API integration, HITL engine.
 */

document.addEventListener('DOMContentLoaded', () => {

  // ─── Global State ────────────────────────────────────────────────────────

  const state = {
    currentScenarioId: 'mixed_q3',
    currentScenario: null,
    currentRole: 'CFO',
    currentScope: 'D1',
    currentStepIndex: 1,
    selectedTxId: 'TX-1001',
    agentStatus: 'Redo',
    auditResult: null,
    contextPacket: null,
    agentResult: null,
    approvedVouchersCount: 0,
    navigationStack: [],   // Breadcrumb trail
    currentWindow: 'W5',   // Active Omnipod window
    currentAgent: 'TaxOptimizationAgent',
    isAgentRunning: false
  };

  // ─── DOM References ───────────────────────────────────────────────────────

  const scenarioSelect       = document.getElementById('scenarioSelect');
  const roleSelect           = document.getElementById('roleSelect');
  const perspectiveBadge     = document.getElementById('perspectiveBadge');
  const perspectiveWindowName= document.getElementById('perspectiveWindowName');
  const scopeSlider          = document.getElementById('scopeSlider');
  const scopeValueLabel      = document.getElementById('scopeValueLabel');
  const scopeTicks           = document.querySelectorAll('.scope-ticks .tick');

  const telGrossTurnover     = document.getElementById('telGrossTurnover');
  const telPotentialSavings  = document.getElementById('telPotentialSavings');
  const telEfficiency        = document.getElementById('telEfficiency');

  const focalEntityTitle     = document.getElementById('focalEntityTitle');
  const focalEntityMeta      = document.getElementById('focalEntityMeta');
  const contextIdTag         = document.getElementById('contextIdTag');
  const domainsGrid          = document.getElementById('domainsGrid');
  const obsList              = document.getElementById('obsList');
  const obsCount             = document.getElementById('obsCount');

  const momsFalt05           = document.getElementById('momsFalt05');
  const momsFalt08           = document.getElementById('momsFalt08');
  const momsFalt10           = document.getElementById('momsFalt10');
  const momsFalt41           = document.getElementById('momsFalt41');
  const momsFalt49           = document.getElementById('momsFalt49');

  const agentSelect          = document.getElementById('agentSelect');
  const agentStatusBadge     = document.getElementById('agentStatusBadge');
  const btnRunFullLoop       = document.getElementById('btnRunFullLoop');
  const btnStepNext          = document.getElementById('btnStepNext');
  const btnResetStepper      = document.getElementById('btnResetStepper');
  const stepDetailsTitle     = document.getElementById('stepDetailsTitle');
  const stepDetailsBody      = document.getElementById('stepDetailsBody');
  const activeDiffTxId       = document.getElementById('activeDiffTxId');
  const diffLegalBasis       = document.getElementById('diffLegalBasis');
  const btnApproveVoucher    = document.getElementById('btnApproveVoucher');
  const hitlStatusText       = document.getElementById('hitlStatusText');

  const canvasNodeCount      = document.getElementById('canvasNodeCount');
  const btnResetCanvas       = document.getElementById('btnResetCanvas');
  const satellitesPills      = document.getElementById('satellitesPills');

  const voucherCount         = document.getElementById('voucherCount');
  const voucherTableBody     = document.getElementById('voucherTableBody');

  const breadcrumbNav        = document.getElementById('breadcrumbNav');
  const windowSidebar        = document.getElementById('windowSidebar');
  const perspectiveDynamicContainer = document.getElementById('perspectiveDynamicContainer');
  const perspectiveDefaultW5Container = document.getElementById('perspectiveDefaultW5Container');
  const btnRun12AgentLoop    = document.getElementById('btnRun12AgentLoop');
  const btnFortnoxSync       = document.getElementById('btnFortnoxSync');
  const btnFortnoxCustomers  = document.getElementById('btnFortnoxCustomers');
  const btnToggleERD         = document.getElementById('btnToggleERD');

  const customerModalOverlay = document.getElementById('customerModalOverlay');
  const btnCloseCustomerModal = document.getElementById('btnCloseCustomerModal');
  const customerCardsGrid    = document.getElementById('customerCardsGrid');
  const custSearchInput      = document.getElementById('custSearchInput');
  const custFilterPills      = document.getElementById('custFilterPills');
  const custKpiCount         = document.getElementById('custKpiCount');
  const custKpiTurnover      = document.getElementById('custKpiTurnover');
  const custKpiSavings       = document.getElementById('custKpiSavings');

  let loadedCustomers = [];
  let currentCustFilter = 'ALL';


  // ─── Spatial Canvas Init ─────────────────────────────────────────────────

  const canvas = new window.SpatialCanvas('spatialCanvas');

  canvas.onNodeClick((node) => {
    if (node.type === 'transaction') {
      selectTransaction(node.id);
      pushBreadcrumb({ id: node.id, name: node.name, type: 'transaction' });
    } else {
      pushBreadcrumb({ id: node.id, name: node.name, type: node.type });
    }
  });

  canvas.onPivot((node) => {
    // Double-click: full context repivot
    pivotContext(node.id, node.type, node.name);
  });

  btnResetCanvas.addEventListener('click', () => {
    canvas.resetLayout();
    Toast.info('Grafvy återställd');
  });

  // ─── Role & Domain Mappings ───────────────────────────────────────────────

  const rolePerspectives = {
    'CFO': 'W5: Financial Management',
    'Ekonomiansvarig': 'W5: Financial Management',
    'Revisor': 'W3: Evaluation',
    'Säljare': 'W2: Matching & Sales',
    'Verkstadschef': 'W4: Resource Allocation'
  };

  const roleDomains = {
    'CFO':              ['Operational', 'Exchange', 'Trust', 'Knowledge', 'Tools'],
    'Ekonomiansvarig':  ['Operational', 'Exchange', 'Trust', 'Knowledge'],
    'Revisor':          ['Operational', 'Exchange', 'Trust'],
    'Säljare':          ['Exchange', 'Interactional Interface', 'Tools'],
    'Verkstadschef':    ['Operational', 'Tools', 'Interactional Interface']
  };

  // ─── Animated Counter ─────────────────────────────────────────────────────

  /**
   * Smoothly animate a numeric value change in an element.
   * @param {HTMLElement} el - Target element
   * @param {number} targetVal - Target numeric value
   * @param {Function} formatter - Format function (value) => string
   * @param {number} duration - Animation duration in ms
   */
  function animateCounter(el, targetVal, formatter, duration = 850) {
    const startStr = el.textContent.replace(/[^\d.-]/g, '');
    const startVal = parseFloat(startStr) || 0;
    if (Math.abs(startVal - targetVal) < 0.01) return;

    const startTime = performance.now();
    const easeOut = (t) => 1 - Math.pow(1 - t, 3);

    function step(now) {
      const elapsed = now - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const current = startVal + (targetVal - startVal) * easeOut(progress);
      el.textContent = formatter(current);
      if (progress < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
  }

  // ─── Format Helpers ───────────────────────────────────────────────────────

  function formatSEK(amount) {
    return new Intl.NumberFormat('sv-SE', {
      style: 'currency', currency: 'SEK', maximumFractionDigits: 0
    }).format(amount);
  }

  function formatSEKShort(amount) {
    if (Math.abs(amount) >= 1000) {
      return (amount / 1000).toFixed(1).replace('.', ',') + ' k SEK';
    }
    return formatSEK(amount);
  }

  // ─── Breadcrumb Navigation ────────────────────────────────────────────────

  function pushBreadcrumb(node) {
    // Avoid duplicate consecutive entries
    const last = state.navigationStack[state.navigationStack.length - 1];
    if (last && last.id === node.id) return;

    state.navigationStack.push(node);
    if (state.navigationStack.length > 6) state.navigationStack.shift();
    renderBreadcrumbs();
  }

  function renderBreadcrumbs() {
    if (!breadcrumbNav) return;
    breadcrumbNav.innerHTML = '';

    state.navigationStack.forEach((crumb, idx) => {
      const item = document.createElement('span');
      item.className = `crumb${idx === state.navigationStack.length - 1 ? ' crumb-active' : ''}`;
      item.textContent = crumb.name.length > 22 ? crumb.name.slice(0, 20) + '\u2026' : crumb.name;
      item.title = crumb.name;

      if (idx < state.navigationStack.length - 1) {
        item.addEventListener('click', () => {
          state.navigationStack = state.navigationStack.slice(0, idx + 1);
          renderBreadcrumbs();
          if (crumb.type === 'transaction') selectTransaction(crumb.id);
          canvas.pivotTo(crumb.id);
        });
      }

      breadcrumbNav.appendChild(item);

      if (idx < state.navigationStack.length - 1) {
        const sep = document.createElement('span');
        sep.className = 'crumb-sep';
        sep.textContent = '›';
        breadcrumbNav.appendChild(sep);
      }
    });

    // Scroll to latest crumb
    requestAnimationFrame(() => {
      if (breadcrumbNav.lastElementChild) {
        breadcrumbNav.lastElementChild.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'end' });
      }
    });
  }

  // ─── Pivot Context (full context repivot on double-click) ─────────────────

  async function pivotContext(entityId, entityType, entityName) {
    Toast.info(`Pivoterar kontext → ${entityName || entityId}`, 2500);
    pushBreadcrumb({ id: entityId, name: entityName || entityId, type: entityType });

    // Update focal entity display
    if (focalEntityTitle) focalEntityTitle.textContent = entityName || entityId;
    if (focalEntityMeta) focalEntityMeta.textContent = `Typ: ${entityType} • Scope: ${state.currentScope}`;

    // Re-resolve context centered on this entity
    try {
      const res = await fetch('/api/context/resolve', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          role: state.currentRole,
          scope: state.currentScope,
          purpose: `Djupanalys av ${entityType}: ${entityName}`,
          task: 'Identifiera relaterade optimeringsmöjligheter',
          target_entity: { id: entityId, title: entityName, type: entityType }
        })
      });
      const packet = await res.json();
      state.contextPacket = packet;
      if (contextIdTag) contextIdTag.textContent = packet.context_id;
      if (packet.recommended_next_nodes) renderSatellites(packet.recommended_next_nodes);
    } catch (err) {
      console.warn('Context pivot error:', err);
    }

    // Refresh graph centered on new focal entity
    await fetchGraphData(entityId);

    // Reset stepper for fresh analysis
    setStep(1);
    if (agentStatusBadge) agentStatusBadge.textContent = 'Redo';
  }

  // ─── API Calls ────────────────────────────────────────────────────────────

  async function loadScenario(scenarioId) {
    try {
      const res = await fetch(`/api/scenario/${scenarioId}`);
      const data = await res.json();
      state.currentScenario = data;
      state.currentScenarioId = scenarioId;

      if (focalEntityTitle) focalEntityTitle.textContent = data.title;
      if (focalEntityMeta) focalEntityMeta.textContent = `${data.transactions.length} transaktioner • Period: ${data.period}`;

      // Seed first breadcrumb
      state.navigationStack = [];
      pushBreadcrumb({ id: scenarioId, name: data.title, type: 'batch' });

      await runWindowAudit();
      await resolveContext();
      await fetchGraphData();
      updateDiffDisplay();
    } catch (err) {
      console.error('Error loading scenario:', err);
      Toast.error('Kunde inte ladda scenariot. Kontrollera att servern kör på port 8765.');
    }
  }

  async function runWindowAudit() {
    if (!state.currentScenario) return;
    try {
      const res = await fetch('/api/window/audit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          transactions: state.currentScenario.transactions,
          input_vat_total: state.currentScenario.input_vat_total,
          period: state.currentScenario.period
        })
      });
      const data = await res.json();
      state.auditResult = data;

      // Animated telemetry update
      const rawGross  = data.total_gross_turnover_sek;
      const rawSav    = data.tax_evaluation.total_potential_savings_sek;
      const rawEff    = data.tax_efficiency_score * 100;

      animateCounter(telGrossTurnover, rawGross, v => formatSEK(v));
      animateCounter(telPotentialSavings, rawSav, v => '+' + formatSEK(v));
      animateCounter(telEfficiency, rawEff, v => v.toFixed(1) + '%');

      const moms = data.momsdeklaration;
      animateCounter(momsFalt05, moms.falt_05_momspliktig_forsaljning_25, formatSEK);
      animateCounter(momsFalt08, moms.falt_08_vmb_marginal, formatSEK);
      animateCounter(momsFalt10, moms.falt_10_utgaende_moms_25, formatSEK);
      animateCounter(momsFalt41, moms.falt_41_omvand_byggmoms, formatSEK);
      animateCounter(momsFalt49, moms.falt_49_moms_att_betala_eller_fa_tillbaka, formatSEK);

      renderObservations(data.observations);
    } catch (err) {
      console.error('Error auditing window:', err);
    }
  }

  async function resolveContext() {
    try {
      const res = await fetch('/api/context/resolve', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          role: state.currentRole,
          scope: state.currentScope,
          purpose: 'Skatterevision och likviditetsoptimering',
          task: 'Granska felaktiga momssatser och outnyttjade avdrag',
          target_entity: {
            id: state.currentScenarioId,
            title: state.currentScenario ? state.currentScenario.title : '',
            transactions: state.currentScenario ? state.currentScenario.transactions : []
          }
        })
      });
      const packet = await res.json();
      state.contextPacket = packet;
      if (contextIdTag) contextIdTag.textContent = packet.context_id;
      if (packet.recommended_next_nodes) renderSatellites(packet.recommended_next_nodes);
    } catch (err) {
      console.error('Error resolving context:', err);
    }
  }

  async function fetchGraphData(focalId = null) {
    try {
      const params = new URLSearchParams({
        scenario_id: state.currentScenarioId,
        scope: state.currentScope,
        role: state.currentRole
      });
      if (focalId) params.set('focal_id', focalId);

      const res = await fetch(`/api/graph?${params}`);
      const graphData = await res.json();
      canvas.setData(graphData, focalId);
      if (canvasNodeCount) canvasNodeCount.textContent = `${graphData.count} Noder`;

      if (graphData.satellites && graphData.satellites.length > 0) {
        renderSatellites(graphData.satellites);
      }
    } catch (err) {
      console.error('Error fetching graph data:', err);
    }
  }

  // ─── Render Functions ─────────────────────────────────────────────────────

  function renderObservations(obs) {
    if (!obsList) return;
    obsList.innerHTML = '';
    if (obsCount) obsCount.textContent = obs.length;
    obs.forEach(o => {
      const item = document.createElement('div');
      item.className = 'obs-item';
      item.innerHTML = `
        <span class="obs-title">${o.metric_name}</span>
        <span class="obs-val">${typeof o.metric_value === 'number' ? formatSEK(o.metric_value) : o.metric_value}</span>
      `;
      obsList.appendChild(item);
    });
  }

  function renderSatellites(satellites) {
    if (!satellitesPills) return;
    satellitesPills.innerHTML = '';
    satellites.forEach(s => {
      const pill = document.createElement('div');
      pill.className = 'sat-pill';
      const name = s.name || s.title;
      const rel = ((s.relevance_score || s.relevance || 0.8) * 100).toFixed(0);
      pill.innerHTML = `
        <span class="sat-name">${name}</span>
        <span class="sat-relevance">${rel}%</span>
      `;
      pill.title = `Dubbelklicka för full pivot → ${name}`;
      pill.addEventListener('click', () => {
        if (s.target) {
          selectTransaction(s.target);
          canvas.pivotTo(s.target);
          pushBreadcrumb({ id: s.target, name, type: 'satellite' });
        }
      });
      pill.addEventListener('dblclick', () => {
        pivotContext(s.target || s.id || name, 'entity', name);
      });
      satellitesPills.appendChild(pill);
    });
  }

  function updateDomainsGrid() {
    const allowed = roleDomains[state.currentRole] || [];
    const allTags = domainsGrid ? domainsGrid.querySelectorAll('.domain-tag') : [];
    allTags.forEach(tag => {
      const dom = tag.getAttribute('data-domain');
      tag.className = allowed.includes(dom) ? 'domain-tag active' : 'domain-tag inactive';
    });
  }

  function selectTransaction(txId) {
    state.selectedTxId = txId;
    updateDiffDisplay();
    // Reset approve button
    if (btnApproveVoucher) {
      btnApproveVoucher.disabled = false;
      btnApproveVoucher.innerHTML = `
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
          <polyline points="20 6 9 17 4 12"></polyline>
        </svg>
        Godkänn Skatteoptimering & Bokför Verifikat
      `;
      btnApproveVoucher.style.background = '';
    }
    if (hitlStatusText) {
      hitlStatusText.textContent = 'Avvaktar mänskligt godkännande (HITL)';
      hitlStatusText.style.color = '';
    }
  }

  function updateDiffDisplay() {
    if (!state.currentScenario) return;
    const tx = state.currentScenario.transactions.find(t => t.transaction_id === state.selectedTxId)
             || state.currentScenario.transactions[0];
    if (!tx) return;

    if (activeDiffTxId) activeDiffTxId.textContent = `${tx.transaction_id} (${tx.description})`;

    const asIsCard = document.querySelector('.diff-card.as-is');
    const toBeCard = document.querySelector('.diff-card.to-be');

    if (tx.is_used_good) {
      const margin = tx.gross_amount - tx.purchase_cost_ex_vat;
      const vmbVat = margin * 0.20;
      const saved  = tx.current_vat_amount - vmbVat;

      asIsCard.innerHTML = `
        <div class="diff-card-title">NUVARANDE BOKFÖRING (AS-IS)</div>
        <div class="diff-metric"><span>Regel:</span> <strong>Standardmoms 25%</strong></div>
        <div class="diff-metric"><span>BAS-Konto:</span> <code>3001 Försäljning 25% moms</code></div>
        <div class="diff-metric alert-negative"><span>Utgående moms:</span> <strong class="text-rose">${formatSEK(tx.current_vat_amount)}</strong></div>
        <div class="diff-metric"><span>Nettomarginal:</span> <strong>${formatSEK(tx.gross_amount / 1.25 - tx.purchase_cost_ex_vat)}</strong></div>
      `;
      toBeCard.innerHTML = `
        <div class="diff-card-title">OPTIMERING (OMNIPOD VMB)</div>
        <div class="diff-metric"><span>Regel:</span> <strong class="text-emerald">VMB Marginalbeskattning (ML 9a kap)</strong></div>
        <div class="diff-metric"><span>BAS-Konto:</span> <code>3051 Försäljning varor VMB</code></div>
        <div class="diff-metric alert-positive"><span>Utgående moms:</span> <strong class="text-emerald">${formatSEK(vmbVat)} (-${formatSEK(saved)})</strong></div>
        <div class="diff-metric"><span>Nettomarginal:</span> <strong class="text-emerald">${formatSEK(tx.gross_amount - vmbVat - tx.purchase_cost_ex_vat)} (+71,4% Vinstökning)</strong></div>
      `;
      if (diffLegalBasis) diffLegalBasis.innerHTML = `<strong>Laglig Grund:</strong> ML (1994:200 / 2023:200) 9a kap. Inköpt från privatperson utan avdragsgill ingående moms. Endast marginalen (${formatSEK(margin)}) beskattas med 20%, vilket sparar ${formatSEK(saved)} i moms.`;

    } else if (tx.is_garden_or_installation_work && tx.customer && !tx.customer.is_company) {
      const labor = tx.labor_share_amount || 8000.0;
      const rutDeduction = labor * 0.50;

      asIsCard.innerHTML = `
        <div class="diff-card-title">NUVARANDE OFFERT (AS-IS)</div>
        <div class="diff-metric"><span>Regel:</span> <strong>Heldebitering utan RUT</strong></div>
        <div class="diff-metric"><span>BAS-Konto:</span> <code>3001 Normalförsäljning</code></div>
        <div class="diff-metric alert-negative"><span>Kundpris att betala:</span> <strong class="text-rose">${formatSEK(tx.gross_amount)}</strong></div>
        <div class="diff-metric"><span>Konverteringsrisk:</span> <strong>Hög tröskel för privatkund</strong></div>
      `;
      toBeCard.innerHTML = `
        <div class="diff-card-title">OPTIMERING (RUT-AVDRAG 50%)</div>
        <div class="diff-metric"><span>Regel:</span> <strong class="text-emerald">IL 67 kap. Skattereduktion RUT</strong></div>
        <div class="diff-metric"><span>BAS-Konto:</span> <code>3002 Försäljning RUT arbetskostnad</code></div>
        <div class="diff-metric alert-positive"><span>Kundpris att betala:</span> <strong class="text-emerald">${formatSEK(tx.gross_amount - rutDeduction)} (-${formatSEK(rutDeduction)})</strong></div>
        <div class="diff-metric"><span>Företagsintäkt:</span> <strong class="text-emerald">${formatSEK(tx.gross_amount)} (Intakt via Skv-rekvisition)</strong></div>
      `;
      if (diffLegalBasis) diffLegalBasis.innerHTML = `<strong>Laglig Grund:</strong> Inkomstskattelagen 67 kap. Installation av robotgräsklippare på tomt omfattas av RUT. Kunden sparar ${formatSEK(rutDeduction)} (50% av arbetet) medan företaget behåller 100% intäkt.`;

    } else if (tx.is_garden_or_installation_work && tx.customer && tx.customer.is_company) {
      asIsCard.innerHTML = `
        <div class="diff-card-title">NUVARANDE FAKTURA (FELAKTIG)</div>
        <div class="diff-metric"><span>Debiterad moms:</span> <strong class="text-rose">${formatSEK(tx.current_vat_amount)} (25%)</strong></div>
        <div class="diff-metric"><span>Efterlevnadsrisk:</span> <strong class="text-rose">Hög (Skatteverket krav)</strong></div>
      `;
      toBeCard.innerHTML = `
        <div class="diff-card-title">OPTIMERING (OMVÄND BYGGMOMS)</div>
        <div class="diff-metric"><span>Regel:</span> <strong class="text-emerald">ML 1 kap. 2 § första stycket 4 b</strong></div>
        <div class="diff-metric"><span>BAS-Konto:</span> <code>3231 Försäljning omvänd byggmoms</code></div>
        <div class="diff-metric alert-positive"><span>Debiterad moms:</span> <strong class="text-emerald">0,00 SEK (Köparen redovisar)</strong></div>
      `;
      if (diffLegalBasis) diffLegalBasis.innerHTML = `<strong>Laglig Grund:</strong> Mervärdesskattelagen 1 kap. 2 §. Köparen har SNI ${tx.customer.sni_code || '43.120'} (byggsektor) med F-skatt. Fakturan ska ställas utan moms till fält 41.`;

    } else {
      asIsCard.innerHTML = `
        <div class="diff-card-title">NUVARANDE HANTERING (AS-IS)</div>
        <div class="diff-metric"><span>Bokföring:</span> <code>1220 Inventarier (Avskrivning 5 år)</code></div>
        <div class="diff-metric"><span>År 1 Skatteavdrag:</span> <strong>${formatSEK(tx.net_amount / 5)}</strong></div>
      `;
      toBeCard.innerHTML = `
        <div class="diff-card-title">OPTIMERING (DIREKTAVSKRIVNING)</div>
        <div class="diff-metric"><span>Regel:</span> <strong class="text-emerald">IL 18 kap. 4 § Mindre värde &lt; 1/2 PBB</strong></div>
        <div class="diff-metric"><span>BAS-Konto:</span> <code>5410 Förbrukningsinventarier</code></div>
        <div class="diff-metric alert-positive"><span>År 1 Skatteavdrag:</span> <strong class="text-emerald">${formatSEK(tx.net_amount)} (100% direkt)</strong></div>
      `;
      if (diffLegalBasis) diffLegalBasis.innerHTML = `<strong>Laglig Grund:</strong> IL 18 kap. 4 §. Inköpet (${formatSEK(tx.net_amount)} ex moms) understiger ett halvt prisbasbelopp (28 650 SEK). 100% direktavdrag godkänns år 1.`;
    }
  }

  // ─── Agent Stepper ────────────────────────────────────────────────────────

  function setStep(stepIndex) {
    state.currentStepIndex = stepIndex;

    for (let i = 1; i <= 6; i++) {
      const node = document.getElementById(`stepNode${i}`);
      const line = document.getElementById(`stepLine${i}`);
      if (!node) continue;

      if (i < stepIndex) {
        node.className = 'step-node completed';
        if (line) line.className = 'step-line completed';
      } else if (i === stepIndex) {
        node.className = 'step-node active';
        if (line) line.className = 'step-line';
      } else {
        node.className = 'step-node';
        if (line) line.className = 'step-line';
      }
    }

    const stepInfos = [
      { title: 'Steg 1: Observation (Observe)',    desc: 'Agenten observerar telemetry: 4 finansiella transaktioner, motparter och momsdeklarationsfält.' },
      { title: 'Steg 2: Analys (Analyze)',         desc: 'Regelmotorn granskar transaktioner mot ML 9a kap (VMB), IL 67 kap (RUT), Byggmoms och PBB-gränser.' },
      { title: 'Steg 3: Diagnos (Identify)',       desc: '4 skatteläckage och optimeringsmöjligheter identifierade. Total potential: +9 296 SEK vinstökning.' },
      { title: 'Steg 4: Förslag (Propose)',        desc: 'Konkreta åtgärdsförslag genererade: Konvertera TX-1001 till VMB konto 3051, TX-1002 till RUT konto 3002.' },
      { title: 'Steg 5: Handling (Act)',           desc: 'Simulerar och förbereder balanserade bokföringsverifikat med automatisk debet- och kreditmatchning.' },
      { title: 'Steg 6: Utvärdering (Evaluate)',  desc: 'Verifierad skattebesparing: 5 296 SEK | Verifierad likviditetsökning: 9 296 SEK. Adoption: 100%.' }
    ];

    const info = stepInfos[stepIndex - 1];
    if (stepDetailsTitle) stepDetailsTitle.textContent = info.title;
    if (stepDetailsBody) stepDetailsBody.textContent = info.desc;
    if (agentStatusBadge) agentStatusBadge.textContent = `Steg ${stepIndex}/6`;
  }

  if (agentSelect) {
    agentSelect.addEventListener('change', (e) => {
      state.currentAgent = e.target.value;
      const opt = agentSelect.options[agentSelect.selectedIndex];
      Toast.info(`Aktiv agent: ${opt ? opt.text : state.currentAgent}`, 2500);
      setStep(1);
    });
  }

  if (btnStepNext) btnStepNext.addEventListener('click', async () => {
    const nextStep = Math.min(state.currentStepIndex + 1, 6);
    setStep(nextStep);
    try {
      const stepNames = ['observe', 'analyze', 'identify', 'propose', 'act', 'evaluate'];
      const stepName = stepNames[nextStep - 1];
      const res = await fetch('/api/agent/step', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          agent_name: state.currentAgent,
          step: stepName,
          role: state.currentRole,
          scope: state.currentScope,
          context: state.contextPacket
        })
      });
      const data = await res.json();
      const stepLabel = info(nextStep);
      const stepData = data.step_data || {};
      const outputMsg = stepData.output || data.output || 'Slutförd';
      if (stepDetailsBody) stepDetailsBody.textContent = `[${data.agent_name}] ${outputMsg}`;
      Toast.info(`${data.agent_name} (${stepLabel}): ${outputMsg}`, 3000);
    } catch (err) {
      console.error('Step error:', err);
      Toast.warning('Agent-steg misslyckades — kontrollera servern.');
    }
  });

  function info(step) {
    return ['Observe', 'Analyze', 'Identify', 'Propose', 'Act', 'Evaluate'][step - 1];
  }

  if (btnResetStepper) btnResetStepper.addEventListener('click', () => {
    setStep(1);
    if (agentStatusBadge) agentStatusBadge.textContent = 'Redo';
    Toast.info('Agentloop återställd');
  });

  if (btnRunFullLoop) btnRunFullLoop.addEventListener('click', async () => {
    if (state.isAgentRunning) return;
    state.isAgentRunning = true;
    if (agentStatusBadge) agentStatusBadge.textContent = `Kör ${state.currentAgent}...`;
    btnRunFullLoop.disabled = true;

    // Animate steps visually with delays
    for (let i = 1; i <= 6; i++) {
      await new Promise(r => setTimeout(r, 380));
      setStep(i);
    }

    try {
      const res = await fetch('/api/agent/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          agent_name: state.currentAgent,
          role: state.currentRole,
          scope: state.currentScope,
          context: state.contextPacket
        })
      });
      const result = await res.json();
      state.agentResult = result;

      if (agentStatusBadge) agentStatusBadge.textContent = 'Slutförd (100%)';
      if (stepDetailsTitle) stepDetailsTitle.textContent = `${result.agent_name} Körning Slutförd`;
      const recs = result.recommendations && result.recommendations.length ? result.recommendations.join(' • ') : 'Inga aktiva förslag.';
      if (stepDetailsBody) stepDetailsBody.textContent = `Rekommendationer: ${recs}`;
      Toast.success(`${result.agent_name} klar! ${(result.recommendations || []).length} rekommendationer genererade.`);
    } catch (err) {
      console.error('Agent run error:', err);
      Toast.error('Agentloop misslyckades. Servern kanske inte svarar.');
      if (agentStatusBadge) agentStatusBadge.textContent = 'Fel';
    } finally {
      state.isAgentRunning = false;
      btnRunFullLoop.disabled = false;
    }
  });

  // ─── HITL Approve Voucher ─────────────────────────────────────────────────

  if (btnApproveVoucher) btnApproveVoucher.addEventListener('click', async () => {
    btnApproveVoucher.disabled = true;
    btnApproveVoucher.innerHTML = `
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
        <polyline points="20 6 9 17 4 12"></polyline>
      </svg>
      Bokfört & Postat till Fortnox API!
    `;
    btnApproveVoucher.style.background = 'linear-gradient(135deg, #059669 0%, #047857 100%)';
    if (hitlStatusText) {
      hitlStatusText.textContent = 'Godkänd av användare (HITL) • Skickad till huvudbok';
      hitlStatusText.style.color = 'var(--accent-emerald)';
    }

    try {
      const res = await fetch('/api/voucher/approve', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          opportunity_id: `opp_${state.selectedTxId}`,
          transaction_id: state.selectedTxId,
          rule: state.selectedTxId === 'TX-1001' ? 'VMB_MARGIN_TAX_ML9A' : 'RUT_ARBETSKOSTNAD_50',
          amount: 16000.0,
          cost: 10000.0
        })
      });
      const data = await res.json();
      if (data.success) {
        addVoucherToTable(data.record.voucher);
        Toast.success(`Verifikat ${data.record.voucher.verifikat_id} bokfört och synkat!`);
      }
    } catch (err) {
      console.error('Approve voucher error:', err);
      Toast.error('Kunde inte posta verifikat.');
    }
  });

  function addVoucherToTable(voucher) {
    state.approvedVouchersCount++;
    if (voucherCount) voucherCount.textContent = `${state.approvedVouchersCount} bokfört verifikat`;

    // Insert rows in correct order (first row first) using appendChild
    voucher.rows.forEach(r => {
      const tr = document.createElement('tr');
      tr.style.animation = 'fadeIn 0.4s ease';
      tr.innerHTML = `
        <td><strong>${voucher.verifikat_id}</strong></td>
        <td>${r.account} (${r.description})</td>
        <td>${r.debet > 0 ? formatSEK(r.debet) : '-'}</td>
        <td>${r.kredit > 0 ? formatSEK(r.kredit) : '-'}</td>
        <td><span class="badge-balanced">BALANSERAD (OK)</span></td>
        <td><span class="badge-balanced">POSTAD</span></td>
      `;
      if (voucherTableBody) voucherTableBody.appendChild(tr);
    });

    // Scroll the voucher drawer to show the new rows
    const drawer = document.getElementById('zoneVoucherDrawer');
    if (drawer) {
      requestAnimationFrame(() => {
        drawer.scrollIntoView({ behavior: 'smooth', block: 'end' });
      });
    }
  }

  // ─── Window Sidebar Routing ───────────────────────────────────────────────

  const windowDefs = [
    { id: 'W1', label: 'Kontextualisering',    icon: '🔍', desc: 'Kunskapsgraf & Entitetssökning' },
    { id: 'W2', label: 'Matchning & Försäljning', icon: '💼', desc: 'Offertbyggare & RUT-konfigurator' },
    { id: 'W3', label: 'Utvärdering',           icon: '📋', desc: 'Revisionslogg & Efterlevnad' },
    { id: 'W4', label: 'Resursallokering',      icon: '🔧', desc: 'Maskinflotta & Verktygspark' },
    { id: 'W5', label: 'Ekonomihantering',      icon: '💰', desc: 'Skatteoptimering & Moms' },
    { id: 'W6', label: 'Personalhantering',     icon: '👥', desc: 'Teamroller & Kompetensmatris' },
    { id: 'W7', label: 'Kommunikation',         icon: '💬', desc: 'Beslutlogg & Mötesprotokoll' },
    { id: 'W8', label: 'Innovation & Teknik',   icon: '🧪', desc: 'Experimentstyrtavla & Hypoteser' },
    { id: 'W9', label: 'Adaptiva Insikter',     icon: '🧠', desc: 'Meta-lärningsloop & Agentanalys' }
  ];

  function renderWindowSidebar() {
    if (!windowSidebar) return;
    windowSidebar.innerHTML = '';

    windowDefs.forEach(w => {
      const item = document.createElement('button');
      item.className = `window-item${w.id === state.currentWindow ? ' active' : ''}`;
      item.id = `winBtn${w.id}`;
      item.title = `${w.id}: ${w.desc}`;
      item.innerHTML = `
        <span class="win-icon">${w.icon}</span>
        <span class="win-label">${w.id}</span>
      `;
      item.addEventListener('click', () => switchWindow(w.id));
      windowSidebar.appendChild(item);
    });
  }

  async function switchWindow(windowId) {
    if (state.currentWindow === windowId) return;
    state.currentWindow = windowId;
    renderWindowSidebar();

    const winDef = windowDefs.find(w => w.id === windowId);
    const label = winDef ? `${windowId}: ${winDef.label}` : windowId;
    if (perspectiveWindowName) perspectiveWindowName.textContent = label;

    // Pulse the perspective badge to signal window change
    if (perspectiveBadge) {
      perspectiveBadge.style.transition = 'box-shadow 0.3s ease';
      perspectiveBadge.style.boxShadow = '0 0 20px rgba(6,182,212,0.6)';
      setTimeout(() => { perspectiveBadge.style.boxShadow = ''; }, 600);
    }

    if (windowId === 'W5') {
      if (perspectiveDynamicContainer) perspectiveDynamicContainer.style.display = 'none';
      if (perspectiveDefaultW5Container) perspectiveDefaultW5Container.style.display = 'block';
      Toast.success('W5: Ekonomihantering — Skatteoptimering aktiv', 2000);
      return;
    }

    // Fetch live data for windows W1-W4, W6-W9
    try {
      if (perspectiveDefaultW5Container) perspectiveDefaultW5Container.style.display = 'none';
      if (perspectiveDynamicContainer) {
        perspectiveDynamicContainer.style.display = 'flex';
        perspectiveDynamicContainer.innerHTML = `<div style="color: var(--text-dim); font-size: 0.8rem; padding: 8px;">Laddar ${windowId}...</div>`;
      }

      const res = await fetch(`/api/window/${windowId}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();

      renderPerspectiveCard(windowId, winDef, data);
      Toast.info(`${windowId}: ${winDef ? winDef.label : windowId} laddat.`, 2500);
    } catch (err) {
      console.error(`Error loading window ${windowId}:`, err);
      Toast.warning(`Kunde inte ladda data för ${windowId}: ${err.message}`, 3000);
    }
  }

  function renderPerspectiveCard(windowId, winDef, data) {
    if (!perspectiveDynamicContainer) return;
    let html = `
      <div class="perspective-card">
        <div class="perspective-card-title">
          <span>${winDef ? winDef.icon : '🌐'}</span>
          <span>${data.title || windowId}</span>
        </div>
    `;

    if (windowId === 'W1') {
      html += `
        <div class="metric-grid-2x2">
          <div class="metric-card-mini"><div class="label">Relevans</div><div class="val positive">94%</div></div>
          <div class="metric-card-mini"><div class="label">Trender</div><div class="val">${(data.active_trends || []).length} aktiva</div></div>
        </div>
        <ul class="perspective-list">
          ${(data.strategic_opportunities || []).map(o => `<li><strong>${o.title}</strong>: +${o.value_sek.toLocaleString('sv-SE')} SEK</li>`).join('')}
        </ul>
      `;
    } else if (windowId === 'W2') {
      html += `
        <div class="metric-grid-2x2">
          <div class="metric-card-mini"><div class="label">Matchscore</div><div class="val positive">${data.optimal_matching_score * 100}%</div></div>
          <div class="metric-card-mini"><div class="label">Resurstillgång</div><div class="val">3 lediga</div></div>
        </div>
        <ul class="perspective-list">
          ${(data.matched_packages || []).map(p => `<li><strong>${p.name}</strong> (${p.vat_treatment})</li>`).join('')}
        </ul>
      `;
    } else if (windowId === 'W3') {
      html += `
        <div class="metric-grid-2x2">
          <div class="metric-card-mini"><div class="label">Regelefterlevnad</div><div class="val positive">${data.compliance_score * 100}%</div></div>
          <div class="metric-card-mini"><div class="label">Kundnöjdhet (CSAT)</div><div class="val positive">${data.customer_feedback_csat} / 5.0</div></div>
        </div>
        <ul class="perspective-list">
          ${(data.audit_checkpoints || []).map(c => `<li>✓ ${c.name} [${c.status}]</li>`).join('')}
        </ul>
      `;
    } else if (windowId === 'W4') {
      html += `
        <div class="metric-grid-2x2">
          <div class="metric-card-mini"><div class="label">Kapacitetsutnyttjande</div><div class="val">${data.capacity_utilization_pct}%</div></div>
          <div class="metric-card-mini"><div class="label">Rörelsekapital</div><div class="val positive">${data.working_capital_available_sek.toLocaleString('sv-SE')} kr</div></div>
        </div>
        <ul class="perspective-list">
          ${(data.allocations_by_department || []).map(a => `<li>${a.department}: ${a.hours_allocated}h (${a.budget_share_pct}% budget)</li>`).join('')}
        </ul>
      `;
    } else if (windowId === 'W6') {
      html += `
        <div class="metric-grid-2x2">
          <div class="metric-card-mini"><div class="label">Team Health Index</div><div class="val positive">${data.team_health_index}/100</div></div>
          <div class="metric-card-mini"><div class="label">Belastningsbalans</div><div class="val positive">${data.workload_distribution_score}/100</div></div>
        </div>
        <ul class="perspective-list">
          ${(data.roles_configured || []).map(r => `<li><strong>${r.role}</strong>: ${r.mandate}</li>`).join('')}
        </ul>
      `;
    } else if (windowId === 'W7') {
      html += `
        <div class="metric-grid-2x2">
          <div class="metric-card-mini"><div class="label">Kanaler</div><div class="val">${(data.active_channels || []).length} aktiva</div></div>
          <div class="metric-card-mini"><div class="label">Status</div><div class="val positive">60 FPS Realtime</div></div>
        </div>
        <ul class="perspective-list">
          ${(data.recent_broadcasts || []).map(b => `<li><strong>${b.sender}</strong>: ${b.msg}</li>`).join('')}
        </ul>
      `;
    } else if (windowId === 'W8') {
      html += `
        <div class="metric-grid-2x2">
          <div class="metric-card-mini"><div class="label">Aktiva Piloter</div><div class="val positive">${data.active_pilots_count} st</div></div>
          <div class="metric-card-mini"><div class="label">FoU-avdrag</div><div class="val positive">Kvalificerad</div></div>
        </div>
        <ul class="perspective-list">
          ${(data.pipeline_stages || []).map(s => `<li>[${s.stage}] ${s.initiative} (${s.status})</li>`).join('')}
        </ul>
      `;
    } else if (windowId === 'W9') {
      html += `
        <div class="metric-grid-2x2">
          <div class="metric-card-mini"><div class="label">Adaptivitet</div><div class="val positive">${data.system_adaptivity_score}%</div></div>
          <div class="metric-card-mini"><div class="label">Meta-Lärande</div><div class="val positive">Aktiv</div></div>
        </div>
        <ul class="perspective-list">
          ${(data.early_signals || []).map(s => `<li>⚠️ ${s.signal} (${Math.round(s.probability * 100)}% sannolikhet)</li>`).join('')}
        </ul>
      `;
    }

    html += `</div>`;
    perspectiveDynamicContainer.innerHTML = html;
  }

  // ─── Header Multi-Agent & Fortnox Actions ──────────────────────────────────

  if (btnRun12AgentLoop) {
    btnRun12AgentLoop.addEventListener('click', async () => {
      Toast.info('⚡ Startar 12-Agent Sluten Loop...', 2000);
      try {
        const res = await fetch('/api/agents/loop', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ role: state.currentRole, scope: state.currentScope })
        });
        const data = await res.json();
        if (data.results) {
          data.results.forEach((ag, idx) => {
            setTimeout(() => {
              Toast.info(`${ag.agent_name}: ${ag.recommendations[0] || 'Slutförd'}`, 2500);
            }, idx * 400);
          });
          setTimeout(() => {
            Toast.success(`✓ Samtliga ${data.executed_agents_count} agenter konvergerade i sluten loop!`, 4000);
          }, data.results.length * 400 + 500);
        }
      } catch (err) {
        Toast.warning(`Fel i 12-agent loop: ${err.message}`, 3000);
      }
    });
  }

  if (btnFortnoxSync) {
    btnFortnoxSync.addEventListener('click', async () => {
      Toast.info('📊 Hämtar levande Fortnox ERP telemetri...', 2000);
      try {
        const res = await fetch('/api/fortnox/summary');
        const data = await res.json();
        const metrics = data.team_dynamics_metrics;
        if (metrics) {
          animateCounter(telGrossTurnover, 115000, 142500, 1000, ' SEK');
          animateCounter(telPotentialSavings, 5296, 21200, 1000, '+', ' SEK');
          animateCounter(telEfficiency, 95.4, metrics.team_health_index, 1000, '', '%');
          Toast.success(`Fortnox Telemetri synkad: Team Health Index ${metrics.team_health_index}/100, Beslutstid ${metrics.decision_time_avg_days} dagar`, 4000);
        }
      } catch (err) {
        Toast.warning(`Fortnox synkroniseringsfel: ${err.message}`, 3000);
      }
    });
  }

  if (btnToggleERD) {
    btnToggleERD.addEventListener('click', async () => {
      Toast.info('🌐 Laddar Universal ERD Kunskapsgraf (15 Entiteter)...', 2000);
      try {
        const res = await fetch('/api/erd/graph');
        const data = await res.json();
        if (data.nodes) {
          canvas.loadData(data);
          if (canvasNodeCount) canvasNodeCount.textContent = `${data.count} Noder (Universal ERD)`;
          Toast.success('Universal ERD Kunskapsgraf aktiv (15 Entiteter)', 3500);
        }
      } catch (err) {
        Toast.warning(`Kunde inte ladda ERD-graf: ${err.message}`, 3000);
      }
    });
  }

  // ─── Fortnox Customers Modal Controller ────────────────────────────────────

  async function openCustomerModal() {
    if (!customerModalOverlay) return;
    customerModalOverlay.style.display = 'flex';
    Toast.info('👥 Hämtar Fortnox kundregister & skattetelemetri...', 1800);
    try {
      const res = await fetch('/api/fortnox/customers');
      const data = await res.json();
      loadedCustomers = data.customers || [];

      if (custKpiCount) custKpiCount.textContent = `${loadedCustomers.length} st`;
      if (custKpiTurnover) custKpiTurnover.textContent = `${Math.round(data.total_turnover_sek || 0).toLocaleString('sv-SE')} SEK`;
      if (custKpiSavings) custKpiSavings.textContent = `+${Math.round(data.total_potential_tax_savings_sek || 0).toLocaleString('sv-SE')} SEK`;

      renderCustomerCards();
      Toast.success(`✓ ${loadedCustomers.length} Fortnox-kunder analyserade & skatteklassificerade!`, 3500);
    } catch (err) {
      Toast.warning(`Kunde inte ladda kunder: ${err.message}`, 3000);
    }
  }

  function closeCustomerModal() {
    if (customerModalOverlay) customerModalOverlay.style.display = 'none';
  }

  function renderCustomerCards() {
    if (!customerCardsGrid) return;
    const query = (custSearchInput?.value || '').toLowerCase().trim();

    const filtered = loadedCustomers.filter(c => {
      const matchQuery = !query ||
        c.name.toLowerCase().includes(query) ||
        c.customer_number.toLowerCase().includes(query) ||
        (c.organisation_number && c.organisation_number.includes(query)) ||
        c.tax_profile_classification.toLowerCase().includes(query) ||
        (c.city && c.city.toLowerCase().includes(query));

      if (!matchQuery) return false;

      if (currentCustFilter === 'ALL') return true;
      if (currentCustFilter === 'RUT') return c.rut_eligible;
      if (currentCustFilter === 'VMB') return c.tax_profile_classification.includes('VMB');
      if (currentCustFilter === 'BYGG') return c.tax_profile_classification.includes('Byggmoms') || c.tax_profile_classification.includes('Omvänd');
      if (currentCustFilter === 'COMPANY') return c.customer_type === 'COMPANY';
      return true;
    });

    if (filtered.length === 0) {
      customerCardsGrid.innerHTML = `
        <div style="grid-column: 1/-1; padding: 40px; text-align: center; color: var(--text-dim);">
          Inga kunder matchar filtreringen.
        </div>
      `;
      return;
    }

    customerCardsGrid.innerHTML = filtered.map(c => {
      const isCompany = c.customer_type === 'COMPANY';
      let taxBadgeClass = 'cust-tax-badge';
      let taxBadgeIcon = '🏷️';
      if (c.tax_profile_classification.includes('VMB')) {
        taxBadgeClass += ' vmb';
        taxBadgeIcon = '🔄';
      } else if (c.tax_profile_classification.includes('Byggmoms') || c.tax_profile_classification.includes('Omvänd')) {
        taxBadgeClass += ' reverse';
        taxBadgeIcon = '🏗️';
      } else if (c.tax_profile_classification.includes('RUT')) {
        taxBadgeIcon = '🏡';
      }

      let paymentPillClass = 'cust-payment-pill';
      if (c.credit_risk_rating === 'LÅG') paymentPillClass += ' positive';
      else if (c.credit_risk_rating === 'FÖRHÖJD') paymentPillClass += ' warning';

      return `
        <div class="customer-card">
          <div class="cust-card-top">
            <div>
              <div class="cust-name">${c.name}</div>
              <div class="cust-submeta">${c.customer_number} • ${c.organisation_number} • ${c.city}</div>
            </div>
            <span class="cust-type-badge ${isCompany ? 'company' : 'private'}">
              ${isCompany ? 'Företag B2B' : 'Privatperson B2C'}
            </span>
          </div>

          <div>
            <span class="${taxBadgeClass}">${taxBadgeIcon} ${c.tax_profile_classification}</span>
          </div>

          <div class="cust-stats-grid">
            <div class="cust-stat">
              <span class="cust-stat-label">Total Omsättning</span>
              <span class="cust-stat-val">${Math.round(c.total_invoiced_gross).toLocaleString('sv-SE')} kr</span>
            </div>
            <div class="cust-stat">
              <span class="cust-stat-label">Skattebesparing</span>
              <span class="cust-stat-val savings">+${Math.round(c.potential_tax_savings_sek).toLocaleString('sv-SE')} kr</span>
            </div>
            <div class="cust-stat">
              <span class="cust-stat-label">Fakturor / Betalning</span>
              <span class="cust-stat-val">${c.invoices_count} st • ${c.payment_terms_days}d villkor</span>
            </div>
            <div class="cust-stat">
              <span class="cust-stat-label">Kreditrisk / Friktion</span>
              <span class="cust-stat-val">${c.credit_risk_rating} (Index ${c.friction_index})</span>
            </div>
          </div>

          <div class="cust-card-bottom">
            <span class="${paymentPillClass}">${c.payment_status} (${c.avg_payment_delay_days > 0 ? '+' : ''}${c.avg_payment_delay_days}d)</span>
            <button class="btn-cust-action" onclick="window.focusCustomerInERD('${c.customer_number}', '${c.name.replace(/'/g, "\\'")}')">
              🌐 Fokusera i ERD
            </button>
          </div>
        </div>
      `;
    }).join('');
  }

  window.focusCustomerInERD = (custNum, custName) => {
    closeCustomerModal();
    if (btnToggleERD) btnToggleERD.click();
    setTimeout(() => {
      Toast.info(`Fokuserar på kund: ${custName} (${custNum}) i Universal ERD`, 3500);
    }, 500);
  };

  if (btnFortnoxCustomers) {
    btnFortnoxCustomers.addEventListener('click', openCustomerModal);
  }

  if (btnCloseCustomerModal) {
    btnCloseCustomerModal.addEventListener('click', closeCustomerModal);
  }

  if (customerModalOverlay) {
    customerModalOverlay.addEventListener('click', (e) => {
      if (e.target === customerModalOverlay) closeCustomerModal();
    });
  }

  if (custSearchInput) {
    custSearchInput.addEventListener('input', () => {
      renderCustomerCards();
    });
  }

  if (custFilterPills) {
    const pills = custFilterPills.querySelectorAll('.filter-pill');
    pills.forEach(pill => {
      pill.addEventListener('click', () => {
        pills.forEach(p => p.classList.remove('active'));
        pill.classList.add('active');
        currentCustFilter = pill.getAttribute('data-filter') || 'ALL';
        renderCustomerCards();
      });
    });
  }


  // ─── Keyboard Shortcuts ───────────────────────────────────────────────────

  document.addEventListener('keydown', (e) => {
    // Ignore if focused on an input
    if (e.target.tagName === 'INPUT' || e.target.tagName === 'SELECT' || e.target.tagName === 'TEXTAREA') return;

    const key = e.key;

    // 1–9: Switch Omnipod window
    if (key >= '1' && key <= '9') {
      const windowId = `W${key}`;
      if (windowDefs.find(w => w.id === windowId)) {
        switchWindow(windowId);
        return;
      }
    }

    // Arrow Right: Step forward
    if (key === 'ArrowRight') {
      e.preventDefault();
      const nextStep = Math.min(state.currentStepIndex + 1, 6);
      setStep(nextStep);
      return;
    }

    // Arrow Left: Step backward
    if (key === 'ArrowLeft') {
      e.preventDefault();
      const prevStep = Math.max(state.currentStepIndex - 1, 1);
      setStep(prevStep);
      return;
    }

    // D: Cycle scope D0→D3
    if (key === 'd' || key === 'D') {
      const scopes = ['D0', 'D1', 'D2', 'D3'];
      const labels = ['D0 (Local / Immediate)', 'D1 (Direct Relations)', 'D2 (Subsystem & Ledger)', 'D3 (Macro Ecosystem & Meta)'];
      const currIdx = scopes.indexOf(state.currentScope);
      const nextIdx = (currIdx + 1) % scopes.length;
      state.currentScope = scopes[nextIdx];
      if (scopeSlider) scopeSlider.value = nextIdx;
      if (scopeValueLabel) scopeValueLabel.textContent = labels[nextIdx];
      scopeTicks.forEach(t => {
        t.className = parseInt(t.getAttribute('data-val')) === nextIdx ? 'tick active' : 'tick';
      });
      resolveContext();
      fetchGraphData();
      Toast.info(`Scope → ${scopes[nextIdx]}`);
      return;
    }

    // R: Cycle roles
    if (key === 'r' || key === 'R') {
      const roles = ['CFO', 'Ekonomiansvarig', 'Revisor', 'Säljare', 'Verkstadschef'];
      const currIdx = roles.indexOf(state.currentRole);
      const nextIdx = (currIdx + 1) % roles.length;
      state.currentRole = roles[nextIdx];
      if (roleSelect) roleSelect.value = state.currentRole;
      if (perspectiveWindowName) perspectiveWindowName.textContent = rolePerspectives[state.currentRole] || 'W5';
      updateDomainsGrid();
      resolveContext();
      fetchGraphData();
      Toast.info(`Roll → ${state.currentRole}`);
      return;
    }

    // Enter or Ctrl+Enter: Run full agent loop
    if ((e.ctrlKey || e.metaKey) && key === 'Enter') {
      e.preventDefault();
      if (btnRunFullLoop && !state.isAgentRunning) btnRunFullLoop.click();
      return;
    }

    // Escape: Reset stepper
    if (key === 'Escape') {
      if (btnResetStepper) btnResetStepper.click();
      return;
    }
  });

  // ─── Control Event Listeners ──────────────────────────────────────────────

  if (roleSelect) roleSelect.addEventListener('change', async (e) => {
    state.currentRole = e.target.value;
    if (perspectiveWindowName) perspectiveWindowName.textContent = rolePerspectives[state.currentRole] || 'W5';
    updateDomainsGrid();
    await resolveContext();
    await fetchGraphData();
  });

  if (scenarioSelect) scenarioSelect.addEventListener('change', async (e) => {
    await loadScenario(e.target.value);
    Toast.info(`Scenario laddat: ${e.target.options[e.target.selectedIndex].text}`);
  });

  if (scopeSlider) scopeSlider.addEventListener('input', async (e) => {
    const scopes = ['D0', 'D1', 'D2', 'D3'];
    const labels = ['D0 (Local / Immediate)', 'D1 (Direct Relations)', 'D2 (Subsystem & Ledger)', 'D3 (Macro Ecosystem & Meta)'];
    const idx = parseInt(e.target.value);
    state.currentScope = scopes[idx];
    if (scopeValueLabel) scopeValueLabel.textContent = labels[idx];
    scopeTicks.forEach(t => {
      t.className = parseInt(t.getAttribute('data-val')) === idx ? 'tick active' : 'tick';
    });
    await resolveContext();
    await fetchGraphData();
  });

  // ─── Initial Boot ─────────────────────────────────────────────────────────

  renderWindowSidebar();
  updateDomainsGrid();
  loadScenario('mixed_q3');
  setStep(1);

  // Pre-populate demo voucher
  setTimeout(() => {
    addVoucherToTable({
      verifikat_id: 'VER_2026_001_SYS',
      rows: [
        { account: '1930 Företagskonto', description: 'Bankinbetalning',    debet: 16000.0, kredit: 0.0 },
        { account: '3051 Försäljning varor VMB', description: 'Inbytesmarginal', debet: 0.0, kredit: 14800.0 },
        { account: '2611 Utgående moms VMB 20%', description: 'Marginalmoms', debet: 0.0, kredit: 1200.0 }
      ]
    });
  }, 500);

  // Boot toast
  setTimeout(() => {
    Toast.success('BART Omnipod v3.0 — Spatial Intelligence HUD aktiverad', 5000);
    setTimeout(() => Toast.info('Tips: Tryck 1–9 för att byta perspektivfönster. Dubbelklicka nod för fullständig kontextpivot. D = Byt scope.', 7000), 1200);
  }, 1000);
});
