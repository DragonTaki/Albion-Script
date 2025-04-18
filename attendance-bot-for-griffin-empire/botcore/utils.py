# ----- ----- ----- -----
# utils.py
# For Albion Online "Griffin Empire" Guild only
# Do not distribute or modify
# Author: DragonTaki (https://github.com/DragonTaki)
# Create Date: 2025/04/18
# Update Date: 2025/04/18
# Version: v1.0
# ----- ----- ----- -----

import os
import time
import hashlib

# Generate random filename based on type
def generate_cache_filename(cache_type):
    timestamp = str(time.time()).encode("utf-8")
    filename_hash = hashlib.sha256(timestamp).hexdigest()[:16]
    return f"{cache_type}_{filename_hash}.cache"

# Construct full path for a cache file
def get_cache_file_path(filename):
    from .config import CACHE_FOLDER
    return os.path.join(CACHE_FOLDER, filename)
