'use strict';

const state = {
  cases: [],
  jobs: [],
  currentCaseId: null,
  report: null,
  graph: null,
  cy: null,
  graphTypes: new Set(),
};

function esc(value) {
  return String(value ?? '')
    .replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;').replaceAll("'", '&#039;');
}

async function fetchJson(url, options = {}) {
  const response = await fetch(url, {headers: {'Accept': 'application/json', ...(options.headers || {})}, ...options});
  let body = null;
  try { body = await response.json(); } catch (_) { body = null; }
  if (!response.ok) throw new Error((body && body.detail) || `HTTP ${response.status}`);
  return body;
}

function badge(value) {
  const normalized = String(value || 'UNKNOWN').toLowerCase();
  return `<span class="badge ${esc(normalized)}">${esc(String(value || 'UNKNOWN').toUpperCase())}</span>`;
}

async function loadHealth() {
  const el = document.getElementById('api-status');
  try {
    const response = await fetch('/health');
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    el.textContent = 'API OK';
    el.className = 'status-pill ok';
  } catch (err) {
    el.textContent = 'API ERROR';
    el.className = 'status-pill error';
  }
}


async function loadSystemStatus() {
  const root = document.getElementById('system-status-grid');
  if (!root) return;
  try {
    const data = await fetchJson('/api/system/status');
    const core = ['api', 'postgres', 'redis', 'neo4j'];
    const items = core.map(name => `<div class="system-item"><strong>${esc(name.toUpperCase())}</strong>${badge(data[name])}</div>`);
    const runner = data.runner || {};
    items.push(`<div class="system-item"><strong>RUNNER</strong>${badge(runner.status)}<span class="target">${runner.age_seconds == null ? '' : runner.age_seconds + ' s'}</span></div>`);
    for (const [name, tool] of Object.entries(data.tools || {})) {
      items.push(`<div class="system-item"><strong>${esc(name)}</strong>${badge(tool.status)}<span class="target">${esc(tool.version || tool.image || '')}</span></div>`);
    }
    root.innerHTML = items.join('');
  } catch (err) {
    root.innerHTML = `<span class="muted">Błąd statusu: ${esc(err.message)}</span>`;
  }
}

async function loadCases() {
  const body = document.getElementById('case-body');
  try {
    const data = await fetchJson('/api/cases');
    state.cases = Array.isArray(data.cases) ? data.cases : [];
    document.getElementById('stat-cases').textContent = state.cases.length;
    document.getElementById('case-summary').textContent = `${state.cases.length} spraw`;
    if (!state.cases.length) {
      body.innerHTML = '<tr><td colspan="3" class="muted">Brak spraw.</td></tr>';
      return;
    }
    body.innerHTML = state.cases.map(item => `
      <tr>
        <td>${badge(item.type)}</td>
        <td><a class="case-link" href="#case-detail" data-case-id="${esc(item.id)}">${esc(item.target || item.id)}</a>
          <span class="target">${esc(item.id)}</span></td>
        <td>${esc(item.observed ?? 0)}</td>
      </tr>`).join('');
    body.querySelectorAll('[data-case-id]').forEach(link => {
      link.addEventListener('click', event => { event.preventDefault(); showCase(link.dataset.caseId); });
    });
  } catch (err) {
    body.innerHTML = `<tr><td colspan="3" class="muted">Błąd: ${esc(err.message)}</td></tr>`;
  }
}

async function searchCases() {
  const input = document.getElementById('case-search');
  const q = (input?.value || '').trim();
  if (!q) { await loadCases(); return; }
  const body = document.getElementById('case-body');
  try {
    const data = await fetchJson(`/api/search?q=${encodeURIComponent(q)}&limit=50`);
    const cases = Array.isArray(data.cases) ? data.cases : [];
    document.getElementById('case-summary').textContent = `${cases.length} wyników`;
    if (!cases.length) {
      body.innerHTML = '<tr><td colspan="3" class="muted">Brak wyników.</td></tr>';
      return;
    }
    body.innerHTML = cases.map(item => `
      <tr><td>${badge(item.type)}</td><td><a class="case-link" href="#case-detail" data-case-id="${esc(item.case_id)}">${esc(item.target || item.case_id)}</a><span class="target">${esc(item.case_id)}</span></td><td>${esc(item.match_count ?? 0)}</td></tr>`).join('');
    body.querySelectorAll('[data-case-id]').forEach(link => link.addEventListener('click', event => { event.preventDefault(); showCase(link.dataset.caseId); }));
  } catch (err) {
    body.innerHTML = `<tr><td colspan="3" class="muted">Błąd: ${esc(err.message)}</td></tr>`;
  }
}

async function loadRelatedCases() {
  const root = document.getElementById('related-cases');
  if (!root || !state.currentCaseId) return;
  root.innerHTML = '<span class="muted">Ładowanie…</span>';
  try {
    const data = await fetchJson(`/api/cases/${encodeURIComponent(state.currentCaseId)}/related?limit=20`);
    const items = Array.isArray(data.related) ? data.related : [];
    if (!items.length) {
      root.innerHTML = '<span class="muted">Brak wykrytych powiązań z innymi sprawami.</span>';
      return;
    }
    root.innerHTML = items.map(item => `<article class="evidence-item medium"><div><strong>${esc(item.target || item.case_id)}</strong> ${badge(item.type)}</div><div class="evidence-meta">${esc(item.shared_count)} wspólnych elementów · ${esc(item.case_id)}</div></article>`).join('');
  } catch (err) {
    root.innerHTML = `<span class="muted">Błąd korelacji: ${esc(err.message)}</span>`;
  }
}


async function loadPivots() {
  const root = document.getElementById('pivot-list');
  const msg = document.getElementById('pivot-message');
  if (!root || !state.currentCaseId) return;
  root.innerHTML = '<span class="muted">Ładowanie…</span>';
  if (msg) { msg.className = 'inline-message'; msg.textContent = ''; }
  try {
    const data = await fetchJson(`/api/cases/${encodeURIComponent(state.currentCaseId)}/pivots?max_depth=3&limit=50`);
    const pivots = Array.isArray(data.pivots) ? data.pivots : [];
    if (!pivots.length) {
      root.innerHTML = '<span class="muted">Brak kandydatów do dalszego pivotu.</span>';
      return;
    }
    root.innerHTML = pivots.map(item => {
      const blocked = item.executable ? '' : ` · ${esc(item.blocked_reason || 'manual')}`;
      const action = item.executable
        ? `<button class="secondary small" type="button" data-pivot-id="${esc(item.pivot_id)}">Dodaj PASSIVE</button>`
        : '';
      return `<article class="evidence-item ${item.score >= 70 ? 'high' : item.score >= 50 ? 'medium' : 'low'}">
        <div><strong>${esc(item.scan_type || item.evidence_type)}</strong> · ${esc(item.target)} ${action}</div>
        <div class="evidence-meta">score=${esc(item.score)} · depth=${esc(item.depth)} · ${esc(item.reason)}${blocked}</div>
      </article>`;
    }).join('');
    root.querySelectorAll('[data-pivot-id]').forEach(button => button.addEventListener('click', () => enqueuePivot(button.dataset.pivotId)));
  } catch (err) {
    root.innerHTML = `<span class="muted">Błąd pivotów: ${esc(err.message)}</span>`;
  }
}

async function enqueuePivot(pivotId) {
  if (!state.currentCaseId) return;
  const msg = document.getElementById('pivot-message');
  try {
    const data = await fetchJson(`/api/cases/${encodeURIComponent(state.currentCaseId)}/pivots/${encodeURIComponent(pivotId)}/enqueue`, {method: 'POST'});
    if (msg) { msg.className = 'inline-message ok'; msg.textContent = `Dodano PASSIVE: ${data.scan_type} ${data.target}`; }
    await Promise.allSettled([loadPivots(), loadJobs()]);
  } catch (err) {
    if (msg) { msg.className = 'inline-message error'; msg.textContent = `Błąd: ${err.message}`; }
  }
}

async function autoEnqueuePivots() {
  if (!state.currentCaseId) return;
  const msg = document.getElementById('pivot-message');
  try {
    const data = await fetchJson(`/api/cases/${encodeURIComponent(state.currentCaseId)}/pivots/auto-enqueue`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({min_score: 60, max_count: 5, max_depth: 3}),
    });
    const count = Array.isArray(data.enqueued) ? data.enqueued.length : 0;
    if (msg) { msg.className = 'inline-message ok'; msg.textContent = `Dodano ${count} zadań PASSIVE.`; }
    await Promise.allSettled([loadPivots(), loadJobs()]);
  } catch (err) {
    if (msg) { msg.className = 'inline-message error'; msg.textContent = `Błąd: ${err.message}`; }
  }
}


async function loadJobs() {
  const body = document.getElementById('job-body');
  try {
    const data = await fetchJson('/api/jobs');
    state.jobs = Array.isArray(data.jobs) ? data.jobs : [];
    document.getElementById('stat-jobs').textContent = state.jobs.length;
    document.getElementById('stat-pending').textContent = state.jobs.filter(x => (x.status || x.queue) === 'PENDING').length;
    document.getElementById('stat-failed').textContent = state.jobs.filter(x => (x.status || x.queue) === 'FAILED').length;
    document.getElementById('job-summary').textContent = `${state.jobs.length} zadań`;
    if (!state.jobs.length) {
      body.innerHTML = '<tr><td colspan="4" class="muted">Brak zadań.</td></tr>';
      return;
    }
    body.innerHTML = state.jobs.slice(0, 100).map(item => `
      <tr><td>${badge(item.status || item.queue)}</td><td>${esc(item.type)}</td>
      <td>${esc(item.target)}</td><td>${item.active ? 'ACTIVE' : 'PASSIVE'}</td></tr>`).join('');
  } catch (err) {
    body.innerHTML = `<tr><td colspan="4" class="muted">Błąd: ${esc(err.message)}</td></tr>`;
  }
}

function updateScanControls() {
  const type = document.getElementById('scan-type').value;
  const mode = document.getElementById('scan-mode');
  const auth = document.getElementById('scan-authorized');
  if (type !== 'DOMAIN') {
    mode.value = 'PASSIVE';
    mode.disabled = true;
  } else {
    mode.disabled = false;
  }
  const active = type === 'DOMAIN' && mode.value === 'ACTIVE';
  auth.disabled = !active;
  if (!active) auth.checked = false;
}

async function submitScan(event) {
  event.preventDefault();
  const type = document.getElementById('scan-type').value;
  const target = document.getElementById('scan-target').value.trim();
  const mode = document.getElementById('scan-mode').value;
  const authorized = document.getElementById('scan-authorized').checked;
  const active = type === 'DOMAIN' && mode === 'ACTIVE';
  const result = document.getElementById('scan-result');
  const button = document.getElementById('scan-submit');
  if (active && !authorized) {
    result.className = 'inline-message error';
    result.textContent = 'ACTIVE wymaga potwierdzenia autoryzacji.';
    return;
  }

  let activeToken = '';
  if (active) {
    activeToken = window.prompt('Podaj token autoryzacyjny ACTIVE:') || '';
    if (!activeToken) {
      result.className = 'inline-message error';
      result.textContent = 'ACTIVE wymaga tokena autoryzacyjnego.';
      return;
    }
  }

  button.disabled = true;
  result.className = 'inline-message';
  result.textContent = 'Dodawanie zadania…';
  try {
    const data = await fetchJson('/api/scan', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(active ? {'X-OSINT-Active-Token': activeToken} : {}),
      },
      body: JSON.stringify({type, target, active, authorized}),
    });
    result.className = 'inline-message ok';
    result.textContent = `PENDING · ${data.type} · ${data.target} · ${data.id}`;
    document.getElementById('scan-target').value = '';
    await refreshAll();
  } catch (err) {
    result.className = 'inline-message error';
    result.textContent = `Błąd: ${err.message}`;
  } finally {
    button.disabled = false;
  }
}

function confidenceQuery() {
  const values = [];
  if (document.getElementById('confidence-high').checked) values.push('HIGH');
  if (document.getElementById('confidence-medium').checked) values.push('MEDIUM');
  if (document.getElementById('confidence-low').checked) values.push('LOW');
  return values;
}

function renderCaseSummary(report) {
  const summary = report.summary || {};
  const cards = [
    ['Evidence', summary.evidence_count ?? 0], ['Findings', summary.finding_count ?? 0],
    ['HIGH', summary.high_count ?? 0], ['MEDIUM', summary.medium_count ?? 0],
  ];
  document.getElementById('case-summary-cards').innerHTML = cards.map(([label, value]) =>
    `<article class="stat-card"><span>${esc(label)}</span><strong>${esc(value)}</strong></article>`).join('');
}

function allEvidence(report) {
  const groups = ['high', 'medium', 'low', 'seed'];
  return groups.flatMap(group => (report[group] || []).map(item => ({...item, confidence: String(item.confidence || group).toUpperCase()})));
}

function renderEvidence() {
  const list = document.getElementById('evidence-list');
  if (!state.report) { list.innerHTML = '<div class="muted">Brak danych.</div>'; return; }
  const filter = document.getElementById('evidence-confidence').value;
  let items = allEvidence(state.report);
  if (filter !== 'ALL') {
    const allowed = new Set(filter.split(','));
    items = items.filter(item => allowed.has(String(item.confidence || '').toUpperCase()));
  }
  if (!items.length) { list.innerHTML = '<div class="muted">Brak evidence dla wybranego filtra.</div>'; return; }
  list.innerHTML = items.map(item => {
    const level = String(item.confidence || 'LOW').toUpperCase();
    const sources = Array.isArray(item.sources) ? item.sources.join(', ') : (item.source || '');
    return `<article class="evidence-item ${esc(level.toLowerCase())}">
      <div>${badge(level)} <span class="evidence-value">${esc(item.type)} · ${esc(item.value)}</span></div>
      <div class="evidence-meta">Źródła: ${esc(sources || 'brak')} · ${esc(item.raw_reference || '')}</div>
    </article>`;
  }).join('');
}

function renderTypeFilter(nodes) {
  state.graphTypes = new Set(nodes.map(n => n.type).filter(Boolean));
  const root = document.getElementById('type-filter');
  root.innerHTML = [...state.graphTypes].sort().map(type =>
    `<label><input type="checkbox" data-node-type="${esc(type)}" checked> ${esc(type)}</label>`).join('');
  root.querySelectorAll('[data-node-type]').forEach(input => input.addEventListener('change', applyGraphTypeFilter));
}

function applyGraphTypeFilter() {
  if (!state.cy) return;
  const enabled = new Set([...document.querySelectorAll('[data-node-type]:checked')].map(x => x.dataset.nodeType));
  state.cy.nodes().forEach(node => node.style('display', enabled.has(node.data('type')) ? 'element' : 'none'));
  state.cy.edges().forEach(edge => {
    const visible = edge.source().style('display') !== 'none' && edge.target().style('display') !== 'none';
    edge.style('display', visible ? 'element' : 'none');
  });
}

function showSelectedElement(element) {
  const panel = document.getElementById('selected-element');
  const d = element.data();
  if (element.isNode()) {
    panel.innerHTML = `<strong>${esc(d.label)}</strong><br><span class="muted">${esc(d.type)} · ${esc(d.id)}</span>`;
  } else {
    panel.innerHTML = `<strong>${esc(d.type)}</strong><br><span class="muted">${esc(d.confidence)} · źródła: ${esc((d.sources || []).join(', '))}</span>`;
  }
}

function renderGraph(data) {
  const warning = document.getElementById('graph-warning');
  state.graph = data;
  if (data.truncated) {
    warning.className = 'inline-message error';
    warning.textContent = `Graf ograniczony do ${data.limit} węzłów.`;
  } else {
    warning.className = 'inline-message';
    warning.textContent = `${data.nodes.length} węzłów · ${data.edges.length} relacji`;
  }
  renderTypeFilter(data.nodes || []);
  const container = document.getElementById('case-graph');
  if (!window.cytoscape) {
    state.cy = null;
    container.innerHTML = '<div class="muted" style="padding:24px">Cytoscape.js jest niedostępny. Sprawdź połączenie internetowe; dane CASE i evidence nadal są dostępne.</div>';
    return;
  }
  const elements = [
    ...(data.nodes || []).map(node => ({data: node})),
    ...(data.edges || []).map(edge => ({data: edge})),
  ];
  if (state.cy) state.cy.destroy();
  state.cy = cytoscape({
    container,
    elements,
    layout: {name: 'cose', animate: false, fit: true, padding: 32},
    minZoom: .15,
    maxZoom: 3,
    wheelSensitivity: .2,
    style: [
      {selector: 'node', style: {'background-color': '#3b82f6', 'label': 'data(label)', 'color': '#dce8f4', 'font-size': 10, 'text-wrap': 'wrap', 'text-max-width': 110, 'text-valign': 'bottom', 'text-margin-y': 7, 'width': 24, 'height': 24, 'border-width': 1, 'border-color': '#93c5fd'}},
      {selector: 'node[type = "Email"]', style: {'background-color': '#a855f7'}},
      {selector: 'node[type = "Profile"]', style: {'background-color': '#06b6d4'}},
      {selector: 'node[type = "IP"]', style: {'background-color': '#f97316'}},
      {selector: 'node[type = "Domain"]', style: {'background-color': '#22c55e'}},
      {selector: 'edge', style: {'width': 1.5, 'line-color': '#52677b', 'target-arrow-color': '#52677b', 'target-arrow-shape': 'triangle', 'curve-style': 'bezier'}},
      {selector: 'edge[confidence = "HIGH"]', style: {'line-color': '#4ade80', 'target-arrow-color': '#4ade80', 'width': 2.4}},
      {selector: 'edge[confidence = "MEDIUM"]', style: {'line-color': '#fbbf24', 'target-arrow-color': '#fbbf24'}},
      {selector: 'edge[confidence = "LOW"]', style: {'line-color': '#64748b', 'target-arrow-color': '#64748b', 'line-style': 'dashed'}},
      {selector: ':selected', style: {'border-width': 3, 'border-color': '#ffffff', 'line-color': '#ffffff', 'target-arrow-color': '#ffffff'}},
    ],
  });
  state.cy.on('tap', 'node,edge', event => showSelectedElement(event.target));
}

async function loadCaseGraph() {
  if (!state.currentCaseId) return;
  const levels = confidenceQuery();
  const warning = document.getElementById('graph-warning');
  if (!levels.length) {
    renderGraph({nodes: [], edges: [], truncated: false, limit: 500});
    warning.className = 'inline-message error';
    warning.textContent = 'Wybierz co najmniej jeden poziom confidence.';
    return;
  }
  try {
    const url = `/api/cases/${encodeURIComponent(state.currentCaseId)}/graph?confidence=${encodeURIComponent(levels.join(','))}&limit=500`;
    renderGraph(await fetchJson(url));
  } catch (err) {
    warning.className = 'inline-message error';
    warning.textContent = `Błąd grafu: ${err.message}`;
  }
}

async function showCase(caseId) {
  state.currentCaseId = caseId;
  const root = document.getElementById('case-detail');
  root.classList.remove('hidden');
  document.getElementById('case-detail-title').textContent = caseId;
  document.getElementById('case-detail-meta').textContent = 'Ładowanie danych…';
  document.getElementById('export-md').href = `/api/cases/${encodeURIComponent(caseId)}/report.md`;
  document.getElementById('export-json').href = `/api/cases/${encodeURIComponent(caseId)}/export.json`;
  document.getElementById('export-csv').href = `/api/cases/${encodeURIComponent(caseId)}/export.csv`;
  try {
    state.report = await fetchJson(`/api/cases/${encodeURIComponent(caseId)}/report`);
    const meta = state.report.case || {};
    document.getElementById('case-detail-title').textContent = meta.target || meta.email || meta.username || caseId;
    document.getElementById('case-detail-meta').textContent = `${meta.type || 'CASE'} · ${meta.mode || ''} · ${meta.status || ''} · ${caseId}`;
    renderCaseSummary(state.report);
    await loadRelatedCases();
    await loadPivots();
    renderEvidence();
    await loadCaseGraph();
    root.scrollIntoView({behavior: 'smooth', block: 'start'});
  } catch (err) {
    document.getElementById('case-detail-meta').textContent = `Błąd: ${err.message}`;
  }
}

function closeCase() {
  document.getElementById('case-detail').classList.add('hidden');
  state.currentCaseId = null;
  state.report = null;
  if (state.cy) { state.cy.destroy(); state.cy = null; }
}

function fitGraph() { if (state.cy) state.cy.fit(undefined, 35); }
function resetGraphLayout() { if (state.cy) state.cy.layout({name: 'cose', animate: false, fit: true, padding: 32}).run(); }

async function refreshAll() {
  await Promise.allSettled([loadHealth(), loadSystemStatus(), loadCases(), loadJobs()]);
}

function init() {
  document.getElementById('scan-form').addEventListener('submit', submitScan);
  document.getElementById('pivot-auto-enqueue')?.addEventListener('click', autoEnqueuePivots);
document.getElementById('case-search-button')?.addEventListener('click', searchCases);
document.getElementById('case-search')?.addEventListener('keydown', event => { if (event.key === 'Enter') { event.preventDefault(); searchCases(); } });
  document.getElementById('scan-type').addEventListener('change', updateScanControls);
  document.getElementById('scan-mode').addEventListener('change', updateScanControls);
  document.getElementById('evidence-confidence').addEventListener('change', renderEvidence);
  ['confidence-high', 'confidence-medium', 'confidence-low'].forEach(id => document.getElementById(id).addEventListener('change', loadCaseGraph));
  updateScanControls();
  refreshAll();
  window.setInterval(refreshAll, 5000);
}

document.addEventListener('DOMContentLoaded', init);
