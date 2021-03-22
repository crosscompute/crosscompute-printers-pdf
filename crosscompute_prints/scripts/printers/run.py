# TODO: Consider print chore query in case echoes are missed
# TODO: Consider print chore query for parallelization
# TODO: Consider merging into crosscompute workers run
import asyncio
# import json
# import msgpack
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
from glob import glob
from invisibleroads_macros_disk import archive_safely, make_folder
from os import remove
from os.path import expanduser, join
from pyppeteer import launch
from pyppeteer.errors import TimeoutError
from shutil import rmtree
from sys import exc_info
from traceback import print_exception


STORAGE_FOLDER = expanduser('~/.crosscompute')


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
    prints_folder = join(STORAGE_FOLDER, 'prints')
    print_id = event_dictionary['x']
    print_folder = make_folder(join(prints_folder, print_id))

    if '?' in event_dictionary:
        document_index = event_dictionary['?']
        server_url = get_server_url()
        client_url = get_client_url()
        url = f'{server_url}/prints/{print_id}/documents/{document_index}.json'
        document_dictionary = requests.get(url).json()
        # path = join(print_folder, str(document_index) + '.msgpack')
        # msgpack.dump(document_dictionary, open(path, 'wb'))
        future = print_document(
            (document_index, document_dictionary), print_folder,
            client_url, print_id)
    elif '@' in event_dictionary:
        document_count = event_dictionary['#']
        file_url = event_dictionary['@']

        def is_ready():
            return len(glob(join(print_folder, '*.pdf'))) == document_count

        future = make_archive(is_ready, print_folder, file_url)
    asyncio.run(future)
    return 1


async def print_document(
        enumerated_document_dictionary, target_folder, client_url,
        print_id):
    document_index, document_dictionary = enumerated_document_dictionary
    target_name = document_dictionary['name']
    target_path = join(target_folder, target_name + '.pdf')
    url = f'{client_url}/prints/{print_id}/documents/{document_index}'
    print(url, target_path)
    while True:
        browser = await launch()
        page = await browser.newPage()
        try:
            await page.goto(url, {'waitUntil': 'networkidle2'})
            break
        except TimeoutError:
            os.system('pkill -9 chrome')
    await page.pdf({
        'path': target_path,
        'printBackground': True,
        'displayHeaderFooter': True,
        'headerTemplate': document_dictionary.get('header') or '<span />',
        'footerTemplate': document_dictionary.get('footer') or '<span />',
    })
    await browser.close()


async def make_archive(is_ready, print_folder, file_url):
    while not is_ready():
        await asyncio.sleep(1)
    archive_path = archive_safely(print_folder, excluded_paths=['*.msgpack'])
    with open(archive_path, 'rb') as data:
        response = requests.put(file_url, data=data)
        print(response.__dict__)
    rmtree(print_folder)
    remove(archive_path)
