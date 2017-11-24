"""
Module responsable de la sauvegarde et des logs.
"""
import json
from datetime import datetime
from status import *
import sys
# for logs
SEVERITY = {0: 'EMERGENCY', 1: 'ALERT', 2: 'CRITICAL', 3: 'ERROR',
            4: 'WARNING', 5: 'NOTICE', 6: 'INFO', 7: 'DEBUG'}

DATE_FORMAT = '%Y%m%d-%H%M%S-%f'

def jdefault(o):
    return o.__dict__


def write_log( severity, item ):
    try:
        f = open('log', 'a')
        f.write(SEVERITY.get(severity) + ': ' + str(item) + '\n')
        f.close()

    except Exception as e:
        sys.exit("Cannot write logs: {0}".format(e))


def save_status( ):
    try:
        f = open('status', 'w')
        f.write(Status.state + '\n')
        f.write(Status.beginDate + '\n')
        f.write(Status.endDate + '\n')
        f.write(str(Status.position) + '\n')
        f.close()

    except OSError as err:
        message = "Couldn't save status: {0}".format(err)
        write_log(2, message)
        sys.exit(message)
    except Exception as e:
        message = "Unexpected error: {0}".format(e)
        write_log(2, message)
        sys.exit(message)


def load_status( ):
    try:
        f = open('status', 'r')
        Status.state = f.readline().rstrip('\n')
        Status.beginDate = f.readline().rstrip('\n')
        Status.endDate = f.readline().rstrip('\n')
        Status.position = int(f.readline())
        f.close()

    except OSError as err:
        message = "Couldn't load status: {0}".format(err)
        write_log(2, message)
        sys.exit(message)
    except Exception as e:
        message = "Unexpected error: {0}".format(e)
        write_log(2, message)
        sys.exit(message)


def add_entry( product ):
    try:
        db_file = open('saq-' + Status.beginDate + '.json', 'a')
        obj_json = json.dumps(product, default=jdefault)
        db_file.write(obj_json + '\n')
        db_file.close()

    except OSError as err:
        message = "Couldn't add entry: {0}".format(err)
        write_log(2, message)
        sys.exit(message)
    except Exception as e:
        message = "Unexpected error: {0}".format(e)
        write_log(2, message)
        sys.exit(message)