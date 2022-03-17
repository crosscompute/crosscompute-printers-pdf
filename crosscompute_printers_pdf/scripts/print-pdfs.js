'use strict';

const fs = require('fs');
const http = require('http');
const os = require('os');
const path = require('path');

const PDFMerger = require('pdf-merger-js');
const express = require('express');
const puppeteer = require('puppeteer');

const args = process.argv.slice(2);
const dataPath = args[0];
const d = JSON.parse(fs.readFileSync(dataPath));

let browser, page;

const go = async (
  serverUri,
  baseFolder,
  batchDictionaries,
  printDefinition
) => {
  await initialize();
  while (batchDictionaries.length) {
    const batchDictionary = batchDictionaries.pop();
    const batchName = batchDictionary.name;
    const sourceUri = serverUri + batchDictionary.uri;
    if (isReady(sourceUri)) {
      const targetPath = `${baseFolder}/${batchName}.pdf`;
      await print(sourceUri + '/o?p', targetPath, printDefinition);
    } else {
      batchDictionaries.push(batchDictionary);
    }
  }
  await browser.close();
}
const initialize = async () => {
  browser = await puppeteer.launch();
  page = await browser.newPage();
}
const isReady = async (batchUri) => {
  const response = await fetch(batchUri + '/d/return_code');
  const responseText = await response.text();
  const returnCode = parseInt(responseText);
  return returnCode == 0;
};
const print = async (sourceUri, targetPath, printDefinition) => {
  console.log(`printing ${sourceUri} to ${targetPath}`);
  const printConfiguration = printDefinition['configuration'];
  const headerFooterOptions = printConfiguration['header-footer'];
  const skipFirst = headerFooterOptions?.['skip-first'];
  const pageNumberOptions = printConfiguration['page-number'];
  const pageNumberLocation = pageNumberOptions?.['location'];
  const containerHtml = getContainerHtml(printConfiguration);
  let displayHeaderFooter = false;
  let headerTemplate = '<span />', footerTemplate = '<span />';
  switch (pageNumberLocation) {
    case 'header': {
      displayHeaderFooter = true;
      headerTemplate = containerHtml;
      break;
    }
    case 'footer': {
      displayHeaderFooter = true;
      footerTemplate = containerHtml;
      break;
    }
  }
  const pdfOptions = {
    path: targetPath, preferCSSPageSize: true, displayHeaderFooter,
    headerTemplate, footerTemplate};
  await page.goto(sourceUri, { waitUntil: 'networkidle2' });
  await savePdf(page, pdfOptions, skipFirst);
}
const getContainerHtml = (printConfiguration) => {
  const headerFooterOptions = printConfiguration['header-footer'];
  const fontFamily = headerFooterOptions?.['font-family'] || 'sans-serif';
  const fontSize = headerFooterOptions?.['font-size'] || '8pt';
  const color = headerFooterOptions?.['color'] || '#808080';
  const padding = headerFooterOptions?.['padding'] || '0.1in 0.25in';
  const pageNumberOptions = printConfiguration['page-number'];
  const pageNumberAlignment = pageNumberOptions?.['alignment'] || 'right';
  const pageNumberHtml = '<span class="pageNumber"></span>';
  let contentHtml = '';
  switch (pageNumberAlignment) {
    case 'left': {
      contentHtml = `<div>${pageNumberHtml}</div>`;
      break;
    }
    case 'center': {
      contentHtml = `<div></div><div>${pageNumberHtml}</div><div></div>`;
      break;
    }
    case 'right': {
      contentHtml = `<div></div><div>${pageNumberHtml}</div>`;
      break;
    }
  }
  return `<section style="width: 100vw; display: flex; justify-content: space-between; font-family: ${fontFamily}; font-size: ${fontSize}; color: ${color}; padding: ${padding};">${contentHtml}</section>`;
}
const savePdf = async (page, pdfOptions, skipFirst) => {
  if (skipFirst) {
    const TEMPORARY_FOLDER = os.homedir() + '/.tmp';
    fs.mkdirSync(TEMPORARY_FOLDER, { recursive: true });
    const temporaryFolder = fs.mkdtempSync(TEMPORARY_FOLDER + '/');
    const headPath = temporaryFolder + '/head.pdf';
    const bodyPath = temporaryFolder + '/body.pdf';
    await page.pdf({
      path: headPath,
      preferCSSPageSize: true,
      displayHeaderFooter: false,
      pageRanges: '1',
    });
    await page.pdf({...pdfOptions, path: bodyPath, pageRanges: '2-'});
    const pdfMerger = new PDFMerger();
    pdfMerger.add(headPath);
    pdfMerger.add(bodyPath);
    await pdfMerger.save(pdfOptions['path']);
    fs.rmSync(temporaryFolder, { recursive: true });
  } else {
    await page.pdf({...pdfOptions});
  }
}

const serverUri = d.uri;
const baseFolder = d.folder;
const batchDictionaries = d.batch_dictionaries;
const printDefinition = d.print_definition;
go(serverUri, baseFolder, batchDictionaries, printDefinition);
