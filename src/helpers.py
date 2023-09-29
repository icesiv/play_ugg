import json
import os
import time
import random

import constant
import pandas as pd


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


def save_to_excel(new_data):
    new_df = pd.DataFrame(new_data)

    try:
        existing_df = pd.read_excel(constant.EXCEL_FILE_PATH)
        combined_df = pd.concat([existing_df, new_df], ignore_index=True)
    except FileNotFoundError:
        combined_df = new_df

    combined_df.to_excel(constant.EXCEL_FILE_PATH, index=False)

    print(
        f'Data has been appended to {constant.EXCEL_FILE_PATH}')


def load_items(column_name, file_name):
    df = pd.read_excel(file_name)

    if column_name in df.columns:
        column_data = df[column_name].tolist()
        return (column_data)
    else:
        print(f"Column '{column_name}' not found in the Excel file.")
        return None
