import json
import subprocess
from pathlib import Path

from crosscompute.routines.printer import BatchPrinter
from invisibleroads_macros_disk import TemporaryStorage


class PdfPrinter(BatchPrinter):

    view_name = 'pdf'

    def render(self, batch_dictionaries, print_configurations):
        with TemporaryStorage() as storage:
            path = Path(storage.folder) / 'c.json'
            with open(path, 'wt') as f:
                json.dump({
                    'uri': self.server_uri,
                    'dictionaries': batch_dictionaries,
                    'configurations': print_configurations,
                }, f)
            subprocess.run([
                'node',
                '--experimental-fetch',
                PACKAGE_FOLDER / 'scripts' / 'print.js',
                path])


PACKAGE_FOLDER = Path(__file__).parent
