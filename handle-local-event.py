import json
import sys
from main import handler


def run_handler():
    event_file = sys.argv[1]
    with open(event_file, 'r') as event_file:
        event = json.loads(event_file.read())

    resp = handler(event, {})
    print('Got response:\n{}'.format(resp))


if len(sys.argv) < 2:
    print('Usage: python handle-local-event.py ./event.json')
else:
    run_handler()
