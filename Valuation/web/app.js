// ─── State ───────────────────────────────────────────────────────────────────
const S = {
  ticker: null,
  data: [null, null, null, null, null]  // passos[0..4]
};

// ─── Utilities ────────────────────────────────────────────────────────────────
const BRL = new Intl.NumberFormat('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
const N2  = new Intl.NumberFormat('pt-BR', { minimumFractionDigits: 0, maximumFractionDigits: 2 });

function fBRL(v)  { return v == null ? '—' : 'R$ ' + BRL.format(v); }
function fM(v)    { return v == null ? '—' : N2.format(v); }
function fPct(v)  { return v == null ? '—' : (v * 100).toFixed(1) + '%'; }
function fPct2(v) { return v == null ? '—' : (v * 100).toFixed(2) + '%'; }
function fX(v)    { return v == null ? '—' : N2.format(v) + 'x'; }

function getDeep(obj, path) {
  return path.reduce((o, k) => (o != null ? o[k] : null), obj);
}
function setDeep(obj, path, val) {
  const last = path[path.length - 1];
  const parent = path.slice(0, -1).reduce((o, k) => o[k], obj);
  parent[last] = val;
}

function el(tag, cls, content) {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (content !== undefined) e.innerHTML = content;
  return e;
}
function app() { return document.getElementById('app'); }

// ─── API ──────────────────────────────────────────────────────────────────────
async function fetchTickers() {
  const r = await fetch('/api/tickers');
  return r.json();
}

async function fetchPasso(ticker, n) {
  try {
    const r = await fetch(`/Acoes/${ticker}/passo${n}.json?_=${Date.now()}`);
    if (!r.ok) return null;
    return await r.json();
  } catch { return null; }
}

async function savePasso(ticker, n) {
  const data = S.data[n - 1];
  const r = await fetch(`/api/passo/${ticker}/${n}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  if (!r.ok) throw new Error('Falha ao salvar');
}

// ─── Router ───────────────────────────────────────────────────────────────────
async function render() {
  const hash = location.hash.slice(1).trim();
  if (!hash) {
    await renderList();
  } else {
    await renderDetail(hash);
  }
}

window.addEventListener('hashchange', render);
render();

// ─── List view ────────────────────────────────────────────────────────────────
async function renderList() {
  setBreadcrumb(null);
  app().innerHTML = '<div class="loading"><div class="spinner"></div>Carregando empresas...</div>';

  let tickers;
  try { tickers = await fetchTickers(); }
  catch { app().innerHTML = '<div class="empty">Erro ao conectar ao servidor.</div>'; return; }

  if (!tickers.length) {
    app().innerHTML = '<div class="empty">Nenhuma empresa encontrada em Acoes/</div>';
    return;
  }

  const cards = await Promise.all(tickers.map(async t => {
    const passos = await Promise.all([1,2,3,4,5].map(n => fetchPasso(t, n)));
    return { ticker: t, passos };
  }));

  const frag = document.createDocumentFragment();
  const header = el('div', 'list-header');
  header.innerHTML = `<h1>Empresas analisadas</h1><p>${tickers.length} empresa${tickers.length !== 1 ? 's' : ''} encontrada${tickers.length !== 1 ? 's' : ''} em Acoes/</p>`;
  frag.appendChild(header);

  const grid = el('div', 'ticker-grid');
  for (const { ticker, passos } of cards) {
    grid.appendChild(buildCard(ticker, passos));
  }
  frag.appendChild(grid);

  app().innerHTML = '';
  app().appendChild(frag);
}

function buildCard(ticker, passos) {
  const [p1, , , p4] = passos;
  const nome   = p1?.empresa?.nome  || ticker;
  const setor  = p1?.empresa?.setor || '—';
  const pais   = p1?.empresa?.pais  || '';
  const precoM = p1?.mercado?.P?.valor ?? p4?.bloco_f?.P;
  const introV = p4?.bloco_f?.Valor_acao;

  let pct = null, cls = 'neutral', label = 'Sem valuation';
  if (precoM != null && introV != null) {
    pct = (precoM - introV) / introV;
    if (pct > 0.02)       { cls = 'negative'; label = '+' + fPct(pct) + ' prêmio'; }
    else if (pct < -0.02) { cls = 'positive'; label = fPct(pct) + ' desconto'; }
    else                  { cls = 'neutral';  label = 'Justo'; }
  }

  const done = passos.filter(Boolean).length;
  const stepsHtml = passos.map(p => `<div class="pipeline-step ${p ? 'done' : ''}"></div>`).join('');

  const a = el('a', 'ticker-card');
  a.href = '#' + ticker;
  a.innerHTML = `
    <div class="card-top">
      <span class="ticker-badge">${ticker}</span>
      <span class="upside-badge ${cls}">${label}</span>
    </div>
    <div class="card-name">${nome}</div>
    <div class="card-sector">${setor}${pais ? ' · ' + pais : ''}</div>
    <div class="price-row">
      <div class="price-item">
        <div class="price-label">Mercado</div>
        <div class="price-value market">${precoM != null ? fBRL(precoM) : '—'}</div>
      </div>
      <div class="price-item">
        <div class="price-label">Intrínseco</div>
        <div class="price-value intrinsic">${introV != null ? fBRL(introV) : '—'}</div>
      </div>
    </div>
    <div class="pipeline-steps">${stepsHtml}</div>
    <div class="pipeline-label">Pipeline: ${done}/5 passos concluídos</div>
  `;
  return a;
}

// ─── Detail view ──────────────────────────────────────────────────────────────
async function renderDetail(ticker) {
  setBreadcrumb(ticker);
  app().innerHTML = '<div class="loading"><div class="spinner"></div>Carregando análise...</div>';

  S.ticker = ticker;
  const passos = await Promise.all([1,2,3,4,5].map(n => fetchPasso(ticker, n)));
  passos.forEach((d, i) => { S.data[i] = d; });

  const [p1, p2, p3, p4, p5] = passos;
  if (!p1 && !p2 && !p3 && !p4 && !p5) {
    app().innerHTML = `<div class="empty">Nenhum dado encontrado para ${ticker}</div>`;
    return;
  }

  const frag = document.createDocumentFragment();
  frag.appendChild(buildHero(ticker, p1, p4));

  const acc = el('div', 'accordion');
  const items = [
    { n: 1, title: 'Extração do Release',     data: p1, fn: renderP1, open: true  },
    { n: 2, title: 'Parâmetros de Mercado',    data: p2, fn: renderP2, open: false },
    { n: 3, title: 'Premissas do Analista',    data: p3, fn: renderP3, open: false },
    { n: 4, title: 'Cálculo DCF',              data: p4, fn: renderP4, open: true  },
    { n: 5, title: 'Sensibilidade / Cenários', data: p5, fn: renderP5, open: false },
  ];
  for (const item of items) acc.appendChild(buildAccItem(item));
  frag.appendChild(acc);

  app().innerHTML = '';
  app().appendChild(frag);
  attachEditListeners();
}

function buildHero(ticker, p1, p4) {
  const nome   = p1?.empresa?.nome  || ticker;
  const setor  = p1?.empresa?.setor || '';
  const pais   = p1?.empresa?.pais  || '';
  const precoM = p1?.mercado?.P?.valor ?? p4?.bloco_f?.P;
  const introV = p4?.bloco_f?.Valor_acao;

  let pct = null, cls = '', verdade = '—';
  if (precoM != null && introV != null) {
    pct = (precoM - introV) / introV;
    const abs = Math.abs(pct * 100).toFixed(1);
    if (pct > 0.02)       { cls = 'overvalued';  verdade = `+${abs}% premium`; }
    else if (pct < -0.02) { cls = 'undervalued'; verdade = `-${abs}% desconto`; }
    else                  { cls = '';             verdade = 'Preço justo'; }
  }

  const div = el('div', 'detail-hero');
  div.innerHTML = `
    <div class="hero-left">
      <div class="hero-company">${nome} <span class="hero-ticker">${ticker}</span></div>
      <div class="hero-meta">${[setor, pais].filter(Boolean).join(' · ')}</div>
    </div>
    <div class="hero-right">
      ${precoM != null ? `
        <div class="hero-price">
          <div class="hero-price-label">Mercado</div>
          <div class="hero-price-value market">${fBRL(precoM)}</div>
        </div>
        <div class="hero-vs">vs</div>
        <div class="hero-price">
          <div class="hero-price-label">Intrínseco</div>
          <div class="hero-price-value intrinsic">${introV != null ? fBRL(introV) : '—'}</div>
        </div>
        ${pct != null ? `
          <div class="hero-verdict">
            <div class="hero-verdict-pct ${cls}">${verdade}</div>
            <div class="hero-verdict-label">${pct > 0.02 ? 'Sobreprecificado' : pct < -0.02 ? 'Subprecificado' : 'Avaliação'}</div>
          </div>
        ` : ''}
      ` : '<div class="hero-verdict"><div class="hero-verdict-label">Valuation não calculado</div></div>'}
    </div>
  `;
  return div;
}

function buildAccItem({ n, title, data, fn, open }) {
  const done = data != null;
  const item = el('div', 'acc-item' + (open && done ? ' open' : ''));

  const hdr = el('button', 'acc-header');
  hdr.innerHTML = `
    <span class="passo-num ${done ? 'done' : 'pending'}">${done ? '✓' : n}</span>
    <span class="acc-title">Passo ${n} — ${title}</span>
    <span class="acc-status">${done ? 'Concluído' : 'Pendente'}</span>
    <span class="acc-chevron">▼</span>
  `;
  hdr.onclick = () => item.classList.toggle('open', !item.classList.contains('open'));

  const body = el('div', 'acc-body');
  body.dataset.passoBody = n;
  if (done) {
    try { fn(body, data, n); }
    catch (e) { body.innerHTML = `<div class="empty">Erro ao renderizar: ${e.message}</div>`; }
  } else {
    body.innerHTML = `<div class="pending-box"><div class="pending-icon">⏳</div><div class="pending-title">Passo ${n} pendente</div><div class="pending-sub">Execute o pipeline para gerar este passo.</div></div>`;
  }

  item.appendChild(hdr);
  item.appendChild(body);
  return item;
}

// ─── Passo 1 — Extração do Release ───────────────────────────────────────────
function renderP1(container, d, passoN) {
  container.innerHTML = `
    <div class="section-grid">
      <div class="section-box">
        <div class="section-title" style="padding:0 12px">DRE — Resultado</div>
        <div class="table-wrap">
          <table>
            <thead><tr><th>Campo</th><th style="text-align:right">Valor</th><th>Conf.</th></tr></thead>
            <tbody id="p1-dre"></tbody>
          </table>
        </div>
      </div>
      <div>
        <div class="section-box" style="margin-bottom:12px">
          <div class="section-title" style="padding:0 12px">Balanço</div>
          <div class="table-wrap">
            <table>
              <thead><tr><th>Campo</th><th style="text-align:right">Valor (M)</th><th>Conf.</th></tr></thead>
              <tbody id="p1-bal"></tbody>
            </table>
          </div>
        </div>
        <div class="section-box">
          <div class="section-title" style="padding:0 12px">Mercado &amp; Operacional</div>
          <div class="table-wrap">
            <table>
              <thead><tr><th>Campo</th><th style="text-align:right">Valor</th><th>Conf.</th></tr></thead>
              <tbody id="p1-mkt"></tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  `;

  fillTable(container.querySelector('#p1-dre'), [
    ['Receita (Rev₀)',   d.dre?.Rev_0,    'dre.Rev_0.valor',            'number', v => fM(v) + 'M'],
    ['EBIT',            d.dre?.EBIT_0,   'dre.EBIT_0.valor',           'number', v => fM(v) + 'M'],
    ['EBITDA',          d.dre?.EBITDA,   'dre.EBITDA.valor',           'number', v => fM(v) + 'M'],
    ['Depreciação',     d.dre?.Dep,      'dre.Dep.valor',              'number', v => fM(v) + 'M'],
    ['Juros',           d.dre?.Juros,    'dre.Juros.valor',            'number', v => fM(v) + 'M'],
    ['LAIR',            d.dre?.LAIR,     'dre.LAIR.valor',             'number', v => fM(v) + 'M'],
    ['IR Pago',         d.dre?.IR_pago,  'dre.IR_pago.valor',          'number', v => fM(v) + 'M'],
    ['IR Efetivo',      d.dre?.IR_ef,    'dre.IR_ef.valor',            'pct',    v => fPct(v)],
    ['Margem EBIT',     d.dre?.Mg_atual, 'dre.Mg_atual.valor',         'pct',    v => fPct(v)],
  ], passoN);

  fillTable(container.querySelector('#p1-bal'), [
    ['Patrimônio Líquido', d.balanco?.PL,    'balanco.PL.valor',    'number', v => fM(v)],
    ['Dívida Bruta',       d.balanco?.D,     'balanco.D.valor',     'number', v => fM(v)],
    ['Caixa',              d.balanco?.Caixa, 'balanco.Caixa.valor', 'number', v => fM(v)],
    ['Dívida Líquida',     d.balanco?.D_liq, 'balanco.D_liq.valor', 'number', v => fM(v)],
    ['Minority Interest',  d.balanco?.MinInt,'balanco.MinInt.valor', 'number', v => fM(v)],
    ['Capital Investido',  d.balanco?.CI,    'balanco.CI.valor',    'number', v => fM(v)],
  ], passoN);

  fillTable(container.querySelector('#p1-mkt'), [
    ['Ações (M)',       d.mercado?.Shares,       'mercado.Shares.valor',       'number', v => fM(v)],
    ['Preço',           d.mercado?.P,            'mercado.P.valor',            'number', v => fBRL(v)],
    ['Market Cap (M)',  d.mercado?.MktCap,        'mercado.MktCap.valor',       'number', v => fM(v)],
    ['Receita Ant.',    d.operacional?.Rev_ant,   'operacional.Rev_ant.valor',  'number', v => fM(v) + 'M'],
    ['Cresc. Recente',  d.operacional?.g_recente, 'operacional.g_recente.valor','pct',    v => fPct(v)],
    ['ROIC Atual',      d.operacional?.ROIC_atual,'operacional.ROIC_atual.valor','pct',   v => fPct(v)],
    ['CAPEX',           d.operacional?.CAPEX,     'operacional.CAPEX.valor',    'number', v => fM(v) + 'M'],
  ], passoN);
}

function fillTable(tbody, rows, passoN) {
  if (!tbody) return;
  for (const [label, obj, path, type, fmt] of rows) {
    const val = obj?.valor ?? obj;
    if (val == null) continue;
    const conf = obj?.confianca;
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td class="field-name">${label}</td>
      <td class="val-num">
        <span class="editable-wrap" data-passo="${passoN}" data-path="${path}" data-type="${type}">
          <span class="ev">${fmt(val)}</span>
          <button class="edit-btn" title="Editar">✏</button>
        </span>
      </td>
      <td>${conf ? `<span class="conf-badge conf-${conf}">${conf}</span>` : ''}</td>
    `;
    tbody.appendChild(tr);
  }
}

// ─── Passo 2 — Parâmetros de Mercado ─────────────────────────────────────────
function renderP2(container, d, passoN) {
  const pm = d.parametros_mercado || {};
  const st = d.status_passo2 || {};
  const alertHTML = (st.alertas || []).map(a => `<div class="alert-box">⚠ ${a}</div>`).join('');

  container.innerHTML = `
    ${alertHTML}
    <div class="table-wrap">
      <table>
        <thead><tr><th>Parâmetro</th><th style="text-align:right">Valor</th><th>Fonte</th></tr></thead>
        <tbody id="p2-tab"></tbody>
      </table>
    </div>
    <div style="margin-top:12px">
      <span class="tag ${st.pronto_para_passo3 ? 'tag-ok' : 'tag-fail'}">
        ${st.pronto_para_passo3 ? '✓ Pronto para Passo 3' : '✗ Bloqueado — revisar alertas'}
      </span>
    </div>
  `;

  const tbody = container.querySelector('#p2-tab');
  const rows = [
    ['Rf (Taxa Livre de Risco)', pm.Rf,       'parametros_mercado.Rf.valor',       'pct',    v => fPct2(v)],
    ['ERP (Prêmio de Risco)',    pm.ERP,      'parametros_mercado.ERP.valor',      'pct',    v => fPct2(v)],
    ['Beta Desalavancado (βu)',  pm.Beta_u,   'parametros_mercado.Beta_u.valor',   'number', v => fM(v)],
    ['Kd pré-IR',                pm.Kd_pre,   'parametros_mercado.Kd_pre.valor',   'pct',    v => fPct2(v)],
    ['IR Marginal',              pm.IR_marg,  'parametros_mercado.IR_marg.valor',  'pct',    v => fPct(v)],
    ['WACC Estimado',            pm.WACC_est, 'parametros_mercado.WACC_est.valor', 'pct',    v => fPct(v)],
  ];
  for (const [label, obj, path, type, fmt] of rows) {
    const val = obj?.valor ?? obj;
    if (val == null) continue;
    const fonte = obj?.fonte || obj?.metodo || obj?.composicao || '';
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td class="field-name">${label}</td>
      <td class="val-num">
        <span class="editable-wrap" data-passo="${passoN}" data-path="${path}" data-type="${type}">
          <span class="ev">${fmt(val)}</span>
          <button class="edit-btn" title="Editar">✏</button>
        </span>
      </td>
      <td class="fonte">${fonte}</td>
    `;
    tbody.appendChild(tr);
  }
}

// ─── Passo 3 — Premissas do Analista ─────────────────────────────────────────
function renderP3(container, d, passoN) {
  const pr  = d.premissas_analiticas || {};
  const nar = d.narrativa_premissas  || {};
  const val = d.validacoes           || {};

  container.innerHTML = `<div class="premissas-grid" id="p3-cards"></div>`;
  const grid = container.querySelector('#p3-cards');

  const premCards = [
    ['g Ano 1',          pr.g1,       'premissas_analiticas.g1',       'pct',    v => fPct(v)],
    ['g Anos 2-5',       pr.g2_5,     'premissas_analiticas.g2_5',     'pct',    v => fPct(v)],
    ['Margem Atual',     pr.Mg_1,     'premissas_analiticas.Mg_1',     'pct',    v => fPct(v)],
    ['Margem Alvo',      pr.Mg_alvo,  'premissas_analiticas.Mg_alvo',  'pct',    v => fPct(v)],
    ['Ano Convergência', pr.Ano_conv, 'premissas_analiticas.Ano_conv', 'number', v => 'Ano ' + v],
    ['Giro de Capital',  pr.StC,      'premissas_analiticas.StC',      'number', v => fX(v)],
    ['g Perpetuidade',   pr.g_perp,   'premissas_analiticas.g_perp',   'pct',    v => fPct(v)],
    ['P(Falência)',       pr.P_fail,   'premissas_analiticas.P_fail',   'number', v => fPct(v)],
  ];
  for (const [label, rawVal, path, type, fmt] of premCards) {
    if (rawVal == null) continue;
    const card = el('div', 'premissa-card');
    card.innerHTML = `
      <div class="premissa-label">${label}</div>
      <div class="premissa-val">
        <span class="editable-wrap" data-passo="${passoN}" data-path="${path}" data-type="${type}">
          <span class="ev">${fmt(rawVal)}</span>
          <button class="edit-btn" title="Editar">✏</button>
        </span>
      </div>
    `;
    grid.appendChild(card);
  }

  for (const [k, titulo] of [['crescimento','Crescimento'],['margem','Margens'],['risco','Risco'],['perpetuidade','Perpetuidade']]) {
    if (!nar[k]) continue;
    const nb = el('div', 'narrative-block');
    nb.innerHTML = `<div class="narrative-title">${titulo}</div><div class="narrative-text">${nar[k]}</div>`;
    container.appendChild(nb);
  }

  const valKeys = Object.entries(val).filter(([k]) => k !== 'pronto_para_passo4');
  if (valKeys.length) {
    const st = el('div', 'section-title'); st.textContent = 'Validações';
    container.appendChild(st);
    const list = el('ul', 'checklist');
    for (const [k, v] of valKeys) {
      const isOk   = v === true  || (typeof v === 'string' && v.startsWith('OK'));
      const isFail = v === false || (typeof v === 'string' && v.startsWith('FALHOU'));
      const li = el('li', `check-item ${isOk ? 'check-ok' : isFail ? 'check-fail' : 'check-info'}`);
      li.innerHTML = `
        <span class="check-icon">${isOk ? '✓' : isFail ? '✗' : '⚠'}</span>
        <div>
          <div class="check-nome">${k.replace(/_/g,' ')}</div>
          <div class="check-detalhe">${typeof v === 'string' ? v : ''}</div>
        </div>
      `;
      list.appendChild(li);
    }
    container.appendChild(list);
  }
}

// ─── Recalcular DCF ───────────────────────────────────────────────────────────
async function runPasso4() {
  const btn    = document.querySelector('.run-btn');
  const status = document.querySelector('.run-status');
  if (btn) { btn.disabled = true; btn.textContent = '⏳ Calculando...'; }
  if (status) status.textContent = 'Propagando passo 1 e 2 → passo 3 e rodando o script...';

  try {
    const resp = await fetch(`/api/run-passo4/${S.ticker}`, { method: 'POST' });
    const text = await resp.text();
    let data;
    try { data = JSON.parse(text); }
    catch { throw new Error(`Servidor retornou resposta inválida:\n${text.slice(0, 400)}`); }
    if (!data.ok) throw new Error(data.error || 'Erro desconhecido');

    S.data[3] = data.passo4;

    const body = document.querySelector('[data-passo-body="4"]');
    if (body) {
      body.innerHTML = '';
      renderP4(body, data.passo4);
      attachEditListeners();
    }
    refreshHero();
  } catch (e) {
    if (status) status.textContent = `Erro: ${e.message}`;
    if (btn) { btn.disabled = false; btn.textContent = '▶ Recalcular DCF'; }
  }
}

// ─── Passo 4 — Cálculo DCF ───────────────────────────────────────────────────
function renderP4(container, d) {
  const ba  = d.bloco_a   || {};
  const bbc = d.bloco_b_c || [];
  const bd  = d.bloco_d   || {};
  const be  = d.bloco_e   || {};
  const bf  = d.bloco_f   || {};
  const cl  = d.checklist || [];

  const runRow = el('div', 'run-btn-row');
  runRow.innerHTML = `
    <button class="run-btn" onclick="runPasso4()">▶ Recalcular DCF</button>
    <span class="run-status">Propaga edições dos passos 1 e 2 e recalcula.</span>
  `;
  container.appendChild(runRow);

  const kpiDiv = el('div', 'kpi-row');
  for (const [lbl, val, cls] of [
    ['WACC',             fPct(ba.WACC_0),         'blue'],
    ['Beta Alavancado',  fM(ba.Beta_L) + 'x',     'blue'],
    ['Ke (Custo Equity)',fPct(ba.Ke),              'purple'],
    ['VP FCF 10 anos',  'R$ ' + fM(d.VP_total) + 'M', 'blue'],
    ['Valor Terminal',  'R$ ' + fM(bd.VP_VT) + 'M',   'purple'],
    ['% VT / Total',    fPct(bd.pct_vt / 100),    'purple'],
  ]) {
    kpiDiv.innerHTML += `<div class="kpi-card"><div class="kpi-label">${lbl}</div><div class="kpi-val ${cls}">${val}</div></div>`;
  }
  container.appendChild(kpiDiv);

  const st1 = el('div', 'section-title'); st1.textContent = 'Projeções de Fluxo de Caixa (10 anos)';
  container.appendChild(st1);

  const maxVP = Math.max(...bbc.map(r => r.VP_FCFF));
  const tw = el('div', 'table-wrap');
  let tbl = `<table><thead><tr>
    <th>Ano</th><th style="text-align:right">g</th>
    <th style="text-align:right">Receita</th><th style="text-align:right">Margem</th>
    <th style="text-align:right">NOPAT</th><th style="text-align:right">FCFF</th>
    <th style="text-align:right">WACC</th><th>VP FCFF</th>
  </tr></thead><tbody>`;
  for (const r of bbc) {
    const barPct = (r.VP_FCFF / maxVP * 100).toFixed(1);
    tbl += `<tr>
      <td style="font-weight:600">${r.t}</td>
      <td class="val-pct">${fPct(r.g)}</td>
      <td class="val-num">${fM(r.Rev)}M</td>
      <td class="val-pct">${fPct(r.Mg)}</td>
      <td class="val-num">${fM(r.NOPAT)}M</td>
      <td class="val-num">${fM(r.FCFF)}M</td>
      <td class="val-pct">${fPct(r.WACC)}</td>
      <td class="bar-cell">
        <div class="bar-wrap">
          <div class="bar-bg"><div class="bar-fill" style="width:${barPct}%"></div></div>
          <span style="font-size:12px;font-weight:600;white-space:nowrap">${fM(r.VP_FCFF)}M</span>
        </div>
      </td>
    </tr>`;
  }
  tbl += '</tbody></table>';
  tw.innerHTML = tbl;
  container.appendChild(tw);

  const st2 = el('div', 'section-title'); st2.textContent = 'Valor da Empresa → Preço por Ação';
  container.appendChild(st2);

  const bridge = el('div', 'bridge');
  for (const [lbl, val, isTot] of [
    ['VP Fluxos (10 anos)',    d.VP_total,       false],
    ['+ Valor Terminal (VP)',  bd.VP_VT,         false],
    ['= Valor Operacional',    be.Valor_op,      true],
    ['+ Caixa',                bf.Caixa,         false],
    ['+ Ativos Não-Op.',       bf.AtvNOp,        false],
    ['- Dívida Bruta',         -bf.D,            false],
    ['- Minority Interest',    bf.MinInt,        false],
    ['= Equity Value',         bf.Equity_Value,  true],
  ]) {
    const cls  = isTot ? 'total' : '';
    const vcls = val >= 0 ? 'positive' : 'negative';
    bridge.innerHTML += `<div class="bridge-row ${cls}">
      <span class="bridge-label">${lbl}</span>
      <span class="bridge-val ${cls ? '' : vcls}">R$ ${fM(val)}M</span>
    </div>`;
  }
  bridge.innerHTML += `
    <div class="bridge-row" style="font-size:13px;color:var(--muted)">
      <span class="bridge-label indent">÷ ${fM(bf.Shares)}M ações</span><span></span>
    </div>
    <div class="bridge-row final">
      <span>Valor / ação</span><span>${fBRL(bf.Valor_acao)}</span>
    </div>
    <div class="bridge-row" style="border-top:none;padding-top:4px">
      <span class="bridge-label" style="font-size:12px">Preço de mercado</span>
      <span style="font-size:13px;color:var(--muted)">${fBRL(bf.P)}</span>
    </div>
  `;
  container.appendChild(bridge);

  if (cl.length) {
    const st3 = el('div', 'section-title'); st3.textContent = 'Checklist de Validação';
    container.appendChild(st3);
    const list = el('ul', 'checklist');
    for (const item of cl) {
      const li = el('li', `check-item ${item.ok ? 'check-ok' : 'check-fail'}`);
      li.innerHTML = `
        <span class="check-icon">${item.ok ? '✓' : '✗'}</span>
        <div>
          <div class="check-nome">${item.nome}</div>
          <div class="check-detalhe">${item.detalhe}</div>
        </div>
      `;
      list.appendChild(li);
    }
    container.appendChild(list);
  }
}

// ─── Passo 5 — Sensibilidade ──────────────────────────────────────────────────
function renderP5(container, d) {
  if (!d) {
    container.innerHTML = `
      <div class="pending-box">
        <div class="pending-icon">📊</div>
        <div class="pending-title">Análise de sensibilidade pendente</div>
        <div class="pending-sub">Execute o pipeline com passo 5 para gerar os cenários.</div>
      </div>
    `;
    return;
  }

  const p5     = d.passo5 || d;
  const precoM = S.data[0]?.mercado?.P?.valor ?? S.data[3]?.bloco_f?.P;

  function diffBadge(intrinsic) {
    if (intrinsic == null || precoM == null) return '';
    const pct  = (precoM - intrinsic) / Math.abs(intrinsic) * 100;
    const css  = pct > 2 ? 'color:var(--red)' : pct < -2 ? 'color:var(--green)' : 'color:var(--muted)';
    return `<div class="cenario-diff" style="${css}">${pct > 0 ? '+' : ''}${pct.toFixed(1)}% vs mercado</div>`;
  }

  const st1 = el('div', 'section-title'); st1.textContent = 'Cenários de Valuation';
  container.appendChild(st1);

  const cGrid = el('div', 'cenarios-grid');
  for (const { cls, nome, val } of [
    { cls: 'bear', nome: 'Bear', val: p5.valor_acao_bear },
    { cls: 'base', nome: 'Base', val: p5.valor_acao_base },
    { cls: 'bull', nome: 'Bull', val: p5.valor_acao_bull },
  ]) {
    const isNeg = val != null && val < 0;
    cGrid.innerHTML += `
      <div class="cenario-card ${cls}">
        <div class="cenario-name">${nome}</div>
        <div class="cenario-val">${isNeg ? '-' : ''}${fBRL(Math.abs(val ?? 0))}</div>
        <div class="cenario-vs">vs mercado ${precoM != null ? fBRL(precoM) : '—'}</div>
        ${diffBadge(val)}
      </div>
    `;
  }
  container.appendChild(cGrid);

  const mais = p5.premissa_mais_sensivel;
  const st2  = el('div', 'section-title'); st2.textContent = 'Breakeven — valor necessário para justificar o preço atual';
  container.appendChild(st2);

  const bGrid = el('div', 'breakeven-grid');
  for (const [label, val, key, type] of [
    ['g Perpetuidade', p5.g_perp_breakeven,  'g_perp_breakeven',  'pct'],
    ['WACC Estimado',  p5.WACC_est_breakeven, 'WACC_est_breakeven','pct'],
    ['Margem Alvo',    p5.Mg_alvo_breakeven,  'Mg_alvo_breakeven', 'pct'],
    ['g Anos 2-5',     p5.g2_5_breakeven,     'g2_5_breakeven',    'pct'],
  ]) {
    if (val == null) continue;
    const isMais = mais && key.startsWith(mais.replace('premissas_analiticas.', '').replace(/\..+/, ''));
    bGrid.innerHTML += `
      <div class="breakeven-card ${isMais ? 'highlight' : ''}">
        <div class="breakeven-label">${label}</div>
        <div class="breakeven-val">${type === 'pct' ? fPct2(val) : fM(val)}</div>
        ${isMais ? '<div class="breakeven-badge">⚡ Mais sensível</div>' : ''}
      </div>
    `;
  }
  container.appendChild(bGrid);

  if (p5.conclusao) {
    const st3 = el('div', 'section-title'); st3.textContent = 'Conclusão';
    container.appendChild(st3);
    const box = el('div', 'conclusao-box');
    for (const line of p5.conclusao.split(/\n/).map(l => l.trim()).filter(Boolean)) {
      const match = line.match(/^(\d+)\.\s*(.+)$/);
      const item  = el('div', 'conclusao-item');
      item.innerHTML = match
        ? `<span class="conclusao-num">${match[1]}.</span><span>${match[2]}</span>`
        : `<span>${line}</span>`;
      box.appendChild(item);
    }
    container.appendChild(box);
  }
}

// ─── Atualiza hero após edição ────────────────────────────────────────────────
function refreshHero() {
  const p1     = S.data[0];
  const p4     = S.data[3];
  const precoM = p1?.mercado?.P?.valor ?? p4?.bloco_f?.P;
  const introV = p4?.bloco_f?.Valor_acao;

  const mEl = document.querySelector('.hero-price-value.market');
  if (mEl && precoM != null) mEl.textContent = fBRL(precoM);

  const verdict = document.querySelector('.hero-verdict');
  if (!verdict || precoM == null || introV == null) return;
  const pct    = (precoM - introV) / introV;
  const pctAbs = Math.abs(pct * 100).toFixed(1);
  const pctEl  = verdict.querySelector('.hero-verdict-pct');
  const lblEl  = verdict.querySelector('.hero-verdict-label');
  if (pctEl) {
    pctEl.className  = 'hero-verdict-pct ' + (pct > 0.02 ? 'overvalued' : pct < -0.02 ? 'undervalued' : '');
    pctEl.textContent = pct > 0.02 ? `+${pctAbs}% premium` : pct < -0.02 ? `-${pctAbs}% desconto` : 'Preço justo';
  }
  if (lblEl) lblEl.textContent = pct > 0.02 ? 'Sobreprecificado' : pct < -0.02 ? 'Subprecificado' : 'Avaliação';
}

// ─── Edição inline ────────────────────────────────────────────────────────────
function attachEditListeners() {
  document.querySelectorAll('.editable-wrap').forEach(wrap => {
    const displayEl = wrap.querySelector('.ev');
    const editBtn   = wrap.querySelector('.edit-btn');
    if (!displayEl || !editBtn) return;
    displayEl.addEventListener('click', () => openEdit(wrap, displayEl));
    editBtn.addEventListener('click', e => { e.stopPropagation(); openEdit(wrap, displayEl); });
  });
}

function openEdit(wrap, displayEl) {
  if (wrap.querySelector('.edit-input')) return;

  const passoN = parseInt(wrap.dataset.passo);
  const path   = wrap.dataset.path.split('.');
  const type   = wrap.dataset.type || 'text';
  const rawVal = getDeep(S.data[passoN - 1], path);

  const inputVal = type === 'pct' ? (rawVal * 100).toFixed(4) : rawVal != null ? String(rawVal) : '';

  const input     = el('input'); input.type = 'text'; input.className = 'edit-input'; input.value = inputVal;
  const saveBtn   = el('button', 'save-btn', '✓');
  const cancelBtn = el('button', 'cancel-btn', '✗');
  const origContent = wrap.innerHTML;

  wrap.innerHTML = '';
  wrap.append(input, saveBtn, cancelBtn);
  input.focus(); input.select();

  const doSave = async () => {
    let newVal = input.value.trim().replace(',', '.');
    if (type === 'number' || type === 'pct') {
      newVal = parseFloat(newVal);
      if (isNaN(newVal)) { input.style.borderColor = 'var(--red)'; return; }
      if (type === 'pct') newVal = newVal / 100;
    }
    try {
      setDeep(S.data[passoN - 1], path, newVal);
      await savePasso(S.ticker, passoN);
      wrap.innerHTML = origContent;
      const newDisplay = wrap.querySelector('.ev');
      if (newDisplay) {
        newDisplay.textContent = (type === 'pct' ? fPct2 : type === 'number' ? fM : String)(newVal);
      }
      wrap.classList.add('saved');
      setTimeout(() => wrap.classList.remove('saved'), 1200);
      refreshHero();
      attachEditListeners();
    } catch {
      wrap.innerHTML = origContent;
      wrap.classList.add('error');
      setTimeout(() => wrap.classList.remove('error'), 1200);
      attachEditListeners();
    }
  };

  const doCancel = () => { wrap.innerHTML = origContent; attachEditListeners(); };

  saveBtn.addEventListener('click', doSave);
  cancelBtn.addEventListener('click', doCancel);
  input.addEventListener('keydown', e => {
    if (e.key === 'Enter')  { e.preventDefault(); doSave(); }
    if (e.key === 'Escape') { e.preventDefault(); doCancel(); }
  });
}

// ─── Breadcrumb ───────────────────────────────────────────────────────────────
function setBreadcrumb(ticker) {
  const bc = document.getElementById('breadcrumb');
  if (!ticker) { bc.innerHTML = ''; return; }
  bc.innerHTML = `
    <a class="back-link" href="#">← Empresas</a>
    <span class="bc-sep">/</span>
    <span class="bc-current">${ticker}</span>
  `;
}
