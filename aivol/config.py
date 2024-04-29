import os
import sys
import json
import yaml
import pickle
import glob
from itertools import groupby

def universal_load(file_path):
    if not os.path.exists(file_path):
        return None
    if file_path.endswith('.json'):
        with open(file_path) as f:
            data = json.load(f)
    elif file_path.endswith('.yaml') or file_path.endswith('.yml'):
        with open(file_path) as f:
            data = yaml.safe_load(f)
    elif file_path.endswith('.pkl'):
        with open(file_path, 'rb') as f:
            data = pickle.load(f)
    else:
        raise ValueError("Unsupported file format")

    data['_from_file'] = file_path
    return data

def universal_store(file_path, data):
    if file_path.endswith('.json'):
        with open(file_path, 'w') as f:
            json.dump(data, f)
    elif file_path.endswith('.yaml') or file_path.endswith('.yml'):
        with open(file_path, 'w') as f:
            yaml.safe_dump(data, f)
    elif file_path.endswith('.pkl'):
        with open(file_path, 'wb') as f:
            pickle.dump(data, f)
    else:
        raise ValueError("Unsupported file format")


def all_equal(iterable):
    g = groupby(iterable)
    return next(g, True) and not next(g, False)

def flatten_dict(d, parent_key='', sep=':'):
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        elif isinstance(v, list):
            for i, item in enumerate(v):
                items.extend(flatten_dict({f"{new_key}{sep}{i}": item}, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)

def folder_to_file(fname):
    if os.path.isdir(fname):
        files = glob.glob(fname + "/*.json") + glob.glob(fname + "/*.yml") + glob.glob(fname + "/*.yaml") + glob.glob(fname + "/*.pkl")
        if files:
            fname = files[0]
    return fname
