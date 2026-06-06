/* WECHIP ROI — admin in-calculator panel.
 * Activates only when the injected config has __admin === true.
 * Adds a top banner (slug + display name + save/revoke + share URL)
 * and admin-only extra inputs (pricePerModule, wechipSharePct, opex JSON). */
(function () {
  'use strict';

  var cfg = window.WECHIP_LINK_CONFIG || {};
  if (!cfg.__admin) return;

  var editingSlug = cfg.__editing_slug || null;

  function $(id) { return document.getElementById(id); }
  function el(tag, attrs, children) {
    var n = document.createElement(tag);
    if (attrs) Object.keys(attrs).forEach(function (k) {
      if (k === 'style') n.setAttribute('style', attrs[k]);
      else if (k === 'html') n.innerHTML = attrs[k];
      else n.setAttribute(k, attrs[k]);
    });
    (children || []).forEach(function (c) {
      n.appendChild(typeof c === 'string' ? document.createTextNode(c) : c);
    });
    return n;
  }

  // ── Banner / top panel ─────────────────────────────────────────────
  var wrap = document.querySelector('.wrap');
  if (!wrap) return;

  var panel = el('div', { id: 'wechip-admin-panel', style:
    'margin:0 0 16px 0;padding:14px 16px;border-radius:10px;' +
    'background:#fff7ed;border:1px solid #fed7aa;color:#7c2d12;' +
    'font-family:-apple-system,BlinkMacSystemFont,sans-serif;font-size:13px' });

  var title = el('div', { style: 'font-weight:700;margin-bottom:8px;font-size:14px' });
  title.textContent = editingSlug ? ('Édition du lien : /c/' + editingSlug) : 'Nouveau lien client';
  panel.appendChild(title);

  var row1 = el('div', { style: 'display:flex;gap:10px;flex-wrap:wrap;margin-bottom:8px' });
  var nameWrap = el('label', { style: 'flex:2;min-width:200px;font-size:11px;font-weight:600' }, ['Nom affiché']);
  var nameInput = el('input', { type: 'text', id: 'admin_display_name',
    style: 'display:block;width:100%;padding:6px 8px;border:1px solid #fdba74;border-radius:6px;font-size:13px;margin-top:2px' });
  nameInput.value = cfg.display_name || '';
  nameWrap.appendChild(nameInput);

  var slugWrap = el('label', { style: 'flex:1;min-width:140px;font-size:11px;font-weight:600' }, ['Slug (URL)']);
  var slugInput = el('input', { type: 'text', id: 'admin_slug', pattern: '[a-z0-9][a-z0-9-]{1,59}',
    placeholder: 'ex: acme-2026',
    style: 'display:block;width:100%;padding:6px 8px;border:1px solid #fdba74;border-radius:6px;font-size:13px;margin-top:2px;font-family:ui-monospace,Menlo,monospace' });
  if (editingSlug) { slugInput.value = editingSlug; slugInput.readOnly = true; slugInput.style.background = '#fef3c7'; }
  slugWrap.appendChild(slugInput);

  row1.appendChild(nameWrap);
  row1.appendChild(slugWrap);
  panel.appendChild(row1);

  // Model lock select: forces customer to a specific scenario, or 'auto' = free choice.
  var modelRow = el('div', { style: 'margin-bottom:8px' });
  var modelLabel = el('label', { for: 'admin_model',
    style: 'font-size:11px;font-weight:600;display:block' }, ['Modèle imposé au client']);
  var modelSelect = el('select', { id: 'admin_model',
    style: 'padding:6px 8px;border:1px solid #fdba74;border-radius:6px;font-size:13px;margin-top:2px;background:#fff' });
  [['auto', 'Auto — le client choisit'],
   ['filaire', 'Filaire — verrouillé'],
   ['solaire', 'Solaire — verrouillé']].forEach(function (pair) {
    var o = el('option', { value: pair[0] }, [pair[1]]);
    if ((cfg.model || 'auto') === pair[0]) o.setAttribute('selected', 'selected');
    modelSelect.appendChild(o);
  });
  modelRow.appendChild(modelLabel);
  modelRow.appendChild(modelSelect);
  panel.appendChild(modelRow);

  var btnRow = el('div', { style: 'display:flex;gap:8px;align-items:center;flex-wrap:wrap' });
  var btnSave = el('button', { type: 'button', id: 'admin_btn_save',
    style: 'padding:8px 16px;background:#ea580c;color:#fff;border:none;border-radius:6px;cursor:pointer;font-weight:600;font-size:13px' });
  btnSave.textContent = editingSlug ? 'Mettre à jour' : 'Créer le lien';
  btnRow.appendChild(btnSave);

  if (editingSlug) {
    var btnRevoke = el('button', { type: 'button', id: 'admin_btn_revoke',
      style: 'padding:8px 14px;background:#fff;color:#991b1b;border:1px solid #fecaca;border-radius:6px;cursor:pointer;font-size:13px' });
    btnRevoke.textContent = 'Révoquer';
    btnRow.appendChild(btnRevoke);
    btnRevoke.addEventListener('click', function () {
      if (!confirm('Révoquer ce lien ? Le client ne pourra plus y accéder.')) return;
      fetch('/admin/api/links/' + editingSlug + '/revoke', { method: 'POST' })
        .then(function (r) { if (r.ok) location.href = '/admin/links'; else alert('Erreur: ' + r.status); });
    });
    var statsLink = el('a', { href: '/admin/links/' + editingSlug + '/stats',
      style: 'color:#7c2d12;font-size:12px;text-decoration:underline' }, ['Voir statistiques']);
    btnRow.appendChild(statsLink);
  }

  var linksLink = el('a', { href: '/admin/links',
    style: 'color:#7c2d12;font-size:12px;text-decoration:underline;margin-left:auto' }, ['← Tous les liens']);
  btnRow.appendChild(linksLink);
  panel.appendChild(btnRow);

  var status = el('div', { id: 'admin_status', style: 'margin-top:8px;font-size:12px;display:none' });
  panel.appendChild(status);

  wrap.insertBefore(panel, wrap.firstChild);

  // ── Admin-only extra inputs (injected near existing panels) ────────

  // Built-in defaults (mirror the values inside the calculator IIFE).
  var DEFAULTS = {
    revPerColDay: 5,
    wechipSharePct: 60,
    priceBase: { filaire: 19000, solaire: 22000 },
    pricePerModule: { filaire: 5500, solaire: 6000 },
    opex: {
      filaire: { base: { brut: 19000, install: 1250, opex: 1200, replCost: 1500 },
                 perModule: { brut: 5500, install: 500, opex: 100, replCost: 250 } },
      solaire: { base: { brut: 22000, install: 1500, opex: 1300, replCost: 1500 },
                 perModule: { brut: 6000, install: 500, opex: 200, replCost: 250 } }
    }
  };

  function currentModel() {
    var solaire = $('btnSolaire');
    return (solaire && solaire.classList.contains('active')) ? 'solaire' : 'filaire';
  }

  function addAdminField(parentPanel, labelText, inputId, attrs, hintText) {
    if (!parentPanel) return null;
    var field = el('div', { class: 'field',
      style: 'border-top:1px dashed #fed7aa;padding-top:8px;margin-top:8px' });
    var lbl = el('label', { for: inputId,
      style: 'color:#9a3412;font-size:11px;font-weight:600' });
    lbl.textContent = '⚙ ' + labelText + ' (admin)';
    var input = el('input', Object.assign({ type: 'number', id: inputId, step: 'any',
      style: 'width:100%;padding:6px 8px;border:1px solid #fdba74;border-radius:6px;font-size:13px;margin-top:4px' }, attrs || {}));
    field.appendChild(lbl);
    field.appendChild(input);
    if (hintText) {
      var hint = el('div', { id: inputId + '_hint',
        style: 'font-size:10px;color:#9a3412;margin-top:3px;font-style:italic' });
      hint.textContent = hintText;
      field.appendChild(hint);
    }
    parentPanel.appendChild(field);
    return input;
  }

  var panels = document.querySelectorAll('.config-row .panel');
  // panels[0] = Configuration, [1] = Investissement, [2] = Hypothèses
  var configPanel  = panels[0];
  var investPanel  = panels[1];
  var hypoPanel    = panels[2];

  // revPerColDay already exists as a hidden input — make it visible to admin.
  var revHidden = $('revPerColDay');
  var revInput;
  if (revHidden && configPanel) {
    var field = el('div', { class: 'field',
      style: 'border-top:1px dashed #fed7aa;padding-top:8px;margin-top:8px' });
    field.appendChild(el('label', { for: 'admin_revPerColDay',
      style: 'color:#9a3412;font-size:11px;font-weight:600' }, ['⚙ Revenu / colonne / jour (admin)']));
    revInput = el('input', { type: 'number', id: 'admin_revPerColDay', step: 'any', min: '0',
      placeholder: String(DEFAULTS.revPerColDay),
      style: 'width:100%;padding:6px 8px;border:1px solid #fdba74;border-radius:6px;font-size:13px;margin-top:4px' });
    revInput.value = Number.isFinite(cfg.revPerColDay) ? cfg.revPerColDay : revHidden.value;
    revHidden.value = revInput.value;
    field.appendChild(revInput);
    var revHint = el('div', { style: 'font-size:10px;color:#9a3412;margin-top:3px;font-style:italic' });
    revHint.textContent = 'Défaut: ' + DEFAULTS.revPerColDay + ' CHF';
    field.appendChild(revHint);
    configPanel.appendChild(field);
    revInput.addEventListener('input', function () {
      revHidden.value = revInput.value;
      try { revHidden.dispatchEvent(new Event('input', { bubbles: true })); } catch (e) {}
    });
  }

  var baseInput   = addAdminField(investPanel, 'Prix base (2 modules)', 'admin_priceBase',
    { min: '0', placeholder: String(DEFAULTS.priceBase[currentModel()]) },
    'Défaut (' + currentModel() + '): ' + DEFAULTS.priceBase[currentModel()] + ' CHF');
  var priceInput  = addAdminField(investPanel, 'Prix / module suppl.', 'admin_pricePerModule',
    { min: '0', placeholder: String(DEFAULTS.pricePerModule[currentModel()]) },
    'Défaut (' + currentModel() + '): ' + DEFAULTS.pricePerModule[currentModel()] + ' CHF (par module au-delà de 2)');
  var shareInput  = addAdminField(hypoPanel,   'Part WECHIP (%)', 'admin_wechipSharePct',
    { min: '0', max: '100', placeholder: String(DEFAULTS.wechipSharePct) },
    'Défaut: ' + DEFAULTS.wechipSharePct + ' %');

  if (baseInput && Number.isFinite(cfg.priceBase)) baseInput.value = cfg.priceBase;
  if (priceInput && Number.isFinite(cfg.pricePerModule)) priceInput.value = cfg.pricePerModule;
  if (shareInput && Number.isFinite(cfg.wechipSharePct)) shareInput.value = cfg.wechipSharePct;

  // Update price hints + placeholders when the model toggle changes.
  function refreshPriceHint() {
    var m = currentModel();
    if (baseInput) {
      baseInput.placeholder = String(DEFAULTS.priceBase[m]);
      var bh = $('admin_priceBase_hint');
      if (bh) bh.textContent = 'Défaut (' + m + '): ' + DEFAULTS.priceBase[m] + ' CHF';
    }
    if (priceInput) {
      priceInput.placeholder = String(DEFAULTS.pricePerModule[m]);
      var ph = $('admin_pricePerModule_hint');
      if (ph) ph.textContent = 'Défaut (' + m + '): ' + DEFAULTS.pricePerModule[m] + ' CHF (par module au-delà de 2)';
    }
  }
  ['btnFilaire', 'btnSolaire'].forEach(function (id) {
    var b = $(id); if (b) b.addEventListener('click', function () { setTimeout(refreshPriceHint, 0); });
  });

  // OPEX JSON in the admin top panel (less common, keep out of main flow)
  var opexWrap = el('div', { style: 'margin-top:10px' });
  opexWrap.appendChild(el('label', { for: 'admin_opex',
    style: 'font-size:11px;font-weight:600;display:block' }, ['Overrides OPEX (JSON, optionnel)']));
  var opexInput = el('textarea', { id: 'admin_opex', rows: '2',
    placeholder: JSON.stringify(DEFAULTS.opex[currentModel()]),
    style: 'width:100%;padding:6px 8px;border:1px solid #fdba74;border-radius:6px;font-size:12px;font-family:ui-monospace,Menlo,monospace;margin-top:2px' });
  if (cfg.opexAssumptions) {
    try { opexInput.value = JSON.stringify(cfg.opexAssumptions); } catch (e) {}
  }
  opexWrap.appendChild(opexInput);
  var opexHint = el('div', { id: 'admin_opex_hint',
    style: 'font-size:10px;color:#7c2d12;margin-top:3px;font-style:italic' });
  opexHint.textContent = 'Défaut (' + currentModel() + '): ' + JSON.stringify(DEFAULTS.opex[currentModel()]);
  opexWrap.appendChild(opexHint);
  panel.appendChild(opexWrap);

  // OPEX payer toggle
  var payerWrap = el('div', { style: 'margin-top:10px;display:flex;align-items:center;gap:8px' });
  var payerInput = el('input', { type: 'checkbox', id: 'admin_opexByWechip',
    style: 'width:16px;height:16px;cursor:pointer' });
  if (cfg.opexByWechip === true) payerInput.checked = true;
  var payerLabel = el('label', { for: 'admin_opexByWechip',
    style: 'font-size:12px;font-weight:600;cursor:pointer' },
    ['OPEX & remplacement pris en charge par WECHIP (au lieu du client)']);
  payerWrap.appendChild(payerInput);
  payerWrap.appendChild(payerLabel);
  var payerHint = el('div', { style: 'font-size:10px;color:#7c2d12;margin-top:3px;font-style:italic;flex-basis:100%' });
  payerHint.textContent = 'Défaut: décoché (client paie l’OPEX en phase de croissance, WECHIP après break-even).';
  payerWrap.appendChild(payerHint);
  panel.appendChild(payerWrap);

  // Sharing-from-start toggle (disables the 2-phase model)
  var phaseWrap = el('div', { style: 'margin-top:10px;display:flex;align-items:center;gap:8px;flex-wrap:wrap' });
  var phaseInput = el('input', { type: 'checkbox', id: 'admin_sharingFromStart',
    style: 'width:16px;height:16px;cursor:pointer' });
  if (cfg.sharingFromStart === true) phaseInput.checked = true;
  var phaseLabel = el('label', { for: 'admin_sharingFromStart',
    style: 'font-size:12px;font-weight:600;cursor:pointer' },
    ['Partage actif dès la 1ère année (pas de modèle 2 phases)']);
  phaseWrap.appendChild(phaseInput);
  phaseWrap.appendChild(phaseLabel);
  var phaseHint = el('div', { style: 'font-size:10px;color:#7c2d12;margin-top:3px;font-style:italic;flex-basis:100%' });
  phaseHint.textContent = 'Défaut: décoché (le partage WECHIP ne s’active qu’après le break-even).';
  phaseWrap.appendChild(phaseHint);
  panel.appendChild(phaseWrap);

  function refreshOpexHint() {
    var m = currentModel();
    opexInput.placeholder = JSON.stringify(DEFAULTS.opex[m]);
    opexHint.textContent = 'Défaut (' + m + '): ' + JSON.stringify(DEFAULTS.opex[m]);
  }
  ['btnFilaire', 'btnSolaire'].forEach(function (id) {
    var b = $(id); if (b) b.addEventListener('click', function () { setTimeout(refreshOpexHint, 0); });
  });

  // Live re-apply admin extras to the calculator so the admin sees impact while tweaking.
  function reapplyToCalc() {
    var liveCfg = Object.assign({}, window.WECHIP_LINK_CONFIG || {});
    var v;
    v = parseFloat(baseInput && baseInput.value); if (Number.isFinite(v)) liveCfg.priceBase = v; else delete liveCfg.priceBase;
    v = parseFloat(priceInput && priceInput.value); if (Number.isFinite(v)) liveCfg.pricePerModule = v; else delete liveCfg.pricePerModule;
    v = parseFloat(shareInput && shareInput.value); if (Number.isFinite(v)) liveCfg.wechipSharePct = v; else delete liveCfg.wechipSharePct;
    if (payerInput && payerInput.checked) liveCfg.opexByWechip = true; else delete liveCfg.opexByWechip;
    if (phaseInput && phaseInput.checked) liveCfg.sharingFromStart = true; else delete liveCfg.sharingFromStart;
    try {
      var raw = (opexInput.value || '').trim();
      if (raw) {
        var parsed = JSON.parse(raw);
        if (parsed && typeof parsed === 'object') liveCfg.opexAssumptions = parsed;
      } else { delete liveCfg.opexAssumptions; }
    } catch (e) { /* leave previous */ }
    window.WECHIP_LINK_CONFIG = liveCfg;
    if (typeof window.__wechipUpdatePhaseLabels === 'function') window.__wechipUpdatePhaseLabels();
    // Re-trigger calculator render via any existing input
    var trigger = $('modulesInput');
    if (trigger) try { trigger.dispatchEvent(new Event('input', { bubbles: true })); } catch (e) {}
  }
  [priceInput, shareInput, opexInput].forEach(function (i) {
    if (i) i.addEventListener('input', reapplyToCalc);
  });
  if (baseInput) baseInput.addEventListener('input', reapplyToCalc);
  if (payerInput) payerInput.addEventListener('change', reapplyToCalc);
  if (phaseInput) phaseInput.addEventListener('change', reapplyToCalc);

  // ── Save handler ──────────────────────────────────────────────────

  function collectConfig() {
    var c = {};
    function num(id) {
      var v = parseFloat($(id) ? $(id).value : '');
      return Number.isFinite(v) ? v : null;
    }
    var v;
    v = num('admin_pricePerModule'); if (v !== null) c.pricePerModule = v;
    v = num('admin_priceBase');      if (v !== null) c.priceBase = v;
    v = num('admin_revPerColDay');   if (v !== null) c.revPerColDay = v;
    v = num('admin_wechipSharePct'); if (v !== null) c.wechipSharePct = v;
    v = num('discountPct');          if (v !== null) c.discountPct = v;
    var modules = parseInt(($('modulesInput') || {}).value, 10);
    if (Number.isFinite(modules)) c.columns = modules * 2;
    var rawOpex = (opexInput.value || '').trim();
    if (rawOpex) {
      try {
        var parsed = JSON.parse(rawOpex);
        if (parsed && typeof parsed === 'object') c.opexAssumptions = parsed;
      } catch (e) { return { error: 'OPEX JSON invalide: ' + e.message }; }
    }
    if (payerInput && payerInput.checked) c.opexByWechip = true;
    if (phaseInput && phaseInput.checked) c.sharingFromStart = true;
    return { config: c };
  }

  function showStatus(msg, ok) {
    status.style.display = 'block';
    status.textContent = msg;
    status.style.color = ok ? '#166534' : '#991b1b';
  }

  btnSave.addEventListener('click', function () {
    var slug = (slugInput.value || '').trim().toLowerCase();
    var name = (nameInput.value || '').trim();
    if (!editingSlug && !/^[a-z0-9][a-z0-9-]{1,59}$/.test(slug)) {
      showStatus('Slug invalide (a-z, 0-9, tiret ; 2–60 caractères, commence par alphanumérique)', false);
      return;
    }
    var collected = collectConfig();
    if (collected.error) { showStatus(collected.error, false); return; }
    var body = { display_name: name, config: collected.config, model: modelSelect.value || 'auto' };
    var url, method;
    if (editingSlug) {
      url = '/admin/api/links/' + editingSlug;
      method = 'PUT';
    } else {
      url = '/admin/api/links';
      method = 'POST';
      body.slug = slug;
    }
    btnSave.disabled = true;
    fetch(url, {
      method: method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    }).then(function (r) {
      return r.json().then(function (j) { return { status: r.status, body: j }; });
    }).then(function (res) {
      btnSave.disabled = false;
      if (res.status >= 200 && res.status < 300 && res.body.ok) {
        var savedSlug = res.body.slug || editingSlug;
        var shareUrl = res.body.url || (location.origin + '/c/' + savedSlug);
        showStatus('✅ Enregistré — lien client : ' + shareUrl + '  (cliquez pour copier)', true);
        status.style.cursor = 'pointer';
        status.onclick = function () {
          try { navigator.clipboard.writeText(shareUrl); status.textContent = '✅ Copié : ' + shareUrl; }
          catch (e) {}
        };
        if (!editingSlug) {
          // Reload as edit mode so further changes go to PUT
          setTimeout(function () { location.href = '/admin?slug=' + savedSlug; }, 1500);
        }
      } else {
        var errs = (res.body && res.body.errors) ? res.body.errors.join(' · ') : ('HTTP ' + res.status);
        showStatus('❌ ' + errs, false);
      }
    }).catch(function (e) {
      btnSave.disabled = false;
      showStatus('❌ Erreur réseau: ' + e.message, false);
    });
  });
})();
