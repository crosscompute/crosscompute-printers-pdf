# TODO: Consider print chore query in case echoes are missed
# TODO: Consider print chore query for parallelization
# TODO: Consider merging into crosscompute workers run
import asyncio
import json
import requests
from crosscompute.routines import (
    get_client_url, get_echoes_client)
from crosscompute.scripts import AuthenticatingScript
from invisibleroads_macros_disk import (
    TemporaryStorage, archive_safely, make_folder)
from os.path import join
from pyppeteer import launch


class RunPrinterScript(AuthenticatingScript):

    def run(self, args, argv):
        super().run(args, argv)
        client_url = get_client_url()
        return run(args.server_url, args.server_token, client_url)


def run(server_url, server_token, client_url):
    echoes_client = get_echoes_client(server_url, server_token)
    for echo_message in echoes_client:
        print(echo_message.__dict__)
        if echo_message.event == 'w':
            d = json.loads(echo_message.data)
            print_id = d['x']
            file_url = d['@']
            asyncio.run(do(print_id, server_url, client_url, file_url))


async def do(print_id, server_url, client_url, file_url):
    url = f'{server_url}/prints/{print_id}.json'
    response = requests.get(url)
    print_dictionary = response.json()
    document_dictionaries = print_dictionary['documents']
    browser = await launch()
    page = await browser.newPage()
    with TemporaryStorage() as storage:
        storage_folder = storage.folder
        documents_folder = make_folder(join(storage_folder, 'documents'))
        for document_index, document_dictionary in enumerate(
                document_dictionaries):
            target_name = document_dictionary['name']
            target_path = join(documents_folder, target_name + '.pdf')
            url = f'{client_url}/prints/{print_id}/documents/{document_index}'
            print(url, target_path)
            await page.goto(url, {'waitUntil': 'networkidle2'})
            await page.pdf({'path': target_path})
        archive_path = archive_safely(documents_folder)
        with open(archive_path, 'rb') as data:
            response = requests.put(file_url, data=data)
            print(response.__dict__)
    await browser.close()
