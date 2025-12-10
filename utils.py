import os
import json
import random
import numpy as np
import pandas as pd

def seed_everything(seed=42):
    random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)
    np.random.seed(seed)

def ensure_dirs(paths):
    for path in paths:
        os.makedirs(path, exist_ok=True)

def save_json(data, path):
    with open(path, 'w') as f:
        json.dump(data, f, indent=4)

def load_json(path):
    with open(path, 'r') as f:
        return json.load(f)

def load_csv(path):
    return pd.read_csv(path)
