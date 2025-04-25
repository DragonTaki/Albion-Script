# ----- ----- ----- -----
# process_textfile.py
# For Albion Online "Griffin Empire" Guild only
# Do not distribute or modify
# Author: DragonTaki (https://github.com/DragonTaki)
# Create Date: 2025/04/23
# Update Date: 2025/04/25
# Version: v1.1
# ----- ----- ----- -----

from .config.constant import TEXTFILE_ENCODING
from .logger import LogLevel, log

# Constants for Textfile Processing
INGAME_GUILD_DATA_COLUMNS = ["Character Name", "Last Seen", "Roles"]
INGAME_GUILD_ONLINE_STRING = "Online"

def parse_txt_file(filepath):
    try:
        with open(filepath, "r", encoding=TEXTFILE_ENCODING) as f:
            lines = [line.strip() for line in f if line.strip()]
        if not lines or lines[0].replace('"', "").split("\t") != INGAME_GUILD_DATA_COLUMNS:
            log(f"Invalid format in file: \"{filepath}\".", LogLevel.WARN)
            return []

        entries = []
        for line in lines[1:]:
            parts = line.replace('"', "").split("\t")
            if len(parts) >= 2 and parts[1].strip() == INGAME_GUILD_ONLINE_STRING:
                entries.append(parts[0].strip())

        log(f"Read attendance from file: \"{filepath}\".")
        return entries

    except Exception as e:
        log(f"Failed to parse \"{filepath}\": {e}.", LogLevel.ERROR)
        return []
