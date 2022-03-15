import json
import subprocess
from crosscompute.routines.printer import BatchPrinter
from invisibleroads_macros_disk import TemporaryStorage
from pathlib import Path


class PdfPrinter(BatchPrinter):

    def render(self, batch_dictionaries, print_definition):
        with TemporaryStorage() as storage:
            path = Path(storage.folder) / 'printer-configuration.json'
            with open(path, 'wt') as f:
                json.dump({
                    'uri': self.server_uri,
                    'folder': self.target_folder,
                    'batch_dictionaries': batch_dictionaries,
                    'print_definition': print_definition,
                }, f)
            subprocess.run([
                'node',
                '--experimental-fetch',
                PACKAGE_FOLDER / 'scripts' / 'print-pdfs.js',
                path])


PACKAGE_FOLDER = Path(__file__).parent
