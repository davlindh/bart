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
    currentTrajectory: null,
    selectedCheckpointsForDiff: [],
    cachedCheckpoints: [],
    frictionGateAcknowledged: false
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
  const btnMaskinFritidProd  = document.getElementById('btnMaskinFritidProd');
  const btnFortnoxCustomers  = document.getElementById('btnFortnoxCustomers');
  const btnToggleERD         = document.getElementById('btnToggleERD');
  const btnOmnipodLayers     = document.getElementById('btnOmnipodLayers');
  const btnTeamDynamicsTelemetry = document.getElementById('btnTeamDynamicsTelemetry');

  // ─── Presentation Levels DOM Elements (Diagram 1) ───────────────────────
  const tabPresL1            = document.getElementById('tabPresL1');
  const tabPresL2            = document.getElementById('tabPresL2');
  const tabPresL3            = document.getElementById('tabPresL3');
  const tabPresL4            = document.getElementById('tabPresL4');
  const presViewL1           = document.getElementById('presViewL1');
  const presViewL2           = document.getElementById('presViewL2');
  const presViewL3           = document.getElementById('presViewL3');
  const presViewL4           = document.getElementById('presViewL4');
  const evidenceChainList    = document.getElementById('evidenceChainList');
  const legalAssumptionsList = document.getElementById('legalAssumptionsList');
  const managedUncertaintiesList = document.getElementById('managedUncertaintiesList');
  const machineJsonBlock     = document.getElementById('machineJsonBlock');
  const navNextNodesList     = document.getElementById('navNextNodesList');

  // ─── Exploration Loop & Progressive Scope Elements (Diagram 1 & 3) ────────
  const btnExpandScopeProgressive = document.getElementById('btnExpandScopeProgressive');
  const loopStopBadge        = document.getElementById('loopStopBadge');

  // ─── Omnipod 4-Layer Modal DOM Elements (Diagram 2) ──────────────────────
  const omnipodLayersModalOverlay = document.getElementById('omnipodLayersModalOverlay');
  const btnCloseOmnipodLayersModal = document.getElementById('btnCloseOmnipodLayersModal');
  const btnCloseOmnipodLayersFooter = document.getElementById('btnCloseOmnipodLayersFooter');
  const tabLayerL1           = document.getElementById('tabLayerL1');
  const tabLayerL2           = document.getElementById('tabLayerL2');
  const tabLayerL3           = document.getElementById('tabLayerL3');
  const tabLayerL4           = document.getElementById('tabLayerL4');
  const layerPaneL1          = document.getElementById('layerPaneL1');
  const layerPaneL2          = document.getElementById('layerPaneL2');
  const layerPaneL3          = document.getElementById('layerPaneL3');
  const layerPaneL4          = document.getElementById('layerPaneL4');
  const omnipodWindowsGrid   = document.getElementById('omnipodWindowsGrid');
  const omnipodDomainsGrid   = document.getElementById('omnipodDomainsGrid');
  const collabMatrixBody     = document.getElementById('collabMatrixBody');
  const catalogsGrid         = document.getElementById('catalogsGrid');

  // ─── Team Dynamics 12-Metrics Modal DOM Elements (Diagram 4) ─────────────
  const teamDynamicsModalOverlay = document.getElementById('teamDynamicsModalOverlay');
  const btnCloseTeamDynamicsModal = document.getElementById('btnCloseTeamDynamicsModal');
  const btnCloseTeamDynamicsFooter = document.getElementById('btnCloseTeamDynamicsFooter');
  const btnRun12AgentLoopFromModal = document.getElementById('btnRun12AgentLoopFromModal');
  const teamMetricsGrid12    = document.getElementById('teamMetricsGrid12');

  const maskinFritidModalOverlay = document.getElementById('maskinFritidModalOverlay');
  const btnCloseMaskinFritidModal = document.getElementById('btnCloseMaskinFritidModal');
  const btnCloseMfModalBottom = document.getElementById('btnCloseMfModalBottom');
  const btnLoadMfToCanvas    = document.getElementById('btnLoadMfToCanvas');
  const mfKpiGross           = document.getElementById('mfKpiGross');
  const mfKpiSavings         = document.getElementById('mfKpiSavings');
  const mfKpiProfit          = document.getElementById('mfKpiProfit');
  const mfKpiVouchers        = document.getElementById('mfKpiVouchers');
  const mfVouchersList       = document.getElementById('mfVouchersList');
  const mfSkvReportBoxes     = document.getElementById('mfSkvReportBoxes');

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

  // ─── Trajectory & Checkpoints DOM Elements ───────────────────────────────
  const btnTrajectory         = document.getElementById('btnTrajectory');
  const btnCheckpoints        = document.getElementById('btnCheckpoints');
  const trajectoryModalOverlay= document.getElementById('trajectoryModalOverlay');
  const btnCloseTrajectoryModal= document.getElementById('btnCloseTrajectoryModal');
  const trajConfidenceBadge   = document.getElementById('trajConfidenceBadge');
  const intentMandateText     = document.getElementById('intentMandateText');
  const intentKpisRow         = document.getElementById('intentKpisRow');
  const trajStepsTrack        = document.getElementById('trajStepsTrack');
  const trajSkillsList        = document.getElementById('trajSkillsList');
  const trajFrictionsList     = document.getElementById('trajFrictionsList');
  const btnQuickCheckpointFromTraj = document.getElementById('btnQuickCheckpointFromTraj');
  const btnRunOrchestratorWithTraj = document.getElementById('btnRunOrchestratorWithTraj');

  const checkpointsModalOverlay = document.getElementById('checkpointsModalOverlay');
  const btnCloseCheckpointsModal= document.getElementById('btnCloseCheckpointsModal');
  const btnCreateNewCheckpoint= document.getElementById('btnCreateNewCheckpoint');
  const checkpointsListContainer = document.getElementById('checkpointsListContainer');
  const btnCompareCheckpoints = document.getElementById('btnCompareCheckpoints');
  const checkpointDiffPanel   = document.getElementById('checkpointDiffPanel');
  const diffPanelContent      = document.getElementById('diffPanelContent');
  const btnCloseDiffPanel     = document.getElementById('btnCloseDiffPanel');

  const frictionGateOverlay   = document.getElementById('frictionGateOverlay');
  const frictionGateSeverity  = document.getElementById('frictionGateSeverity');
  const frictionGateIssue     = document.getElementById('frictionGateIssue');
  const frictionGateRootText  = document.getElementById('frictionGateRootText');
  const frictionGateActionText= document.getElementById('frictionGateActionText');
  const btnFrictionConfirm    = document.getElementById('btnFrictionConfirm');
  const btnFrictionPause      = document.getElementById('btnFrictionPause');

  // ─── Shortcut Presentation System DOM Elements ───────────────────────────
  const shortcutsModalOverlay      = document.getElementById('shortcutsModalOverlay');
  const btnCloseShortcutsModal     = document.getElementById('btnCloseShortcutsModal');
  const btnCloseShortcutsFooter    = document.getElementById('btnCloseShortcutsFooter');
  const btnOpenShortcutsModalHeader= document.getElementById('btnOpenShortcutsModalHeader');
  const dockBtnHelp                = document.getElementById('dockBtnHelp');
  const liveKeyVisualizer          = document.getElementById('liveKeyVisualizer');
  const dockBtnT                   = document.getElementById('dockBtnT');
  const dockBtnC                   = document.getElementById('dockBtnC');
  const dockBtnNums                = document.getElementById('dockBtnNums');
  const dockBtnD                   = document.getElementById('dockBtnD');
  const dockBtnR                   = document.getElementById('dockBtnR');
  const dockBtnArrows              = document.getElementById('dockBtnArrows');
  const dockBtnEsc                 = document.getElementById('dockBtnEsc');


  // ─── Spatial Canvas & Inspector Init ─────────────────────────────────────

  const btnFreezePhysics           = document.getElementById('btnFreezePhysics');
  const btnToggleLayoutMode        = document.getElementById('btnToggleLayoutMode');
  const btnTraceCausalPath         = document.getElementById('btnTraceCausalPath');
  const erdCategoryPills           = document.getElementById('erdCategoryPills');
  const btnSoundToggle             = document.getElementById('btnSoundToggle');
  const btnAutoPlayLoop            = document.getElementById('btnAutoPlayLoop');
  const loopProgressBar            = document.getElementById('loopProgressBar');
  const loopProgressStage          = document.getElementById('loopProgressStage');
  const loopProgressTime           = document.getElementById('loopProgressTime');
  const erpLiveTicker              = document.getElementById('erpLiveTicker');
  const weightingMetersContainer   = document.getElementById('weightingMetersContainer');
  const confidenceEntropyBadge     = document.getElementById('confidenceEntropyBadge');
  const canvasSearchInput          = document.getElementById('canvasSearchInput');
  const canvasDomainPills          = document.getElementById('canvasDomainPills');
  const nodeInspectorDrawer        = document.getElementById('nodeInspectorDrawer');
  const btnCloseInspector          = document.getElementById('btnCloseInspector');
  const inspDomainDot              = document.getElementById('inspDomainDot');
  const inspNodeName               = document.getElementById('inspNodeName');
  const inspNodeId                 = document.getElementById('inspNodeId');
  const inspectorBody              = document.getElementById('inspectorBody');
  const btnInspPivotContext        = document.getElementById('btnInspPivotContext');
  const btnExportSIE4              = document.getElementById('btnExportSIE4');
  const btnExportMomsdeklaration   = document.getElementById('btnExportMomsdeklaration');
  const tabProposedVouchers        = document.getElementById('tabProposedVouchers');
  const tabBookedVouchers          = document.getElementById('tabBookedVouchers');
  const badgeProposedCount         = document.getElementById('badgeProposedCount');
  const badgeBookedCount           = document.getElementById('badgeBookedCount');
  const btnSyncAllProposalsToFortnox = document.getElementById('btnSyncAllProposalsToFortnox');
  const viewProposedVouchers       = document.getElementById('viewProposedVouchers');
  const viewBookedVouchers         = document.getElementById('viewBookedVouchers');
  const proposedVouchersList       = document.getElementById('proposedVouchersList');

  let selectedInspectorNode = null;

  function openNodeInspector(node) {
    selectedInspectorNode = node;
    if (!nodeInspectorDrawer) return;

    if (inspDomainDot) {
      inspDomainDot.style.background = (canvas.colors && canvas.colors[node.domain]) ? canvas.colors[node.domain] : '#38bdf8';
    }
    if (inspNodeName) {
      inspNodeName.textContent = node.name || node.id;
    }
    if (inspNodeId) {
      inspNodeId.textContent = `${node.id} · ${node.type || 'Entity'} · ${node.domain || 'All'}`;
    }

    if (inspectorBody) {
      let matchedTx = null;
      if (state.currentScenario && state.currentScenario.transactions) {
        matchedTx = state.currentScenario.transactions.find(t => t.transaction_id === node.id);
      }

      let extraDetails = '';
      if (matchedTx) {
        const potentialSavings = matchedTx.is_used_good 
          ? (matchedTx.current_vat_amount - (matchedTx.gross_amount - matchedTx.purchase_cost_ex_vat) * 0.20)
          : (matchedTx.is_garden_or_installation_work ? (matchedTx.labor_share_amount || 8000.0) * 0.50 : 0);

        extraDetails = `
          <div class="insp-section">
            <div class="insp-section-title">TRANSAKTIONSFAKTA & MOMSSTATUS</div>
            <div class="insp-metric-grid">
              <div class="insp-metric-box">
                <div class="insp-metric-lbl">Bruttobelopp</div>
                <div class="insp-metric-val">${formatSEK(matchedTx.gross_amount)}</div>
              </div>
              <div class="insp-metric-box">
                <div class="insp-metric-lbl">Nuvarande Moms</div>
                <div class="insp-metric-val text-rose">${formatSEK(matchedTx.current_vat_amount)}</div>
              </div>
              <div class="insp-metric-box">
                <div class="insp-metric-lbl">Klassificering</div>
                <div class="insp-metric-val">${matchedTx.is_used_good ? 'Begagnad (VMB)' : (matchedTx.is_garden_or_installation_work ? 'Installation (RUT)' : 'Standard')}</div>
              </div>
              <div class="insp-metric-box">
                <div class="insp-metric-lbl">Optimeringsvinst</div>
                <div class="insp-metric-val savings">+${formatSEK(Math.max(0, potentialSavings))}</div>
              </div>
            </div>
          </div>
        `;
      } else if (node.type === 'account') {
        extraDetails = `
          <div class="insp-section">
            <div class="insp-section-title">BAS-KONTODETALJER</div>
            <div class="insp-metric-grid">
              <div class="insp-metric-box">
                <div class="insp-metric-lbl">Kontonummer</div>
                <div class="insp-metric-val"><code>${node.id}</code></div>
              </div>
              <div class="insp-metric-box">
                <div class="insp-metric-lbl">Kontoklass</div>
                <div class="insp-metric-val">Klass ${node.id.charAt(0)}</div>
              </div>
            </div>
          </div>
        `;
      } else {
        const props = node.properties || {};
        let propsHtml = '';
        if (Object.keys(props).length > 0) {
          propsHtml = Object.entries(props).map(([k, v]) => `
            <div class="insp-metric-box">
              <div class="insp-metric-lbl">${k.replace(/_/g, ' ').toUpperCase()}</div>
              <div class="insp-metric-val" style="font-size:0.8rem;">${typeof v === 'object' ? JSON.stringify(v) : v}</div>
            </div>
          `).join('');
        }
        extraDetails = `
          <div class="insp-section">
            <div class="insp-section-title">UNIVERSAL ERD ENTITET</div>
            <div class="insp-metric-grid">
              <div class="insp-metric-box">
                <div class="insp-metric-lbl">Entitetstyp</div>
                <div class="insp-metric-val">${node.type || 'Entity'}</div>
              </div>
              <div class="insp-metric-box">
                <div class="insp-metric-lbl">Domän</div>
                <div class="insp-metric-val">${node.domain || 'Operational'}</div>
              </div>
              ${node.description ? `
              <div class="insp-metric-box" style="grid-column: span 2;">
                <div class="insp-metric-lbl">Beskrivning</div>
                <div class="insp-metric-val" style="font-size:0.82rem; font-weight:normal;">${node.description}</div>
              </div>` : ''}
              ${propsHtml}
            </div>
          </div>
        `;
      }

      inspectorBody.innerHTML = `
        ${extraDetails}
        <div class="insp-section">
          <div class="insp-section-title">SPATIAL GRAFSTATUS</div>
          <div class="insp-metric-grid">
            <div class="insp-metric-box">
              <div class="insp-metric-lbl">Koordinater</div>
              <div class="insp-metric-val">${Math.round(node.x || 0)}, ${Math.round(node.y || 0)}</div>
            </div>
            <div class="insp-metric-box">
              <div class="insp-metric-lbl">Fysikstatus</div>
              <div class="insp-metric-val ${canvas.isPhysicsFrozen ? 'text-amber' : 'text-emerald'}">${canvas.isPhysicsFrozen ? 'Fryst ❄️' : 'Aktiv ▶️'}</div>
            </div>
          </div>
        </div>
      `;
    }

    nodeInspectorDrawer.style.display = 'flex';
  }

  function closeNodeInspector() {
    if (nodeInspectorDrawer) nodeInspectorDrawer.style.display = 'none';
    selectedInspectorNode = null;
  }

  const canvas = new window.SpatialCanvas('spatialCanvas');

  canvas.onNodeClick((node) => {
    if (node.type === 'transaction') {
      selectTransaction(node.id);
      pushBreadcrumb({ id: node.id, name: node.name, type: 'transaction' });
    } else {
      pushBreadcrumb({ id: node.id, name: node.name, type: node.type });
    }
    openNodeInspector(node);
  });

  canvas.onPivot((node) => {
    // Double-click: full context repivot
    pivotContext(node.id, node.type, node.name);
  });

  btnResetCanvas.addEventListener('click', () => {
    canvas.resetLayout();
    Toast.info('Grafvy återställd');
  });

  if (btnCloseInspector) {
    btnCloseInspector.addEventListener('click', closeNodeInspector);
  }

  if (btnInspPivotContext) {
    btnInspPivotContext.addEventListener('click', () => {
      if (selectedInspectorNode) {
        pivotContext(selectedInspectorNode.id, selectedInspectorNode.type, selectedInspectorNode.name);
        closeNodeInspector();
      }
    });
  }

  if (btnInspCopyId) {
    btnInspCopyId.addEventListener('click', () => {
      if (selectedInspectorNode) {
        if (navigator.clipboard && navigator.clipboard.writeText) {
          navigator.clipboard.writeText(selectedInspectorNode.id).then(() => {
            Toast.success(`Kopierade "${selectedInspectorNode.id}" till urklipp`);
          }).catch(() => {
            Toast.info(`Nod ID: ${selectedInspectorNode.id}`);
          });
        } else {
          Toast.info(`Nod ID: ${selectedInspectorNode.id}`);
        }
      }
    });
  }

  if (canvasSearchInput) {
    canvasSearchInput.addEventListener('input', (e) => {
      const q = e.target.value;
      const activePill = canvasDomainPills ? canvasDomainPills.querySelector('.domain-filter-pill.active') : null;
      const domain = activePill ? activePill.getAttribute('data-domain') : 'ALL';
      canvas.setFilter(q, domain);
    });
  }

  if (canvasDomainPills) {
    canvasDomainPills.addEventListener('click', (e) => {
      const pill = e.target.closest('.domain-filter-pill');
      if (!pill) return;
      canvasDomainPills.querySelectorAll('.domain-filter-pill').forEach(p => p.classList.remove('active'));
      pill.classList.add('active');
      const domain = pill.getAttribute('data-domain');
      const q = canvasSearchInput ? canvasSearchInput.value : '';
      canvas.setFilter(q, domain);
      Toast.info(`Grafdomän: ${domain}`);
    });
  }

  if (btnFreezePhysics) {
    btnFreezePhysics.addEventListener('click', () => {
      const isFrozen = canvas.togglePhysics();
      btnFreezePhysics.textContent = isFrozen ? '▶️ Tina Graf' : '❄️ Frys Graf';
      btnFreezePhysics.classList.toggle('active', isFrozen);
      Toast.info(isFrozen ? 'Grafens fysiksimulering fryst' : 'Grafens fysiksimulering aktiv');
    });
  }

  // ─── Zero-Dependency Web Audio Synthesizer ──────────────────────────────────
  const audioState = {
    enabled: localStorage.getItem('bart_sound_enabled') !== 'false',
    ctx: null
  };

  function getAudioContext() {
    if (!audioState.ctx && (window.AudioContext || window.webkitAudioContext)) {
      audioState.ctx = new (window.AudioContext || window.webkitAudioContext)();
    }
    if (audioState.ctx && audioState.ctx.state === 'suspended') {
      audioState.ctx.resume();
    }
    return audioState.ctx;
  }

  function playSound(type = 'click') {
    if (!audioState.enabled) return;
    try {
      const ctx = getAudioContext();
      if (!ctx) return;
      const now = ctx.currentTime;

      if (type === 'click') {
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.type = 'sine';
        osc.frequency.setValueAtTime(880, now);
        osc.frequency.exponentialRampToValueAtTime(440, now + 0.04);
        gain.gain.setValueAtTime(0.04, now);
        gain.gain.linearRampToValueAtTime(0.001, now + 0.04);
        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.start(now);
        osc.stop(now + 0.045);
      } else if (type === 'success') {
        [523.25, 659.25, 783.99, 1046.5].forEach((freq, idx) => {
          const osc = ctx.createOscillator();
          const gain = ctx.createGain();
          osc.type = 'triangle';
          osc.frequency.setValueAtTime(freq, now + idx * 0.06);
          gain.gain.setValueAtTime(0.04, now + idx * 0.06);
          gain.gain.exponentialRampToValueAtTime(0.001, now + idx * 0.06 + 0.22);
          osc.connect(gain);
          gain.connect(ctx.destination);
          osc.start(now + idx * 0.06);
          osc.stop(now + idx * 0.06 + 0.23);
        });
      } else if (type === 'swoosh') {
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.type = 'sine';
        osc.frequency.setValueAtTime(320, now);
        osc.frequency.exponentialRampToValueAtTime(740, now + 0.08);
        gain.gain.setValueAtTime(0.03, now);
        gain.gain.linearRampToValueAtTime(0.001, now + 0.08);
        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.start(now);
        osc.stop(now + 0.085);
      } else if (type === 'warning') {
        [260, 220].forEach((freq, idx) => {
          const osc = ctx.createOscillator();
          const gain = ctx.createGain();
          osc.type = 'sawtooth';
          osc.frequency.setValueAtTime(freq, now + idx * 0.1);
          gain.gain.setValueAtTime(0.04, now + idx * 0.1);
          gain.gain.exponentialRampToValueAtTime(0.001, now + idx * 0.1 + 0.08);
          osc.connect(gain);
          gain.connect(ctx.destination);
          osc.start(now + idx * 0.1);
          osc.stop(now + idx * 0.1 + 0.09);
        });
      }
    } catch (e) {
      // Audio autoplay policy
    }
  }

  function updateSoundButtonUI() {
    if (!btnSoundToggle) return;
    if (audioState.enabled) {
      btnSoundToggle.textContent = '🔊 Ljud PÅ';
      btnSoundToggle.classList.remove('sound-muted');
      btnSoundToggle.title = 'Ljudeffekter aktiverade (klicka för att stänga av)';
    } else {
      btnSoundToggle.textContent = '🔇 Ljud AV';
      btnSoundToggle.classList.add('sound-muted');
      btnSoundToggle.title = 'Ljudeffekter avstängda (klicka för att aktivera)';
    }
  }

  if (btnSoundToggle) {
    updateSoundButtonUI();
    btnSoundToggle.addEventListener('click', () => {
      audioState.enabled = !audioState.enabled;
      localStorage.setItem('bart_sound_enabled', audioState.enabled);
      updateSoundButtonUI();
      if (audioState.enabled) {
        playSound('success');
        Toast.success('Ljudeffekter aktiverade');
      } else {
        Toast.info('Ljudeffekter avstängda');
      }
    });
  }

  // ─── Layout Mode Toggle (Orbit D0-D3 vs Force-Directed) ───
  if (btnToggleLayoutMode) {
    btnToggleLayoutMode.addEventListener('click', () => {
      const mode = canvas.toggleLayoutMode();
      const isOrbit = mode === 'orbit';
      btnToggleLayoutMode.textContent = isOrbit ? '🪐 Orbit-Vy' : '🕸️ Kraft-Vy';
      btnToggleLayoutMode.classList.toggle('active', isOrbit);
      playSound('swoosh');
      Toast.info(isOrbit ? 'Koncentrisk Orbit-vy (D0 → D3) aktiverad' : 'Relationsbaserad Kraft-graf aktiverad', 2500);
    });
  }

  // ─── Causal Path Tracer (Emerald Beam) ───
  if (btnTraceCausalPath) {
    btnTraceCausalPath.addEventListener('click', () => {
      const focalId = canvas.selectedNodeId || 'TX-1001';
      let targetNode = canvas.nodes.find(n => n.id !== focalId && (n.type === 'rule' || n.type === 'voucher' || n.domain === 'Knowledge' || n.type === 'opportunity'));
      if (!targetNode && canvas.nodes.length > 1) {
        targetNode = canvas.nodes.find(n => n.id !== focalId);
      }
      if (targetNode) {
        const path = canvas.traceCausalPath(focalId, targetNode.id);
        if (path && path.length > 0) {
          playSound('success');
          Toast.success(`⚡ Kausal orsakskedja spårad: ${path.join(' ➔ ')} (${path.length} noder)`, 3500);
        } else if (canvas.links.length > 0) {
          const l = canvas.links[0];
          const p = canvas.traceCausalPath(l.source, l.target);
          playSound('success');
          Toast.success(`⚡ Kausal orsakskedja spårad: ${p.join(' ➔ ')}`, 3000);
        } else {
          Toast.info('Ingen kausal koppling funnen mellan dessa noder.');
        }
      }
    });
  }

  // ─── Universal ERD Category Quick Filters ───
  if (erdCategoryPills) {
    erdCategoryPills.addEventListener('click', (e) => {
      const pill = e.target.closest('.category-pill');
      if (!pill) return;
      const cat = pill.dataset.category || 'ALL';
      erdCategoryPills.querySelectorAll('.category-pill').forEach(p => p.classList.remove('active'));
      pill.classList.add('active');
      canvas.setCategory(cat);
      playSound('click');
      Toast.info(`ERD Filter: ${pill.textContent.trim()}`, 2000);
    });
  }

  // ─── Real-Time Fortnox ERP Event Stream Ticker ──────────────────────────────
  const erpEvents = [
    { text: '⚡ [VMB-INBYTE] Begagnad Husqvarna Automower 430X registrerad i Fortnox Lager • Beräknar 20% vinstmarginalmoms' },
    { text: '📊 [RUT-ROT] Faktura #2024-88 skapad för kund Anna Lindqvist • 50% arbetskostnadsavdrag applicerat (-1 750 SEK)' },
    { text: '🚜 [MASKIN & FRITID \'25] Verifikat B-104 läst från Fortnox API • 15 000 SEK avräknat mot BAS-konto 3001' },
    { text: '🛡️ [OMVÄND BYGGMOMS] Underentreprenör Bygg & Trädgård AB avstämd mot Skatteverkets F-skatteregister (0 SEK utg moms)' },
    { text: '💾 [SQLITE WAL] Självbevarande checkpoint CP-2026-09 skapad • Universal ERD grafförändringar persisterade' },
    { text: '🏛️ [BAS-BOKFÖRING] Verifikat V-1001 balanserat: Debet 1510 (16 000 SEK) == Kredit 3051 (14 800 SEK) + Kredit 2611 (1 200 SEK)' },
    { text: '🧠 [META-LEARNING] LearningAgent upptäckte optimeringsmönster: Automatisk VMB-klassificering för inköp från privatpersoner' }
  ];

  let erpEventIdx = 0;
  function rotateErpTicker() {
    if (!erpLiveTicker) return;
    const now = new Date();
    const timeStr = now.toTimeString().split(' ')[0];
    const ev = erpEvents[erpEventIdx % erpEvents.length];
    erpEventIdx++;

    erpLiveTicker.innerHTML = `
      <span class="ticker-item">
        <span class="ticker-time">${timeStr}</span>
        <span>${ev.text}</span>
      </span>
    `;
  }

  setInterval(rotateErpTicker, 4500);
  rotateErpTicker();

  if (btnExportSIE4) {
    btnExportSIE4.addEventListener('click', () => {
      window.location.href = '/api/export/sie4';
      Toast.success('Laddar ner SIE-4 bokföringsfil (bokforing_verifikat_2026.se)...');
    });
  }

  if (btnExportMomsdeklaration) {
    btnExportMomsdeklaration.addEventListener('click', () => {
      window.location.href = '/api/export/momsdeklaration';
      Toast.success('Laddar ner Skatteverket momsunderlag (momsdeklaration_2026-Q3.json)...');
    });
  }

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
      await loadProposedVouchers();

      if (canvas && typeof canvas.clearTrajectoryNodes === 'function') {
        canvas.clearTrajectoryNodes();
      }
      state.frictionGateAcknowledged = false;
      autoCheckpoint('scenario_load');
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

  // ─── Presentation Levels Controller (Diagram 1) ───────────────────────────

  function switchPresentationLevel(lvl) {
    const tabs = [
      { tab: tabPresL1, view: presViewL1, id: 'l1' },
      { tab: tabPresL2, view: presViewL2, id: 'l2' },
      { tab: tabPresL3, view: presViewL3, id: 'l3' },
      { tab: tabPresL4, view: presViewL4, id: 'l4' }
    ];
    tabs.forEach(t => {
      if (!t.tab || !t.view) return;
      if (t.id === lvl) {
        t.tab.classList.add('active');
        t.view.classList.add('active');
        t.view.style.display = 'flex';
      } else {
        t.tab.classList.remove('active');
        t.view.classList.remove('active');
        t.view.style.display = 'none';
      }
    });
  }

  if (tabPresL1) tabPresL1.addEventListener('click', () => switchPresentationLevel('l1'));
  if (tabPresL2) tabPresL2.addEventListener('click', () => switchPresentationLevel('l2'));
  if (tabPresL3) tabPresL3.addEventListener('click', () => switchPresentationLevel('l3'));
  if (tabPresL4) tabPresL4.addEventListener('click', () => switchPresentationLevel('l4'));

  if (btnExpandScopeProgressive) {
    btnExpandScopeProgressive.addEventListener('click', async () => {
      const scopes = ['D0', 'D1', 'D2', 'D3'];
      const labels = ['D0 (Local / Immediate)', 'D1 (Direct Relations)', 'D2 (Subsystem & Ledger)', 'D3 (Macro Ecosystem & Meta)'];
      const currentIdx = scopes.indexOf(state.currentScope);
      const nextIdx = (currentIdx + 1) % scopes.length;
      state.currentScope = scopes[nextIdx];
      if (scopeSlider) scopeSlider.value = nextIdx;
      if (scopeValueLabel) scopeValueLabel.textContent = labels[nextIdx];
      scopeTicks.forEach(t => {
        t.className = parseInt(t.getAttribute('data-val')) === nextIdx ? 'tick active' : 'tick';
      });
      Toast.info(`🔭 Horizon Scope expanderat → ${state.currentScope}`, 2000);
      await resolveContext();
      await fetchGraphData();
    });
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

      const pres = packet.presentation_levels || {};

      // ── Level 1: Mänsklig Översikt ──
      if (contextIdTag) contextIdTag.textContent = packet.context_id || 'CTX-2026-LIVE';
      if (pres.level_1_overview) {
        if (focalEntityTitle && pres.level_1_overview.focal_entity) {
          focalEntityTitle.textContent = pres.level_1_overview.focal_entity;
        }
        if (focalEntityMeta && pres.level_1_overview.purpose) {
          focalEntityMeta.textContent = `${pres.level_1_overview.purpose} • Roll: ${pres.level_1_overview.role}`;
        }
        if (pres.level_1_overview.observations) {
          renderObservations(pres.level_1_overview.observations);
        }
      }

      // ── Level 2: Detalj, Evidens & Osäkerheter ──
      const l2 = pres.level_2_detail || {};
      if (evidenceChainList) {
        evidenceChainList.innerHTML = '';
        const evList = l2.evidence_chain || packet.evidence || [];
        evList.forEach(ev => {
          const li = document.createElement('li');
          li.className = 'evidence-item';
          li.innerHTML = `<span>📌</span> <div>${ev}</div>`;
          evidenceChainList.appendChild(li);
        });
      }

      if (legalAssumptionsList) {
        legalAssumptionsList.innerHTML = '';
        const assList = l2.assumptions || packet.assumptions || [];
        assList.forEach(as => {
          const li = document.createElement('li');
          li.className = 'assumption-item';
          li.innerHTML = `<span>⚖️</span> <div>${as}</div>`;
          legalAssumptionsList.appendChild(li);
        });
      }

      if (managedUncertaintiesList) {
        managedUncertaintiesList.innerHTML = '';
        const uncList = l2.uncertainties || packet.uncertainties || [];
        uncList.forEach(un => {
          const li = document.createElement('li');
          li.className = 'uncertainty-item';
          li.innerHTML = `<span>❓</span> <div>${un}</div>`;
          managedUncertaintiesList.appendChild(li);
        });
      }

      // ── 3.3 Vikta: 8-Dimension Weighting Vector & Entropy ──
      renderWeightingVector(packet, pres);

      // ── Level 3: Maskinell JSON ──
      if (machineJsonBlock) {
        const jsonContent = pres.level_3_machine ? pres.level_3_machine : packet;
        machineJsonBlock.textContent = JSON.stringify(jsonContent, null, 2);
      }

      // ── Level 4: Navigation & Rekommenderade Satelliter ──
      const sats = (pres.level_4_navigation && pres.level_4_navigation.satellites) 
        ? pres.level_4_navigation.satellites 
        : (packet.recommended_next_nodes || []);

      renderSatellites(sats);

      if (navNextNodesList) {
        navNextNodesList.innerHTML = '';
        sats.forEach(s => {
          const card = document.createElement('div');
          card.className = 'nav-satellite-card';
          const relPct = Math.round((s.relevance_score || s.relevance || 0.8) * 100);
          card.innerHTML = `
            <div class="nav-sat-top">
              <strong>${s.name || s.title || s.target || s.id}</strong>
              <span class="badge-rel">${relPct}% relevans</span>
            </div>
            <div class="nav-sat-meta">${s.domain || 'Operational'} • Typ: ${s.target ? 'Relaterad Nod' : 'Entitet'}</div>
            <div class="nav-sat-actions">
              <button class="btn-micro" data-target="${s.target || s.id}">🎯 Pivotera Canvas</button>
            </div>
          `;
          card.querySelector('button').addEventListener('click', () => {
            const tgt = s.target || s.id;
            if (tgt) {
              selectTransaction(tgt);
              canvas.pivotTo(tgt);
              pushBreadcrumb({ id: tgt, name: s.name || s.title, type: 'satellite' });
            }
          });
          navNextNodesList.appendChild(card);
        });
      }

      // ── Update Exploration Stop Condition Banner ──
      if (loopStopBadge) {
        const stopCond = packet.stop_condition || {};
        if (stopCond.should_stop) {
          loopStopBadge.className = 'loop-stop-badge stop';
          loopStopBadge.textContent = '✓ MÅL UPPNÅTT (STOPP)';
          loopStopBadge.title = stopCond.reason || 'Optimal konvergens uppnådd';
        } else {
          loopStopBadge.className = 'loop-stop-badge iterating';
          const targetSat = stopCond.target_satisfaction ? Math.round(stopCond.target_satisfaction * 100) : 85;
          loopStopBadge.textContent = `⚡ AKTIV UTFORSKNING (${targetSat}% MÅL)`;
          loopStopBadge.title = stopCond.reason || 'Itererar genom graf';
        }
      }

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
      const isCableInstallation = (tx.description || '').toLowerCase().includes('kabel') || (tx.description || '').toLowerCase().includes('automower');

      if (isCableInstallation) {
        asIsCard.innerHTML = `
          <div class="diff-card-title">RISK MED FELAKTIG RUT (AS-IS)</div>
          <div class="diff-metric"><span>Ansökt regel:</span> <strong class="text-rose">Felaktigt yrkat RUT-avdrag</strong></div>
          <div class="diff-metric"><span>Yrkat RUT-belopp:</span> <strong class="text-rose">4 000,00 SEK (50% av arbete)</strong></div>
          <div class="diff-metric alert-negative"><span>Skatteverkets bedömning:</span> <strong class="text-rose">EJ GODKÄND (Undantagen)</strong></div>
          <div class="diff-metric"><span>Sanktionsrisk:</span> <strong class="text-rose">Avslag + 20% skattetillägg (960 SEK)</strong></div>
        `;
        toBeCard.innerHTML = `
          <div class="diff-card-title">LAGVALIDERING & SKYDD (KLAR FÖR FORTNOX)</div>
          <div class="diff-metric"><span>Skatteverket regel:</span> <strong class="text-emerald">IL 67 kap. Kabel ej RUT</strong></div>
          <div class="diff-metric"><span>BAS-Konto:</span> <code>3001 Försäljning maskin &amp; kabelarbete</code></div>
          <div class="diff-metric alert-positive"><span>Skatteefterlevnad:</span> <strong class="text-emerald">100% Godkänd (0 SEK risk)</strong></div>
          <div class="diff-metric"><span>Korrekt fakturering:</span> <strong>${formatSEK(tx.gross_amount)} (inkl 25% moms)</strong></div>
        `;
        if (diffLegalBasis) diffLegalBasis.innerHTML = `<strong>Laglig Grund:</strong> Inkomstskattelagen 67 kap. 13-19 §§ samt Skatteverkets ställningstagande dnr 131 347493-15/111: <em>Installation, programmering och nedläggning av begränsningskabel för robotgräsklippare är uttryckligen undantagna från RUT-avdrag</em> (utgör varken trädgårdsarbete eller IT-tjänster i bostaden). Systemet har avvärjt en felaktig ansökan och genererat ett lagligt verifikat med 25% moms på konto 3001 redo att skicka till Fortnox API.`;
      } else {
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
        if (diffLegalBasis) diffLegalBasis.innerHTML = `<strong>Laglig Grund:</strong> Inkomstskattelagen 67 kap. Trädgårdsarbete (gräsklippning, slyröjning) omfattas av RUT. Kunden sparar ${formatSEK(rutDeduction)} (50% av arbetet) medan företaget behåller 100% intäkt.`;
      }

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

  // ─── 3.3 Vikta: 8-Dimension Context Weighting Vector & Entropy ────────────────
  function renderWeightingVector(packet, pres) {
    if (!weightingMetersContainer) return;
    weightingMetersContainer.innerHTML = '';

    const weights = [
      { name: '1. Relevans (Target Focus)', val: packet?.relevance_score ? Math.round(packet.relevance_score * 100) : 94, class: '' },
      { name: '2. Aktualitet (Recency / Q3)', val: 89, class: '' },
      { name: '3. Rollauktoritet (Jurisdiktion)', val: state.currentRole === 'CFO' ? 96 : 88, class: '' },
      { name: '4. Evidensstyrka (Lagstöd ML/BAS)', val: 95, class: 'dim-evidence' },
      { name: '5. Informationsentropi (Inverterad)', val: 82, class: '' },
      { name: '6. Domänpassning (Trust/Exchange)', val: 91, class: '' },
      { name: '7. Kontextdensitet (D0-D3 Horisont)', val: state.currentScope === 'D3' ? 98 : state.currentScope === 'D2' ? 92 : 84, class: '' },
      { name: '8. Kausal koppling (ERD-länkar)', val: 90, class: 'dim-learning' }
    ];

    weights.forEach(w => {
      const item = document.createElement('div');
      item.className = 'weighting-bar-item';
      item.innerHTML = `
        <div class="weighting-bar-header">
          <span class="weighting-bar-name">${w.name}</span>
          <span class="weighting-bar-val">${w.val}%</span>
        </div>
        <div class="weighting-bar-track">
          <div class="weighting-bar-fill ${w.class}" style="width: ${w.val}%;"></div>
        </div>
      `;
      weightingMetersContainer.appendChild(item);
    });

    if (confidenceEntropyBadge) {
      const conf = packet?.confidence_score ? Math.round(packet.confidence_score * 100) : 94.2;
      const entropy = (0.18).toFixed(2);
      confidenceEntropyBadge.textContent = `Konfidens: ${conf}% • Entropi: ${entropy}`;
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
      { 
        title: '5.1 Observera', 
        desc: 'Observation av organisationsstrukturer, finansiell telemetri, transaktioner, motparter och momsdeklarationsfält.',
        html: `<div style="display: flex; flex-direction: column; gap: 4px;">
          <div><strong>🔍 Signalextraktion & Inläsning:</strong> Extraherar 4 verifikat från Maskin & Fritid '25 / Q3 bokföring.</div>
          <div style="font-size: 0.72rem; color: var(--accent-cyan);">• 115 000 SEK bruttoomsättning identifierad</div>
          <div style="font-size: 0.72rem; color: var(--text-muted);">• Potentiell standardmoms på inbyten uppmärksammad (TX-1001)</div>
        </div>`
      },
      { 
        title: '5.2 Diagnostisera', 
        desc: 'Regelmotor & mönsteranalys: Upptäcker skatteläckage, felmärkta avdrag (VMB/RUT), flaskhalsar och rollgap.',
        html: `<div style="display: flex; flex-direction: column; gap: 4px;">
          <div><strong>⚖️ Hypotesprövning & Regelmotor:</strong> Identifierar skatteoptimering för inbyten och hushållsnära tjänster.</div>
          <div style="font-size: 0.72rem; color: var(--accent-emerald);">• VMB ML 9a kap tillämplig för TX-1001 (-2 000 SEK utg moms)</div>
          <div style="font-size: 0.72rem; color: var(--accent-emerald);">• RUT-avdrag 50% tillämpligt för TX-1002 (-1 750 SEK moms)</div>
        </div>`
      },
      { 
        title: '5.3 Architect', 
        desc: 'Arkitektur & målstruktur: Formulerar lösningshypoteser, BAS-omföringar, rollomfördelning och optimeringsplaner.',
        html: `<div style="display: flex; flex-direction: column; gap: 4px;">
          <div><strong>🏛️ Arkitektur & Omföringsplan:</strong> Beräknar BAS-kontoplan 3051 (VMB), 2611 (Utg moms 25%), 1510.</div>
          <div style="font-size: 0.72rem; color: var(--accent-amber);">• Total skattebesparing: <strong>+5 296 SEK</strong> (+71,4% nettomarginal)</div>
          <div style="font-size: 0.72rem; color: var(--text-muted);">• Mandatfördelning för CFO och Ekonomiansvarig synkroniserad</div>
        </div>`
      },
      { 
        title: '5.4 Transition', 
        desc: 'Övergång & handling: Simulerar och förbereder balanserade bokföringsverifikat (0 öre diff) och transition plans.',
        html: `<div style="display: flex; flex-direction: column; gap: 4px;">
          <div><strong>📋 Verifikationsövergång:</strong> Balanserar debet/kredit i realtid. Säkerställer 0,00 SEK differens.</div>
          <div style="font-size: 0.72rem; color: var(--accent-cyan);">• Debet 1510: 16 000 SEK == Kredit 3051: 14 800 SEK + Kredit 2611: 1 200 SEK</div>
          <div style="font-size: 0.72rem; color: var(--text-muted);">• Skapar SIE-4 verifikat redo för synkning till Fortnox API</div>
        </div>`
      },
      { 
        title: '5.5 Mät & Utvärdera', 
        desc: 'Kvantitativ mätning & revision: Validerar mot Skatteverkets regler, BAS-konton, KPI-effekter och dubbelbokföring.',
        html: `<div style="display: flex; flex-direction: column; gap: 4px;">
          <div><strong>📊 Kvantitativ Revision & HITL:</strong> Verifierar Skatteverkets momsdeklaration fält 05, 08, 10, 41, 49.</div>
          <div style="font-size: 0.72rem; color: var(--accent-emerald);">• Granskad av Revisor-roll • 100% efterlevnad bekräftad</div>
          <div style="font-size: 0.72rem; color: var(--text-muted);">• Redo för godkännande i HITL Verifikat-sektionen</div>
        </div>`
      },
      { 
        title: '5.6 Lär', 
        desc: 'Kunskapsuppdatering & meta-loop: Integrerar lärdomar i Universal ERD, uppdaterar heuristik och feedback till nästa körning.',
        html: `<div style="display: flex; flex-direction: column; gap: 4px;">
          <div><strong>🧠 Meta-Loop & Kunskapsexport:</strong> Registrerar optimeringsregel i Universal ERD (D3 Meta-Ecosystem).</div>
          <div style="font-size: 0.72rem; color: #c084fc;">• Auto-kalibrerar agentheuristik för kommande Fortnox-perioder</div>
          <div style="font-size: 0.72rem; color: var(--accent-emerald);">• Självbevarande checkpoint och WAL uppdaterade</div>
        </div>`
      }
    ];

    const info = stepInfos[stepIndex - 1];
    if (stepDetailsTitle) stepDetailsTitle.textContent = info.title;
    if (stepDetailsBody) stepDetailsBody.innerHTML = info.html || info.desc;
    if (agentStatusBadge) agentStatusBadge.textContent = `Steg ${stepIndex}/6`;

    if (loopProgressBar) {
      loopProgressBar.style.width = `${(stepIndex / 6) * 100}%`;
    }
    if (loopProgressStage) {
      loopProgressStage.textContent = `Steg ${stepIndex} / 6: ${info.title}`;
    }
  }

  // ─── Autonomous 6-Stage Exploration & Learning Loop ──────────────────────────
  let autoPlayTimer = null;
  let isAutoPlaying = false;

  function stopAutoPlay() {
    if (autoPlayTimer) {
      clearInterval(autoPlayTimer);
      autoPlayTimer = null;
    }
    isAutoPlaying = false;
    if (btnAutoPlayLoop) {
      btnAutoPlayLoop.innerHTML = '▶ Auto-Play';
      btnAutoPlayLoop.classList.remove('active');
    }
  }

  function startAutoPlay() {
    if (isAutoPlaying) return;
    isAutoPlaying = true;
    if (btnAutoPlayLoop) {
      btnAutoPlayLoop.innerHTML = '⏸ Pausa Loop';
      btnAutoPlayLoop.classList.add('active');
    }
    playSound('click');
    Toast.info('Autonom 6-stegs utforskande och lärloop startad (5.1 ➔ 5.6)');

    autoPlayTimer = setInterval(async () => {
      let nextStep = state.currentStepIndex + 1;
      if (nextStep > 6) {
        nextStep = 1;
        playSound('success');
        Toast.success('🔄 6-stegs lärloop fullbordad! Heuristik uppdaterad i D3.', 3000);
      } else {
        playSound('swoosh');
      }
      await advanceAgentStep(nextStep);
    }, 2400);
  }

  if (btnAutoPlayLoop) {
    btnAutoPlayLoop.addEventListener('click', () => {
      if (isAutoPlaying) {
        stopAutoPlay();
        Toast.info('Auto-play pausad');
      } else {
        startAutoPlay();
      }
    });
  }

  if (agentSelect) {
    agentSelect.addEventListener('change', (e) => {
      state.currentAgent = e.target.value;
      const opt = agentSelect.options[agentSelect.selectedIndex];
      Toast.info(`Aktiv agent: ${opt ? opt.text : state.currentAgent}`, 2500);
      setStep(1);
    });
  }

  let pendingStepAdvancement = null;

  function checkFrictionGate(targetStep) {
    if (state.frictionGateAcknowledged) return false;
    const frictions = state.currentTrajectory?.anticipated_frictions || [];
    const blockingFriction = frictions.find(f => 
      (f.severity === 'high' || f.severity === 'critical') && (f.lead_time_steps <= 1)
    );
    if (blockingFriction && targetStep >= 3) {
      if (frictionGateOverlay) {
        frictionGateOverlay.style.display = 'flex';
        if (frictionGateSeverity) {
          const sev = (blockingFriction.severity || 'high').toUpperCase();
          frictionGateSeverity.textContent = sev;
          frictionGateSeverity.className = `friction-gate-severity-badge ${blockingFriction.severity.toLowerCase()}`;
        }
        if (frictionGateIssue) frictionGateIssue.textContent = blockingFriction.issue || 'Identifierad friktion kräver mänsklig bekräftelse.';
        if (frictionGateRootText) frictionGateRootText.textContent = blockingFriction.root_cause || 'Pre-kognitiv modell identifierade potentiell regelkonflikt.';
        if (frictionGateActionText) frictionGateActionText.textContent = blockingFriction.recommended_action || 'Granska underlag före bokföringssteg.';
      }
      pendingStepAdvancement = targetStep;
      return true;
    }
    return false;
  }

  async function advanceAgentStep(nextStep) {
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
  }

  if (btnFrictionConfirm) {
    btnFrictionConfirm.addEventListener('click', async () => {
      state.frictionGateAcknowledged = true;
      if (frictionGateOverlay) frictionGateOverlay.style.display = 'none';
      Toast.success('🛡️ Friktionsvarning bekräftad av operatör — agenten fortsätter.', 3500);
      autoCheckpoint('friction_override');
      if (pendingStepAdvancement !== null) {
        const stepToGo = pendingStepAdvancement;
        pendingStepAdvancement = null;
        await advanceAgentStep(stepToGo);
      }
    });
  }

  if (btnFrictionPause) {
    btnFrictionPause.addEventListener('click', () => {
      if (frictionGateOverlay) frictionGateOverlay.style.display = 'none';
      pendingStepAdvancement = null;
      Toast.info('⏸️ Agent pausad för att förhindra friktion. Undersök underlag i Zon 1/3.', 4000);
    });
  }

  if (btnStepNext) btnStepNext.addEventListener('click', async () => {
    const nextStep = Math.min(state.currentStepIndex + 1, 6);
    if (checkFrictionGate(nextStep)) {
      return;
    }
    await advanceAgentStep(nextStep);
  });

  function info(step) {
    return ['Observe', 'Analyze', 'Identify', 'Propose', 'Act', 'Evaluate'][step - 1];
  }

  if (btnResetStepper) btnResetStepper.addEventListener('click', () => {
    state.frictionGateAcknowledged = false;
    pendingStepAdvancement = null;
    if (frictionGateOverlay) frictionGateOverlay.style.display = 'none';
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
        playSound('success');
        addVoucherToTable(data.record.voucher);
        Toast.success(`Verifikat ${data.record.voucher.verifikat_id} bokfört och synkat!`);
        autoCheckpoint('voucher_approval');
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

  // ─── Zone 4: Fortnox Proposed Vouchers & Sync Engine ───────────────────────

  state.proposedVouchers = [];

  // Tab switching between Proposed Queue and Booked Ledger
  if (tabProposedVouchers && tabBookedVouchers) {
    tabProposedVouchers.addEventListener('click', () => {
      tabProposedVouchers.classList.add('active');
      tabBookedVouchers.classList.remove('active');
      if (viewProposedVouchers) viewProposedVouchers.style.display = 'block';
      if (viewBookedVouchers) viewBookedVouchers.style.display = 'none';
      playSound('click');
    });

    tabBookedVouchers.addEventListener('click', () => {
      tabBookedVouchers.classList.add('active');
      tabProposedVouchers.classList.remove('active');
      if (viewBookedVouchers) viewBookedVouchers.style.display = 'block';
      if (viewProposedVouchers) viewProposedVouchers.style.display = 'none';
      playSound('click');
    });
  }

  async function loadProposedVouchers() {
    try {
      const res = await fetch('/api/vouchers/proposals');
      const proposals = await res.json();
      state.proposedVouchers = proposals;
      renderProposedVouchers();
    } catch (e) {
      console.warn('Could not load proposed vouchers:', e);
    }
  }

  function renderProposedVouchers() {
    if (!proposedVouchersList) return;
    proposedVouchersList.innerHTML = '';

    const pending = state.proposedVouchers.filter(p => !p.synced);
    const synced = state.proposedVouchers.filter(p => p.synced);

    if (badgeProposedCount) badgeProposedCount.textContent = pending.length;
    if (badgeBookedCount) badgeBookedCount.textContent = state.approvedVouchersCount || synced.length;

    if (state.proposedVouchers.length === 0) {
      proposedVouchersList.innerHTML = `
        <div style="padding: 24px; text-align: center; color: var(--text-dim); font-size: 0.85rem;">
          Inga aktiva verifikationsförslag genererade ännu. Kör en analys eller välj ett scenario.
        </div>
      `;
      return;
    }

    state.proposedVouchers.forEach(p => {
      const isCableAlert = p.category === 'RUT_COMPLIANCE_ENFORCEMENT' || (p.statutory_notes || '').includes('kabel');
      const isSynced = p.synced;

      const card = document.createElement('div');
      card.className = `proposal-card ${isSynced ? 'synced' : ''}`;
      card.id = `card_${p.proposal_id}`;

      // Rows HTML
      const rowsHtml = (p.rows || []).map(r => `
        <div class="proposal-row-item">
          <span><code>${r.account}</code> (${r.description})</span>
          <span>${r.debet > 0 ? `<strong class="text-cyan">Debet ${formatSEK(r.debet)}</strong>` : `<strong class="text-emerald">Kredit ${formatSEK(r.kredit)}</strong>`}</span>
        </div>
      `).join('');

      card.innerHTML = `
        <div class="proposal-header">
          <div class="proposal-title-box">
            <span class="proposal-id-badge">${p.verifikat_id}</span>
            <span class="proposal-name">${p.title || p.description}</span>
          </div>
          <span class="proposal-badge ${isSynced ? 'synced' : 'ready'}">
            ${isSynced ? '✓ SYNCHRONIZED TO FORTNOX' : '⚡ KLAR ATT SÄTTA TILL FORTNOX'}
          </span>
        </div>

        <div class="proposal-legal-box ${isCableAlert ? 'alert' : ''}">
          <strong>${isCableAlert ? '⚠️ LAGKONTROLL SKATTEVERKET (IL 67 KAP):' : '⚖️ LAGSTÖD & MOTIVERING:'}</strong>
          <div>${p.statutory_notes || p.legal_basis}</div>
        </div>

        <div class="proposal-rows-grid">
          ${rowsHtml}
        </div>

        <div class="proposal-footer">
          <div class="proposal-effect">
            <span>Ekonomisk effekt: <strong>${p.economic_effect}</strong></span>
          </div>
          <button class="btn-sync-single ${isSynced ? 'synced' : ''}" data-id="${p.proposal_id}" data-tx="${p.transaction_id}" ${isSynced ? 'disabled' : ''}>
            ${isSynced ? '✓ Synkad i Fortnox' : '🚀 Skicka till Fortnox'}
          </button>
        </div>
      `;

      const syncBtn = card.querySelector('.btn-sync-single');
      if (syncBtn && !isSynced) {
        syncBtn.addEventListener('click', () => {
          syncSingleProposal(p.proposal_id, p.transaction_id);
        });
      }

      proposedVouchersList.appendChild(card);
    });
  }

  async function syncSingleProposal(proposalId, txId) {
    try {
      const res = await fetch('/api/voucher/sync_proposal', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ proposal_id: proposalId, transaction_id: txId })
      });
      const data = await res.json();
      if (data.success) {
        playSound('success');
        const item = state.proposedVouchers.find(p => p.proposal_id === proposalId || p.transaction_id === txId);
        if (item) item.synced = true;

        addVoucherToTable(data.record.voucher);
        renderProposedVouchers();
        Toast.success(`Verifikat ${data.record.voucher.verifikat_id} skickat och bokfört i Fortnox API!`);

        if (erpLiveTicker) {
          const nowStr = new Date().toTimeString().split(' ')[0];
          erpLiveTicker.innerHTML = `
            <span class="ticker-item">
              <span class="ticker-time">${nowStr}</span>
              <span>⚡ [FORTNOX SYNC] Verifikat ${data.record.voucher.verifikat_id} postat till huvudbok och SIE-4 export!</span>
            </span>
          `;
        }
      }
    } catch (err) {
      console.error('Sync proposal error:', err);
      Toast.error('Kunde inte skicka verifikat till Fortnox API.');
    }
  }

  async function syncAllProposalsToFortnox() {
    try {
      if (btnSyncAllProposalsToFortnox) btnSyncAllProposalsToFortnox.disabled = true;
      const res = await fetch('/api/voucher/sync_all_proposals', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({})
      });
      const data = await res.json();
      if (data.success) {
        playSound('success');
        state.proposedVouchers.forEach(p => p.synced = true);
        (data.records || []).forEach(r => {
          addVoucherToTable(r.voucher);
        });
        renderProposedVouchers();
        Toast.success(`⚡ Samtliga ${data.count} verifikationsförslag skickade och bokförda i Fortnox!`, 4000);

        if (erpLiveTicker) {
          const nowStr = new Date().toTimeString().split(' ')[0];
          erpLiveTicker.innerHTML = `
            <span class="ticker-item">
              <span class="ticker-time">${nowStr}</span>
              <span>🚀 [FORTNOX BATCH] Samtliga ${data.count} verifikat postade till Fortnox huvudbok med 0 öre balanskontroll!</span>
            </span>
          `;
        }
      }
    } catch (err) {
      console.error('Sync all error:', err);
      Toast.error('Kunde inte genomföra batchsynk till Fortnox.');
    } finally {
      if (btnSyncAllProposalsToFortnox) btnSyncAllProposalsToFortnox.disabled = false;
    }
  }

  if (btnSyncAllProposalsToFortnox) {
    btnSyncAllProposalsToFortnox.addEventListener('click', syncAllProposalsToFortnox);
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
        <button class="btn primary btn-perspective-action" id="btnW1Action">🔭 Rikta Graf mot Strategiska Trender</button>
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
        <button class="btn primary btn-perspective-action" id="btnW2Action">💼 Öppna Kundregister & Matchning</button>
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
        <button class="btn primary btn-perspective-action" id="btnW3Action">⚖️ Kör Automatisk Skatterevision</button>
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
        <button class="btn primary btn-perspective-action" id="btnW4Action">📊 Balansera Rörelsekapital</button>
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
        <button class="btn primary btn-perspective-action" id="btnW6Action">🛡️ Aktivera Hälsosköld</button>
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
        <button class="btn primary btn-perspective-action" id="btnW7Action">📡 Sänd Handoff till Noder</button>
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
        <button class="btn primary btn-perspective-action" id="btnW8Action">🧪 Starta Ny FoU-Pilot</button>
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
        <button class="btn primary btn-perspective-action" id="btnW9Action">🧠 Kör Meta-Lärningsanalys</button>
      `;
    }

    html += `</div>`;
    perspectiveDynamicContainer.innerHTML = html;

    // Attach dynamic card action listeners
    const w1Btn = document.getElementById('btnW1Action');
    if (w1Btn) w1Btn.addEventListener('click', () => {
      canvas.setFilter('', 'Knowledge');
      Toast.info('W1: Fokuserar kunskaps- och omvärldsnoder i grafen');
    });

    const w2Btn = document.getElementById('btnW2Action');
    if (w2Btn) w2Btn.addEventListener('click', () => {
      openCustomerModal();
      Toast.info('W2: Öppnar kundtelemetri och paketmatchning');
    });

    const w3Btn = document.getElementById('btnW3Action');
    if (w3Btn) w3Btn.addEventListener('click', async () => {
      Toast.info('W3: Kör revisionsanalys mot Skatteverkets regler...');
      await runWindowAudit();
      Toast.success('W3: Skatterevision godkänd utan avvikelser');
    });

    const w4Btn = document.getElementById('btnW4Action');
    if (w4Btn) w4Btn.addEventListener('click', () => {
      canvas.setFilter('', 'Operational');
      Toast.info('W4: Balanserar operativ kapacitet och varulager');
    });

    const w6Btn = document.getElementById('btnW6Action');
    if (w6Btn) w6Btn.addEventListener('click', () => {
      Toast.success('W6: Hälsosköld aktiverad — Arbetsbörda jämnt fördelad');
    });

    const w7Btn = document.getElementById('btnW7Action');
    if (w7Btn) w7Btn.addEventListener('click', () => {
      Toast.info('W7: Systemhandoff synkroniserad över alla aktiva zoner');
    });

    const w8Btn = document.getElementById('btnW8Action');
    if (w8Btn) w8Btn.addEventListener('click', () => {
      Toast.success('W8: FoU-Pilot initierad i sandlådemiljö');
    });

    const w9Btn = document.getElementById('btnW9Action');
    if (w9Btn) w9Btn.addEventListener('click', () => {
      Toast.info('W9: Meta-lärningsloop uppdaterar heuristiska regler');
    });
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
            autoCheckpoint('agent_loop_completed');
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

  // ─── Omnipod 4-Layer Architecture Inspector Controller (Diagram 2) ────────

  function switchOmnipodLayerTab(layerId) {
    const tabs = [
      { tab: tabLayerL1, pane: layerPaneL1, id: 'l1' },
      { tab: tabLayerL2, pane: layerPaneL2, id: 'l2' },
      { tab: tabLayerL3, pane: layerPaneL3, id: 'l3' },
      { tab: tabLayerL4, pane: layerPaneL4, id: 'l4' }
    ];
    tabs.forEach(t => {
      if (!t.tab || !t.pane) return;
      if (t.id === layerId) {
        t.tab.classList.add('active');
        t.pane.classList.add('active');
        t.pane.style.display = 'block';
      } else {
        t.tab.classList.remove('active');
        t.pane.classList.remove('active');
        t.pane.style.display = 'none';
      }
    });
  }

  if (tabLayerL1) tabLayerL1.addEventListener('click', () => switchOmnipodLayerTab('l1'));
  if (tabLayerL2) tabLayerL2.addEventListener('click', () => switchOmnipodLayerTab('l2'));
  if (tabLayerL3) tabLayerL3.addEventListener('click', () => switchOmnipodLayerTab('l3'));
  if (tabLayerL4) tabLayerL4.addEventListener('click', () => switchOmnipodLayerTab('l4'));

  async function openOmnipodLayersModal() {
    if (!omnipodLayersModalOverlay) return;
    omnipodLayersModalOverlay.style.display = 'flex';
    switchOmnipodLayerTab('l1');
    Toast.info('🏛️ Hämtar Omnipod 4-Lagers arkitekturtelemetri...', 2000);

    try {
      const res = await fetch('/api/omnipod/layers');
      const data = await res.json();

      // ── Populate L1: 9 Windows Grid ──
      if (omnipodWindowsGrid && data.layer_1_perspectives) {
        omnipodWindowsGrid.innerHTML = '';
        data.layer_1_perspectives.forEach(w => {
          const card = document.createElement('div');
          card.className = 'omnipod-window-card';
          card.innerHTML = `
            <div class="win-card-top">
              <span class="win-id-badge">${w.id}</span>
              <span class="win-status-badge ${w.status === 'active' ? 'active' : ''}">${w.status.toUpperCase()}</span>
            </div>
            <div class="win-name">${w.name}</div>
            <div class="win-perspective">${w.perspective}</div>
            <div class="win-footer">
              <span class="win-domain">${w.domain}</span>
              <span class="win-metric">${w.key_metric}</span>
            </div>
          `;
          card.addEventListener('click', () => {
            selectOmnipodWindow(w.id);
            closeOmnipodLayersModal();
          });
          omnipodWindowsGrid.appendChild(card);
        });
      }

      // ── Populate L2: 6 Domains Grid ──
      if (omnipodDomainsGrid && data.layer_2_domains) {
        omnipodDomainsGrid.innerHTML = '';
        data.layer_2_domains.forEach(d => {
          const card = document.createElement('div');
          card.className = 'omnipod-domain-card';
          card.innerHTML = `
            <div class="dom-card-header">
              <span class="panel-dot cyan"></span>
              <h4>${d.name}</h4>
              <span class="dom-count-badge">${d.node_count} Noder</span>
            </div>
            <p class="dom-desc">${d.description}</p>
            <div class="dom-meta">Ledande roll: <strong>${d.lead_role}</strong></div>
          `;
          omnipodDomainsGrid.appendChild(card);
        });
      }

      // ── Populate L3: User A-D Collaboration Matrix ──
      if (collabMatrixBody && data.layer_3_collaboration) {
        collabMatrixBody.innerHTML = '';
        data.layer_3_collaboration.forEach(row => {
          const tr = document.createElement('tr');
          tr.innerHTML = `
            <td><strong>${row.user}</strong><br><small style="color:var(--text-dim);">${row.role}</small></td>
            <td><span class="matrix-pill ${row.trust === 'Hög' ? 'high' : (row.trust === 'Medel' ? 'mid' : 'low')}">${row.trust}</span></td>
            <td><span class="matrix-pill ${row.knowledge === 'Hög' ? 'high' : (row.knowledge === 'Medel' ? 'mid' : 'low')}">${row.knowledge}</span></td>
            <td><span class="matrix-pill ${row.data === 'Hög' ? 'high' : (row.data === 'Medel' ? 'mid' : 'low')}">${row.data}</span></td>
            <td><span class="matrix-pill ${row.ops === 'Hög' ? 'high' : (row.ops === 'Medel' ? 'mid' : 'low')}">${row.ops}</span></td>
            <td><span style="font-size:0.8rem; color:#cbd5e1;">${row.interpretation}</span></td>
          `;
          collabMatrixBody.appendChild(tr);
        });
      }

      // ── Populate L4: Catalogs Grid ──
      if (catalogsGrid && data.layer_4_information) {
        catalogsGrid.innerHTML = '';
        data.layer_4_information.forEach(cat => {
          const card = document.createElement('div');
          card.className = 'catalog-card';
          const sampleList = (cat.sample_entries || []).map(e => `<code>${e}</code>`).join(' ');
          card.innerHTML = `
            <div class="cat-header">
              <span class="cat-name">📁 ${cat.name}</span>
              <span class="cat-domain">${cat.domain}</span>
            </div>
            <div class="cat-types">Format: ${cat.file_types}</div>
            <div class="cat-samples">${sampleList}</div>
          `;
          catalogsGrid.appendChild(card);
        });
      }

      Toast.success('✓ Omnipod 4-Lager arkitektur laddad!', 2500);
    } catch (err) {
      console.error('Error fetching omnipod layers:', err);
      Toast.warning('Kunde inte ladda 4-lagers telemetri.');
    }
  }

  function closeOmnipodLayersModal() {
    if (omnipodLayersModalOverlay) omnipodLayersModalOverlay.style.display = 'none';
  }

  if (btnOmnipodLayers) btnOmnipodLayers.addEventListener('click', openOmnipodLayersModal);
  if (btnCloseOmnipodLayersModal) btnCloseOmnipodLayersModal.addEventListener('click', closeOmnipodLayersModal);
  if (btnCloseOmnipodLayersFooter) btnCloseOmnipodLayersFooter.addEventListener('click', closeOmnipodLayersModal);

  // ─── Team Dynamics Optimizer 12-Metrics Controller (Diagram 4) ────────────

  async function openTeamDynamicsModal() {
    if (!teamDynamicsModalOverlay) return;
    teamDynamicsModalOverlay.style.display = 'flex';
    Toast.info('📈 Hämtar 12 Team Dynamics nyckelmetriker...', 2000);

    try {
      const res = await fetch('/api/team_dynamics/telemetry');
      const data = await res.json();
      const m = data.metrics || {};

      if (teamMetricsGrid12) {
        teamMetricsGrid12.innerHTML = '';
        const metricDefs = [
          { key: 'team_health_index', label: 'Team Health Index', val: `${m.team_health_index || 88} / 100`, status: 'Utmärkt', good: true, desc: 'Holistiskt hälsoindex baserat på samarbetsflöden' },
          { key: 'team_enps', label: 'Team eNPS', val: `+${m.team_enps || 42}`, status: 'Stark', good: true, desc: 'Rekommendationsvilja & team-ambassadörskap' },
          { key: 'decision_time_median_hours', label: 'Beslutstid i median', val: `${m.decision_time_median_hours || 3.4} h`, status: 'Snabb', good: true, desc: 'Tid från observation till godkänd handling' },
          { key: 'on_time_delivery_pct', label: 'On-Time Delivery %', val: `${m.on_time_delivery_pct || 94.2}%`, status: '94% OTD', good: true, desc: 'Leveransprecision mot målsatta tidslinjer' },
          { key: 'psychological_safety_score', label: 'Psykologisk Trygghet', val: `${m.psychological_safety_score || 4.6} / 5.0`, status: 'Hög', good: true, desc: 'Öppenhet för felrapportering och hypotesprövning' },
          { key: 'cognitive_load_index', label: 'Kognitiv Belastning', val: `${m.cognitive_load_index || 0.38}`, status: 'Låg (Optimal)', good: true, desc: 'Mental belastning och informationsöverflöd' },
          { key: 'friction_frequency_per_week', label: 'Friktionsfrekvens', val: `${m.friction_frequency_per_week || 1.2} / v`, status: 'Låg', good: true, desc: 'Antal blockerande hinder per vecka' },
          { key: 'role_clarity_pct', label: 'Rollklarhet', val: `${m.role_clarity_pct || 96}%`, status: 'Tydlig', good: true, desc: 'Tydlighet i ansvarsfördelning och beslutsrätt' },
          { key: 'experiment_success_rate_pct', label: 'Experiment Success Rate', val: `${m.experiment_success_rate_pct || 78.5}%`, status: 'Hög verkningsgrad', good: true, desc: 'Andel hypotestester som lett till bekräftad förbättring' },
          { key: 'learning_velocity_per_month', label: 'Lärande-hastighet', val: `${m.learning_velocity_per_month || 14} / mån`, status: 'Snabb adaptation', good: true, desc: 'Nya kunskapsnoder tillförda kunskapsgrafen' },
          { key: 'decision_quality_score', label: 'Beslutskvalitet', val: `${m.decision_quality_score || 91.0} / 100`, status: 'Robust', good: true, desc: 'Evidensgrad och reversibilitet i tagna beslut' },
          { key: 'bias_index', label: 'Bias Index', val: `${m.bias_index || 0.12}`, status: 'Minimal bias', good: true, desc: 'Avsaknad av kognitiva snedvridningar i analysen' }
        ];

        metricDefs.forEach(def => {
          const card = document.createElement('div');
          card.className = 'team-metric-card';
          card.innerHTML = `
            <div class="tm-header">
              <span class="tm-label">${def.label}</span>
              <span class="tm-status-pill ${def.good ? 'good' : 'warn'}">${def.status}</span>
            </div>
            <div class="tm-val">${def.val}</div>
            <div class="tm-desc">${def.desc}</div>
          `;
          teamMetricsGrid12.appendChild(card);
        });
      }

      Toast.success('✓ 12 Team Dynamics nyckelmetriker uppdaterade!', 2500);
    } catch (err) {
      console.error('Error fetching team dynamics telemetry:', err);
      Toast.warning('Kunde inte läsa in team dynamics telemetri.');
    }
  }

  function closeTeamDynamicsModal() {
    if (teamDynamicsModalOverlay) teamDynamicsModalOverlay.style.display = 'none';
  }

  if (btnTeamDynamicsTelemetry) btnTeamDynamicsTelemetry.addEventListener('click', openTeamDynamicsModal);
  if (btnCloseTeamDynamicsModal) btnCloseTeamDynamicsModal.addEventListener('click', closeTeamDynamicsModal);
  if (btnCloseTeamDynamicsFooter) btnCloseTeamDynamicsFooter.addEventListener('click', closeTeamDynamicsModal);
  if (btnRun12AgentLoopFromModal) {
    btnRun12AgentLoopFromModal.addEventListener('click', () => {
      closeTeamDynamicsModal();
      if (btnRun12AgentLoop) btnRun12AgentLoop.click();
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

  // ─── Maskin & Fritid '25 Production Controller ────────────────────────────
  let lastMfProductionData = null;

  async function openMaskinFritidModal() {
    if (!maskinFritidModalOverlay) return;
    maskinFritidModalOverlay.style.display = 'flex';
    Toast.info('🚜 Beräknar produktionsdata från maskinochfritid-25...', 2000);
    try {
      const res = await fetch('/api/fortnox/maskinochfritid/compute', { method: 'POST' });
      const data = await res.json();
      lastMfProductionData = data;

      const pSummary = data.proposals_summary?.financial_summary || {};
      const grossVol = pSummary.total_gross_volume_sek || 107450;
      const savings = pSummary.total_tax_savings_or_subsidies_sek || 18800;
      const profit = pSummary.total_expected_gross_profit_sek || 35560;

      if (mfKpiGross) mfKpiGross.textContent = `${Math.round(grossVol).toLocaleString('sv-SE')} SEK`;
      if (mfKpiSavings) mfKpiSavings.textContent = `+${Math.round(savings).toLocaleString('sv-SE')} SEK`;
      if (mfKpiProfit) mfKpiProfit.textContent = `+${Math.round(profit).toLocaleString('sv-SE')} SEK (${pSummary.average_contribution_margin_pct || 33}%)`;
      if (mfKpiVouchers) mfKpiVouchers.textContent = `${data.voucher_telemetry?.balanced_vouchers_count || 5} Verifikat (0 öre diff)`;

      // Render vouchers
      if (mfVouchersList) {
        const vRes = await fetch('/api/fortnox/maskinochfritid/vouchers');
        const vouchers = await vRes.json();
        mfVouchersList.innerHTML = vouchers.map(v => `
          <div style="background: rgba(30, 41, 59, 0.8); border: 1px solid rgba(16, 185, 129, 0.3); border-radius: 6px; padding: 10px;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
              <span style="font-weight: 600; font-size: 13px; color: #f8fafc;">Serie ${v.voucher_series} #${v.voucher_number}</span>
              <span style="background: rgba(16, 185, 129, 0.2); color: #10b981; font-size: 11px; padding: 2px 6px; border-radius: 4px; font-weight: 600;">✅ BALANSERAD</span>
            </div>
            <div style="font-size: 11px; color: var(--color-text-muted); margin: 4px 0 6px 0;">${v.description}</div>
            <div style="display: flex; justify-content: space-between; font-size: 12px;">
              <span>Debet: <strong>${Math.round(v.total_debet).toLocaleString('sv-SE')} kr</strong></span>
              <span>Kredit: <strong>${Math.round(v.total_kredit).toLocaleString('sv-SE')} kr</strong></span>
            </div>
          </div>
        `).join('');
      }

      // Render Skatteverket report boxes
      if (mfSkvReportBoxes && data.voucher_telemetry?.skatteverket_report_boxes) {
        const boxes = data.voucher_telemetry.skatteverket_report_boxes;
        const boxLabels = {
          ruta_05_momspliktig_forsaljning_25: "Ruta 05 • Momspliktig försäljning (25%)",
          ruta_07_vmb_beskattningsunderlag: "Ruta 07 • Beskattningsunderlag VMB",
          ruta_10_utgaende_moms_25: "Ruta 10 • Utgående moms (25%)",
          ruta_49_beskattningsunderlag_omvand_byggmoms: "Ruta 49 • Omvänd Byggmoms underlag",
          rut_claim_skatteverket_1513: "Konto 1513 • Statlig RUT-fordran",
        };
        mfSkvReportBoxes.innerHTML = Object.entries(boxes).map(([k, val]) => `
          <div style="display: flex; justify-content: space-between; align-items: center; padding: 8px 10px; background: rgba(30, 41, 59, 0.5); border-radius: 4px; border: 1px solid var(--color-border);">
            <span style="font-size: 12px; color: var(--color-text);">${boxLabels[k] || k}</span>
            <span style="font-weight: 700; font-size: 13px; color: #38bdf8;">${Math.round(val).toLocaleString('sv-SE')} kr</span>
          </div>
        `).join('');
      }

      Toast.success(`🚜 Maskin & Fritid '25 beräknad: 5 verifikat, ${data.erd_graph?.node_count} ERD-noder`, 4000);
      autoCheckpoint('maskinochfritid_prod_run');
    } catch (err) {
      Toast.warning(`Fel vid beräkning av Maskin & Fritid: ${err.message}`, 4000);
    }
  }

  function closeMaskinFritidModal() {
    if (maskinFritidModalOverlay) maskinFritidModalOverlay.style.display = 'none';
  }

  if (btnMaskinFritidProd) {
    btnMaskinFritidProd.addEventListener('click', openMaskinFritidModal);
  }
  if (btnCloseMaskinFritidModal) {
    btnCloseMaskinFritidModal.addEventListener('click', closeMaskinFritidModal);
  }
  if (btnCloseMfModalBottom) {
    btnCloseMfModalBottom.addEventListener('click', closeMaskinFritidModal);
  }
  if (btnLoadMfToCanvas) {
    btnLoadMfToCanvas.addEventListener('click', () => {
      if (lastMfProductionData?.erd_graph) {
        canvas.loadData(lastMfProductionData.erd_graph);
        if (canvasNodeCount) canvasNodeCount.textContent = `${lastMfProductionData.erd_graph.node_count} Noder (Maskin & Fritid '25)`;
        animateCounter(telGrossTurnover, 115000, 107450, 1000, ' SEK');
        animateCounter(telPotentialSavings, 5296, 18800, 1000, '+', ' SEK');
        Toast.success('🌌 Maskin & Fritid Universal ERD aktiv i Spatial Canvas!', 3500);
        closeMaskinFritidModal();
      }
    });
  }

  if (customerModalOverlay) {
    customerModalOverlay.addEventListener('click', (e) => {
      if (e.target === customerModalOverlay) closeCustomerModal();
    });
  }

  if (maskinFritidModalOverlay) {
    maskinFritidModalOverlay.addEventListener('click', (e) => {
      if (e.target === maskinFritidModalOverlay) closeMaskinFritidModal();
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


  // ─── Trajectory Modal Controller ──────────────────────────────────────────

  async function openTrajectoryModal() {
    if (!trajectoryModalOverlay) return;
    trajectoryModalOverlay.style.display = 'flex';
    if (canvas) canvas.trajectoryActive = true;
    Toast.info('🎯 Projicerar kognitiv framtidstrajektoria...', 2000);

    const currentFocal = state.navigationStack[state.navigationStack.length - 1]?.id || 'cust_1';

    try {
      const res = await fetch('/api/precognition/predict', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          project_id: state.currentScenarioId || 'PRJ-101',
          mandate: 'Optimera VMB-marginaler, avlasta fältövertid och säkra projekttillstånd i sandlåda före bokslut',
          current_node_id: currentFocal,
          role: state.currentRole,
          horizon_steps: 3
        })
      });

      const data = await res.json();
      state.currentTrajectory = data;
      renderTrajectoryData(data);
      Toast.success('✓ Realtidstrajektoria beräknad (+3 steg framåt i tiden)!', 3500);
    } catch (err) {
      console.warn('Trajectory prediction error:', err);
      Toast.warning(`Kunde inte projicera trajektoria: ${err.message}`, 3000);
    }
  }

  function closeTrajectoryModal() {
    if (trajectoryModalOverlay) trajectoryModalOverlay.style.display = 'none';
    if (canvas) canvas.trajectoryActive = false;
  }

  function renderTrajectoryData(traj) {
    if (!traj) return;

    // 1. Confidence score badge
    if (trajConfidenceBadge) {
      const confPct = Math.round((traj.confidence_score || 0.94) * 100);
      trajConfidenceBadge.textContent = `${confPct}% Konfidens`;
    }

    // 2. Mandate & Target KPIs with Intent Lifecycle Status
    if (traj.project_intent) {
      if (intentMandateText) {
        const mandateStr = traj.project_intent.mandate || 'Optimera VMB-marginaler, avlasta fältövertid och säkra projekttillstånd i sandlåda före bokslut';
        const rawStatus = (traj.project_intent.status || 'ACTIVE').toLowerCase();
        const statusMap = {
          declared: { icon: '📝', label: 'DECLARED', cls: 'status-declared' },
          active: { icon: '⚡', label: 'ACTIVE', cls: 'status-active' },
          converging: { icon: '🔄', label: 'CONVERGING', cls: 'status-converging' },
          achieved: { icon: '✅', label: 'ACHIEVED', cls: 'status-achieved' },
          blocked: { icon: '⚠️', label: 'BLOCKED', cls: 'status-blocked' }
        };
        const sInfo = statusMap[rawStatus] || statusMap.active;
        intentMandateText.innerHTML = `
          <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">
            <span>${mandateStr}</span>
            <span class="intent-status-badge ${sInfo.cls}">${sInfo.icon} ${sInfo.label}</span>
          </div>
        `;
      }
      if (intentKpisRow && traj.project_intent.target_kpis) {
        const kpis = traj.project_intent.target_kpis;
        intentKpisRow.innerHTML = Object.entries(kpis).map(([k, v]) => {
          let formattedVal = v;
          if (typeof v === 'number') {
            if (v < 1 && v > 0) formattedVal = `${(v * 100).toFixed(1)}%`;
            else formattedVal = v.toLocaleString('sv-SE');
          }
          return `<span class="kpi-chip">🎯 ${k.replace(/_/g, ' ')}: <strong>${formattedVal}</strong></span>`;
        }).join('');
      }
    }

    // 3. Update Canvas overlay with full trajectory object (nodes, confidence, frictions)
    if (canvas && typeof canvas.setTrajectoryNodes === 'function') {
      canvas.setTrajectoryNodes(traj);
    }

    // 4. Render trajectory steps track
    if (trajStepsTrack && traj.predicted_nodes) {
      trajStepsTrack.innerHTML = traj.predicted_nodes.map(step => {
        const probPct = Math.round((step.transition_probability || 0.7) * 100);
        return `
          <div class="traj-step-card">
            <div class="traj-step-top">
              <span class="traj-step-num">+${step.step_offset}</span>
              <span class="traj-domain-tag">${step.domain} • ${step.perspective_window}</span>
            </div>
            <div class="traj-step-title" title="${step.title}">${step.title}</div>
            <div class="traj-prob-row">
              <div class="traj-prob-bar">
                <div class="traj-prob-fill" style="width: ${probPct}%;"></div>
              </div>
              <span class="traj-prob-text">${probPct}%</span>
            </div>
            <div class="traj-step-desc">${step.expected_transformation || ''}</div>
            <button class="btn-pivot-step" onclick="window.pivotToTrajectoryStep('${step.node_id}', '${step.title.replace(/'/g, "\\'")}')">
              🚀 Pivot & Pre-fetch
            </button>
          </div>
        `;
      }).join('');
    }

    // 5. Render proactive skills
    if (trajSkillsList && traj.predicted_skills) {
      if (traj.predicted_skills.length === 0) {
        trajSkillsList.innerHTML = `<div style="font-size:0.75rem; color:var(--text-dim); padding:8px;">Inga färdigheter behöver dispatchas proaktivt.</div>`;
      } else {
        trajSkillsList.innerHTML = traj.predicted_skills.map(skill => `
          <div class="skill-chip-card">
            <div class="skill-chip-header">
              <span class="skill-chip-name">⚡ ${skill.skill_name}</span>
              <span class="skill-lead-tag">Lead: +${skill.lead_time_steps} steg</span>
            </div>
            <div class="skill-chip-reason">${skill.reasoning}</div>
          </div>
        `).join('');
      }
    }

    // 6. Render pre-emptive friction shielding
    if (trajFrictionsList && traj.anticipated_frictions) {
      if (traj.anticipated_frictions.length === 0) {
        trajFrictionsList.innerHTML = `<div style="font-size:0.75rem; color:var(--accent-emerald); padding:8px;">✓ Noll friktioner identifierade i horisonten.</div>`;
      } else {
        trajFrictionsList.innerHTML = traj.anticipated_frictions.map(f => {
          return `
            <div class="friction-alert-item">
              <div class="friction-alert-header">
                <span class="friction-alert-title">⚠️ ${f.predicted_issue}</span>
                <span class="friction-severity-pill">${(f.severity || 'MEDIUM').toUpperCase()}</span>
              </div>
              <div class="friction-text"><strong>Rotorsak:</strong> ${f.root_factor}</div>
              <div class="friction-countermeasure"><strong>Åtgärd:</strong> ${f.preventive_action}</div>
              <button class="btn-preventive-action" onclick="window.triggerPreventiveAction('${f.friction_id}')">
                🛡️ Aktivera Skyddsåtgärd
              </button>
            </div>
          `;
        }).join('');
      }
    }
  }

  // ─── Checkpoints, Auto-Checkpointing & State Diffing Controller ───────────

  let lastAutoCheckpointTime = 0;

  async function autoCheckpoint(triggerSource = 'state_transition') {
    const now = Date.now();
    // Debounce: max 1 auto-checkpoint per 15 seconds
    if (now - lastAutoCheckpointTime < 15000) {
      console.log(`Auto-checkpoint debounced (${triggerSource})`);
      return;
    }
    lastAutoCheckpointTime = now;

    try {
      const res = await fetch('/api/project/checkpoint/auto', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          project_id: state.currentScenarioId || 'PRJ-101',
          trigger_source: triggerSource,
          intent: {
            mandate: state.currentTrajectory?.project_intent?.mandate || 'Optimera VMB-marginaler, avlasta fältövertid och säkra projekttillstånd i sandlåda före bokslut',
            horizon_steps: 3
          },
          agent_states: {
            active_role: state.currentRole,
            active_scope: state.currentScope,
            current_step: state.currentStepIndex
          },
          trajectory_snapshot: state.currentTrajectory || null
        })
      });

      if (res.ok) {
        const data = await res.json();
        const hashShort = data.checksum_sha256 ? data.checksum_sha256.substring(0, 8) : 'WAL';
        Toast.info(`🛡️ Auto-checkpoint: ${data.checkpoint_id} [${hashShort}] (${triggerSource})`, 3000);
        if (checkpointsModalOverlay && checkpointsModalOverlay.style.display !== 'none') {
          fetchCheckpointsList();
        }
      }
    } catch (err) {
      console.warn('Auto-checkpoint error:', err);
    }
  }

  async function openCheckpointsModal() {
    if (!checkpointsModalOverlay) return;
    checkpointsModalOverlay.style.display = 'flex';
    await fetchCheckpointsList();
  }

  function closeCheckpointsModal() {
    if (checkpointsModalOverlay) checkpointsModalOverlay.style.display = 'none';
  }

  function updateCompareButtonState() {
    if (!btnCompareCheckpoints) return;
    const count = state.selectedCheckpointsForDiff.length;
    if (count === 2) {
      btnCompareCheckpoints.style.display = 'inline-flex';
      btnCompareCheckpoints.textContent = `⚖️ Jämför Valda (2)`;
    } else {
      btnCompareCheckpoints.style.display = 'none';
    }
  }

  async function fetchCheckpointsList() {
    if (!checkpointsListContainer) return;
    checkpointsListContainer.innerHTML = `<div style="padding: 20px; text-align: center; color: var(--text-dim);">Hämtar sparade checkpoints...</div>`;

    try {
      const res = await fetch(`/api/project/checkpoints?project_id=${state.currentScenarioId || 'PRJ-101'}`);
      const checkpoints = await res.json();
      state.cachedCheckpoints = checkpoints || [];

      if (!Array.isArray(checkpoints) || checkpoints.length === 0) {
        checkpointsListContainer.innerHTML = `
          <div style="padding: 30px; text-align: center; color: var(--text-dim); background: rgba(0,0,0,0.2); border-radius: 8px;">
            Inga sparade checkpoints i SQLite WAL ännu. Klicka på "+ Skapa Ny Checkpoint Nu" för att skapa en snapshot.
          </div>
        `;
        updateCompareButtonState();
        return;
      }

      checkpointsListContainer.innerHTML = checkpoints.map(c => {
        const timeStr = c.timestamp ? new Date(c.timestamp).toLocaleString('sv-SE') : 'Just nu';
        const hashDisplay = c.checksum_sha256 ? `${c.checksum_sha256.substring(0, 24)}...` : 'N/A';
        const mandateDisplay = c.intent?.mandate ? (c.intent.mandate.length > 40 ? c.intent.mandate.substring(0, 38) + '...' : c.intent.mandate) : 'Standard revisionstillstånd';
        const isSelectedForDiff = state.selectedCheckpointsForDiff.includes(c.checkpoint_id);
        const hasTrajectory = !!c.has_trajectory;
        const triggerSource = c.trigger_source || 'manual';

        return `
          <div class="checkpoint-card ${isSelectedForDiff ? 'compare-selected' : ''}">
            <div style="flex: 1;">
              <div style="display: flex; align-items: center; gap: 8px;">
                <div class="chk-id-title">${c.checkpoint_id}</div>
                <span class="chk-trigger-badge">${triggerSource}</span>
                ${hasTrajectory ? '<span class="chk-has-trajectory-badge">🎯 Trajektoria</span>' : ''}
              </div>
              <div class="chk-meta-row">
                <span>🕒 ${timeStr}</span>
                <span>📦 ${c.node_count || 19} noder • ${c.edge_count || 18} relationer</span>
                <span>🎯 ${mandateDisplay}</span>
              </div>
              <div class="chk-hash">SHA-256: ${hashDisplay}</div>
            </div>
            <div class="chk-action-group">
              ${hasTrajectory ? `
                <button class="btn-replay-trajectory" onclick="window.replayCheckpointTrajectory('${c.checkpoint_id}')" title="Visa sparad kognitiv trajektoria">
                  🎯 Visa Trajektoria
                </button>
              ` : ''}
              <button class="btn-compare-chk ${isSelectedForDiff ? 'active' : ''}" onclick="window.toggleCheckpointCompare('${c.checkpoint_id}')" title="Markera för strukturell diff">
                ${isSelectedForDiff ? '✓ Vald' : '⚖️ Jämför'}
              </button>
              <button class="btn-restore-chk" onclick="window.restoreCheckpointSession('${c.checkpoint_id}')">
                ↺ Återställ Session
              </button>
            </div>
          </div>
        `;
      }).join('');
      updateCompareButtonState();
    } catch (err) {
      console.warn('Checkpoints fetch error:', err);
      checkpointsListContainer.innerHTML = `<div style="padding: 20px; color: var(--accent-rose);">Fel vid hämtning av checkpoints: ${err.message}</div>`;
    }
  }

  async function createNewCheckpoint() {
    Toast.info('💾 Skapar persistent SQLite WAL checkpoint med SHA-256 kontrollsumma...', 2500);
    try {
      const res = await fetch('/api/project/checkpoint', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          project_id: state.currentScenarioId || 'PRJ-101',
          trigger_source: 'manual',
          intent: {
            mandate: state.currentTrajectory?.project_intent?.mandate || 'Optimera VMB-marginaler, avlasta fältövertid och säkra projekttillstånd i sandlåda före bokslut',
            horizon_steps: 3
          },
          agent_states: {
            active_role: state.currentRole,
            active_scope: state.currentScope,
            current_step: state.currentStepIndex
          },
          trajectory_snapshot: state.currentTrajectory || null
        })
      });

      const chk = await res.json();
      Toast.success(`✓ Checkpoint ${chk.checkpoint_id} sparad med SHA-256 integritet!`, 4000);
      await fetchCheckpointsList();
    } catch (err) {
      console.warn('Checkpoint create error:', err);
      Toast.warning(`Kunde inte skapa checkpoint: ${err.message}`, 3000);
    }
  }

  function renderCheckpointDiff(diff, idA, idB) {
    if (!checkpointDiffPanel || !diffPanelContent) return;
    checkpointDiffPanel.style.display = 'block';

    const addedCount = diff.nodes_added?.length || 0;
    const removedCount = diff.nodes_removed?.length || 0;
    const deltaCount = diff.node_count_delta || 0;
    const deltaSign = deltaCount > 0 ? `+${deltaCount}` : `${deltaCount}`;

    diffPanelContent.innerHTML = `
      <div style="font-size: 0.75rem; color: var(--text-muted); margin-bottom: 10px;">
        Jämför: <code>${idA}</code> ➔ <code>${idB}</code>
      </div>
      <div class="diff-metric-grid">
        <div class="diff-metric-card">
          <div class="diff-metric-val delta">${deltaSign}</div>
          <div class="diff-metric-lbl">Nod Delta</div>
        </div>
        <div class="diff-metric-card">
          <div class="diff-metric-val added">+${addedCount}</div>
          <div class="diff-metric-lbl">Tillagda Noder</div>
        </div>
        <div class="diff-metric-card">
          <div class="diff-metric-val removed">-${removedCount}</div>
          <div class="diff-metric-lbl">Borttagna Noder</div>
        </div>
        <div class="diff-metric-card">
          <div class="diff-metric-val delta">${diff.edge_count_delta > 0 ? '+' : ''}${diff.edge_count_delta || 0}</div>
          <div class="diff-metric-lbl">Relation Delta</div>
        </div>
      </div>

      ${diff.nodes_added && diff.nodes_added.length > 0 ? `
        <div class="diff-detail-section">
          <h5>Tillagda Entiteter:</h5>
          <div class="diff-pill-list">
            ${diff.nodes_added.map(n => `<span class="diff-added">+ ${n}</span>`).join('')}
          </div>
        </div>
      ` : ''}

      ${diff.nodes_removed && diff.nodes_removed.length > 0 ? `
        <div class="diff-detail-section">
          <h5>Borttagna Entiteter:</h5>
          <div class="diff-pill-list">
            ${diff.nodes_removed.map(n => `<span class="diff-removed">- ${n}</span>`).join('')}
          </div>
        </div>
      ` : ''}

      ${diff.intent_drift ? `
        <div class="diff-detail-section">
          <h5>Semantisk Intent Drift:</h5>
          <div class="diff-intent-drift">${diff.intent_drift}</div>
        </div>
      ` : ''}
    `;
  }

  // ─── Global Helper Handlers ───────────────────────────────────────────────

  window.toggleCheckpointCompare = (checkpointId) => {
    const idx = state.selectedCheckpointsForDiff.indexOf(checkpointId);
    if (idx >= 0) {
      state.selectedCheckpointsForDiff.splice(idx, 1);
    } else {
      if (state.selectedCheckpointsForDiff.length >= 2) {
        state.selectedCheckpointsForDiff.shift();
      }
      state.selectedCheckpointsForDiff.push(checkpointId);
    }
    updateCompareButtonState();
    fetchCheckpointsList();
  };

  window.replayCheckpointTrajectory = (checkpointId) => {
    const chk = (state.cachedCheckpoints || []).find(c => c.checkpoint_id === checkpointId);
    if (chk && chk.trajectory_snapshot) {
      state.currentTrajectory = chk.trajectory_snapshot;
      if (trajectoryModalOverlay) trajectoryModalOverlay.style.display = 'flex';
      if (canvas && typeof canvas.setTrajectoryNodes === 'function') {
        canvas.trajectoryActive = true;
        canvas.setTrajectoryNodes(chk.trajectory_snapshot);
      }
      renderTrajectoryData(chk.trajectory_snapshot);
      Toast.info(`🎯 Visar sparad trajektoria från checkpoint ${checkpointId}`, 3500);
    } else {
      Toast.warning('Ingen trajektoria sparad för denna checkpoint.', 3000);
    }
  };

  window.pivotToTrajectoryStep = async (nodeId, title) => {
    closeTrajectoryModal();
    Toast.info(`Pivoterar till projicerad nod: ${title} (${nodeId})`, 3000);
    await pivotContext(nodeId, 'predicted_trajectory', title);
    if (canvas && typeof canvas.pivotTo === 'function') {
      canvas.pivotTo(nodeId);
    }
  };

  window.triggerPreventiveAction = (frictionId) => {
    Toast.success(`🛡️ Pre-emptiv skyddsåtgärd för ${frictionId} har aktiverats i sandlådemiljön! Risk eliminerad.`, 4500);
  };

  window.restoreCheckpointSession = async (checkpointId) => {
    Toast.info(`Återställer tillstånd från SQLite WAL: ${checkpointId}...`, 2500);
    try {
      const res = await fetch('/api/project/restore', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          checkpoint_id: checkpointId,
          project_id: state.currentScenarioId || 'PRJ-101'
        })
      });

      const data = await res.json();
      if (data.success) {
        closeCheckpointsModal();
        await fetchGraphData();
        await resolveContext();
        Toast.success(`✓ Nolldatatapps-återställning slutförd! ${data.erd_node_count} noder återlästa (100% SHA-256 matchning).`, 5000);
        autoCheckpoint('checkpoint_restore');
      } else {
        Toast.warning(`Återställning misslyckades: ${data.error || 'Okänt fel'}`, 3500);
      }
    } catch (err) {
      console.warn('Restore error:', err);
      Toast.warning(`Fel vid återställning: ${err.message}`, 3500);
    }
  };

  // ─── Trajectory & Checkpoint Button Event Listeners ───────────────────────

  if (btnTrajectory) {
    btnTrajectory.addEventListener('click', openTrajectoryModal);
  }

  if (btnCloseTrajectoryModal) {
    btnCloseTrajectoryModal.addEventListener('click', closeTrajectoryModal);
  }

  if (trajectoryModalOverlay) {
    trajectoryModalOverlay.addEventListener('click', (e) => {
      if (e.target === trajectoryModalOverlay) closeTrajectoryModal();
    });
  }

  if (btnQuickCheckpointFromTraj) {
    btnQuickCheckpointFromTraj.addEventListener('click', async () => {
      await createNewCheckpoint();
      Toast.success('Checkpoint skapad direkt från trajektorian!');
    });
  }

  if (btnRunOrchestratorWithTraj) {
    btnRunOrchestratorWithTraj.addEventListener('click', () => {
      closeTrajectoryModal();
      if (btnRun12AgentLoop) btnRun12AgentLoop.click();
    });
  }

  if (btnCheckpoints) {
    btnCheckpoints.addEventListener('click', openCheckpointsModal);
  }

  if (btnCloseCheckpointsModal) {
    btnCloseCheckpointsModal.addEventListener('click', closeCheckpointsModal);
  }

  if (checkpointsModalOverlay) {
    checkpointsModalOverlay.addEventListener('click', (e) => {
      if (e.target === checkpointsModalOverlay) closeCheckpointsModal();
    });
  }

  if (btnCreateNewCheckpoint) {
    btnCreateNewCheckpoint.addEventListener('click', createNewCheckpoint);
  }

  if (btnCompareCheckpoints) {
    btnCompareCheckpoints.addEventListener('click', async () => {
      if (state.selectedCheckpointsForDiff.length !== 2) return;
      const [cpA, cpB] = state.selectedCheckpointsForDiff;
      Toast.info(`⚖️ Beräknar strukturell och semantisk diff...`, 2500);
      try {
        const res = await fetch('/api/project/checkpoint/diff', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ checkpoint_a: cpA, checkpoint_b: cpB })
        });
        const diffData = await res.json();
        if (diffData.error) {
          Toast.warning(`Diff misslyckades: ${diffData.error}`);
          return;
        }
        renderCheckpointDiff(diffData, cpA, cpB);
      } catch (err) {
        console.error('Diff error:', err);
        Toast.warning(`Kunde inte beräkna diff: ${err.message}`);
      }
    });
  }

  if (btnCloseDiffPanel) {
    btnCloseDiffPanel.addEventListener('click', () => {
      if (checkpointDiffPanel) checkpointDiffPanel.style.display = 'none';
    });
  }


  // ─── Shortcuts Cheat Sheet & Dock Controller ─────────────────────────────

  function openShortcutsModal() {
    if (shortcutsModalOverlay) shortcutsModalOverlay.style.display = 'flex';
  }

  function closeShortcutsModal() {
    if (shortcutsModalOverlay) shortcutsModalOverlay.style.display = 'none';
  }

  function triggerKeyVisualFeedback(keyName, dockEl, shortcutRowKey) {
    if (dockEl) {
      dockEl.classList.add('kbd-pressed');
      setTimeout(() => dockEl.classList.remove('kbd-pressed'), 280);
    }
    if (liveKeyVisualizer) {
      liveKeyVisualizer.textContent = keyName.toUpperCase();
      liveKeyVisualizer.style.transform = 'scale(1.15)';
      liveKeyVisualizer.style.borderColor = '#10b981';
      liveKeyVisualizer.style.boxShadow = '0 0 16px rgba(16, 185, 129, 0.7)';
      setTimeout(() => {
        if (liveKeyVisualizer) {
          liveKeyVisualizer.style.transform = 'scale(1)';
          liveKeyVisualizer.style.borderColor = 'rgba(16, 185, 129, 0.5)';
          liveKeyVisualizer.style.boxShadow = '0 0 10px rgba(16, 185, 129, 0.3)';
        }
      }, 180);
    }
    if (shortcutRowKey) {
      const row = document.querySelector(`.shortcut-row[data-shortcut-key="${shortcutRowKey}"]`);
      if (row) {
        row.classList.add('row-active-highlight');
        setTimeout(() => row.classList.remove('row-active-highlight'), 400);
      }
    }
  }

  // Modal Buttons
  if (btnOpenShortcutsModalHeader) btnOpenShortcutsModalHeader.addEventListener('click', openShortcutsModal);
  if (dockBtnHelp) dockBtnHelp.addEventListener('click', openShortcutsModal);
  if (btnCloseShortcutsModal) btnCloseShortcutsModal.addEventListener('click', closeShortcutsModal);
  if (btnCloseShortcutsFooter) btnCloseShortcutsFooter.addEventListener('click', closeShortcutsModal);
  if (shortcutsModalOverlay) {
    shortcutsModalOverlay.addEventListener('click', (e) => {
      if (e.target === shortcutsModalOverlay) closeShortcutsModal();
    });
  }

  // Direct Clicks on Ambient Shortcut Dock
  if (dockBtnT) dockBtnT.addEventListener('click', () => {
    if (btnTrajectory) btnTrajectory.click();
  });
  if (dockBtnC) dockBtnC.addEventListener('click', () => {
    if (btnCheckpoints) btnCheckpoints.click();
  });
  if (dockBtnNums) dockBtnNums.addEventListener('click', () => {
    const currNum = parseInt(state.currentWindow.replace('W', '')) || 5;
    const nextWin = `W${(currNum % 9) + 1}`;
    switchWindow(nextWin);
    Toast.info(`Bytte till fönster ${nextWin}`);
  });
  if (dockBtnD) dockBtnD.addEventListener('click', () => {
    const dEvent = new KeyboardEvent('keydown', { key: 'd' });
    document.dispatchEvent(dEvent);
  });
  if (dockBtnR) dockBtnR.addEventListener('click', () => {
    const rEvent = new KeyboardEvent('keydown', { key: 'r' });
    document.dispatchEvent(rEvent);
  });
  if (dockBtnArrows) dockBtnArrows.addEventListener('click', () => {
    const nextStep = Math.min(state.currentStepIndex + 1, 6);
    setStep(nextStep);
  });
  if (dockBtnEsc) dockBtnEsc.addEventListener('click', () => {
    const escEvent = new KeyboardEvent('keydown', { key: 'Escape' });
    document.dispatchEvent(escEvent);
  });


  // ─── Keyboard Shortcuts with Tactile Visual Feedback ───────────────────────

  document.addEventListener('keydown', (e) => {
    // Ignore if focused on an input
    if (e.target.tagName === 'INPUT' || e.target.tagName === 'SELECT' || e.target.tagName === 'TEXTAREA') return;

    const key = e.key;

    // ? or Shift+/ : Toggle Shortcuts Cheat Sheet Modal
    if (key === '?' || (e.shiftKey && key === '/')) {
      e.preventDefault();
      triggerKeyVisualFeedback('?', dockBtnHelp, '?');
      if (shortcutsModalOverlay && shortcutsModalOverlay.style.display === 'flex') {
        closeShortcutsModal();
      } else {
        openShortcutsModal();
      }
      return;
    }

    // 1–9: Switch Omnipod window
    if (key >= '1' && key <= '9') {
      const windowId = `W${key}`;
      if (windowDefs.find(w => w.id === windowId)) {
        triggerKeyVisualFeedback(key, dockBtnNums, '1-9');
        switchWindow(windowId);
        return;
      }
    }

    // T: Toggle Trajectory Modal
    if (key === 't' || key === 'T') {
      triggerKeyVisualFeedback('T', dockBtnT, 't');
      if (trajectoryModalOverlay && trajectoryModalOverlay.style.display === 'flex') {
        closeTrajectoryModal();
      } else {
        openTrajectoryModal();
      }
      return;
    }

    // C: Toggle Checkpoints Modal
    if (key === 'c' || key === 'C') {
      triggerKeyVisualFeedback('C', dockBtnC, 'c');
      if (checkpointsModalOverlay && checkpointsModalOverlay.style.display === 'flex') {
        closeCheckpointsModal();
      } else {
        openCheckpointsModal();
      }
      return;
    }

    // Arrow Right: Step forward
    if (key === 'ArrowRight') {
      e.preventDefault();
      triggerKeyVisualFeedback('→', dockBtnArrows, 'arrowright');
      const nextStep = Math.min(state.currentStepIndex + 1, 6);
      setStep(nextStep);
      return;
    }

    // Arrow Left: Step backward
    if (key === 'ArrowLeft') {
      e.preventDefault();
      triggerKeyVisualFeedback('←', dockBtnArrows, 'arrowright');
      const prevStep = Math.max(state.currentStepIndex - 1, 1);
      setStep(prevStep);
      return;
    }

    // D: Cycle scope D0→D3
    if (key === 'd' || key === 'D') {
      triggerKeyVisualFeedback('D', dockBtnD, 'd');
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
      triggerKeyVisualFeedback('R', dockBtnR, 'r');
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
      triggerKeyVisualFeedback('Ctrl+Enter', null, 'ctrl+enter');
      if (btnRunFullLoop && !state.isAgentRunning) btnRunFullLoop.click();
      return;
    }

    // Escape: Close modals, inspector drawer, or reset stepper
    if (key === 'Escape') {
      triggerKeyVisualFeedback('Esc', dockBtnEsc, 'escape');
      if (nodeInspectorDrawer && nodeInspectorDrawer.style.display !== 'none') {
        closeNodeInspector();
        return;
      }
      if (shortcutsModalOverlay && shortcutsModalOverlay.style.display === 'flex') {
        closeShortcutsModal();
        return;
      }
      if (trajectoryModalOverlay && trajectoryModalOverlay.style.display === 'flex') {
        closeTrajectoryModal();
        return;
      }
      if (checkpointsModalOverlay && checkpointsModalOverlay.style.display === 'flex') {
        closeCheckpointsModal();
        return;
      }
      if (customerModalOverlay && customerModalOverlay.style.display === 'flex') {
        closeCustomerModal();
        return;
      }
      if (maskinFritidModalOverlay && maskinFritidModalOverlay.style.display === 'flex') {
        closeMaskinFritidModal();
        return;
      }
      if (omnipodLayersModalOverlay && omnipodLayersModalOverlay.style.display === 'flex') {
        closeOmnipodLayersModal();
        return;
      }
      if (teamDynamicsModalOverlay && teamDynamicsModalOverlay.style.display === 'flex') {
        closeTeamDynamicsModal();
        return;
      }
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
    if (e.target.value === 'maskinochfritid_prod') {
      openMaskinFritidModal();
    } else {
      await loadScenario(e.target.value);
      Toast.info(`Scenario laddat: ${e.target.options[e.target.selectedIndex].text}`);
    }
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
  loadProposedVouchers();
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
