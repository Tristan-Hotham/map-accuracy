// map-accuracy: distortion grid explorer (canvas) and comparison chart. Data: data/site.json (built by code/04_results.py).
(function () {
  'use strict';
  const COL = { 'world map': '#B4442E', 'route map': '#C98A2B', 'sea chart': '#2F6A9E', 'survey': '#3E7D5A' };
  const PAPER = '#F3ECDA', INK = '#2B2119', MUT = '#6E604E', LAND = '#E4D5B0', REAL = 'rgba(120,100,70,.28)';
  const $ = id => document.getElementById(id);
  let S = null, cur = null, t = 1, view = { cx: 0, cy: 0, s: 100 }, dpr = 1, W = 0, H = 0, hit = [], playing = false;
  const L = { land: true, real: true, grid: true, area: false, pts: true, arr: false, hull: true, lab: true };

  // ---------- chrome ----------
  $('theme').addEventListener('click', () => { const r = document.documentElement, d = r.dataset.theme ? r.dataset.theme === 'dark' : matchMedia('(prefers-color-scheme: dark)').matches; r.dataset.theme = d ? 'light' : 'dark'; drawChart(); });
  const ct = $('cartouche'); const fold = f => { ct.classList.toggle('folded', f); $('ctToggle').setAttribute('aria-expanded', String(!f)); };
  if (innerWidth < 600) fold(true);
  $('ctToggle').addEventListener('click', () => fold(!ct.classList.contains('folded')));
  $('ctFold').addEventListener('click', () => fold(true));
  const lp = $('lp'), lb = $('lyrBtn');
  lb.addEventListener('click', () => { const o = !lp.classList.contains('open'); lp.classList.toggle('open', o); lb.setAttribute('aria-expanded', String(o)); });
  const CB = { lyLand: 'land', lyReal: 'real', lyGrid: 'grid', lyArea: 'area', lyPts: 'pts', lyArr: 'arr', lyHull: 'hull', lyLab: 'lab' };
  Object.entries(CB).forEach(([id, k]) => $(id).addEventListener('change', e => { L[k] = e.target.checked; syncChips(); draw(); keys(); }));
  const CHIP = { grid: 'grid', arrows: 'arr', area: 'area' };
  document.querySelectorAll('.chip[data-v]').forEach(b => b.addEventListener('click', () => {
    const k = CHIP[b.dataset.v]; L[k] = !L[k];
    Object.entries(CB).forEach(([id, kk]) => { $(id).checked = L[kk]; }); syncChips(); draw(); keys();
  }));
  function syncChips() { document.querySelectorAll('.chip[data-v]').forEach(b => b.setAttribute('aria-pressed', String(!!L[CHIP[b.dataset.v]]))); }

  // ---------- canvas ----------
  const cv = $('cv'), cx = cv.getContext('2d'), pane = $('mapWrap');
  function resize() {
    dpr = Math.min(window.devicePixelRatio || 1, 2); const r = pane.getBoundingClientRect(); W = r.width; H = r.height;
    cv.width = Math.round(W * dpr); cv.height = Math.round(H * dpr); if (cur) draw();
  }
  window.addEventListener('resize', () => { resize(); if (cur) fit(false); });
  const X = x => (W / 2 + (x - view.cx) * view.s), Y = y => (H / 2 - (y - view.cy) * view.s);
  function fit() {
    const h = cur.hull; let x0 = 1e9, x1 = -1e9, y0 = 1e9, y1 = -1e9;
    h.forEach(p => { x0 = Math.min(x0, p[0]); x1 = Math.max(x1, p[0]); y0 = Math.min(y0, p[1]); y1 = Math.max(y1, p[1]); });
    let bx0 = 10, bx1 = W - 10, by0 = innerWidth < 1000 ? 150 : 150, by1 = H - 175;
    if (W >= 1000) { bx0 = 375; bx1 = W - 300; by0 = 40; }
    if (bx1 - bx0 < 300) { bx0 = 10; bx1 = W - 10; }
    view.s = Math.min((bx1 - bx0) / (x1 - x0), (by1 - by0) / (y1 - y0));
    view.cx = (x0 + x1) / 2 - ((bx0 + bx1) / 2 - W / 2) / view.s; view.cy = (y0 + y1) / 2 + ((by0 + by1) / 2 - H / 2) / view.s;
  }
  const ramp = v => { // log2 areal scale -> colour (blue shrunk, red enlarged)
    const c = Math.max(-1, Math.min(1, v / 2)); const a = [47, 106, 158], m = [201, 194, 180], b = [180, 68, 46];
    const f = c < 0 ? -c : c, e = c < 0 ? a : b; return `rgba(${Math.round(m[0] + (e[0] - m[0]) * f)},${Math.round(m[1] + (e[1] - m[1]) * f)},${Math.round(m[2] + (e[2] - m[2]) * f)},.6)`;
  };
  function path(arr, close) {
    cx.beginPath(); arr.forEach((p, i) => { const x = X(p[0] + t * p[2]), y = Y(p[1] + t * p[3]); i ? cx.lineTo(x, y) : cx.moveTo(x, y); }); if (close) cx.closePath();
  }
  function draw() {
    if (!cur) return;
    cx.setTransform(dpr, 0, 0, dpr, 0, 0); cx.fillStyle = PAPER; cx.fillRect(0, 0, W, H);
    const col = COL[cur.purpose];
    if (L.land) { cx.fillStyle = LAND; cur.land.forEach(l => { path(l, true); cx.fill(); }); cx.strokeStyle = 'rgba(150,120,70,.55)'; cx.lineWidth = .7; cur.coast.forEach(l => { path(l, false); cx.stroke(); }); }
    if (L.area) { cur.cells.forEach(c => { const g = .25; const P = [[c[0], c[1], c[3], c[4]], [c[0] + g, c[1], c[5], c[6]], [c[0] + g, c[1] + g, c[7], c[8]], [c[0], c[1] + g, c[9], c[10]]]; cx.fillStyle = ramp(c[2]); path(P, true); cx.fill(); }); }
    if (L.hull) { cx.setLineDash([5, 4]); cx.strokeStyle = 'rgba(110,96,78,.7)'; cx.lineWidth = 1.2; cx.beginPath(); cur.hull.forEach((p, i) => i ? cx.lineTo(X(p[0]), Y(p[1])) : cx.moveTo(X(p[0]), Y(p[1]))); cx.stroke(); cx.setLineDash([]); }
    if (L.real) { cx.strokeStyle = REAL; cx.lineWidth = 1; cur.grid.forEach(l => { cx.beginPath(); l.forEach((p, i) => i ? cx.lineTo(X(p[0]), Y(p[1])) : cx.moveTo(X(p[0]), Y(p[1]))); cx.stroke(); }); }
    if (L.grid) { cx.strokeStyle = col; cx.lineWidth = 1.6; cur.grid.forEach(l => { path(l, false); cx.stroke(); }); }
    if (L.arr) { cx.strokeStyle = 'rgba(43,33,25,.55)'; cx.lineWidth = 1; cur.pts.forEach(p => { cx.beginPath(); cx.moveTo(X(p[0]), Y(p[1])); cx.lineTo(X(p[0] + p[2]), Y(p[1] + p[3])); cx.stroke(); }); }
    hit = [];
    if (L.pts) {
      const r = Math.max(2.2, Math.min(4.5, 900 / Math.sqrt(cur.pts.length) / 40 + view.s / 400));
      cur.pts.forEach((p, i) => { const x = X(p[0] + t * p[2]), y = Y(p[1] + t * p[3]); hit.push([x, y, i]);
        cx.beginPath(); cx.arc(x, y, r + 1.2, 0, 7); cx.fillStyle = '#fff'; cx.fill(); cx.beginPath(); cx.arc(x, y, r, 0, 7); cx.fillStyle = INK; cx.fill(); });
    }
    if (L.lab) {
      const h = cur.home; const hx = X(h[1] + t * (h[3] || 0)), hy = Y(h[2] + t * (h[4] || 0));
      cx.beginPath(); cx.arc(hx, hy, 7, 0, 7); cx.strokeStyle = '#B4442E'; cx.lineWidth = 2.5; cx.stroke();
      label('home: ' + h[0], hx + 10, hy - 10, '#B4442E', 'bold 14px "Source Serif 4",Georgia,serif');
      const top = cur.pts.map((p, i) => [p[4], i]).sort((a, b) => b[0] - a[0]).slice(0, 4);
      const used = [[hx, hy]];
      top.forEach(([e, i]) => { const p = cur.pts[i]; const x = X(p[0] + t * p[2]), y = Y(p[1] + t * p[3]);
        if (used.some(u => Math.abs(u[0] - x) < 170 && Math.abs(u[1] - y) < 18) || x > W - 60) return; used.push([x, y]);
        label(`${p[5].split(' (')[0]}: ${fmtKm(e)}`, x + 7, y + 4, INK, '12px "IBM Plex Mono",monospace'); });
    }
  }
  function label(s, x, y, c, f) { cx.font = f; cx.lineWidth = 4; cx.strokeStyle = 'rgba(243,236,218,.95)'; cx.lineJoin = 'round'; cx.strokeText(s, x, y); cx.fillStyle = c; cx.fillText(s, x, y); }
  const fmtKm = v => v >= 10 ? Math.round(v).toLocaleString('en-GB') + ' km' : (v >= 1 ? v.toFixed(1) : v.toFixed(2)) + ' km';

  function keys() {
    const m = cur, col = COL[m.purpose];
    $('mkeys').innerHTML = `<b class="t">${m.name}</b><div>${m.date} · ${m.purpose}</div>
      <table><tr class="kx"><td>places</td><td>${m.n.toLocaleString('en-GB')}</td></tr><tr><td>median error</td><td>${fmtKm(m.km)}</td></tr>
      <tr><td>share of size</td><td>${m.rel}%<span class="kx"> (${m.rello} to ${m.relhi})</span></td></tr><tr class="kx"><td>vs neighbours</td><td>${m.loc}%</td></tr>
      <tr class="kx"><td>turned</td><td>${Math.abs(m.turn) > 170 ? 'south at top' : Math.abs(m.turn) < 0.5 ? 'north up' : Math.abs(Math.round(m.turn)) + '° ' + (m.turn >= 0 ? 'anticlockwise' : 'clockwise')}</td></tr></table>
      <div class="row kx"><span class="sw" style="background:${col}"></span>grid as the map draws it</div>
      <div class="row kx"><span class="sw" style="background:rgba(120,100,70,.5)"></span>regular grid on the real ground</div>
      <div class="row kx"><span class="dt"></span>a place measured; ring: the map's home</div>
      ${L.area ? '<div class="kx">Stretch of each cell</div><div class="ramp kx"></div><div class="ends kx"><span>shrunk 4x</span><span>same</span><span>4x bigger</span></div>' : ''}
      <div class="kx" style="color:#6E604E;margin-top:4px">Grid reliable only near places (dashed outline). <a href="https://maps.tristanhotham.com/${m.slug}/" style="color:#B4442E">Full study</a></div>`;
  }
  function select(k, keepView) {
    cur = S.maps.find(m => m.k === k); if (!cur) return;
    document.querySelectorAll('.thumb').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.k === k)));
    if (!keepView) fit(); keys(); draw(); $('tip').style.display = 'none';
  }

  // thumbnails
  function thumbs() {
    const box = $('thumbs');
    S.maps.forEach(m => {
      const b = document.createElement('button'); b.className = 'thumb'; b.dataset.k = m.k; b.type = 'button'; b.setAttribute('aria-pressed', 'false');
      b.innerHTML = `<canvas width="176" height="116"></canvas>${m.short}<small>${m.date.split(' (')[0]} · ${m.rel}%</small>`;
      box.appendChild(b); b.addEventListener('click', () => select(m.k));
      const c = b.querySelector('canvas').getContext('2d'); let x0 = 1e9, x1 = -1e9, y0 = 1e9, y1 = -1e9;
      m.hull.forEach(p => { x0 = Math.min(x0, p[0]); x1 = Math.max(x1, p[0]); y0 = Math.min(y0, p[1]); y1 = Math.max(y1, p[1]); });
      const s = Math.min(164 / (x1 - x0), 104 / (y1 - y0)), ox = 88 - (x0 + x1) / 2 * s, oy = 58 + (y0 + y1) / 2 * s;
      c.fillStyle = PAPER; c.fillRect(0, 0, 176, 116); c.fillStyle = LAND;
      m.land.forEach(l => { c.beginPath(); l.forEach((p, i) => { const x = ox + (p[0] + p[2]) * s, y = oy - (p[1] + p[3]) * s; i ? c.lineTo(x, y) : c.moveTo(x, y); }); c.fill(); });
      c.strokeStyle = COL[m.purpose]; c.lineWidth = 1;
      m.grid.forEach(l => { c.beginPath(); l.forEach((p, i) => { const x = ox + (p[0] + p[2]) * s, y = oy - (p[1] + p[3]) * s; i ? c.lineTo(x, y) : c.moveTo(x, y); }); c.stroke(); });
    });
  }

  // pan, zoom, hover
  let drag = null, pinch = null;
  cv.addEventListener('pointerdown', e => { drag = { x: e.clientX, y: e.clientY, cx: view.cx, cy: view.cy, moved: false }; cv.setPointerCapture(e.pointerId); cv.classList.add('drag'); });
  cv.addEventListener('pointermove', e => {
    if (drag && !pinch) { const dx = e.clientX - drag.x, dy = e.clientY - drag.y; if (Math.abs(dx) + Math.abs(dy) > 3) drag.moved = true; view.cx = drag.cx - dx / view.s; view.cy = drag.cy + dy / view.s; draw(); }
    else if (e.pointerType === 'mouse') hover(e);
  });
  cv.addEventListener('pointerup', e => { cv.classList.remove('drag'); if (drag && !drag.moved) hover(e, true); drag = null; });
  cv.addEventListener('wheel', e => { e.preventDefault(); zoomAt(e.offsetX, e.offsetY, Math.exp(-e.deltaY * 0.0015)); }, { passive: false });
  cv.addEventListener('touchstart', e => { if (e.touches.length === 2) { const [a, b] = e.touches; pinch = { d: Math.hypot(a.clientX - b.clientX, a.clientY - b.clientY), s: view.s }; } }, { passive: true });
  cv.addEventListener('touchmove', e => { if (pinch && e.touches.length === 2) { const [a, b] = e.touches; const r = cv.getBoundingClientRect(); const d = Math.hypot(a.clientX - b.clientX, a.clientY - b.clientY);
    zoomAt((a.clientX + b.clientX) / 2 - r.left, (a.clientY + b.clientY) / 2 - r.top, pinch.s * d / pinch.d / view.s); } }, { passive: true });
  cv.addEventListener('touchend', () => { pinch = null; });
  function zoomAt(px, py, f) { const wx = view.cx + (px - W / 2) / view.s, wy = view.cy - (py - H / 2) / view.s; view.s = Math.max(5, Math.min(view.s * f, 40000)); view.cx = wx - (px - W / 2) / view.s; view.cy = wy + (py - H / 2) / view.s; draw(); }
  function hover(e, click) {
    const r = cv.getBoundingClientRect(), x = e.clientX - r.left, y = e.clientY - r.top; let best = null, bd = click ? 22 : 12;
    hit.forEach(h => { const d = Math.hypot(h[0] - x, h[1] - y); if (d < bd) { bd = d; best = h; } });
    const tip = $('tip'); if (!best) { if (click) tip.style.display = 'none'; else if (!tip.dataset.pin) tip.style.display = 'none'; return; }
    showTip(best[2], best[0], best[1], click);
  }
  function showTip(i, x, y, pin) {
    const p = cur.pts[i], tip = $('tip');
    tip.innerHTML = `<b>${p[5]}</b>${p[6] ? p[6] + '<br>' : ''}${cur.short}: drawn ${fmtKm(p[4])} from where it is, after the best fit`;
    tip.style.display = 'block'; tip.dataset.pin = pin ? '1' : '';
    const tw = tip.offsetWidth, th = tip.offsetHeight; tip.style.left = Math.min(W - tw - 8, Math.max(8, x + 12)) + 'px'; tip.style.top = Math.min(H - th - 8, Math.max(8, y - th - 10)) + 'px';
  }

  // slider and play
  const sl = $('t');
  function setT(v) { t = v; sl.value = Math.round(v * 100); $('tLab').textContent = v >= .995 ? 'as drawn' : (v <= .005 ? 'real ground' : Math.round(v * 100) + '%'); draw(); }
  sl.addEventListener('input', () => { playing = false; $('play').textContent = 'Play'; setT(sl.value / 100); });
  $('play').addEventListener('click', () => {
    if (playing) { playing = false; $('play').textContent = 'Play'; return; }
    playing = true; $('play').textContent = 'Pause'; const t0 = performance.now(), dur = 5200;
    const step = now => { if (!playing) return; const u = ((now - t0) % dur) / dur; setT(0.5 - 0.5 * Math.cos(u * 2 * Math.PI)); requestAnimationFrame(step); };
    requestAnimationFrame(step);
  });

  // search
  const q = $('q'), sug = $('sug'); let IDX = [], opts = [], sel = -1;
  q.addEventListener('input', () => {
    const v = q.value.trim().toLowerCase(); sug.innerHTML = ''; sel = -1;
    if (v.length < 2) { sug.style.display = 'none'; return; }
    opts = IDX.filter(o => o.n.toLowerCase().includes(v)).sort((a, b) => (a.n.toLowerCase().startsWith(v) ? 0 : 1) - (b.n.toLowerCase().startsWith(v) ? 0 : 1)).slice(0, 12);
    opts.forEach((o, j) => { const li = document.createElement('li'); li.setAttribute('role', 'option'); li.innerHTML = `${o.n} <span>${o.m}</span>`;
      li.addEventListener('mousedown', ev => { ev.preventDefault(); go(o); }); sug.appendChild(li); });
    sug.style.display = opts.length ? 'block' : 'none';
  });
  q.addEventListener('keydown', e => { const lis = sug.querySelectorAll('li'); if (!lis.length) return;
    if (e.key === 'ArrowDown' || e.key === 'ArrowUp') { e.preventDefault(); sel = (sel + (e.key === 'ArrowDown' ? 1 : -1) + lis.length) % lis.length; lis.forEach((l, j) => l.setAttribute('aria-selected', String(j === sel))); }
    if (e.key === 'Enter') { e.preventDefault(); go(opts[Math.max(0, sel)]); } if (e.key === 'Escape') sug.style.display = 'none'; });
  q.addEventListener('blur', () => setTimeout(() => { sug.style.display = 'none'; }, 150));
  function go(o) {
    sug.style.display = 'none'; q.value = o.n; select(o.k, true); fit(); const p = cur.pts[o.i];
    view.s *= 2.2; view.cx = p[0] + t * p[2]; view.cy = p[1] + t * p[3]; draw(); showTip(o.i, X(view.cx), Y(view.cy), true);
  }

  // ---------- chart ----------
  let metric = 'rel';
  document.querySelectorAll('#chart .ctl button').forEach(b => b.addEventListener('click', () => { metric = b.dataset.m; document.querySelectorAll('#chart .ctl button').forEach(x => x.setAttribute('aria-pressed', String(x === b))); drawChart(); }));
  function drawChart() {
    if (!S) return; const svg = $('chartSvg'); const w = 700, h = 380, l = 58, r = 22, tp = 14, bt = 44;
    const rows = S.maps.map(m => ({ k: m.k, s: m.short, y: m.year, p: m.purpose, h: m.supp, v: metric === 'rel' ? m.rel : metric === 'loc' ? m.loc : m.km,
      lo: metric === 'rel' ? m.rello : metric === 'loc' ? m.loclo : m.kmlo, hi: metric === 'rel' ? m.relhi : metric === 'loc' ? m.lochi : m.kmhi }))
      .concat(S.sets.map(m => ({ k: null, s: m.short, y: m.year, p: 'survey', h: true, v: metric === 'rel' ? m.rel : metric === 'loc' ? m.loc : m.km,
        lo: metric === 'rel' ? m.rello : metric === 'loc' ? m.loclo : null, hi: metric === 'rel' ? m.relhi : metric === 'loc' ? m.lochi : null })));
    const vals = rows.flatMap(d => [d.v, d.lo || d.v, d.hi || d.v]); const y0 = Math.log10(Math.min(...vals) * 0.7), y1 = Math.log10(Math.max(...vals) * 1.4);
    const sx = x => l + (x - 50) / 1850 * (w - l - r), sy = v => tp + (y1 - Math.log10(v)) / (y1 - y0) * (h - tp - bt);
    let o = '';
    const ticks = [0.2, 0.5, 1, 2, 5, 10, 20, 50, 100, 200, 500, 1000].filter(v => Math.log10(v) >= y0 && Math.log10(v) <= y1);
    ticks.forEach(v => { o += `<line x1="${l}" x2="${w - r}" y1="${sy(v)}" y2="${sy(v)}" stroke="currentColor" stroke-opacity=".12"/><text x="${l - 6}" y="${sy(v) + 4}" text-anchor="end" font-size="11">${v}${metric === 'km' ? '' : '%'}</text>`; });
    [200, 500, 800, 1100, 1400, 1700].forEach(x => { o += `<text x="${sx(x)}" y="${h - bt + 18}" text-anchor="middle" font-size="11">${x}</text>`; });
    o += `<text x="${(l + w - r) / 2}" y="${h - 6}" text-anchor="middle" font-size="11">date of the map</text>`;
    o += `<text transform="translate(13 ${(tp + h - bt) / 2}) rotate(-90)" text-anchor="middle" font-size="11">${metric === 'rel' ? 'error, % of the area\'s size' : metric === 'loc' ? 'error, % of distance to neighbours' : 'median error, km'}</text>`;
    const OFF = { pisana: [-8, 16, 'end'], catalan: [8, 16, 'start'], idrisi: [-8, -8, 'end'], saxton: [-8, -8, 'end'], ino: [-8, -8, 'end'] };
    rows.forEach(d => { const c = COL[d.p], x = sx(d.y), y = sy(d.v);
      if (d.lo) o += `<line x1="${x}" x2="${x}" y1="${sy(d.lo)}" y2="${sy(d.hi)}" stroke="${c}" stroke-width="2.5" stroke-opacity=".6"/>`;
      o += `<circle cx="${x}" cy="${y}" r="${d.h ? 5.5 : 7}" fill="${d.h ? 'var(--card)' : c}" stroke="${c}" stroke-width="2.2" ${d.k ? `data-k="${d.k}" style="cursor:pointer"` : ''}><title>${d.s}: ${d.v}${metric === 'km' ? ' km' : '%'}</title></circle>`;
      const of = OFF[d.k] || (d.s === 'Ino sheets' ? [-9, -6, 'end'] : d.s === 'Saxton sheets' ? [8, 14, 'start'] : [9, -7, 'start']);
      o += `<text class="lab" x="${x + of[0]}" y="${y + of[1]}" text-anchor="${of[2]}" font-size="12.5">${d.s}</text>`; });
    svg.innerHTML = o;
    svg.querySelectorAll('circle[data-k]').forEach(cn => cn.addEventListener('click', () => { select(cn.dataset.k); $('mapWrap').scrollIntoView({ behavior: 'smooth' }); }));
  }
  function table() {
    const tb = document.querySelector('#tbl tbody');
    tb.innerHTML = S.maps.concat(S.sets).map(m => `<tr><td>${m.name}</td><td>${m.date}</td><td class="r">${m.n.toLocaleString('en-GB')}</td><td class="r">${m.km}</td><td class="r">${m.rel}%</td><td class="r">${m.loc}%</td></tr>`).join('');
  }

  // ---------- go ----------
  resize();
  fetch('data/site.json').then(r => r.json()).then(d => {
    S = d; $('nojs').style.display = 'none';
    S.maps.forEach(m => m.pts.forEach((p, i) => IDX.push({ n: p[5], m: m.short, k: m.k, i })));
    thumbs(); table(); drawChart();
    const want = new URLSearchParams(location.search).get('m');
    select(S.maps.some(m => m.k === want) ? want : 'hereford');
    window.__ready = true;
  }).catch(e => { $('nojs').textContent = 'The map data could not be loaded.'; console.error(e); });
})();
