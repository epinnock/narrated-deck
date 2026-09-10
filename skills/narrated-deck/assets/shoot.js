// Screenshot every slide of a built deck at 1920x1080 with Playwright.
// Usage: node shoot.js <deck-dir> [playwright-module-path]
// Playwright resolution order: argv[3], $PLAYWRIGHT_MODULE, then a plain require('playwright')
// (install with `npm i -D playwright && npx playwright install chromium` in the deck directory).
const path = require('path');
const fs = require('fs');

const DIR = path.resolve(process.argv[2] || '.');
const PW = process.argv[3] || process.env.PLAYWRIGHT_MODULE || 'playwright';
let chromium;
try {
  ({ chromium } = require(PW));
} catch (e) {
  ({ chromium } = require(require.resolve(PW, { paths: [DIR, process.cwd()] })));
}
const URL_BASE = 'file://' + path.join(DIR, 'index.html') + '?clean';

(async () => {
  fs.mkdirSync(path.join(DIR, 'slides'), { recursive: true });
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
  await page.goto(`${URL_BASE}#slide-1`, { waitUntil: 'load' });
  const total = await page.evaluate(() => document.querySelectorAll('.slide').length);
  for (let n = 1; n <= total; n++) {
    const nn = String(n).padStart(2, '0');
    await page.goto(`${URL_BASE}#slide-${n}`, { waitUntil: 'load' });
    await page.evaluate(() => document.fonts.ready);
    await page.waitForTimeout(500);
    const out = path.join(DIR, 'slides', `slide-${nn}.png`);
    await page.screenshot({ path: out });
    console.log('wrote', out);
  }
  await browser.close();
  console.log(`${total} slides captured`);
})().catch((e) => { console.error(e); process.exit(1); });
