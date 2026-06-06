/* WECHIP ROI — per-lead link config: apply locked values, wire change/print events.
 * Runs before the main calculator IIFE so window.WECHIP_LINK_CONFIG is available
 * to the closure-scoped constants there. */
(function () {
  'use strict';

  var cfgEl = document.getElementById('wechip-link-config');
  var cfg = {};
  try { cfg = JSON.parse((cfgEl && cfgEl.textContent) || '{}') || {}; } catch (e) { cfg = {}; }
  window.WECHIP_LINK_CONFIG = cfg;

  // Phase-card labels reflect who pays OPEX in the growth phase.
  function updatePhaseLabels() {
    var c = window.WECHIP_LINK_CONFIG || {};
    var fromStart = c.sharingFromStart === true;
    var p1 = document.getElementById('phaseOpex1');
    if (p1) p1.textContent = (c.opexByWechip === true || fromStart) ? 'Couverts par WECHIP' : 'À charge du client';
    var share = Number.isFinite(c.wechipSharePct) ? c.wechipSharePct : 60;
    var sl = document.getElementById('phaseShareLabel');
    if (sl) sl.textContent = String(share) + ' % WECHIP';
    var rev1 = document.getElementById('phaseRev1');
    if (rev1) rev1.textContent = fromStart ? (String(share) + ' % WECHIP') : '100 % client';
  }
  window.__wechipUpdatePhaseLabels = updatePhaseLabels;
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', updatePhaseLabels);
  } else {
    updatePhaseLabels();
  }

  // In admin mode, the admin-panel.js owns all UI changes; this file stays out of the way
  // so the calculator behaves like a blank canvas the admin can tweak freely.
  if (cfg.__admin) return;

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

  // ── Hide buttons that don't belong on a per-lead customer link ──
  // "Réinitialiser" would wipe admin-supplied values, and "Partager" leaks
  // a /?mod=...&rev=... URL that bypasses this trackable link.
  function hideCustomerButtons() {
    ['btnReset', 'btnShare'].forEach(function (id) {
      var b = document.getElementById(id);
      if (b) b.style.display = 'none';
    });
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', hideCustomerButtons);
  } else {
    hideCustomerButtons();
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

  // ── Forced model (Filaire / Solaire) ──
  // When admin sets a model lock, click the matching button so the calculator's
  // own setModel() runs (state stays consistent), then disable both toggle buttons.
  // Deferred until DOMContentLoaded because the calculator IIFE binds its click
  // handlers below this script and must run before our programmatic .click().
  if (cfg.model === 'filaire' || cfg.model === 'solaire') {
    var forcedId = cfg.model === 'solaire' ? 'btnSolaire' : 'btnFilaire';
    var otherId  = cfg.model === 'solaire' ? 'btnFilaire' : 'btnSolaire';

    function applyForcedModel() {
      var forcedBtn = $(forcedId);
      var otherBtn  = $(otherId);

      function disableScenarioBtn(btn) {
        if (!btn) return;
        btn.disabled = true;
        btn.setAttribute('aria-disabled', 'true');
        btn.style.opacity = '0.6';
        btn.style.cursor = 'not-allowed';
      }

      if (forcedBtn && !forcedBtn.classList.contains('active')) {
        try { forcedBtn.click(); } catch (e) {}
      }
      disableScenarioBtn(forcedBtn);
      disableScenarioBtn(otherBtn);

      var scenarioField = forcedBtn ? forcedBtn.closest('.field') : null;
      var scenarioLabel = scenarioField ? scenarioField.querySelector('label') : null;
      if (scenarioLabel && !scenarioLabel.querySelector('.wc-lock')) {
        var icon = document.createElement('span');
        icon.className = 'wc-lock';
        icon.title = 'Modèle verrouillé par WECHIP';
        icon.setAttribute('aria-label', 'verrouillé');
        icon.style.cssText = 'display:inline-block;margin-left:6px;font-size:11px;color:var(--wc-fg-3,#888)';
        icon.textContent = '🔒';
        scenarioLabel.appendChild(icon);
      }
    }

    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', applyForcedModel);
    } else {
      applyForcedModel();
    }
  }

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
