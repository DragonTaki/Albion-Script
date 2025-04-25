# ----- ----- ----- -----
# cache.py
# For Albion Online "Griffin Empire" Guild only
# Do not distribute or modify
# Author: DragonTaki (https://github.com/DragonTaki)
# Create Date: 2025/04/18
# Update Date: 2025/04/25
# Version: v1.5
# ----- ----- ----- -----

import os
import pickle
from datetime import datetime, timezone, timedelta
from enum import Enum

from botcore.config.constant import CONSTANTS
EXTENSIONS = CONSTANTS.EXTENSIONS
from botcore.config.settings import CACHE_FOLDER
from .logger import LogLevel, log
from .utils import (
    generate_cache_filename,
    get_cache_file_path,
    get_relative_path_to_target,
    ensure_folder_exists
)

# Settings for Cache
CACHE_EXPIRY_HOURS = 8
MAX_CACHE_VERSIONS = 1

# Constants for Cache
## Cache Types
class CacheType(Enum):
    MEMBERLIST = "memberlist"
    ATTENDANCE = "attendance"
    TEXTFILE   = "textfile"
    SCREENSHOT = "screenshot"
CACHE_TYPES = [e.value for e in CacheType]

# Save cache as JSON data in binary format
def save_to_cache(data_dict):
    if not isinstance(data_dict, dict):
        log("Cache data must be a dictionary.", LogLevel.ERROR)
        return

    required_keys = {"timestamp", "type", "json_data"}
    if not required_keys.issubset(data_dict):
        log(f"Cache data missing required keys: '{required_keys}'", LogLevel.ERROR)
        return

    cache_type = data_dict["type"]
    if cache_type not in CACHE_TYPES:
        log(f"Unsupported cache type: '{cache_type}'", LogLevel.ERROR)
        return

    filename = generate_cache_filename(cache_type)
    full_path = get_cache_file_path(filename)

    try:
        ensure_folder_exists(os.path.abspath(os.path.join(CACHE_FOLDER)))
        with open(full_path, "wb") as f:
            pickle.dump({
                "timestamp": datetime.now(timezone.utc),
                "type": cache_type,
                "json_data": data_dict["json_data"]
            }, f)
        relative_path = get_relative_path_to_target(full_path)
        log(f"{cache_type.capitalize()} data cached as \"{relative_path}\".")

        cleanup_old_cache_files(cache_type, keep_count=MAX_CACHE_VERSIONS)

    except Exception as e:
        log(f"Failed to save cache: {e}", LogLevel.ERROR)

def save_to_cache_if_needed(cache_type, data, if_save_to_cache, saved_item_name=""):
    """
    Save data to cache if the condition is met.
    
    :param cache_type: Cache type (e.g., CacheType.MEMBERLIST, CacheType.SCREENSHOT, etc.)
    :param data: Data to be cached (could be a dictionary or other structures)
    :param if_save_to_cache: Flag to check if the data should be saved to cache
    :param additional_info: Additional information to log or display (optional)
    """
    if if_save_to_cache:
        if data:
            cache_data = {
                "timestamp": datetime.now(timezone.utc),
                "type": cache_type.value,
                "json_data": data
            }
            save_to_cache(cache_data)
            log(f"{saved_item_name} saved to cache.")
        else:
            log(f"Failed. Nothing saved to cache.", LogLevel.ERROR)

# Load the latest valid cache of given type
def load_from_cache(cache_type):
    cache_folder_path = os.path.abspath(os.path.join(CACHE_FOLDER))
    ensure_folder_exists(cache_folder_path)

    cache_files = [
        f for f in os.listdir(cache_folder_path)
        if f.endswith(EXTENSIONS.cache) and f.startswith(f"{cache_type}_")
    ]
    latest_valid = None
    latest_valid_file = None
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
                log(f"Inconsistent type in file \"{fname}\" (found: '{data_type}'), file removed.", LogLevel.WARN)
                continue

            if datetime.now(timezone.utc) - ctime >= timedelta(hours=CACHE_EXPIRY_HOURS):
                os.remove(full_path)
                continue

            if latest_time is None or ctime > latest_time:
                latest_time = ctime
                latest_valid = cache
                latest_valid_file = full_path

        except Exception as e:
            os.remove(get_cache_file_path(fname))
            log(f"Invalid cache file \"{fname}\", removed due to error: {e}", LogLevel.WARN)

    if latest_valid:
        relative_path = get_relative_path_to_target(latest_valid_file)
        log(f"Success loaded \"{relative_path}\" {cache_type} cache.")
        return latest_valid["json_data"]

    return None

# Delete old cache files, keeping only the latest `keep_count`
def cleanup_old_cache_files(cache_type, keep_count):
    types_to_clean = CACHE_TYPES if cache_type == "all" else [cache_type]
    deleted_count = 0
    cache_folder_path = os.path.abspath(os.path.join(CACHE_FOLDER))
    ensure_folder_exists(cache_folder_path)

    for ctype in types_to_clean:
        if ctype not in CACHE_TYPES:
            log(f"Invalid cache type for cleanup: '{ctype}'", LogLevel.ERROR)
            continue

        try:
            all_files = [
                f for f in os.listdir(cache_folder_path)
                if f.startswith(f"{ctype}_") and f.endswith(EXTENSIONS.cache)
            ]
            full_paths = [
                (get_cache_file_path(f), os.path.getmtime(get_cache_file_path(f)))
                for f in all_files
            ]
            full_paths.sort(key=lambda x: x[1], reverse=True)

            files_to_delete = full_paths[keep_count:]
            for file_path, _ in files_to_delete:
                os.remove(file_path)
                relative_path = get_relative_path_to_target(file_path)
                log(f"Removed old cache: \"{relative_path}\".", LogLevel.WARN)
                deleted_count += 1
        except Exception as e:
            log(f"Error during cache cleanup: {e}", LogLevel.ERROR)

    return deleted_count

# Clear all cache files
def clear_all_cache_files():
    return cleanup_old_cache_files("all", keep_count=0)
