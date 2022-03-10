const puppeteer = require('puppeteer');

const args = process.argv.slice(2);
const sourceUrl = args[0];
const targetPath = args[1];

(async () => {
  const browser = await puppeteer.launch();
  const page = await browser.newPage();
  await page.goto(sourceUrl, { waitUntil: 'networkidle2' });
  await page.pdf({ path: targetPath });
  await browser.close();
})();
