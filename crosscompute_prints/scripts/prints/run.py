import asyncio
import json
import requests
from crosscompute.scripts import AuthenticatingScript
from invisibleroads_macros_disk import (
    TemporaryStorage, archive_safely, make_folder)
from os.path import join
from pyppeteer import launch
from sseclient import SSEClient


# !!!
CLIENT_HOST = 'https://projects.iixyfqfy.crosscompute.com'


class RunPrinterScript(AuthenticatingScript):

    def run(self, args, argv):
        super().run(args, argv)
        return run(args.host, args.token)


def get_echoes_client(host, token):
    url = f'{host}/echoes/{token}.json'
    return SSEClient(url)


def run(host, token):
    echoes_client = get_echoes_client(host, token)
    for echo_message in echoes_client:
        print(echo_message.__dict__)
        if echo_message.event == 'w':
            d = json.loads(echo_message.data)
            print_id = d['x']
            document_count = d['#']
            file_url = d['@']
            print(print_id, document_count)
            asyncio.run(do(print_id, document_count, file_url))


async def do(print_id, document_count, file_url):
    with TemporaryStorage() as storage:
        storage_folder = storage.folder
        documents_folder = make_folder(join(storage_folder, 'documents'))
        for document_index in range(document_count):
            url = f'{CLIENT_HOST}/prints/{print_id}/documents/{document_index}'
            print(url)
            target_path = join(documents_folder, f'{document_index}.pdf')
            await save_pdf(target_path, url)
        archive_path = archive_safely(documents_folder)
        with open(archive_path, 'rb') as data:
            response = requests.put(file_url, data=data)
        print(response.__dict__)


async def save_pdf(target_path, url):
    browser = await launch()
    page = await browser.newPage()
    await page.goto(url, {'waitUntil': 'networkidle2'})
    await page.pdf({'path': target_path})
    await browser.close()
