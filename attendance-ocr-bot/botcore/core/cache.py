# ----- ----- ----- -----
# cache.py
# For Albion Online "Griffin Empire" Guild only
# Do not distribute or modify
# Author: DragonTaki (https://github.com/DragonTaki)
# Create Date: 2025/04/18
# Update Date: 2025/04/26
# Version: v1.6
# ----- ----- ----- -----

import os
import pickle
from datetime import datetime, timezone, timedelta
from typing import Any

from botcore.config.constant import CacheType, EXTENSIONS
from botcore.config.settings_manager import settings
from botcore.logging.app_logger import LogLevel, log
from .utils import (
    generate_cache_filename,
    get_cache_file_path,
    get_relative_path_to_target,
    ensure_folder_exists,
)

# ----- Cache Settings -----
CACHE_EXPIRY_HOURS = 8
MAX_CACHE_VERSIONS = 1

CACHE_TYPES = list(CacheType)


# ----- Internal Helpers -----
def _is_valid_cache_structure(data: dict) -> bool:
    """
    Check whether a dictionary follows the expected cache format.
    
    This function verifies that the provided dictionary contains the required keys 
    for the cache structure. The expected keys are: {"timestamp", "type", "json_data"}.

    Args:
        data (dict): The dictionary to be validated.

    Returns:
        bool: True if the dictionary contains the required keys, False otherwise.
    """
    required_keys = {"timestamp", "type", "json_data"}
    return isinstance(data, dict) and required_keys.issubset(data)

def _is_cache_expired(timestamp: datetime) -> bool:
    """
    Determine whether a cache timestamp is expired based on configured expiry hours.
    
    This function checks if the provided cache timestamp exceeds the configured expiration 
    period (in hours). If the timestamp is older than the configured expiry time, it returns True, 
    indicating that the cache is expired.

    Args:
        timestamp (datetime): The timestamp to be checked for expiry.

    Returns:
        bool: True if the cache is expired, False otherwise.
    """
    return datetime.now(timezone.utc) - timestamp >= timedelta(hours=CACHE_EXPIRY_HOURS)

def _remove_file_safely(file_path: str, reason: str = "") -> None:
    """
    Attempt to delete a file and log the action with a reason or any encountered error.
    
    This function tries to delete the specified file and logs the action. 
    If the deletion is successful, it logs the reason (if provided). 
    If the deletion fails, it logs an error with the exception message.

    Args:
        file_path (str): The absolute path to the file to be deleted.
        reason (str, optional): The reason for file removal. Defaults to an empty string, 
                                which indicates no specific reason.

    Returns:
        None
    """
    try:
        os.remove(file_path)
        if reason:
            log(f"Removed file '{file_path}' due to {reason}.", LogLevel.WARN)
        else:
            log(f"Removed file '{file_path}'.", LogLevel.WARN)
    except Exception as e:
        log(f"Failed to remove '{file_path}': {e}", LogLevel.ERROR)


# ----- Save to Cache -----
def save_to_cache(data_dict: dict) -> None:
    """
    Save a dictionary to disk as a binary cache file.
    The dictionary must contain keys: 'timestamp', 'type', and 'json_data'.

    Args:
        data_dict (dict): The cache data to be saved.
    """
    if not _is_valid_cache_structure(data_dict):
        log("Invalid cache data format. Must include 'timestamp', 'type', 'json_data'.", LogLevel.ERROR)
        return

    try:
        cache_type = CacheType(data_dict["type"])
    except ValueError:
        log(f"Unsupported cache type: '{data_dict['type']}'", LogLevel.ERROR)
        return

    filename = generate_cache_filename(cache_type)
    full_path = get_cache_file_path(filename)
    ensure_folder_exists(os.path.abspath(settings.folder_paths.cache))

    try:
        with open(full_path, "wb") as f:
            pickle.dump(data_dict, f)
        relative_path = get_relative_path_to_target(full_path)
        log(f"{cache_type.name.capitalize()} data cached as '{relative_path}'.")
        cleanup_old_cache_files(cache_type, keep_count=MAX_CACHE_VERSIONS)
    except Exception as e:
        log(f"Failed to save cache: {e}", LogLevel.ERROR)

def save_to_cache_if_needed(cache_type: CacheType, data: Any, if_save: bool, saved_item_name: str = "") -> None:
    """
    Save cache data only if the if_save flag is True and data is not empty.

    Args:
        cache_type (CacheType): The type of data to be cached.
        data (Any): The actual data object to be saved.
        if_save (bool): Whether to proceed with saving the data.
        saved_item_name (str, optional): Optional label for logging purpose.
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

def load_from_cache(cache_type: CacheType) -> Any:
    """
    Load the latest valid cache file of a given type.

    Args:
        cache_type (CacheType): CacheType enum member.

    Returns:
        Any: Cached 'json_data' content if valid cache is found; otherwise None.
    """
    if cache_type not in CACHE_TYPES:
        log(f"Invalid cache type requested: '{cache_type.name}'", LogLevel.ERROR)
        return None

    cache_folder = os.path.abspath(settings.folder_paths.cache)
    ensure_folder_exists(cache_folder)

    cache_prefix = f"{cache_type.value}_"

    cache_files = [
        f for f in os.listdir(cache_folder)
        if f.startswith(cache_prefix) and f.endswith(EXTENSIONS.cache)
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

            if cache.get("type") != cache_type.value:
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
def cleanup_old_cache_files(cache_type: CacheType, keep_count: int) -> int:
    """
    Remove old cache files of the specified type, keeping only the latest N versions.
    If the cache_type is CacheType.ALL, all cache files are cleaned except for the latest N versions of each type.

    Args:
        cache_type (CacheType): Specific cache type to clean. If CacheType.ALL, all cache types will be cleaned.
        keep_count (int): Number of recent files to retain.

    Returns:
        int: Number of deleted files.
    """
    deleted_count = 0
    cache_folder = os.path.abspath(settings.folder_paths.cache)
    ensure_folder_exists(cache_folder)

    if cache_type == CacheType.ALL:
        # When ALL is selected, clean all cache types
        cache_types_to_clean = [ct for ct in CacheType if ct != CacheType.ALL]
    elif cache_type in CACHE_TYPES:
        # Otherwise, clean only the specific cache type
        cache_types_to_clean = [cache_type]
    else:
        log(f"Invalid cache type during cleanup: '{cache_type.name}'", LogLevel.ERROR)
        return deleted_count

    try:
        for c_type in cache_types_to_clean:
            cache_prefix = f"{c_type.value}_"

            matched_files = [
                f for f in os.listdir(cache_folder)
                if f.startswith(cache_prefix) and f.endswith(EXTENSIONS.cache)
            ]

            full_paths = [
                (get_cache_file_path(f), os.path.getmtime(get_cache_file_path(f)))
                for f in matched_files
            ]
            full_paths.sort(key=lambda x: x[1], reverse=True)

            # Delete files beyond the keep_count
            for file_path, _ in full_paths[keep_count:]:
                _remove_file_safely(file_path)
                deleted_count += 1

    except Exception as e:
        log(f"Error during cache cleanup for type '{cache_type.name}': {e}", LogLevel.ERROR)

    return deleted_count

def clear_all_cache_files() -> int:
    """
    Remove all cache files from the cache folder.

    Returns:
        int: Number of deleted files.
    """
    return cleanup_old_cache_files(CacheType.ALL, keep_count=0)
