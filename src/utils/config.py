import json

def load_config(path="config.json"):
    with open(path, "r") as f:
        return json.load(f)