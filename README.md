# PDF Printers for CrossCompute

## Installation

```bash
# Install node version manager
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/master/install.sh | bash
# Reload bash configuration
source ~/.bashrc
# Install latest version of node
nvm install node
# Install dependencies globally
sudo dnf -y install chromium
npm install -g express pdf-merger-js puppeteer
# Install package
pip install crosscompute-printers-pdf
```

## Usage

```bash
# Batch print
crosscompute --print pdf --print-folder /tmp/abc
```
