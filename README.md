# PDF Printers for CrossCompute

## Installation

```bash
# Install node version manager
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/master/install.sh | bash
# Install latest version of node
nvm install node
# Install dependencies globally
npm install -g express puppeteer
# Install package
pip install crosscompute-printers-pdf
```

## Usage

```bash
# Batch print
crosscompute --print pdf --print-folder /tmp/abc
```
