/**
 * BART Spatial Canvas v3.0 — Interactive HTML5 Canvas Graph Visualizer
 * Full pivot-navigation, opportunity rings, minimap overlay, smooth pan-zoom.
 * Zero-dependency, 60fps force-directed relational layout.
 */

// Polyfill for CanvasRenderingContext2D.roundRect (Chrome <99, Firefox <112, Safari <15.4)
if (!CanvasRenderingContext2D.prototype.roundRect) {
  CanvasRenderingContext2D.prototype.roundRect = function(x, y, w, h, r) {
    if (w < 2 * r) r = w / 2;
    if (h < 2 * r) r = h / 2;
    this.beginPath();
    this.moveTo(x + r, y);
    this.arcTo(x + w, y, x + w, y + h, r);
    this.arcTo(x + w, y + h, x, y + h, r);
    this.arcTo(x, y + h, x, y, r);
    this.arcTo(x, y, x + w, y, r);
    this.closePath();
    return this;
  };
}


class SpatialCanvas {
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
    this.ctx = this.canvas.getContext('2d');
    this.nodes = [];
    this.links = [];
    this.selectedNodeId = null;
    this.hoveredNodeId = null;
    this.onNodeClickCallback = null;
    this.onPivotCallback = null;

    // Viewport transform (pan + zoom)
    this.viewport = { x: 0, y: 0, scale: 1.0 };
    this.targetViewport = { x: 0, y: 0, scale: 1.0 };
    this.isPanning = false;
    this.panStart = { x: 0, y: 0 };
    this.panOrigin = { x: 0, y: 0 };

    // Domain color mappings
    this.domainColors = {
      'Operational': '#06b6d4',
      'Exchange': '#f59e0b',
      'Trust': '#10b981',
      'Knowledge': '#8b5cf6',
      'Tools': '#38bdf8',
      'Interactional Interface': '#ec4899',
      'Interactional': '#ec4899',
      'Default': '#94a3b8'
    };

    // Universal ERD Entity Glyphs & Short Labels
    this.typeGlyphs = {
      'organization': '🏛️',
      'team': '👥',
      'person': '👤',
      'role': '🎭',
      'capability': '⚡',
      'assignment': '📋',
      'observation': '👁️',
      'diagnosis': '🩺',
      'intervention': '🛠️',
      'transition_plan': '🗺️',
      'communication': '💬',
      'experiment': '🧪',
      'measurement': '📏',
      'learning': '💡',
      'knowledge': '📚',
      'voucher': '🧾',
      'account': '📊',
      'batch': '📦',
      'rule': '⚖️',
      'transaction': '💳'
    };

    // Opportunity ring state (animated pulsing)
    this.opportunityNodeIds = new Set();
    this.ringPhase = 0;

    this.dragNode = null;
    this.isDragMove = false;
    this.mouse = { x: 0, y: 0, isDown: false };

    // Real-time Cognitive Trajectory state
    this.trajectoryNodes = [];
    this.trajectoryFrictions = [];
    this.trajectoryConfidence = 0;
    this.trajectoryIntentStatus = 'active';
    this.trajectoryActive = false;  // true when modal is open (full opacity)

    // Filter & Physics state
    this.isPhysicsFrozen = false;
    this.filterQuery = '';
    this.filterDomain = 'ALL';

    // Layout Mode: 'force' (relational force) or 'orbit' (concentric D0-D3 rings)
    this.layoutMode = 'force';
    this.orbitalPhase = 0;

    // Visual FX: Particle glow & ripple waves
    this.particles = [];
    this.rippleWaves = [];

    // Universal ERD Category Filter & Causal Path Tracer
    this.activeCategory = 'ALL';
    this.tracedPathNodes = new Set();
    this.tracedPathLinks = new Set();
    this.pathTracePhase = 0;

    // Minimap
    this.minimapCanvas = null;
    this.minimapCtx = null;

    this.init();
  }

  init() {
    this.resize();
    window.addEventListener('resize', () => this.resize());

    this.canvas.addEventListener('mousemove', (e) => this.handleMouseMove(e));
    this.canvas.addEventListener('mousedown', (e) => this.handleMouseDown(e));
    this.canvas.addEventListener('mouseup', (e) => this.handleMouseUp(e));
    this.canvas.addEventListener('click', (e) => this.handleClick(e));
    this.canvas.addEventListener('wheel', (e) => this.handleWheel(e), { passive: false });
    this.canvas.addEventListener('dblclick', (e) => this.handleDblClick(e));

    // Setup minimap
    this._setupMinimap();

    this.animate();
  }

  _setupMinimap() {
    const wrapper = this.canvas.parentElement;
    let mm = wrapper.querySelector('#spatialMinimap');
    if (!mm) {
      mm = document.createElement('canvas');
      mm.id = 'spatialMinimap';
      // Use CSS pixels for layout; DPR-scale the internal buffer
      mm.style.cssText = `
        position: absolute; bottom: 44px; right: 12px;
        width: 140px; height: 90px;
        border: 1px solid rgba(6,182,212,0.25);
        border-radius: 6px;
        background: rgba(7,10,18,0.75);
        backdrop-filter: blur(8px);
        pointer-events: none;
        z-index: 10;
      `;
      wrapper.style.position = 'relative';
      wrapper.appendChild(mm);
    }
    // DPR-scale minimap buffer
    const dpr = window.devicePixelRatio || 1;
    mm.width = 140 * dpr;
    mm.height = 90 * dpr;
    this.minimapCanvas = mm;
    this.minimapCtx = mm.getContext('2d');
    this.minimapCtx.scale(dpr, dpr);
    this.minimapW = 140;  // CSS pixel dimensions for drawing logic
    this.minimapH = 90;
  }

  resize() {
    const rect = this.canvas.parentElement.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;
    this.canvas.width = rect.width * dpr;
    this.canvas.height = rect.height * dpr;
    this.ctx.scale(dpr, dpr);
    this.width = rect.width;
    this.height = rect.height;
  }

  // ─── World ↔ Screen coordinate helpers ────────────────────────────────────

  worldToScreen(wx, wy) {
    return {
      x: wx * this.viewport.scale + this.viewport.x,
      y: wy * this.viewport.scale + this.viewport.y
    };
  }

  screenToWorld(sx, sy) {
    return {
      x: (sx - this.viewport.x) / this.viewport.scale,
      y: (sy - this.viewport.y) / this.viewport.scale
    };
  }

  // ─── Data ─────────────────────────────────────────────────────────────────

  loadData(graphData, focalId = null) {
    return this.setData(graphData, focalId);
  }

  setData(graphData, focalId = null) {
    const existingNodes = new Map(this.nodes.map(n => [n.id, n]));
    const centerX = this.width / 2;
    const centerY = this.height / 2;

    this.nodes = graphData.nodes.map((nodeData, idx) => {
      const existing = existingNodes.get(nodeData.id);
      const angle = (idx / graphData.nodes.length) * Math.PI * 2;
      const radius = nodeData.scope === 'D0' ? 40 : (nodeData.scope === 'D1' ? 95 : 160);

      return {
        ...nodeData,
        x: existing ? existing.x : centerX + Math.cos(angle) * radius + (Math.random() - 0.5) * 20,
        y: existing ? existing.y : centerY + Math.sin(angle) * radius + (Math.random() - 0.5) * 20,
        vx: 0,
        vy: 0,
        radius: nodeData.size ? nodeData.size / 2 : 12,
        color: this.domainColors[nodeData.domain] || this.domainColors['Default']
      };
    });

    this.links = graphData.links.map(l => ({
      source: l.source,
      target: l.target,
      relation: l.relation,
      strength: l.strength || 1.0
    }));

    // Mark opportunity nodes (financial_impact > 500 SEK)
    this.opportunityNodeIds.clear();
    this.nodes.forEach(n => {
      if (n.financial_impact && n.financial_impact > 500) {
        this.opportunityNodeIds.add(n.id);
      }
    });

    const pivotTarget = focalId || graphData.focal_id;
    if (pivotTarget) {
      this.selectedNodeId = pivotTarget;
      this._animatePivotToNode(pivotTarget);
    } else if (!this.selectedNodeId && this.nodes.length > 0) {
      const focal = this.nodes.find(n => n.type === 'batch' || n.id === 'TX-1001') || this.nodes[0];
      this.selectedNodeId = focal.id;
    }
  }

  setTrajectoryNodes(nodes) {
    this.trajectoryNodes = Array.isArray(nodes) ? nodes : [];
  }

  setFullTrajectory(trajectoryData) {
    if (!trajectoryData) return;
    this.trajectoryNodes = trajectoryData.predicted_nodes || [];
    this.trajectoryFrictions = trajectoryData.anticipated_frictions || [];
    this.trajectoryConfidence = trajectoryData.confidence_score || 0;
    this.trajectoryIntentStatus = trajectoryData.computed_intent_status || 'active';
    this.trajectoryActive = true;
  }

  clearTrajectoryOverlay() {
    this.trajectoryActive = false;
  }

  clearTrajectoryNodes() {
    this.trajectoryNodes = [];
    this.trajectoryFrictions = [];
    this.trajectoryConfidence = 0;
    this.trajectoryIntentStatus = 'active';
    this.trajectoryActive = false;
  }

  setFilter(query = '', domain = 'ALL') {
    this.filterQuery = (query || '').toLowerCase().trim();
    this.filterDomain = domain || 'ALL';
  }

  togglePhysics() {
    this.isPhysicsFrozen = !this.isPhysicsFrozen;
    return this.isPhysicsFrozen;
  }

  setLayoutMode(mode) {
    this.layoutMode = mode === 'orbit' ? 'orbit' : 'force';
    return this.layoutMode;
  }

  toggleLayoutMode() {
    this.layoutMode = this.layoutMode === 'orbit' ? 'force' : 'orbit';
    return this.layoutMode;
  }

  setCategory(cat = 'ALL') {
    this.activeCategory = cat || 'ALL';
  }

  addRipple(x, y, color = '#38bdf8') {
    this.rippleWaves.push({
      x,
      y,
      r: 12,
      alpha: 0.85,
      color: color || '#38bdf8'
    });
    if (this.rippleWaves.length > 8) this.rippleWaves.shift();
  }

  spawnParticles(x, y, color = '#38bdf8', count = 4) {
    for (let i = 0; i < count; i++) {
      const angle = Math.random() * Math.PI * 2;
      const speed = Math.random() * 1.5 + 0.5;
      this.particles.push({
        x: x + (Math.random() - 0.5) * 8,
        y: y + (Math.random() - 0.5) * 8,
        vx: Math.cos(angle) * speed,
        vy: Math.sin(angle) * speed,
        size: Math.random() * 2.5 + 1.2,
        color: color || '#38bdf8',
        life: 1.0,
        alpha: 1.0
      });
    }
    if (this.particles.length > 60) this.particles.splice(0, this.particles.length - 60);
  }

  traceCausalPath(startId, endId) {
    this.tracedPathNodes.clear();
    this.tracedPathLinks.clear();
    if (!startId || !endId || startId === endId) return [];

    const queue = [[startId]];
    const visited = new Set([startId]);

    let foundPath = null;
    while (queue.length > 0) {
      const path = queue.shift();
      const curr = path[path.length - 1];
      if (curr === endId) {
        foundPath = path;
        break;
      }

      const neighbors = [];
      this.links.forEach(l => {
        if (l.source === curr && !visited.has(l.target)) {
          neighbors.push(l.target);
          visited.add(l.target);
        } else if (l.target === curr && !visited.has(l.source)) {
          neighbors.push(l.source);
          visited.add(l.source);
        }
      });

      for (const n of neighbors) {
        queue.push([...path, n]);
      }
    }

    if (foundPath) {
      foundPath.forEach(nid => this.tracedPathNodes.add(nid));
      for (let i = 0; i < foundPath.length - 1; i++) {
        const u = foundPath[i];
        const v = foundPath[i + 1];
        this.links.forEach((l, idx) => {
          if ((l.source === u && l.target === v) || (l.source === v && l.target === u)) {
            this.tracedPathLinks.add(idx);
          }
        });
      }
    }
    return foundPath || [];
  }

  clearTracedPath() {
    this.tracedPathNodes.clear();
    this.tracedPathLinks.clear();
  }

  getNode(id) {
    return this.nodes.find(n => n.id === id);
  }

  // ─── Pivot To Node (animated smooth pan-zoom) ─────────────────────────────

  pivotTo(nodeId) {
    this.selectedNodeId = nodeId;
    this._animatePivotToNode(nodeId);
  }

  _animatePivotToNode(nodeId) {
    const node = this.getNode(nodeId);
    if (!node) return;

    // Compute target viewport so node is centered
    const targetScale = Math.min(1.6, Math.max(0.7, this.viewport.scale));
    const targetX = this.width / 2 - node.x * targetScale;
    const targetY = this.height / 2 - node.y * targetScale;

    this.targetViewport = { x: targetX, y: targetY, scale: targetScale };
  }

  // ─── Event Handlers ───────────────────────────────────────────────────────

  _getMousePos(e) {
    const rect = this.canvas.getBoundingClientRect();
    return { x: e.clientX - rect.left, y: e.clientY - rect.top };
  }

  _hitTestNode(sx, sy) {
    const world = this.screenToWorld(sx, sy);
    for (let i = this.nodes.length - 1; i >= 0; i--) {
      const n = this.nodes[i];
      const dx = world.x - n.x;
      const dy = world.y - n.y;
      const r = n.radius + 4;
      if (dx * dx + dy * dy <= r * r) return n.id;
    }
    return null;
  }

  handleMouseMove(e) {
    const pos = this._getMousePos(e);
    this.mouse.x = pos.x;
    this.mouse.y = pos.y;

    if (this.isPanning) {
      this.viewport.x = this.panOrigin.x + (pos.x - this.panStart.x);
      this.viewport.y = this.panOrigin.y + (pos.y - this.panStart.y);
      this.targetViewport.x = this.viewport.x;
      this.targetViewport.y = this.viewport.y;
      return;
    }

    if (this.dragNode) {
      const world = this.screenToWorld(pos.x, pos.y);
      this.dragNode.x = world.x;
      this.dragNode.y = world.y;
      this.isDragMove = true;
      return;
    }

    const hit = this._hitTestNode(pos.x, pos.y);
    this.hoveredNodeId = hit;
    this.canvas.style.cursor = hit ? 'pointer' : 'grab';
  }

  handleMouseDown(e) {
    const pos = this._getMousePos(e);
    this.mouse.isDown = true;
    this.isDragMove = false;

    const hit = this._hitTestNode(pos.x, pos.y);
    if (hit) {
      this.dragNode = this.getNode(hit);
    } else if (e.button === 0) {
      this.isPanning = true;
      this.panStart = { x: pos.x, y: pos.y };
      this.panOrigin = { x: this.viewport.x, y: this.viewport.y };
      this.canvas.style.cursor = 'grabbing';
    }
  }

  handleMouseUp(e) {
    this.dragNode = null;
    this.isPanning = false;
    this.mouse.isDown = false;
    this.canvas.style.cursor = 'grab';
  }

  handleClick(e) {
    if (this.isDragMove) { this.isDragMove = false; return; }
    const pos = this._getMousePos(e);
    const hit = this._hitTestNode(pos.x, pos.y);
    if (hit) {
      this.selectedNodeId = hit;
      const node = this.getNode(hit);
      if (node) {
        this.addRipple(node.x, node.y, node.color);
        this.spawnParticles(node.x, node.y, node.color, 8);
      }
      if (this.onNodeClickCallback) this.onNodeClickCallback(node);
    }
  }

  handleDblClick(e) {
    const pos = this._getMousePos(e);
    const hit = this._hitTestNode(pos.x, pos.y);
    if (hit) {
      this.selectedNodeId = hit;
      const node = this.getNode(hit);
      // Double-click triggers full pivot (context repivot signal)
      if (this.onPivotCallback) this.onPivotCallback(node);
      this._animatePivotToNode(hit);
    } else {
      // Double-click on empty → reset zoom
      this.targetViewport = { x: 0, y: 0, scale: 1.0 };
    }
  }

  handleWheel(e) {
    e.preventDefault();
    const pos = this._getMousePos(e);
    const delta = e.deltaY > 0 ? 0.9 : 1.1;
    const newScale = Math.max(0.3, Math.min(3.0, this.targetViewport.scale * delta));

    // Zoom toward cursor
    const worldPos = this.screenToWorld(pos.x, pos.y);
    this.targetViewport.scale = newScale;
    this.targetViewport.x = pos.x - worldPos.x * newScale;
    this.targetViewport.y = pos.y - worldPos.y * newScale;
  }

  onNodeClick(cb) { this.onNodeClickCallback = cb; }
  onPivot(cb) { this.onPivotCallback = cb; }
  // Kept as alias for backward compat
  _setTrajectoryNodesCompat(nodes) { this.trajectoryNodes = nodes || []; }

  resetLayout() {
    const centerX = this.width / 2;
    const centerY = this.height / 2;
    this.nodes.forEach((n, idx) => {
      const angle = (idx / this.nodes.length) * Math.PI * 2;
      const radius = n.scope === 'D0' ? 30 : (n.scope === 'D1' ? 90 : 160);
      n.x = centerX + Math.cos(angle) * radius;
      n.y = centerY + Math.sin(angle) * radius;
      n.vx = 0;
      n.vy = 0;
    });
    this.targetViewport = { x: 0, y: 0, scale: 1.0 };
  }

  // ─── Simulation ───────────────────────────────────────────────────────────

  simulate() {
    if (this.isPhysicsFrozen) return;

    const centerX = this.width / 2;
    const centerY = this.height / 2;
    const damping = 0.85;

    if (this.layoutMode === 'orbit') {
      this.orbitalPhase += 0.003;

      const ringD0 = [];
      const ringD1 = [];
      const ringD2 = [];
      const ringD3 = [];

      this.nodes.forEach(n => {
        const typeL = (n.type || '').toLowerCase();
        if (n.id === this.selectedNodeId || n.scope === 'D0' || typeL === 'batch' || typeL === 'organization') {
          ringD0.push(n);
        } else if (n.scope === 'D1' || ['role', 'assignment', 'person', 'voucher'].includes(typeL)) {
          ringD1.push(n);
        } else if (n.scope === 'D2' || ['observation', 'diagnosis', 'intervention', 'team', 'account'].includes(typeL)) {
          ringD2.push(n);
        } else {
          ringD3.push(n);
        }
      });

      const positionRing = (arr, radius, speedMultiplier) => {
        const count = arr.length || 1;
        arr.forEach((n, idx) => {
          if (n === this.dragNode) return;
          const angle = (idx / count) * Math.PI * 2 + this.orbitalPhase * speedMultiplier;
          const targetX = centerX + Math.cos(angle) * radius;
          const targetY = centerY + Math.sin(angle) * radius;
          n.vx += (targetX - n.x) * 0.08;
          n.vy += (targetY - n.y) * 0.08;
        });
      };

      positionRing(ringD0, 0, 0);
      positionRing(ringD1, 140, 0.5);
      positionRing(ringD2, 270, -0.35);
      positionRing(ringD3, 410, 0.2);

      this.nodes.forEach(n => {
        if (n !== this.dragNode) {
          n.x += n.vx;
          n.y += n.vy;
          n.vx *= 0.78;
          n.vy *= 0.78;
        }
      });
    } else {
      // Standard Force-Directed Relational Simulation
      for (let i = 0; i < this.nodes.length; i++) {
        const n1 = this.nodes[i];
        n1.vx += (centerX - n1.x) * 0.004;
        n1.vy += (centerY - n1.y) * 0.004;

        for (let j = i + 1; j < this.nodes.length; j++) {
          const n2 = this.nodes[j];
          const dx = n2.x - n1.x;
          const dy = n2.y - n1.y;
          const dist = Math.sqrt(dx * dx + dy * dy) || 1;
          const minDist = n1.radius + n2.radius + 40;
          if (dist < minDist) {
            const force = (minDist - dist) / dist * 0.22;
            n1.vx -= dx * force;
            n1.vy -= dy * force;
            n2.vx += dx * force;
            n2.vy += dy * force;
          }
        }
      }

      this.links.forEach(l => {
        const s = this.getNode(l.source);
        const t = this.getNode(l.target);
        if (s && t) {
          const dx = t.x - s.x;
          const dy = t.y - s.y;
          const dist = Math.sqrt(dx * dx + dy * dy) || 1;
          const targetDist = 80;
          const force = (dist - targetDist) * 0.02 * l.strength;
          s.vx += (dx / dist) * force;
          s.vy += (dy / dist) * force;
          t.vx -= (dx / dist) * force;
          t.vy -= (dy / dist) * force;
        }
      });

      this.nodes.forEach(n => {
        if (n !== this.dragNode) {
          n.x += n.vx;
          n.y += n.vy;
          n.vx *= damping;
          n.vy *= damping;
          const pad = n.radius + 10;
          n.x = Math.max(pad, Math.min(this.width - pad, n.x));
          n.y = Math.max(pad, Math.min(this.height - pad, n.y));
        }
      });
    }

    // Ambient particle emission on focal and opportunity nodes
    if (Math.random() < 0.3 && this.nodes.length > 0) {
      const focal = this.getNode(this.selectedNodeId);
      if (focal) {
        this.spawnParticles(focal.x, focal.y, focal.color, 1);
      }
      this.opportunityNodeIds.forEach(id => {
        const opp = this.getNode(id);
        if (opp && Math.random() < 0.2) {
          this.spawnParticles(opp.x, opp.y, '#f59e0b', 1);
        }
      });
    }

    // Smooth viewport interpolation
    const lerpFactor = 0.1;
    this.viewport.x += (this.targetViewport.x - this.viewport.x) * lerpFactor;
    this.viewport.y += (this.targetViewport.y - this.viewport.y) * lerpFactor;
    this.viewport.scale += (this.targetViewport.scale - this.viewport.scale) * lerpFactor;

    // Advance ring phase for pulsing animation
    this.ringPhase += 0.04;
  }

  // ─── Render ───────────────────────────────────────────────────────────────

  render() {
    const ctx = this.ctx;
    ctx.clearRect(0, 0, this.width, this.height);

    ctx.save();
    ctx.translate(this.viewport.x, this.viewport.y);
    ctx.scale(this.viewport.scale, this.viewport.scale);

    // ── Concentric Orbit Rings (D0-D3) ──
    if (this.layoutMode === 'orbit') {
      const centerX = this.width / 2;
      const centerY = this.height / 2;
      const rings = [
        { r: 40, label: 'D0: Focal Point (Kärna)', color: 'rgba(6, 182, 212, 0.35)' },
        { r: 140, label: 'D1: Direct Relations (Roller & Verifikat)', color: 'rgba(16, 185, 129, 0.3)' },
        { r: 270, label: 'D2: Subsystem & Team (Observationer & Diagnoser)', color: 'rgba(245, 158, 11, 0.25)' },
        { r: 410, label: 'D3: Macro / Meta-Ecosystem (Lärdomar & Kunskap)', color: 'rgba(139, 92, 246, 0.2)' },
      ];
      rings.forEach(ring => {
        ctx.save();
        ctx.beginPath();
        ctx.arc(centerX, centerY, ring.r, 0, Math.PI * 2);
        ctx.strokeStyle = ring.color;
        ctx.lineWidth = 1.2 / this.viewport.scale;
        ctx.setLineDash([5 / this.viewport.scale, 7 / this.viewport.scale]);
        ctx.stroke();

        ctx.font = `600 ${9 / this.viewport.scale}px "Inter", sans-serif`;
        ctx.fillStyle = ring.color.replace('0.', '0.85');
        ctx.textAlign = 'left';
        ctx.fillText(ring.label, centerX + 10 / this.viewport.scale, centerY - ring.r + 12 / this.viewport.scale);
        ctx.restore();
      });
    }

    // ── Expanding Ripple Waves ──
    this.rippleWaves.forEach(w => {
      ctx.save();
      ctx.beginPath();
      ctx.arc(w.x, w.y, w.r, 0, Math.PI * 2);
      ctx.strokeStyle = `rgba(6, 182, 212, ${w.alpha})`;
      ctx.lineWidth = 2.2 / this.viewport.scale;
      ctx.stroke();
      ctx.restore();
      w.r += 1.8;
      w.alpha -= 0.025;
    });
    this.rippleWaves = this.rippleWaves.filter(w => w.alpha > 0);

    // ── Sparkling Particles ──
    this.particles.forEach(p => {
      ctx.save();
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.size / this.viewport.scale, 0, Math.PI * 2);
      ctx.fillStyle = p.color;
      ctx.globalAlpha = p.alpha;
      ctx.fill();
      ctx.restore();
      p.x += p.vx;
      p.y += p.vy;
      p.life -= 0.028;
      p.alpha = Math.max(0, p.life);
    });
    this.particles = this.particles.filter(p => p.life > 0);

    // ── Draw Causal Traced Path Beam ──
    if (this.tracedPathLinks && this.tracedPathLinks.size > 0) {
      this.pathTracePhase = (this.pathTracePhase || 0) + 0.05;
      this.tracedPathLinks.forEach(linkIdx => {
        const l = this.links[linkIdx];
        if (!l) return;
        const s = this.getNode(l.source);
        const t = this.getNode(l.target);
        if (!s || !t) return;

        ctx.save();
        ctx.beginPath();
        ctx.moveTo(s.x, s.y);
        ctx.lineTo(t.x, t.y);
        ctx.strokeStyle = 'rgba(16, 185, 129, 0.85)';
        ctx.lineWidth = 3.5 / this.viewport.scale;
        ctx.shadowColor = '#10b981';
        ctx.shadowBlur = 10;
        ctx.stroke();

        ctx.setLineDash([8 / this.viewport.scale, 6 / this.viewport.scale]);
        ctx.lineDashOffset = -(this.pathTracePhase * 16);
        ctx.strokeStyle = '#ffffff';
        ctx.lineWidth = 2 / this.viewport.scale;
        ctx.stroke();
        ctx.restore();
      });
    }

    // Draw Links
    this.links.forEach(l => {
      const s = this.getNode(l.source);
      const t = this.getNode(l.target);
      if (!s || !t) return;
      const isHighlight = s.id === this.selectedNodeId || t.id === this.selectedNodeId;

      ctx.beginPath();
      ctx.moveTo(s.x, s.y);
      ctx.lineTo(t.x, t.y);
      ctx.strokeStyle = isHighlight ? 'rgba(6,182,212,0.5)' : 'rgba(255,255,255,0.07)';
      ctx.lineWidth = isHighlight ? 1.5 / this.viewport.scale : 1 / this.viewport.scale;
      ctx.stroke();

      if (l.relation && (isHighlight || this.viewport.scale >= 0.75)) {
        const midX = (s.x + t.x) / 2;
        const midY = (s.y + t.y) / 2;
        ctx.font = `${(isHighlight ? 9 : 8) / this.viewport.scale}px "JetBrains Mono", monospace`;
        const textW = ctx.measureText(l.relation).width;
        const padX = 3 / this.viewport.scale;
        const bH = 11 / this.viewport.scale;
        
        ctx.fillStyle = isHighlight ? 'rgba(15, 23, 42, 0.88)' : 'rgba(15, 23, 42, 0.65)';
        ctx.beginPath();
        if (ctx.roundRect) ctx.roundRect(midX - textW / 2 - padX, midY - bH / 2, textW + padX * 2, bH, 2 / this.viewport.scale);
        else ctx.rect(midX - textW / 2 - padX, midY - bH / 2, textW + padX * 2, bH);
        ctx.fill();

        ctx.fillStyle = isHighlight ? '#38bdf8' : 'rgba(148,163,184,0.75)';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(l.relation, midX, midY);
      }
    });

    // ── Draw Real-time Cognitive Trajectory Path ──
    if (this.trajectoryNodes && this.trajectoryNodes.length > 0) {
      const isAmbient = !this.trajectoryActive;
      const baseAlpha = isAmbient ? 0.35 : 1.0;

      // Collect friction node IDs for warning markers
      const frictionNodeIds = new Set();
      const frictionSeverities = {};
      if (this.trajectoryFrictions) {
        this.trajectoryFrictions.forEach(f => {
          // Map frictions to trajectory node domains
          this.trajectoryNodes.forEach(tn => {
            if (tn.domain === f.domain || f.lead_time_steps <= 1) {
              frictionNodeIds.add(tn.node_id);
              frictionSeverities[tn.node_id] = f.severity || 'medium';
            }
          });
        });
      }

      let prev = this.getNode(this.selectedNodeId) || this.nodes[0];
      this.trajectoryNodes.forEach((tNode, idx) => {
        const matchNode = this.nodes.find(n => 
          n.id === tNode.node_id || 
          (n.name && tNode.title && n.name.toLowerCase().includes(tNode.title.toLowerCase().substring(0, 8)))
        );
        if (matchNode && prev && prev !== matchNode) {
          ctx.save();
          ctx.globalAlpha = baseAlpha;

          // ── Animated dashed connector arc ──
          ctx.setLineDash([7 / this.viewport.scale, 5 / this.viewport.scale]);
          ctx.lineDashOffset = -(this.ringPhase * 14);
          ctx.beginPath();

          // Curved arc instead of straight line for visual distinction
          const cpX = (prev.x + matchNode.x) / 2 + (matchNode.y - prev.y) * 0.15;
          const cpY = (prev.y + matchNode.y) / 2 - (matchNode.x - prev.x) * 0.15;
          ctx.moveTo(prev.x, prev.y);
          ctx.quadraticCurveTo(cpX, cpY, matchNode.x, matchNode.y);

          const isFriction = frictionNodeIds.has(tNode.node_id);
          ctx.strokeStyle = isFriction ? '#f43f5e' : '#10b981';
          ctx.lineWidth = 2.4 / this.viewport.scale;
          ctx.stroke();

          // ── Confidence Halo — radius proportional to transition_probability ──
          const prob = tNode.transition_probability || 0.65;
          const haloRadius = matchNode.radius + 8 + prob * 12 + Math.sin(this.ringPhase * 2.5) * 3;
          const haloAlpha = 0.15 + prob * 0.35;
          
          ctx.beginPath();
          ctx.arc(matchNode.x, matchNode.y, haloRadius, 0, Math.PI * 2);
          if (isFriction) {
            const severity = frictionSeverities[tNode.node_id];
            const sColor = severity === 'critical' ? '244,63,94' : severity === 'high' ? '251,146,60' : '234,179,8';
            ctx.strokeStyle = `rgba(${sColor},${haloAlpha})`;
            ctx.fillStyle = `rgba(${sColor},${haloAlpha * 0.15})`;
            ctx.fill();
          } else {
            ctx.strokeStyle = `rgba(16, 185, 129, ${haloAlpha})`;
          }
          ctx.lineWidth = 1.8 / this.viewport.scale;
          ctx.stroke();

          // ── Friction Warning Diamond ──
          if (isFriction) {
            const dSize = 7 / this.viewport.scale;
            const dx = matchNode.x + matchNode.radius + 6 / this.viewport.scale;
            const dy = matchNode.y - matchNode.radius - 6 / this.viewport.scale;
            const pulse = Math.sin(this.ringPhase * 4) * 0.3 + 0.7;
            ctx.setLineDash([]);
            ctx.beginPath();
            ctx.moveTo(dx, dy - dSize);
            ctx.lineTo(dx + dSize, dy);
            ctx.lineTo(dx, dy + dSize);
            ctx.lineTo(dx - dSize, dy);
            ctx.closePath();
            ctx.fillStyle = `rgba(244,63,94,${pulse})`;
            ctx.fill();
            ctx.strokeStyle = 'rgba(255,255,255,0.8)';
            ctx.lineWidth = 1 / this.viewport.scale;
            ctx.stroke();

            // ⚠ icon
            ctx.font = `${8 / this.viewport.scale}px sans-serif`;
            ctx.fillStyle = '#fff';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillText('⚠', dx, dy);
          }

          // ── Step Offset Badge ──
          const midX = cpX;
          const midY = cpY;
          ctx.setLineDash([]);
          const probTxt = Math.round(prob * 100);
          const badgeText = `+${idx + 1} (${probTxt}%)`;

          // Badge background pill
          ctx.font = `bold ${9 / this.viewport.scale}px "JetBrains Mono", monospace`;
          const tw = ctx.measureText(badgeText).width;
          const px = 4 / this.viewport.scale;
          const py = 3 / this.viewport.scale;

          ctx.beginPath();
          const bx = midX - tw / 2 - px;
          const by = midY - 7 / this.viewport.scale - py;
          const bw = tw + px * 2;
          const bh = 12 / this.viewport.scale + py;
          if (ctx.roundRect) ctx.roundRect(bx, by, bw, bh, 4 / this.viewport.scale);
          else { ctx.rect(bx, by, bw, bh); }
          ctx.fillStyle = isFriction ? 'rgba(244,63,94,0.85)' : 'rgba(16,185,129,0.85)';
          ctx.fill();

          ctx.fillStyle = '#fff';
          ctx.textAlign = 'center';
          ctx.textBaseline = 'middle';
          ctx.fillText(badgeText, midX, midY - 2 / this.viewport.scale);

          ctx.restore();
          prev = matchNode;
        }
      });
    }

    // Draw Nodes
    this.nodes.forEach(n => {
      const matchesCategory = !this.activeCategory || this.activeCategory === 'ALL' ||
        (this.activeCategory === 'PEOPLE' && ['team_member', 'role', 'person'].includes(n.type)) ||
        (this.activeCategory === 'PLANS' && ['plan', 'step', 'action', 'task', 'goal'].includes(n.type)) ||
        (this.activeCategory === 'LEARNING' && ['learning', 'pattern', 'optimization', 'friction', 'skill'].includes(n.type)) ||
        (this.activeCategory === 'FINANCE' && ['financial_entry', 'invoice', 'voucher', 'batch', 'account', 'cost'].includes(n.type));

      const matchesDomain = this.filterDomain === 'ALL' || n.domain === this.filterDomain;
      const matchesQuery = !this.filterQuery || 
        (n.name && n.name.toLowerCase().includes(this.filterQuery)) ||
        (n.id && n.id.toLowerCase().includes(this.filterQuery)) ||
        (n.type && n.type.toLowerCase().includes(this.filterQuery));
      const isDimmed = !matchesCategory || !matchesDomain || !matchesQuery;

      ctx.save();
      if (isDimmed) ctx.globalAlpha = 0.18;

      const isSelected = n.id === this.selectedNodeId;
      const isHovered = n.id === this.hoveredNodeId;
      const hasOpportunity = this.opportunityNodeIds.has(n.id);
      const isTraced = this.tracedPathNodes && this.tracedPathNodes.has(n.id);

      // ── Traced Causal Path Halo (Emerald) ──
      if (isTraced) {
        ctx.beginPath();
        ctx.arc(n.x, n.y, n.radius + 8, 0, Math.PI * 2);
        ctx.fillStyle = 'rgba(16, 185, 129, 0.35)';
        ctx.fill();
        ctx.strokeStyle = '#10b981';
        ctx.lineWidth = 2 / this.viewport.scale;
        ctx.stroke();
      }

      // ── Opportunity Ring (pulsing amber) ──
      if (hasOpportunity) {
        const pulse = Math.sin(this.ringPhase) * 0.5 + 0.5; // 0..1
        const ringRadius = n.radius + 10 + pulse * 8;
        const alpha = 0.15 + pulse * 0.35;
        const grad = ctx.createRadialGradient(n.x, n.y, n.radius, n.x, n.y, ringRadius + 6);
        grad.addColorStop(0, `rgba(245,158,11,${alpha})`);
        grad.addColorStop(1, 'rgba(245,158,11,0)');
        ctx.beginPath();
        ctx.arc(n.x, n.y, ringRadius + 6, 0, Math.PI * 2);
        ctx.fillStyle = grad;
        ctx.fill();

        // Solid ring border
        ctx.beginPath();
        ctx.arc(n.x, n.y, ringRadius, 0, Math.PI * 2);
        ctx.strokeStyle = `rgba(245,158,11,${0.4 + pulse * 0.4})`;
        ctx.lineWidth = 1.5 / this.viewport.scale;
        ctx.stroke();
      }

      // ── Selection / Hover Aura ──
      if (isSelected || isHovered) {
        ctx.beginPath();
        ctx.arc(n.x, n.y, n.radius + (isSelected ? 8 : 4), 0, Math.PI * 2);
        ctx.fillStyle = isSelected ? 'rgba(6,182,212,0.25)' : 'rgba(255,255,255,0.12)';
        ctx.fill();
      }

      // ── Node Core ──
      ctx.beginPath();
      ctx.arc(n.x, n.y, n.radius, 0, Math.PI * 2);
      ctx.fillStyle = n.color;
      ctx.fill();
      ctx.strokeStyle = isSelected ? '#ffffff' : 'rgba(0,0,0,0.4)';
      ctx.lineWidth = (isSelected ? 2.5 : 1.5) / this.viewport.scale;
      ctx.stroke();

      // ── Entity Glyph Inside Node ──
      const glyph = this.typeGlyphs[n.type];
      if (glyph && n.radius >= 10) {
        ctx.save();
        const glyphSize = Math.max(9, n.radius * 0.95) / this.viewport.scale;
        ctx.font = `${glyphSize}px "Segoe UI Emoji", "Apple Color Emoji", sans-serif`;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(glyph, n.x, n.y);
        ctx.restore();
      }

      // ── Label ──
      const fontSize = (isSelected ? 11 : 10) / this.viewport.scale;
      ctx.font = `${isSelected ? '600 ' : ''}${fontSize}px "Inter", sans-serif`;
      const nameStr = n.name || n.label || n.id || '';
      const label = nameStr.length > 18 ? nameStr.substring(0, 16) + '..' : nameStr;
      ctx.fillText(label, n.x, n.y + n.radius + 12 / this.viewport.scale);

      // ── Opportunity amount badge ──
      if (hasOpportunity && n.financial_impact) {
        const badgeY = n.y - n.radius - 6 / this.viewport.scale;
        const amt = `+${Math.round(n.financial_impact / 1000)}k`;
        const bFontSize = 8 / this.viewport.scale;
        ctx.font = `700 ${bFontSize}px "JetBrains Mono"`;
        const tw = ctx.measureText(amt).width;
        ctx.fillStyle = 'rgba(245,158,11,0.9)';
        ctx.beginPath();
        ctx.roundRect(n.x - tw / 2 - 3 / this.viewport.scale, badgeY - bFontSize, tw + 6 / this.viewport.scale, bFontSize + 3 / this.viewport.scale, 3 / this.viewport.scale);
        ctx.fill();
        ctx.fillStyle = '#0f172a';
        ctx.fillText(amt, n.x, badgeY - 1 / this.viewport.scale);
      }

      ctx.restore();
    });

    // ── Tooltip ──
    if (this.hoveredNodeId) {
      const n = this.getNode(this.hoveredNodeId);
      if (n) {
        const text = n.details ? `${n.name} • ${n.details}` : n.name;
        ctx.font = `10px "Inter", sans-serif`;
        const textWidth = ctx.measureText(text).width;
        const boxX = n.x - textWidth / 2;
        const boxY = n.y - n.radius - 28 / this.viewport.scale;

        ctx.fillStyle = 'rgba(7,10,18,0.92)';
        ctx.strokeStyle = 'rgba(6,182,212,0.55)';
        ctx.lineWidth = 1 / this.viewport.scale;
        ctx.beginPath();
        ctx.roundRect(boxX - 8 / this.viewport.scale, boxY, textWidth + 16 / this.viewport.scale, 18 / this.viewport.scale, 4 / this.viewport.scale);
        ctx.fill();
        ctx.stroke();

        ctx.fillStyle = '#f8fafc';
        ctx.textAlign = 'center';
        ctx.fillText(text, n.x, boxY + 12 / this.viewport.scale);
      }
    }

    ctx.restore();

    // ── Minimap ──
    this._renderMinimap();
  }

  _renderMinimap() {
    if (!this.minimapCtx || this.nodes.length === 0) return;
    const mm = this.minimapCtx;
    const mw = this.minimapW || 140;
    const mh = this.minimapH || 90;

    mm.clearRect(0, 0, mw, mh);

    // Find bounds of all nodes
    let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
    this.nodes.forEach(n => {
      minX = Math.min(minX, n.x); minY = Math.min(minY, n.y);
      maxX = Math.max(maxX, n.x); maxY = Math.max(maxY, n.y);
    });
    const span = Math.max(maxX - minX, maxY - minY, 200);
    const padding = 12;
    const scale = (Math.min(mw, mh) - padding * 2) / span;

    const toMm = (wx, wy) => ({
      x: padding + (wx - minX) * scale,
      y: padding + (wy - minY) * scale
    });

    // Draw links
    mm.strokeStyle = 'rgba(255,255,255,0.08)';
    mm.lineWidth = 0.5;
    this.links.forEach(l => {
      const s = this.getNode(l.source);
      const t = this.getNode(l.target);
      if (!s || !t) return;
      const sp = toMm(s.x, s.y), tp = toMm(t.x, t.y);
      mm.beginPath();
      mm.moveTo(sp.x, sp.y);
      mm.lineTo(tp.x, tp.y);
      mm.stroke();
    });

    // Draw nodes
    this.nodes.forEach(n => {
      const p = toMm(n.x, n.y);
      const r = Math.max(2, n.radius * scale * 0.6);
      mm.beginPath();
      mm.arc(p.x, p.y, r, 0, Math.PI * 2);
      mm.fillStyle = n.id === this.selectedNodeId ? '#06b6d4' : (n.color + 'bb');
      mm.fill();
    });

    // Viewport rectangle indicator
    const vpX = (-this.viewport.x / this.viewport.scale - minX) * scale + padding;
    const vpY = (-this.viewport.y / this.viewport.scale - minY) * scale + padding;
    const vpW = (this.width / this.viewport.scale) * scale;
    const vpH = (this.height / this.viewport.scale) * scale;

    mm.strokeStyle = 'rgba(6,182,212,0.6)';
    mm.lineWidth = 1;
    mm.strokeRect(vpX, vpY, vpW, vpH);
  }

  animate() {
    this.simulate();
    this.render();
    requestAnimationFrame(() => this.animate());
  }
}

window.SpatialCanvas = SpatialCanvas;
