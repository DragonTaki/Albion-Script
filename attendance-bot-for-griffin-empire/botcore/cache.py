# ----- ----- ----- -----
# cache.py
# For Albion Online "Griffin Empire" Guild only
# Do not distribute or modify
# Author: DragonTaki (https://github.com/DragonTaki)
# Create Date: 2025/04/18
# Update Date: 2025/04/18
# Version: v1.1
# ----- ----- ----- -----

import os
import time
import pickle
import hashlib
import json  # 🔴 Add for JSON serialization
from datetime import datetime, timezone, timedelta
from .config import CACHE_EXPIRY_HOURS
from .logger import log

# 🔴 Constants for cache
CACHE_FOLDER = "cache"
CACHE_TYPES = ["players", "attendance", "ocr"]  # three cache types
CACHE_FILE_EXT = ".cache"
# 🔴 Generate random filename based on type
def generate_cache_filename(cache_type):  # 🔴 Ensure cache_type is received
    timestamp = str(time.time()).encode("utf-8")
    filename_hash = hashlib.sha256(timestamp).hexdigest()[:16]
    return f"{cache_type}_{filename_hash}{CACHE_FILE_EXT}"

# 🔴 Save cache (JSON data in binary format)
def save_to_cache(data_dict):
    # 🔴 Validate data_dict before saving
    if not isinstance(data_dict, dict):
        log("Cache data must be a dictionary.", "e")
        return

    required_keys = {"type", "json_data"}
    if not required_keys.issubset(data_dict):
        log(f"Cache data missing required keys: {required_keys}", "e")
        return

    if data_dict["type"] not in CACHE_TYPES:  # 🔴 Use constant
        log(f"Unsupported cache type: {data_dict['type']}", "e")
        return

    cache_type = data_dict["type"]
    filename = generate_cache_filename(cache_type)
    full_path = os.path.join(CACHE_FOLDER, filename)

    try:
        os.makedirs(CACHE_FOLDER, exist_ok=True)  # 🔴 Ensure directory exists
        with open(full_path, "wb") as f:
            pickle.dump({
                "timestamp": datetime.now(timezone.utc),
                "type": cache_type,
                "json_data": data_dict["json_data"]
            }, f)
        log(f"{cache_type.capitalize()} data cached as \"{filename}\".")
    except Exception as e:
        log(f"Failed to save cache: {e}", "e")

# 🔴 Load the latest valid cache of given type
def load_from_cache(cache_type):
    # 🔴 List all files with matching prefix and extension
    cache_files = [f for f in os.listdir(CACHE_FOLDER)
                   if f.endswith(CACHE_FILE_EXT) and f.startswith(f"{cache_type}_")]
    latest_valid = None
    latest_time = None

    for fname in cache_files:
        try:
            full_path = os.path.join(CACHE_FOLDER, fname)
            if os.path.getsize(full_path) == 0:
                os.remove(full_path)
                continue
            with open(full_path, "rb") as f:
                cache = pickle.load(f)

            ctime = cache.get("timestamp")
            data_type = cache.get("type")

            # 🔴 Added: type consistency check
            if data_type != cache_type:
                os.remove(full_path)
                log(f"Inconsistent type in \"{fname}\" (found: {data_type}), file removed.", "w")
                continue

            if datetime.now(timezone.utc) - ctime >= timedelta(hours=CACHE_EXPIRY_HOURS):
                os.remove(full_path)
                continue

            if latest_time is None or ctime > latest_time:
                latest_time = ctime
                latest_valid = cache

        except Exception as e:
            os.remove(full_path)
            log(f"Invalid cache file \"{fname}\" removed due to error: {e}", "w")

    if latest_valid:
        log(f"Valid {cache_type} cache loaded.")
        return latest_valid["json_data"]

    log(f"No valid {cache_type} cache found.", "w")
    return None

# 🔴 Optional: remove all cache files
def clear_all_cache_files():
    if not os.path.exists(CACHE_FOLDER):
        return 0
    count = 0
    for fname in os.listdir(CACHE_FOLDER):
        if fname.endswith(CACHE_FILE_EXT):
            try:
                os.remove(os.path.join(CACHE_FOLDER, fname))
                count += 1
            except:
                continue
    return count
