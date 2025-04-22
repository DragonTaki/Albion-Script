# ----- ----- ----- -----
# utils.py
# For Albion Online "Griffin Empire" Guild only
# Do not distribute or modify
# Author: DragonTaki (https://github.com/DragonTaki)
# Create Date: 2025/04/18
# Update Date: 2025/04/22
# Version: v1.1
# ----- ----- ----- -----

import os
import time
import hashlib
import sys

from .logger import log

# Constants for detecting PyInstaller environment
IS_PACKAGED = hasattr(sys, "_MEIPASS")
BASE_PATH = os.getcwd()

# Constants for general usage
DEFAULT_ENCODING = "utf-8"
DEFAULT_HASH_LENGTH = 16

# Ensure a folder exists before using it
def ensure_folder_exists(folder_path):
    """Create the folder if it doesn't exist"""
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

# Generate random filename based on type
def generate_cache_filename(cache_type):
    """Generate a unique cache filename with prefix"""
    timestamp = str(time.time()).encode(DEFAULT_ENCODING)
    filename_hash = hashlib.sha256(timestamp).hexdigest()[:DEFAULT_HASH_LENGTH]
    return f"{cache_type}_{filename_hash}.cache"

# Construct full path for a cache file
def get_cache_file_path(filename):
    """Return full path and ensure the cache folder exists"""
    from .config import CACHE_FOLDER
    ensure_folder_exists(CACHE_FOLDER)
    return os.path.join(CACHE_FOLDER, filename)

# Unified path resolver for resources in packaged or dev mode
def get_path(*relative_parts):
    """Get correct file path whether running from source or PyInstaller package"""
    return os.path.join(BASE_PATH, *relative_parts)

# Get the relative path from the current working directory to a target file
def get_relative_path_to_target(filepath):
    """
    Calculate the relative path from BASE_PATH to the target file,
    supporting both absolute and relative input.
    Return relative path to BASE_PATH if same drive, else return absolute path.
    """
    if not filepath or not isinstance(filepath, str):
        log("Invalid filepath provided to get_relative_path_to_target.", "w")
        return None

    try:
        # Normalize input to absolute path
        filepath = os.path.abspath(filepath)
        # Try to calculate relative path
        return os.path.relpath(filepath, BASE_PATH)
    except ValueError as e:
        # Handle case where drives differ (e.g., E: vs C:)
        return filepath
