const { chromium } = require('playwright');
(async () => {
  const [,, html, png, sel] = process.argv;
  const b = await chromium.launch(); const p = await b.newPage({ deviceScaleFactor: 4 });
  await p.goto('file://' + require('path').resolve(html)); await p.evaluate(() => document.fonts.ready);
  const el = await p.$(sel || '#fig'); await el.screenshot({ path: png });
  const bb = await el.boundingBox(); console.log(png, Math.round(bb.width), 'x', Math.round(bb.height), 'css px');
  // texto que se sale de su caja
  const over = await p.evaluate(() => [...document.querySelectorAll('.c,.et,.r,.h')].filter(e => e.scrollWidth > e.clientWidth + 1 || e.scrollHeight > e.clientHeight + 1).map(e => e.textContent.trim().slice(0, 40)));
  console.log('desbordes:', over.length ? over : 'ninguno');
  await b.close();
})();
