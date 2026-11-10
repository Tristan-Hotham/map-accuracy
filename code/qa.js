// QA: serve the studies folder, open index.html at desktop and phone widths, log console errors and save screenshots to qa/.
// Usage: PW=/path/to/playwright node code/qa.js. Google Fonts and site-nav are skipped.
const fs = require('fs'), path = require('path'), http = require('http');
const { chromium } = require(process.env.PW || 'playwright');
const ROOT = path.resolve(__dirname, '..'), STUDIES = path.dirname(ROOT), SLUG = path.basename(ROOT);
const TYPES = { '.html': 'text/html', '.js': 'application/javascript', '.json': 'application/json', '.png': 'image/png', '.css': 'text/css', '.jpg': 'image/jpeg' };
const PORT = 8800 + Math.floor(Math.random() * 90);
const srv = http.createServer((q, s) => { const f = path.join(STUDIES, decodeURIComponent(q.url.split('?')[0]));
  fs.readFile(f, (e, b) => { if (e) { s.writeHead(404); s.end(); return; } s.writeHead(200, { 'content-type': TYPES[path.extname(f)] || 'application/octet-stream' }); s.end(b); }); }).listen(PORT);
const PAGE = `http://localhost:${PORT}/${SLUG}/index.html`;
const SHOTS = [
  { out: 'qa/desktop.png', w: 1280, h: 800 },
  { out: 'qa/desktop_peutinger_area.png', w: 1280, h: 800, q: 'm=peutinger', eval: "document.querySelector('.chip[data-v=area]').click();document.getElementById('lyrBtn').click()" },
  { out: 'qa/desktop_search.png', w: 1280, h: 800, eval: "const q=document.querySelector('#q');q.value='Dover';q.dispatchEvent(new Event('input'));document.querySelector('#sug li').dispatchEvent(new MouseEvent('mousedown'))" },
  { out: 'qa/desktop_t0.png', w: 1280, h: 800, q: 'm=ptolemy', eval: "const s=document.getElementById('t');s.value=30;s.dispatchEvent(new Event('input'));document.querySelector('.chip[data-v=arrows]').click()" },
  { out: 'qa/phone.png', w: 390, h: 800, dpr: 2 },
  { out: 'qa/phone_gough.png', w: 390, h: 800, dpr: 2, q: 'm=gough' },
  { out: 'qa/phone_full.png', w: 390, h: 800, dpr: 1, full: true },
  { out: 'qa/desktop_full.png', w: 1280, h: 800, full: true },
];
(async () => {
  const browser = await chromium.launch();
  const errors = [];
  for (const s of SHOTS) {
    const ctx = await browser.newContext({ viewport: { width: s.w, height: s.h }, deviceScaleFactor: s.dpr || 1 });
    const page = await ctx.newPage();
    await page.route(/fonts\.(googleapis|gstatic)\.com|maps\.tristanhotham\.com\/assets/, r => r.abort());
    page.on('console', m => { if (m.type() === 'error' && !/Failed to load resource/.test(m.text())) errors.push(`[${s.out}] ${m.text().slice(0, 300)}`); });
    page.on('pageerror', e => errors.push(`[${s.out}] pageerror ${e.message}`));
    await page.goto(`${PAGE}${s.q ? '?' + s.q : ''}`, { waitUntil: 'load' });
    await page.waitForFunction(() => window.__ready, null, { timeout: 60000 });
    await page.waitForTimeout(800);
    if (s.eval) { await page.evaluate(s.eval); await page.waitForTimeout(800); }
    const info = await page.evaluate(() => ({ scrollW: document.documentElement.scrollWidth, w: innerWidth, fs: document.querySelectorAll('.mfs-btn').length, thumbs: document.querySelectorAll('.thumb').length, tip: document.getElementById('tip').style.display }));
    await page.screenshot({ path: path.join(ROOT, s.out), fullPage: !!s.full });
    console.log('ok', s.out, JSON.stringify(info));
    await ctx.close();
  }
  await browser.close(); srv.close();
  console.log('ERRORS:', errors.length); errors.forEach(e => console.log(e));
  process.exit(0);
})();
