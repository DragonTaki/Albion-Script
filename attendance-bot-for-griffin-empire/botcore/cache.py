# ----- ----- ----- -----
# cache.py
# For Albion Online "Griffin Empire" Guild only
# Do not distribute or modify
# Author: DragonTaki (https://github.com/DragonTaki)
# Create Date: 2025/04/18
# Update Date: 2025/04/18
# Version: v1.2
# ----- ----- ----- -----

import os
from datetime import datetime, timezone, timedelta

import pickle

from .config import CacheType, CACHE_EXPIRY_HOURS, CACHE_FOLDER, MAX_CACHE_VERSIONS
from .logger import log
from .utils import generate_cache_filename, get_cache_file_path

# Extracted valid types for internal lookup
CACHE_TYPES = [e.value for e in CacheType]
CACHE_FILE_EXT = ".cache"

# Cleanup old cache files, keeping only the latest `keep_count`
def cleanup_old_cache_files(cache_type, keep_count):
    types_to_clean = CACHE_TYPES if cache_type == "all" else [cache_type]

    deleted_count = 0

    for ctype in types_to_clean:
        if ctype not in CACHE_TYPES:
            log(f"Invalid cache type for cleanup: {ctype}", "e")
            continue

        try:
            all_files = [
                f for f in os.listdir(CACHE_FOLDER)
                if f.startswith(f"{ctype}_") and f.endswith(CACHE_FILE_EXT)
            ]
            full_paths = [
                (get_cache_file_path(f), os.path.getmtime(get_cache_file_path(f)))
                for f in all_files
            ]
            full_paths.sort(key=lambda x: x[1], reverse=True)

            files_to_delete = full_paths[keep_count:]
            for file_path, _ in files_to_delete:
                os.remove(file_path)
                log(f"Removed old cache: {os.path.basename(file_path)}.", "w")
                deleted_count += 1
        except Exception as e:
            log(f"Error during cache cleanup: {e}.", "e")

    return deleted_count

# Save cache as JSON data in binary format
def save_to_cache(data_dict):
    if not isinstance(data_dict, dict):
        log("Cache data must be a dictionary.", "e")
        return

    required_keys = {"type", "json_data"}
    if not required_keys.issubset(data_dict):
        log(f"Cache data missing required keys: {required_keys}.", "e")
        return

    cache_type = data_dict["type"]
    if cache_type not in CACHE_TYPES:
        log(f"Unsupported cache type: {cache_type}.", "e")
        return

    filename = generate_cache_filename(cache_type)
    full_path = get_cache_file_path(filename)

    try:
        os.makedirs(CACHE_FOLDER, exist_ok=True)
        with open(full_path, "wb") as f:
            pickle.dump({
                "timestamp": datetime.now(timezone.utc),
                "type": cache_type,
                "json_data": data_dict["json_data"]
            }, f)
        log(f"{cache_type.capitalize()} data cached as \"{filename}\".")

        cleanup_old_cache_files(cache_type, keep_count=MAX_CACHE_VERSIONS)

    except Exception as e:
        log(f"Failed to save cache: {e}", "e")

# Load the latest valid cache of given type
def load_from_cache(cache_type):
    cache_files = [
        f for f in os.listdir(CACHE_FOLDER)
        if f.endswith(CACHE_FILE_EXT) and f.startswith(f"{cache_type}_")
    ]
    latest_valid = None
    latest_time = None

    for fname in cache_files:
        try:
            full_path = get_cache_file_path(fname)
            if os.path.getsize(full_path) == 0:
                os.remove(full_path)
                continue

            with open(full_path, "rb") as f:
                cache = pickle.load(f)

            ctime = cache.get("timestamp")
            data_type = cache.get("type")

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
            os.remove(get_cache_file_path(fname))
            log(f"Invalid cache file \"{fname}\" removed due to error: {e}", "w")

    if latest_valid:
        log(f"Valid {cache_type} cache loaded.")
        return latest_valid["json_data"]

    log(f"No valid {cache_type} cache found.", "w")
    return None

def clear_all_cache_files():
    return cleanup_old_cache_files("all", keep_count=0)
