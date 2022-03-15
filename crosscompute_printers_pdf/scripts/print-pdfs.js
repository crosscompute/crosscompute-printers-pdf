'use strict';

const fs = require('fs');
const http = require('http');
const path = require('path');

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
  console.log(`saving prints to ${baseFolder}`);
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
  const page_number_settings = printDefinition['page-number']
  if (page_number_settings) {
    page_number_settings['location']
    page_number_settings['alignment']
    page_number_settings['font-family']
    page_number_settings['font-size']
    page_number_settings['color']
    page_number_settings['padding']
    page_number_settings['skip-first']
  }
  // await page.goto(sourceUri, { waitUntil: 'networkidle2' });
  // await page.pdf({ path: targetPath });
  // displayHeaderFooter: true,
  // headerTemplate: '<span />'
  // footerTemplate: x,
}
const getPdfOptions = (printDefinition) => {
  return {
    // 'displayHeaderFooter':
    // 'headerTemplate':
    // 'footerTemplate':
  }
}

const serverUri = d.uri;
const baseFolder = d.folder;
const batchDictionaries = d.batch_dictionaries;
const printDefinition = d.print_definition;
go(serverUri, baseFolder, batchDictionaries, printDefinition);
