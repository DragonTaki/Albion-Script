# ----- ----- ----- -----
# process_textfile.py
# For Albion Online "Griffin Empire" Guild only
# Do not distribute or modify
# Author: DragonTaki (https://github.com/DragonTaki)
# Create Date: 2025/04/23
# Update Date: 2025/04/23
# Version: v1.0
# ----- ----- ----- -----

from .config import LogLevel
from .logger import log

# Constants
REQUIRED_COLUMNS = ["Character Name", "Last Seen", "Roles"]

def parse_txt_file(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]
        if not lines or lines[0].replace('"', "").split("\t") != REQUIRED_COLUMNS:
            log(f"Invalid format in file: \"{filepath}\".", LogLevel.WARN)
            return []
        entries = []
        for line in lines[1:]:
            parts = line.replace('"', "").split("\t")
            if len(parts) >= 2 and parts[1].strip() == "Online":
                entries.append(parts[0].strip())
        log(f"Read attendance from file: \"{filepath}\".")
        return entries
    except Exception as e:
        log(f"Failed to parse \"{filepath}\": {e}.", LogLevel.ERROR)
        return []
