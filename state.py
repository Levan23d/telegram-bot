import json
import os

from config import DATA_FILE, STATS_FILE

user_category = {}
user_state = {}
temp_data = {}


def load_data():
    if not os.path.exists(DATA_FILE):
        data = {"categories": {}}
        save_data(data)
        return data

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_stats():
    if not os.path.exists(STATS_FILE):
        data = {
            "users": {},
            "total_starts": 0,
            "category_clicks": {}
        }
        save_stats(data)
        return data

    with open(STATS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_stats(data):
    with open(STATS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


data_store = load_data()
stats_store = load_stats()
