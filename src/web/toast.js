/**
 * BART Toast Notification System
 * Stacked, auto-dismissing toasts with severity levels and smooth entrance/exit animations.
 */

class ToastManager {
  constructor() {
    this.container = null;
    this.toasts = [];
    this._ensureContainer();
  }

  _ensureContainer() {
    let c = document.getElementById('toastContainer');
    if (!c) {
      c = document.createElement('div');
      c.id = 'toastContainer';
      c.style.cssText = `
        position: fixed;
        bottom: 24px;
        right: 24px;
        z-index: 9999;
        display: flex;
        flex-direction: column-reverse;
        gap: 10px;
        pointer-events: none;
      `;
      document.body.appendChild(c);
    }
    this.container = c;
  }

  /**
   * Show a toast notification.
   * @param {string} message - The message to display.
   * @param {'success'|'warning'|'info'|'error'} type - Severity level.
   * @param {number} duration - Auto-dismiss duration in ms (default 4500).
   */
  show(message, type = 'info', duration = 4500) {
    const id = `toast-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;

    const colors = {
      success: { bg: 'rgba(5,150,105,0.95)', border: 'rgba(16,185,129,0.5)', icon: '✓', iconColor: '#10b981' },
      warning: { bg: 'rgba(120,53,15,0.95)', border: 'rgba(245,158,11,0.5)', icon: '⚠', iconColor: '#f59e0b' },
      error:   { bg: 'rgba(127,29,29,0.95)', border: 'rgba(239,68,68,0.5)',  icon: '✕', iconColor: '#f87171' },
      info:    { bg: 'rgba(7,53,84,0.95)',   border: 'rgba(6,182,212,0.5)',  icon: '💡', iconColor: '#06b6d4' }
    };
    const c = colors[type] || colors.info;

    const el = document.createElement('div');
    el.id = id;
    el.setAttribute('role', 'alert');
    el.style.cssText = `
      display: flex;
      align-items: flex-start;
      gap: 10px;
      padding: 12px 16px;
      min-width: 280px;
      max-width: 380px;
      background: ${c.bg};
      border: 1px solid ${c.border};
      border-radius: 10px;
      backdrop-filter: blur(16px);
      box-shadow: 0 8px 32px rgba(0,0,0,0.5), 0 0 0 1px rgba(255,255,255,0.04);
      font-family: 'Inter', sans-serif;
      font-size: 12.5px;
      color: #f1f5f9;
      line-height: 1.4;
      pointer-events: all;
      cursor: pointer;
      transform: translateX(120%);
      opacity: 0;
      transition: transform 0.32s cubic-bezier(0.34,1.56,0.64,1), opacity 0.25s ease;
    `;

    el.innerHTML = `
      <span style="font-size:15px;color:${c.iconColor};flex-shrink:0;margin-top:1px;">${c.icon}</span>
      <span style="flex:1;">${message}</span>
      <span style="font-size:14px;color:rgba(148,163,184,0.6);flex-shrink:0;cursor:pointer;margin-top:-1px;" class="toast-close">×</span>
    `;

    el.querySelector('.toast-close').addEventListener('click', (e) => {
      e.stopPropagation();
      this._dismiss(id);
    });
    el.addEventListener('click', () => this._dismiss(id));

    this.container.appendChild(el);
    this.toasts.push({ id, el, timer: null });

    // Trigger entrance animation
    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        el.style.transform = 'translateX(0)';
        el.style.opacity = '1';
      });
    });

    if (duration > 0) {
      const entry = this.toasts.find(t => t.id === id);
      if (entry) {
        entry.timer = setTimeout(() => this._dismiss(id), duration);
      }
    }

    return id;
  }

  _dismiss(id) {
    const idx = this.toasts.findIndex(t => t.id === id);
    if (idx === -1) return;

    const { el, timer } = this.toasts[idx];
    if (timer) clearTimeout(timer);

    el.style.transform = 'translateX(120%)';
    el.style.opacity = '0';
    setTimeout(() => {
      el.remove();
    }, 300);

    this.toasts.splice(idx, 1);
  }

  success(msg, duration) { return this.show(msg, 'success', duration); }
  warning(msg, duration) { return this.show(msg, 'warning', duration); }
  error(msg, duration)   { return this.show(msg, 'error', duration); }
  info(msg, duration)    { return this.show(msg, 'info', duration); }
}

window.Toast = new ToastManager();
