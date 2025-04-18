# ----- ----- ----- -----
# config.py
# For Albion Online "Griffin Empire" Guild only
# Do not distribute or modify
# Author: DragonTaki (https://github.com/DragonTaki)
# Create Date: 2025/04/18
# Update Date: 2025/04/18
# Version: v1.0
# ----- ----- ----- -----

from enum import Enum

# Guild Info List
GUILD_INFO_LIST = [{"name":"Griffin Empire", "id":"sAFfW_tPSkuU_49gvg4sZQ", "tag":"GE"}]

# CSV Headers
CSV_HEADERS = ["Player", "7DaysAttendance", "14DaysAttendance", "28DaysAttendance"]
INTERVALS = [7, 14, 28]

# Folder paths
CACHE_FOLDER = "cache"
SCREENSHOT_FOLDER = "screenshot"

# Cache Types Enum
class CacheType(Enum):
    PLAYERS = "players"
    ATTENDANCE = "attendance"
    OCR = "ocr"

# Cache Settings
CACHE_EXPIRY_HOURS = 8
MAX_CACHE_VERSIONS = 1

# CSV Settings
MAX_CSV_VERSIONS = 3

# Time Formats
DATE_FORMAT = "%d-%m-%Y"
TIMESTAMP_FORMAT = "%d/%m/%Y %H:%M:%S"
