"""
Module responsable de la sauvegarde et des logs.
"""
import json

def jdefault(o):
    return o.__dict__

def write_log( item ):
    f = open('log', 'w')
    f.write(str(item))
    f.close()

def save_position( position ):
    f = open('status', 'w')
    f.write(str(position))
    f.close()

def load_position():
    f = open('status', 'r')
    pos = int(f.readline())
    f.close()
    return pos

def add_entry( product ):
    db_file = open('saq.json', 'a')
    obj_json = json.dumps(product, default=jdefault)
    db_file.write(obj_json + '\n')
    db_file.close()