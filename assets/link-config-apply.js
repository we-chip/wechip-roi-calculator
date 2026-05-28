/* WECHIP ROI — per-lead link config: apply locked values, wire change/print events.
 * Runs before the main calculator IIFE so window.WECHIP_LINK_CONFIG is available
 * to the closure-scoped constants there. */
(function () {
  'use strict';

  var cfgEl = document.getElementById('wechip-link-config');
  var cfg = {};
  try { cfg = JSON.parse((cfgEl && cfgEl.textContent) || '{}') || {}; } catch (e) { cfg = {}; }
  window.WECHIP_LINK_CONFIG = cfg;

  var hasConfig = cfg && (cfg.display_name || Object.keys(cfg).some(function (k) { return k !== 'display_name'; }));
  if (!hasConfig) return;

  // Derive slug from URL: /c/<slug>
  var m = window.location.pathname.match(/^\/c\/([a-z0-9][a-z0-9-]{1,59})/i);
  var slug = m ? m[1] : null;

  function $(id) { return document.getElementById(id); }

  function setVal(id, v) {
    var el = $(id);
    if (!el) return;
    el.value = String(v);
    try { el.dispatchEvent(new Event('input', { bubbles: true })); } catch (e) {}
  }

  function lock(id) {
    var el = $(id);
    if (!el) return;
    el.setAttribute('aria-disabled', 'true');
    el.setAttribute('readonly', 'readonly');
    if (el.tagName === 'INPUT' && el.type !== 'hidden') {
      el.disabled = true;
      el.style.opacity = '0.6';
      el.style.cursor = 'not-allowed';
      var label = el.closest('.field') ? el.closest('.field').querySelector('label') : null;
      if (label && !label.querySelector('.wc-lock')) {
        var icon = document.createElement('span');
        icon.className = 'wc-lock';
        icon.title = 'Valeur verrouillée par WECHIP';
        icon.setAttribute('aria-label', 'verrouillé');
        icon.style.cssText = 'display:inline-block;margin-left:6px;font-size:11px;color:var(--wc-fg-3,#888)';
        icon.textContent = '🔒';
        label.appendChild(icon);
      }
    }
  }

  // ── Display name banner ──
  if (cfg.display_name) {
    var wrap = document.querySelector('.wrap');
    if (wrap) {
      var banner = document.createElement('div');
      banner.id = 'wechip-link-banner';
      banner.textContent = 'Proposition personnalisée — ' + cfg.display_name;
      banner.style.cssText =
        'margin:0 0 16px 0;padding:10px 14px;border-radius:8px;' +
        'background:var(--wc-ink-100,#f3f4f6);border:1px solid var(--wc-border-subtle,#e5e7eb);' +
        'font-weight:600;font-size:13px;color:var(--wc-fg-1,#111)';
      wrap.insertBefore(banner, wrap.firstChild);
      try { document.title = document.title + ' — ' + cfg.display_name; } catch (e) {}
    }
  }

  // ── Preset values ──
  if (Number.isFinite(cfg.revPerColDay)) setVal('revPerColDay', cfg.revPerColDay);
  if (Number.isFinite(cfg.discountPct))  setVal('discountPct',  cfg.discountPct);
  if (Number.isFinite(cfg.columns)) {
    var modules = Math.max(2, Math.min(8, Math.round(cfg.columns / 2)));
    setVal('modulesInput', modules);
  }

  // ── Lock controls ──
  // revPerColDay is hidden but admin-controlled — mark aria for AT users.
  lock('revPerColDay');
  // Per-module pricing has no DOM input; the IIFE reads cfg.pricePerModule directly.

  // ── Event reporting (best-effort) ──
  if (!slug) return;

  function send(type, payload) {
    try {
      fetch('/c/' + slug + '/event', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ type: type, payload: payload || {} }),
        keepalive: true
      }).catch(function () {});
    } catch (e) {}
  }

  var debounceTimers = {};
  function debouncedChange(field, value) {
    clearTimeout(debounceTimers[field]);
    debounceTimers[field] = setTimeout(function () {
      send('change', { field: field, value: value });
    }, 400);
  }

  function wireField(id) {
    var el = $(id);
    if (!el) return;
    el.addEventListener('change', function () { debouncedChange(id, el.value); });
    el.addEventListener('input',  function () { debouncedChange(id, el.value); });
  }

  // Customer-interactive fields tracked for analytics:
  wireField('modulesInput');
  wireField('discountPct');

  ['btnFilaire', 'btnSolaire'].forEach(function (id) {
    var el = $(id);
    if (el) el.addEventListener('click', function () {
      send('change', { field: 'model', value: id === 'btnSolaire' ? 'solaire' : 'filaire' });
    });
  });

  window.addEventListener('beforeprint', function () { send('print', {}); });
})();
