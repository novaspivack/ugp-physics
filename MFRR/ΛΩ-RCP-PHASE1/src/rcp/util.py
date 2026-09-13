import json
import math
import os
import random
import numpy as np

def set_seed(s):
    random.seed(s)
    np.random.seed(s)

def phi():
    return (1.0 + math.sqrt(5.0)) / 2.0

def Lambda():
    return math.log(phi()) / math.log(2.0 * math.pi)

def save_json(obj, path):
    with open(path, "w") as f:
        json.dump(obj, f, indent=2)

def ensure_dirs():
    os.makedirs("results", exist_ok=True)
    os.makedirs("logs", exist_ok=True)

