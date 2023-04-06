# PDF Printers for CrossCompute

## Installation

```bash
# Install packages
sudo dnf -y install chromium npm
# Install latest version of node
sudo npm cache clean -f
sudo npm install -g n
sudo n latest
# Install package
pip install crosscompute-printers-pdf
# Install dependencies
cd $(python -c "import crosscompute_printers_pdf; print(crosscompute_printers_pdf.__path__[0] + '/scripts')")
npm install
```

## Usage

1. Add prints to your configuration file.

```yaml
print:
  variables:
    - id: report
      view: pdf
      path: report.pdf
      configuration:
        header-footer:
          font-family: sans-serif
          font-size: 8pt
          color: '#808080'
          padding: 0.1in 0.25in
          skip-first: true
        page-number:
          location: footer
          alignment: right
        name: 'm{mean}-v{variance}-{timestamp}.pdf'
```

2. Run batch print.

```bash
crosscompute --print
```
