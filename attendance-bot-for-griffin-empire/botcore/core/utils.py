# ----- ----- ----- -----
# utils.py
# For Albion Online "Griffin Empire" Guild only
# Do not distribute or modify
# Author: DragonTaki (https://github.com/DragonTaki)
# Create Date: 2025/04/18
# Update Date: 2025/04/26
# Version: v1.4
# ----- ----- ----- -----

import hashlib
import os
import time
from datetime import datetime
from typing import Optional

from botcore.config.constant import DATETIME_FORMATS, TEXTFILE_ENCODING
from botcore.config.settings import FOLDER_PATHS
from botcore.config.runtime import EXE_BASE_PATH, MEIPASS_PATH
from .logger import log, LogLevel

# ----- Constants ----- #
DEFAULT_HASH_LENGTH = 16  # Length for generated file hash


def ensure_folder_exists(folder_path: str) -> None:
    """
    Ensure that a folder exists. If it doesn't exist, create it.
    Internal use only.

    Args:
        folder_path (str): The path of the folder to check and create.
    """
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)


def is_valid_folder_name(folder_name: str) -> bool:
    """
    Check if a folder name matches the expected folder date format (YYYY-MM-DD).
    Public utility.

    Args:
        folder_name (str): The folder name to validate.

    Returns:
        bool: True if the folder name matches the date format, False otherwise.
    """
    try:
        datetime.strptime(folder_name, DATETIME_FORMATS.folder)
        return True
    except ValueError:
        return False


def generate_cache_filename(cache_type: str) -> str:
    """
    Generate a unique filename for cache storage based on current timestamp.

    Args:
        cache_type (str): The type of cache (e.g., 'attendance', 'player').

    Returns:
        str: A unique cache filename in the format `<cache_type>_<hash>.cache`.
    """
    timestamp = str(time.time()).encode(TEXTFILE_ENCODING)
    filename_hash = hashlib.sha256(timestamp).hexdigest()[:DEFAULT_HASH_LENGTH]
    return f"{cache_type}_{filename_hash}.cache"


def get_cache_file_path(filename: str) -> str:
    """
    Get the full cache file path and ensure the cache folder exists.

    Args:
        filename (str): The filename of the cache file.

    Returns:
        str: The full path to the cache file.
    """
    ensure_folder_exists(FOLDER_PATHS.cache)
    return os.path.join(FOLDER_PATHS.cache, filename)


def get_runtime_base(use_meipass: bool = False) -> str:
    """
    Get the correct base path depending on runtime environment (EXE or MEIPASS).

    Args:
        use_meipass (bool): Whether to use the MEIPASS path (default is False).

    Returns:
        str: The base path to use (either EXE or MEIPASS path).
    """
    return MEIPASS_PATH if use_meipass and MEIPASS_PATH else EXE_BASE_PATH


def get_path(*relative_parts: str, use_meipass: bool = False) -> str:
    """
    Construct a full path from base directory + relative path segments.

    Args:
        relative_parts (str): One or more relative path segments to append to the base path.
        use_meipass (bool): Whether to use MEIPASS for path resolution (default is False).

    Returns:
        str: The full constructed path.
    """
    return os.path.join(get_runtime_base(use_meipass), *relative_parts)


def get_relative_path_to_target(filepath: str) -> Optional[str]:
    """
    Get a relative path to a target file from the base folder.
    Returns absolute path if drives mismatch or error occurs.

    Args:
        filepath (str): The full absolute path to the target file.

    Returns:
        Optional[str]: The relative path to the target file, or the absolute path if an error occurs.
    """
    if not filepath or not isinstance(filepath, str):
        log("Invalid filepath provided to get_relative_path_to_target.", LogLevel.WARN)
        return None

    try:
        filepath = os.path.abspath(filepath)
        return os.path.relpath(filepath, EXE_BASE_PATH)
    except ValueError:
        return filepath


def get_file_checksum(filepath: str) -> str:
    """
    Compute MD5 checksum of a file for integrity validation.

    Args:
        filepath (str): The path to the file to compute the checksum.

    Returns:
        str: The MD5 checksum of the file.
    """
    with open(filepath, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


def check_file_checksum(filepath: str, expected_checksum: str) -> bool:
    """
    Validate whether a file's checksum matches the expected hash.

    Args:
        filepath (str): The path to the file to check.
        expected_checksum (str): The expected MD5 checksum of the file.

    Returns:
        bool: True if the file's checksum matches the expected checksum, False otherwise.
    """
    if not os.path.exists(filepath):
        return False
    return get_file_checksum(filepath) == expected_checksum


def list_dirs_sorted_by_date(base_path: str) -> list[str]:
    """
    List all subdirectories in the given path, sorted by their name (assuming date-based folder names).

    Args:
        base_path (str): The base path to list subdirectories from.

    Returns:
        list[str]: A sorted list of subdirectory names, sorted by date (in YYYY-MM-DD format).
    """
    if not os.path.exists(base_path):
        return []

    folders = [
        name for name in os.listdir(base_path)
        if os.path.isdir(os.path.join(base_path, name))
    ]

    # Sort by folder name (example is YYYY-MM-DD format)
    folders.sort()
    return folders
