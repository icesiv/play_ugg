import json
import os
import time
import random
from datetime import datetime


def get_file(filename):
    return os.path.join(os.path.dirname(__file__), filename)


def load_config():
    with open(get_file('../config.json')) as f:
        return json.load(f)


def wait(max, min=1):
    random_seconds = random.uniform(min, max)
    time.sleep(random_seconds)


def current_time():
    return time.time()

def current_time_text():
    now = datetime.now()
    date_time = now.strftime("%m-%d-%Y %H-%M")
    return date_time
