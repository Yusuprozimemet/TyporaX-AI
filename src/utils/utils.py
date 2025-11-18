# tools/utils.py
import os
import json
import pandas as pd
import logging
import sys
import io
from datetime import datetime

# Ensure log directory exists
os.makedirs("data", exist_ok=True)

# Create handlers that are safe for Unicode on Windows consoles.
# FileHandler: write UTF-8 encoded logs. StreamHandler: wrap stdout with
# a TextIOWrapper forcing UTF-8 with replacement for unencodable chars.
file_handler = logging.FileHandler("data/typorax.log", encoding="utf-8")
try:
    stream_wrapper = io.TextIOWrapper(
        sys.stdout.buffer, encoding="utf-8", errors="replace")
    stream_handler = logging.StreamHandler(stream_wrapper)
except Exception:
    # Fallback: use default StreamHandler if wrapper fails
    stream_handler = logging.StreamHandler()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[file_handler, stream_handler]
)


def get_logger(name: str = None):
    """
    Return a logger with the given name (or module name).
    Use this instead of logging directly.
    """
    return logging.getLogger(name or __name__)


def ensure_dir(path):
    os.makedirs(path, exist_ok=True)
    get_logger().debug(f"Ensured directory exists: {path}")
    return path


def load_json(path, default=None):
    if default is None:
        default = {}
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            get_logger().debug(f"Loaded JSON from {path}")
            return data
        except Exception as e:
            get_logger().error(f"Failed to load JSON {path}: {e}")
            return default
    else:
        get_logger().debug(f"JSON not found: {path}, returning default")
        return default


def save_json(data, path):
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        get_logger().debug(f"Saved JSON to {path}")
    except Exception as e:
        get_logger().error(f"Failed to save JSON {path}: {e}")


def log_activity(user_dir, activity):
    log_path = f"{user_dir}/activity.log"
    timestamp = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(f"{timestamp}: {activity}\n")
        get_logger("activity").info(
            f"User activity [{os.path.basename(user_dir)}]: {activity}")
    except Exception as e:
        get_logger("activity").error(f"Failed to log activity: {e}")
