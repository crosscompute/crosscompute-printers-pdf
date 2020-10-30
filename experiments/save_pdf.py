import asyncio
from pyppeteer import launch


async def save_pdf(target_path, url):
    browser = await launch()
    page = await browser.newPage()
    await page.goto(url, {'waitUntil': 'networkidle2'})
    await page.pdf({'path': target_path})
    await browser.close()


asyncio.run(save_pdf('/tmp/x.pdf', 'https://google.com'))
