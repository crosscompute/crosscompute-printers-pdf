# TODO: Consider print chore query in case echoes are missed
# TODO: Consider print chore query for parallelization
# TODO: Consider merging into crosscompute workers run

import asyncio
import os
import requests
import time
from collections import defaultdict
from crosscompute.exceptions import (
    CrossComputeConnectionError,
    CrossComputeKeyboardInterrupt)
from crosscompute.routines import (
    get_client_url,
    get_server_url,
    yield_echo)
from crosscompute.scripts import OutputtingScript, run_safely
from glob import glob
from invisibleroads_macros_disk import (
    TemporaryStorage, archive_safely, make_folder)
from os import remove
from os.path import exists, expanduser, join
from PyPDF2 import PdfFileMerger, PdfFileReader
from pyppeteer import launch
from pyppeteer.errors import TimeoutError
from shutil import rmtree
from sys import exc_info
from tempfile import mkstemp
from traceback import print_exception
import tinycss2


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
        # import pudb; pudb.set_trace()
        future = print_document(
            (document_index, document_dictionary), print_folder,
            client_url, print_id)
    elif '@' in event_dictionary:
        document_count = event_dictionary['#']
        file_url = event_dictionary['@']

        def is_ready():
            new_document_count = len(glob(join(print_folder, '*.pdf')))
            return new_document_count == document_count

        future = make_archive(is_ready, print_folder, file_url)
    asyncio.run(future)
    return 1


async def print_document(
        enumerated_document_dictionary, target_folder, client_url,
        print_id):
    document_index, document_dictionary = enumerated_document_dictionary
    target_name = document_dictionary['name']
    target_path = join(target_folder, target_name + '.pdf')

    if exists(target_path):
        target_path = mkstemp(
            suffix='.pdf', prefix=target_name + '-', dir=target_folder)[1]


    url = f'{client_url}/prints/{print_id}/documents/{document_index}'
    print('***')
    print(url)
    print(target_path)
    while True:
        browser = await launch()
        page = await browser.newPage()
        try:
            await page.goto(url, {'waitUntil': 'networkidle2'})
            break
        except TimeoutError:
            # !!! Rethink whether this is still necessary
            os.system('pkill -9 chrome')

    header_html = document_dictionary.get('header', '')
    footer_html = document_dictionary.get('footer', '')

    # Required to extract orientation on pages
    styles_list = document_dictionary.get('styles', [])
    styles_text = '\n'.join(styles_list)
    styles = tinycss2.parse_stylesheet(styles_text)
    # if styles_list:
    #    styles = styles_list[0]

    await page.pdf({
        'path': target_path,
        'printBackground': True,
        'displayHeaderFooter': True,
        'headerTemplate': header_html or '<span />',
        'footerTemplate': footer_html or '<span />',
    })

    raw_report = PdfFileReader(target_path)
    orientations_by_page = get_orientations_from_css(styles)
    print(orientations_by_page)
    pages_with_diff_orientation = get_page_ranges_from_orientation(
        orientations_by_page, raw_report.numPages)
    print(pages_with_diff_orientation)
    general_orientation = 'landscape'
    filter_by_general_orientation = [
        orientation[1] for orientation in orientations_by_page if
        orientation[0] == 'general']
    if len(filter_by_general_orientation):
        general_orientation = filter_by_general_orientation[0]

    print(general_orientation)

    in_word = 'portrait'
    out_word = 'landscape'
    if general_orientation == 'landscape':
        in_word = 'landscape'
        out_word = 'portrait'

    range_pages = get_numeric_ranges(
        pages_with_diff_orientation, raw_report.numPages, in_word, out_word)
    if pages_with_diff_orientation:
        with TemporaryStorage() as storage:
            document_paths = []
            for (orientation, pages) in range_pages:
                landscape = orientation == 'landscape'  # predicate
                print(orientation, pages, landscape)
                document_path = join(
                    storage.folder, f'document-{pages[0]}.pdf')
                pages_str = ','.join([str(page) for page in pages])

                if (
                    'visibility' in header_html or
                    'visibility' in footer_html and
                    len(pages) > 1 and 1 in pages
                ):
                    cover_path = join(storage.folder, 'cover.pdf')
                    document_paths.append(cover_path)

                    await page.pdf({
                        'path': cover_path,
                        'printBackground': True,
                        'displayHeaderFooter': True,
                        'headerTemplate': '<span />',
                        'footerTemplate': '<span />',
                        'pageRanges': '1',
                        'landScape': landscape,  # True or False
                    })

                    document_path = join(
                        storage.folder, f'document-{pages[1]}.pdf')
                    pages_str = ','.join([str(page) for page in pages[1:]])

                document_paths.append(document_path)
                await page.pdf({
                    'path': document_path,
                    'printBackground': True,
                    'displayHeaderFooter': True,
                    'headerTemplate': header_html or '<span />',
                    'footerTemplate': footer_html or '<span />',
                    'pageRanges': pages_str,
                    'landscape': landscape,
                })

            target_pdf = PdfFileMerger()
            for path in document_paths:
                target_pdf.append(PdfFileReader(path))
            target_pdf.write(target_path)
    elif 'visibility' in header_html or 'visibility' in footer_html:
        with TemporaryStorage() as storage:
            cover_path = join(storage.folder, 'cover.pdf')
            document_path = join(storage.folder, 'document.pdf')
            await page.pdf({
                'path': cover_path,
                'printBackground': True,
                'displayHeaderFooter': True,
                'headerTemplate': '<span />',
                'footerTemplate': '<span />',
                'pageRanges': '1',
            })
            await page.pdf({
                'path': document_path,
                'printBackground': True,
                'displayHeaderFooter': True,
                'headerTemplate': header_html or '<span />',
                'footerTemplate': footer_html or '<span />',
                'pageRanges': '2-',
            })
            target_pdf = PdfFileMerger()
            target_pdf.append(PdfFileReader(cover_path))
            target_pdf.append(PdfFileReader(document_path))
            target_pdf.write(target_path)

    await browser.close()


async def make_archive(is_ready, print_folder, file_url):
    while not is_ready():
        await asyncio.sleep(1)
    archive_path = archive_safely(print_folder)
    with open(archive_path, 'rb') as data:
        response = requests.put(file_url, data=data)
        print(response.__dict__)
    rmtree(print_folder)
    remove(archive_path)


def has_orientation_rule(list_tokens):
    size_token = None
    literal_token = None
    orientation_token = None
    for token in list_tokens:
        # 1. @general { size: landscape; color: blue } DONE

        # [ size: landscape, color: blue ]
        if token.type == 'ident' and token.lower_value == 'size':
            size_token = token
            literal_token = None
            orientation_token = None
        elif size_token and token.type == 'literal' and token.value == ':':
            literal_token = token
            orientation_token = None
        elif (
            literal_token and token.type == 'ident' and token.lower_value in [
                'portrait', 'landscape']
        ):
            orientation_token = token
            break
        elif token.type == 'whitespace':
            pass
        else:
            size_token = None
            literal_token = None
            orientation_token = None

    if size_token and literal_token and orientation_token:
        return orientation_token.lower_value


def get_orientations_from_css(css):
    page_orientations = []
    print(css)
    for token in css:
        print(token)
        if token.type == 'at-rule' and token.lower_at_keyword == 'page':
            print('---- prelude ')
            print(token.prelude)
            if len(token.prelude) <= 1:  # Remove all withespace tokens
                orientation = has_orientation_rule(token.content)
                if orientation:
                    page_orientations.append(('general', orientation))

            for rule in token.prelude:
                if rule.type == 'ident':
                    page_orientations.append((
                        'keyword', rule.value,
                        has_orientation_rule(token.content)))
                elif rule.type == 'function':
                    for arg in rule.arguments:
                        page_orientations.append((
                            'function', rule.lower_name, arg.value,
                            has_orientation_rule(token.content)))

    return page_orientations


def get_page_ranges_from_orientation(orientations, last_value=-1):
    pages_with_diff_orientation = []
    filter_by_general_orientation = [
        orientation[1] for orientation in orientations
        if orientation[0] == 'general']

    general_orientation = 'landscape'
    if len(filter_by_general_orientation):
        general_orientation = filter_by_general_orientation[0]

    for orientation in orientations:
        if orientation[-1] != general_orientation:
            if orientation[0] == 'keyword':
                if orientation[1] == 'first':
                    pages_with_diff_orientation.append(1)
                if orientation[1] == 'last':
                    pages_with_diff_orientation.append(last_value)
            if orientation[0] == 'function':
                if orientation[1] == 'nth-child':
                    pages_with_diff_orientation.append(int(orientation[2]))

    pages_with_diff_orientation = sorted(pages_with_diff_orientation)

    # general = lanscape
    # [-1, 2, 3, 4]
    # [2, 3, 4, -1]
    if pages_with_diff_orientation and pages_with_diff_orientation[0] == -1:
        return pages_with_diff_orientation[1:] + [
            pages_with_diff_orientation[0]]

    return pages_with_diff_orientation


def get_numeric_ranges(steps, limit, in_word='portrait', out_word='landscape'):
    # [('portrait', [1,2,3,4,5]), ('landscape', [6]), ]
    sorted_steps = sorted(steps)
    ranges = []
    current_range = []
    even = False
    for x in range(1, limit + 1):
        if x in sorted_steps:
            if even:
                current_range.append(x)
            else:
                if current_range:
                    ranges.append((out_word, current_range))
                current_range = [x]
                even = True
        else:
            if even:
                if current_range:
                    ranges.append((in_word, current_range))
                current_range = [x]
                even = False
            else:
                current_range.append(x)

    if even:
        ranges.append((in_word, current_range))
    else:
        ranges.append((out_word, current_range))
    return ranges
