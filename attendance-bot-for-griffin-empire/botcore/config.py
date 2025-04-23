# ----- ----- ----- -----
# config.py
# For Albion Online "Griffin Empire" Guild only
# Do not distribute or modify
# Author: DragonTaki (https://github.com/DragonTaki)
# Create Date: 2025/04/18
# Update Date: 2025/04/23
# Version: v1.2
# ----- ----- ----- -----

from enum import Enum
from types import SimpleNamespace

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
LOG_FOLDER = "log"
REPORT_FOLDER = "report"
TEMP_FOLDER = "temp"

# File Formats
CACHE_EXTENSION = ".cache"
CSV_EXTENSION = ".csv"
IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg")
LOG_EXTENSION = ".log"
TEXT_EXTENSIONS = (".txt",)

CSV_REPORT_PREFIX = "attendance_data_"
CSV_TIMESTAMP_FORMAT = "%d%m%Y_%H%M%S"
EXTRA_ATTENDANCE_FOLDER_FORMAT = "%d-%m-%Y"
LOG_TIMESTAMP_FORMAT = "%d-%m-%Y_%H.%M.%S"
LOG_RUNTIME_PREFIX = "runtime_log_"
LOG_USERSAVED_PREFIX = "user_saved_log_"

FILENAME_TEMPLATE = "{prefix}{name}{ext}"

DAILY_SUMMARY = SimpleNamespace(
    TEXTFILE = SimpleNamespace(
        META    = FILENAME_TEMPLATE.format(prefix="text_", name="meta",    ext=".meta"),
        SUMMARY = FILENAME_TEMPLATE.format(prefix="text_", name="summary", ext=".json"),
    ),
    SCREENSHOT = SimpleNamespace(
        META    = FILENAME_TEMPLATE.format(prefix="screenshot_", name="meta",    ext=".meta"),
        SUMMARY = FILENAME_TEMPLATE.format(prefix="screenshot_", name="summary", ext=".json"),
    )
)

# Cache Types
class CacheType(Enum):
    MEMBERLIST = "memberlist"
    ATTENDANCE = "attendance"
    TEXTFILE   = "textfile"
    SCREENSHOT = "screenshot"

# Cache Settings
CACHE_EXPIRY_HOURS = 8
MAX_CACHE_VERSIONS = 1

# CSV Settings
MAX_CSV_VERSIONS = 3

# Logger Time Formats
TIMESTAMP_FORMAT = "%d/%m/%Y %H:%M:%S"

# Logger Levels
class LogLevel(Enum):
    INIT  = ("init",  None)  # No color for init
    DEBUG = ("debug", "gray")
    INFO  = ("info",  "white")
    WARN  = ("warn",  "yellow")
    ERROR = ("error", "red")

    def __init__(self, label, color):
        self._label = label
        self._color = color

    @property
    def label(self) -> str:
        # Always return uppercase label like INIT, INFO, etc.
        return self._label.upper()

    @property
    def color(self) -> str | None:
        return self._color

# Debug Settings
DEBUG_MODE = True
FORCE_NEW_DAILY_SUMMARY = False

# Limit Version
TRIAL_VERSION = True
TRIAL_DATE = 7
EXPIRE_DATE = "2025-04-30"
