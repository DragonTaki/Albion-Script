# ----- ----- ----- -----
# config.py
# For Albion Online "Griffin Empire" Guild only
# Do not distribute or modify
# Author: DragonTaki (https://github.com/DragonTaki)
# Create Date: 2025/04/18
# Update Date: 2025/04/22
# Version: v1.1
# ----- ----- ----- -----

from enum import Enum

# Guild Info List
GUILD_INFO_LIST = [{"name":"Griffin Empire", "id":"sAFfW_tPSkuU_49gvg4sZQ", "tag":"GE"}]

# CSV Headers
CSV_HEADERS = ["Player", "7DaysAttendance", "14DaysAttendance", "28DaysAttendance"]

# Attendance Days
INTERVALS = [7, 14, 28]
DAYS_LOOKBACK = max(INTERVALS)

# Folder Paths
CACHE_FOLDER = "cache"
DEBUG_FOLDER = "temp_debug"
EXTRA_ATTENDANCE_FOLDER = "extra_attendance"
EXTRA_ATTENDANCE_FOLDER_FORMAT = "%d-%m-%Y"
REPORT_FOLDER = "report"
TEMP_FOLDER = "temp"

# File Formats
TEXT_EXTENSIONS = (".txt")
IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg")
CACHE_EXTENSION = ".cache"
CSV_EXTENSION = ".csv"

# Cache Types Enum
class CacheType(Enum):
    MEMBERLIST = "memberlist"
    ATTENDANCE = "attendance"
    TEXTFILE = "textfile"
    SCREENSHOT = "screenshot"

# Cache Settings
CACHE_EXPIRY_HOURS = 8
MAX_CACHE_VERSIONS = 1

# CSV Settings
MAX_CSV_VERSIONS = 3
CSV_REPORT_PREFIX = "attendance_data_"
CSV_TIMESTAMP_FORMAT = "%d%m%Y_%H%M%S"

# Time Formats
TIMESTAMP_FORMAT = "%d/%m/%Y %H:%M:%S"

# Limit Version
TRIAL_VERSION = True
TRIAL_DATE = 7
EXPIRE_DATE = "YYYY-MM-DD"