import json
import os

SETTINGS_FILE = os.getenv("SETTINGS_FILE", "settings.json")

def get_settings():
    if not os.path.exists(SETTINGS_FILE):
        raise FileNotFoundError(f"Settings file not found: {SETTINGS_FILE}")

    with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)
