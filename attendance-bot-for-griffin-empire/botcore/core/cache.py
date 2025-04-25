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

from botcore.config.constant import EXTENSIONS
from botcore.config.settings import FOLDER_PATHS
from .logger import LogLevel, log
from .utils import (
    generate_cache_filename,
    get_cache_file_path,
    get_relative_path_to_target,
    ensure_folder_exists
)

# ----- Cache Settings -----
CACHE_EXPIRY_HOURS = 8
MAX_CACHE_VERSIONS = 1

# ----- Cache Type Enum -----
class CacheType(Enum):
    MEMBERLIST = "memberlist"
    ATTENDANCE = "attendance"
    TEXTFILE   = "textfile"
    SCREENSHOT = "screenshot"

CACHE_TYPES = [e.value for e in CacheType]

# ----- Internal Helpers -----
def _is_valid_cache_structure(data: dict) -> bool:
    """Check if cache dict contains required keys."""
    required_keys = {"timestamp", "type", "json_data"}
    return isinstance(data, dict) and required_keys.issubset(data)

def _is_cache_expired(timestamp: datetime) -> bool:
    """Determine if cache is expired."""
    return datetime.now(timezone.utc) - timestamp >= timedelta(hours=CACHE_EXPIRY_HOURS)

def _remove_file_safely(file_path: str, reason: str = ""):
    """Attempt to remove a file and log if necessary."""
    try:
        os.remove(file_path)
        if reason:
            log(f"Removed file '{file_path}' due to {reason}.", LogLevel.WARN)
    except Exception as e:
        log(f"Failed to remove '{file_path}': {e}", LogLevel.ERROR)

# ----- Save to Cache -----
def save_to_cache(data_dict: dict):
    """
    Save dictionary data to a binary cache file.
    Expected dict format: {"timestamp": ..., "type": ..., "json_data": ...}
    """
    if not _is_valid_cache_structure(data_dict):
        log("Invalid cache data format. Must include 'timestamp', 'type', 'json_data'.", LogLevel.ERROR)
        return

    cache_type = data_dict["type"]
    if cache_type not in CACHE_TYPES:
        log(f"Unsupported cache type: '{cache_type}'", LogLevel.ERROR)
        return

    filename = generate_cache_filename(cache_type)
    full_path = get_cache_file_path(filename)
    ensure_folder_exists(os.path.abspath(FOLDER_PATHS.cache))

    try:
        with open(full_path, "wb") as f:
            pickle.dump(data_dict, f)
        relative_path = get_relative_path_to_target(full_path)
        log(f"{cache_type.capitalize()} data cached as '{relative_path}'.")
        cleanup_old_cache_files(cache_type, keep_count=MAX_CACHE_VERSIONS)
    except Exception as e:
        log(f"Failed to save cache: {e}", LogLevel.ERROR)


def save_to_cache_if_needed(cache_type: CacheType, data, if_save: bool, saved_item_name=""):
    """
    Wrapper to conditionally save data to cache.
    """
    if not isinstance(cache_type, CacheType):
        log("Invalid cache type argument. Must be a CacheType enum.", LogLevel.ERROR)
        return

    if if_save:
        if data:
            cache_data = {
                "timestamp": datetime.now(timezone.utc),
                "type": cache_type.value,
                "json_data": data
            }
            save_to_cache(cache_data)
            log(f"{saved_item_name} saved to cache.")
        else:
            log("Data is empty. Nothing saved to cache.", LogLevel.WARN)

# ----- Load from Cache -----
def load_from_cache(cache_type: str):
    """
    Load the latest valid (non-expired) cache of given type.
    Returns json_data if valid cache exists, else None.
    """
    if cache_type not in CACHE_TYPES:
        log(f"Invalid cache type requested: '{cache_type}'", LogLevel.ERROR)
        return None

    cache_folder = os.path.abspath(FOLDER_PATHS.cache)
    ensure_folder_exists(cache_folder)

    cache_files = [
        f for f in os.listdir(cache_folder)
        if f.startswith(f"{cache_type}_") and f.endswith(EXTENSIONS.cache)
    ]

    latest_valid = None
    latest_time = None
    latest_file = None

    for fname in cache_files:
        full_path = get_cache_file_path(fname)

        try:
            if os.path.getsize(full_path) == 0:
                _remove_file_safely(full_path, "empty content")
                continue

            with open(full_path, "rb") as f:
                cache = pickle.load(f)

            if cache.get("type") != cache_type:
                _remove_file_safely(full_path, "inconsistent cache type")
                continue

            if _is_cache_expired(cache.get("timestamp", datetime.min.replace(tzinfo=timezone.utc))):
                _remove_file_safely(full_path, "expired timestamp")
                continue

            ctime = cache["timestamp"]
            if latest_time is None or ctime > latest_time:
                latest_valid = cache
                latest_time = ctime
                latest_file = full_path

        except Exception as e:
            _remove_file_safely(full_path, f"exception while loading: {e}")

    if latest_valid:
        relative_path = get_relative_path_to_target(latest_file)
        log(f"Loaded valid cache from '{relative_path}'.")
        return latest_valid["json_data"]

    return None

# ----- Cache Cleanup -----
def cleanup_old_cache_files(cache_type: str, keep_count: int):
    """
    Delete older versions of cache files, keeping only the latest 'keep_count' files.
    Returns number of deleted files.
    """
    deleted_count = 0
    cache_folder = os.path.abspath(FOLDER_PATHS.cache)
    ensure_folder_exists(cache_folder)

    types_to_clean = CACHE_TYPES if cache_type == "all" else [cache_type]

    for ctype in types_to_clean:
        if ctype not in CACHE_TYPES:
            log(f"Invalid cache type during cleanup: '{ctype}'", LogLevel.ERROR)
            continue

        try:
            matched_files = [
                f for f in os.listdir(cache_folder)
                if f.startswith(f"{ctype}_") and f.endswith(EXTENSIONS.cache)
            ]
            full_paths = [
                (get_cache_file_path(f), os.path.getmtime(get_cache_file_path(f)))
                for f in matched_files
            ]
            full_paths.sort(key=lambda x: x[1], reverse=True)

            for file_path, _ in full_paths[keep_count:]:
                _remove_file_safely(file_path, "exceed version limit")
                deleted_count += 1
        except Exception as e:
            log(f"Error during cache cleanup for type '{ctype}': {e}", LogLevel.ERROR)

    return deleted_count


def clear_all_cache_files():
    """Convenience method to remove all cache files."""
    return cleanup_old_cache_files("all", keep_count=0)
