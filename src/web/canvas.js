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
      'Default': '#94a3b8'
    };

    // Opportunity ring state (animated pulsing)
    this.opportunityNodeIds = new Set();
    this.ringPhase = 0;

    this.dragNode = null;
    this.isDragMove = false;
    this.mouse = { x: 0, y: 0, isDown: false };

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
    const centerX = this.width / 2;
    const centerY = this.height / 2;
    const damping = 0.85;

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

      if (isHighlight && l.relation) {
        const midX = (s.x + t.x) / 2;
        const midY = (s.y + t.y) / 2;
        ctx.font = `${8 / this.viewport.scale}px "JetBrains Mono"`;
        ctx.fillStyle = 'rgba(148,163,184,0.7)';
        ctx.textAlign = 'center';
        ctx.fillText(l.relation, midX, midY - 3 / this.viewport.scale);
      }
    });

    // Draw Nodes
    this.nodes.forEach(n => {
      const isSelected = n.id === this.selectedNodeId;
      const isHovered = n.id === this.hoveredNodeId;
      const hasOpportunity = this.opportunityNodeIds.has(n.id);

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
