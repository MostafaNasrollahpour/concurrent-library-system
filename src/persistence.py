import os
import json
from .logger import log_message


def load_json(file_path, default):
    """Load JSON data from file, return default if file doesn't exist or error"""
    if os.path.exists(file_path):
        try:
            with open(file_path, "r") as f:
                return json.load(f)
        except Exception as e:
            log_message(f"Error loading {file_path}: {e}")
    return default


def save_json(file_path, data):
    """Save data to JSON file"""
    try:
        log_dir = os.path.dirname(file_path)
        if not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
            
        with open(file_path, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        log_message(f"Error saving {file_path}: {e}")