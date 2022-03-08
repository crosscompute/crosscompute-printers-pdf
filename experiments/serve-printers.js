const express = require('express');
const fs = require('fs');
const path = require('path');
const puppeteer = require('puppeteer');

const args = process.argv.slice(1);
const baseFolder = args[1] || '.';
console.log(`saving to ${baseFolder}`);

let browser, page;
const initialize = async() => {
  browser = await puppeteer.launch();
  page = await browser.newPage();
}
const print = async(sourceUri, targetPath) => {
  await page.goto(sourceUri, { waitUntil: 'networkidle2' });
  await page.pdf({ path: targetPath });
  await browser.close();
}

const app = express();
const host = process.env.HOST || 'localhost';
const port = process.env.PORT || 8718;

initialize();
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

app.post('/printers/pdf.json', function(req, res) {
  const sourceUri = req.body.uri;
  const folder = req.body.folder;
  const targetName = req.body.name;
  const targetFolder = `${baseFolder}/${folder}`;
  const targetPath = `${targetFolder}/${targetName}.pdf`;
  if (!path.normalize(targetPath).startsWith(baseFolder)) {
    return res.status(400).send({});
  }
  if (!fs.existsSync(targetFolder)) {
    fs.mkdirSync(targetFolder, { recursive: true });
  }
  print(sourceUri, targetPath);
  res.send({});
});

app.listen(port, () => console.log(`listening at http://${host}:${port}`));
