# CrossCompute Prints

## Installation

```
curl --silent --location https://dl.yarnpkg.com/rpm/yarn.repo | sudo tee /etc/yum.repos.d/yarn.repo
sudo dnf -y install nodejs yarn
sudo dnf -y install chromium
# sudo dnf -y install freetype-devel
# sudo dnf -y install libXScrnSaver-devel
# sudo dnf -y install libX11-xcb libXcomposite libXcursor libXdamage libXext libXi libXtst libXss libXScrnSaver libXrandr libasound alsa-lib
pip install -e .
```

## Troubleshooting

```
BrowserError: Browser closed unexpectedly: 

$(python -c "from pyppeteer.launcher import Launcher; print(' '.join(Launcher().cmd))")
```
