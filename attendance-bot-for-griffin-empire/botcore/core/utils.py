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
import sys
import time
from datetime import datetime
from typing import Callable, Optional

from botcore.config.constant import DATETIME_FORMATS, TEXTFILE_ENCODING
from botcore.config.settings import FOLDER_PATHS
from botcore.config.runtime import EXE_BASE_PATH, MEIPASS_PATH
from .logger import log, LogLevel

# ----- Constants -----
DEFAULT_HASH_LENGTH = 16  # Length for generated file hash

def _ensure_folder_exists(folder_path: str) -> None:
    """
    Ensure that a folder exists. If it doesn't exist, create it.
    Internal use only.
    """
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)


def is_valid_folder_name(folder_name: str) -> bool:
    """
    Check if a folder name matches the expected folder date format.
    Public utility.
    """
    try:
        datetime.strptime(folder_name, DATETIME_FORMATS.folder)
        return True
    except ValueError:
        return False


def generate_cache_filename(cache_type: str) -> str:
    """
    Generate a unique filename for cache storage.
    Public utility.
    """
    timestamp = str(time.time()).encode(TEXTFILE_ENCODING)
    filename_hash = hashlib.sha256(timestamp).hexdigest()[:DEFAULT_HASH_LENGTH]
    return f"{cache_type}_{filename_hash}.cache"


def get_cache_file_path(filename: str) -> str:
    """
    Get the full cache file path and ensure the folder exists.
    Public utility.
    """
    _ensure_folder_exists(FOLDER_PATHS.cache)
    return os.path.join(FOLDER_PATHS.cache, filename)


def get_runtime_base(use_meipass: bool = False) -> str:
    """
    Get the correct base path depending on runtime environment.
    Public utility.
    """
    return MEIPASS_PATH if use_meipass and MEIPASS_PATH else EXE_BASE_PATH


def get_path(*relative_parts: str, use_meipass: bool = False) -> str:
    """
    Construct a full path from base directory + relative path segments.
    Public utility.
    """
    return os.path.join(get_runtime_base(use_meipass), *relative_parts)


def get_relative_path_to_target(filepath: str) -> Optional[str]:
    """
    Get a relative path to a target file from the base folder.
    Returns absolute path if drives mismatch or error occurs.
    Public utility.
    """
    if not filepath or not isinstance(filepath, str):
        log("Invalid filepath provided to get_relative_path_to_target.", LogLevel.WARN)
        return None

    try:
        filepath = os.path.abspath(filepath)
        return os.path.relpath(filepath, BASE_PATH)
    except ValueError:
        return filepath


def _get_file_checksum(filepath: str) -> str:
    """
    Compute MD5 checksum of a file.
    Internal use only.
    """
    with open(filepath, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


def check_file_checksum(filepath: str, expected_checksum: str) -> bool:
    """
    Validate whether a file's checksum matches the expected hash.
    Public utility.
    """
    if not os.path.exists(filepath):
        return False
    return _get_file_checksum(filepath) == expected_checksum
