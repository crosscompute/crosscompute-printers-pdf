# CrossCompute Prints

## Installation

```
curl --silent --location https://dl.yarnpkg.com/rpm/yarn.repo | sudo tee /etc/yum.repos.d/yarn.repo
sudo dnf -y install chromium freetype-devel nodejs yarn
pip install -e .
```

## Troubleshooting

```
BrowserError: Browser closed unexpectedly: 

$(python -c "from pyppeteer.launcher import Launcher; print(' '.join(Launcher().cmd))")
```
