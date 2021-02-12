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
    asyncio.run(do(print_id, file_url))
    return 1


async def do(print_id, file_url):
    client_url = get_client_url()
    server_url = get_server_url()
    url = f'{server_url}/prints/{print_id}.json'
    response = requests.get(url)
    print_dictionary = response.json()
    document_dictionaries = print_dictionary['documents']
    with TemporaryStorage() as storage:
        storage_folder = storage.folder
        documents_folder = make_folder(join(storage_folder, 'documents'))
        for document_index, document_dictionary in enumerate(
                document_dictionaries):
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

            await page.pdf({'path': target_path, 'printBackground': True})
            await browser.close()
        archive_path = archive_safely(documents_folder)
        with open(archive_path, 'rb') as data:
            response = requests.put(file_url, data=data)
            print(response.__dict__)
