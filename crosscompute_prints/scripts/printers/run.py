# TODO: Consider print chore query in case echoes are missed
# TODO: Consider print chore query for parallelization
# TODO: Consider merging into crosscompute workers run
import asyncio
# import json
import os
import requests
import time
from collections import defaultdict
from crosscompute.exceptions import (
    CrossComputeConnectionError,
    CrossComputeKeyboardInterrupt)
from crosscompute.routines import (
    get_client_url,
    # get_echoes_client,
    get_server_url,
    # render_object,
    yield_echo)
from crosscompute.scripts import OutputtingScript, run_safely
from invisibleroads_macros_disk import (
    TemporaryStorage, archive_safely, make_folder)
from os.path import join
from pyppeteer import launch
from pyppeteer.errors import TimeoutError
from sys import exc_info
from traceback import print_exception


class RunPrinterScript(OutputtingScript):

    def run(self, args, argv):
        super().run(args, argv)
        is_quiet = args.is_quiet
        as_json = args.as_json

        run_safely(run_printer, {
        }, is_quiet, as_json)


def run_printer(is_quiet=False, as_json=False):
    d = defaultdict(int)
    # TODO: Move loop to yield_echo
    while True:
        try:
            for [
                event_name, event_dictionary,
            ] in yield_echo(d, is_quiet, as_json):
                if event_name == 'w' or d['ping count'] % 100 == 0:
                    d['result count'] += process_print_input_stream(
                        event_dictionary, is_quiet, as_json)
        except CrossComputeKeyboardInterrupt:
            break
        except (
            CrossComputeConnectionError,
            requests.exceptions.HTTPError,
        ) as e:
            print(e)
            time.sleep(1)
        except Exception:
            print_exception(*exc_info())
            time.sleep(1)
    return dict(d)


def process_print_input_stream(event_dictionary, is_quiet, as_json):
    print_id = event_dictionary['x']
    file_url = event_dictionary['@']
    client_url = get_client_url()
    server_url = get_server_url()
    url = f'{server_url}/prints/{print_id}.json'
    print_dictionary = requests.get(url).json()
    document_dictionaries = print_dictionary['documents']
    with TemporaryStorage() as storage:
        storage_folder = storage.folder
        documents_folder = make_folder(join(storage_folder, 'documents'))

        loop = asyncio.get_event_loop()
        loop.run_until_complete(asyncio.wait([print_document(
            _, documents_folder, client_url, print_id,
        ) for _ in enumerate(document_dictionaries)]))
        loop.close()

        archive_path = archive_safely(documents_folder)
        with open(archive_path, 'rb') as data:
            response = requests.put(file_url, data=data)
            print(response.__dict__)
    return 1


async def print_document(
        enumerated_document_dictionary,
        documents_folder,
        client_url,
        print_id):
    document_index, document_dictionary = enumerated_document_dictionary
    browser = await launch()
    page = await browser.newPage()
    target_name = document_dictionary['name']
    target_path = join(documents_folder, target_name + '.pdf')
    url = f'{client_url}/prints/{print_id}/documents/{document_index}'
    print(url, target_path)
    while True:
        try:
            await page.goto(url, {'waitUntil': 'networkidle2'})
            break
        except TimeoutError:
            os.system('pkill -9 chrome')
            browser = await launch()
            page = await browser.newPage()
    d = {
        'path': target_path,
        'printBackground': True,
        'displayHeaderFooter': True,
    }
    if 'header' in document_dictionary:
        d['headerTemplate'] = document_dictionary['header']
    else:
        d['headerTemplate'] = '<span />'
    if 'footer' in document_dictionary:
        d['footerTemplate'] = document_dictionary['footer']
    else:
        d['footerTemplate'] = '<span />'
    print(d)
    await page.pdf(d)
    await browser.close()
