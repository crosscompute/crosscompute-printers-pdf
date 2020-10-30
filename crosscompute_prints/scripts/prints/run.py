from crosscompute.scripts import AuthenticatingScript
from sseclient import SSEClient


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
