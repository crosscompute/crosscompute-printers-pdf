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

const isReady = async (batchUri) => {
  const response = await fetch(batchUri + '/d/return_code');
  const responseText = await response.text();
  const returnCode = parseInt(responseText);
  return returnCode == 0;
};
const initialize = async () => {
  browser = await puppeteer.launch();
  page = await browser.newPage();
}
const print = async (sourceUri, targetPath) => {
  console.log(`printing ${sourceUri} to ${targetPath}`);
  await page.goto(sourceUri, { waitUntil: 'networkidle2' });
  await page.pdf({ path: targetPath });
}
const go = async (serverUri, batchDictionaries, baseFolder) => {
  console.log(`saving prints to ${baseFolder}`);
  await initialize();
  while (batchDictionaries.length) {
    const batchDictionary = batchDictionaries.pop();
    const batchName = batchDictionary.name;
    const sourceUri = serverUri + batchDictionary.uri;
    if (isReady(sourceUri)) {
      const targetPath = `${baseFolder}/${batchName}.pdf`;
      await print(sourceUri + '/o?p', targetPath);
    } else {
      batchDictionaries.push(batchDictionary);
    }
  }
  await browser.close();
}

const serverUri = d.uri;
const batchDictionaries = d.batch_dictionaries;
const baseFolder = d.folder;
go(serverUri, batchDictionaries, baseFolder);
