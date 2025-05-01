# ----- ----- ----- -----
# process_textfile.py
# For Albion Online "Griffin Empire" Guild only
# Do not distribute or modify
# Author: DragonTaki (https://github.com/DragonTaki)
# Create Date: 2025/04/23
# Update Date: 2025/05/01
# Version: v1.2
# ----- ----- ----- -----

from botcore.config.constant import TEXTFILE_ENCODING
from botcore.logging.app_logger import LogLevel, log


# ----- Constants ----- #
INGAME_GUILD_DATA_COLUMNS = ["Character Name", "Last Seen", "Roles"]
INGAME_GUILD_ONLINE_STRING = "Online"


# ----- Main Function ----- #
def parse_txt_file(filepath: str) -> list[str]:
    """
    Parse a text file containing in-game guild data and extract online player names.

    The file is expected to be tab-delimited and start with a header matching
    `INGAME_GUILD_DATA_COLUMNS`. Only entries with the second column equal to
    `INGAME_GUILD_ONLINE_STRING` are considered online and extracted.

    Args:
        filepath (str): The path to the `.txt` file to be parsed.

    Returns:
        list[str]: A list of player names who are currently online.
                   Returns an empty list if the file format is invalid or an error occurs.
    """
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
