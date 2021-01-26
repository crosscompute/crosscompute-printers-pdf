# TODO: Consider print chore query in case echoes are missed
# TODO: Consider print chore query for parallelization
# TODO: Consider merging into crosscompute workers run
import asyncio
import json
import requests
from collections import defaultdict
from crosscompute.routines import (
    get_client_url,
    get_echoes_client,
    get_server_url,
    render_object)
from crosscompute.scripts import OutputtingScript, run_safely
from invisibleroads_macros_disk import (
    TemporaryStorage, archive_safely, make_folder)
from os.path import join
from pyppeteer import launch


class RunPrinterScript(OutputtingScript):

    def run(self, args, argv):
        super().run(args, argv)
        is_quiet = args.is_quiet
        as_json = args.as_json

        run_safely(run_printer, {
        }, is_quiet, as_json)


def run_printer(is_quiet=False, as_json=False):
    prints_dictionary = defaultdict(int)
    try:
        for echo_message in get_echoes_client():
            event_name = echo_message.event
            if event_name == 'message':
                if not is_quiet and not as_json:
                    print('.', end='', flush=True)
                prints_dictionary['ping count'] += 1
            elif not is_quiet:
                print('\n' + render_object(echo_message.__dict__, as_json))

            if event_name == 'w':
                d = json.loads(echo_message.data)
                print_id = d['x']
                file_url = d['@']
                asyncio.run(do(print_id, file_url))
    except KeyboardInterrupt:
        pass
    return dict(prints_dictionary)


async def do(print_id, file_url):
    client_url = get_client_url()
    server_url = get_server_url()
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
            await page.pdf({'path': target_path, 'printBackground': True})
        archive_path = archive_safely(documents_folder)
        with open(archive_path, 'rb') as data:
            response = requests.put(file_url, data=data)
            print(response.__dict__)
    await browser.close()
