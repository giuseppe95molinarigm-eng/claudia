const { chromium } = require('playwright');
(async () => {
  const [,, html, pdf] = process.argv;
  const b = await chromium.launch();
  const p = await b.newPage();
  p.on('console', m => { if (m.type() === 'error' || m.type()==='warning') console.log('console:', m.text()); });
  await p.goto('file://' + html, { waitUntil: 'load' });
  await p.waitForFunction(() => window.__pagedDone === true, null, {timeout: 900000});
  const last = await p.evaluate(() => document.querySelectorAll('.pagedjs_page').length);
  console.log('pages', last);
  await p.pdf({ path: pdf, preferCSSPageSize: true, printBackground: true });
  await b.close();
})();
