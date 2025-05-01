# ----- ----- ----- -----
# constant.py
# For Albion Online "Griffin Empire" Guild only
# Do not distribute or modify
# Author: DragonTaki (https://github.com/DragonTaki)
# Create Date: 2025/04/25
# Update Date: 2025/04/25
# Version: v1.0
# ----- ----- ----- -----

import re
from enum import Enum

from botcore.safe_namespace import SafeNamespace
from .static_settings import DATE_FORMAT


# ----- Constants ----- #
# CSV Headers
CSV_HEADERS = ["Player", "7DaysAttendance", "14DaysAttendance", "28DaysAttendance"]


# Attendance Days
INTERVALS = [7, 14, 28]
DAYS_LOOKBACK = max(INTERVALS)


# Cache Types
class CacheType(Enum):
    MEMBERLIST = "memberlist"
    KILLBOARD  = "killboard"
    TEXTFILE   = "textfile"
    SCREENSHOT = "screenshot"
    ALL        = "all"


# File Formats
TEXTFILE_ENCODING = "utf-8"

EXTENSIONS = SafeNamespace(
    csv   = ".csv",
    cache = ".cache",
    log   = ".log",
    text  = (".txt",),
    image = (".jpg", ".jpeg", ".png"),
)


FORMAT_CONVERT_MAP = {
    "DD"   : "%d",  # 2024/01/`01`
    "D"    : "%-d", # 2024/01/`1`
    "MM"   : "%m",  # 2024/`01`/01
    "M"    : "%-m", # 2024/`1`/01
    "YYYY" : "%Y",  # `2024`/01/01
    "YY"   : "%y",  # `24`/01/01
}

## Combination functions
def join_date(sep: str = "", user_format: str = DATE_FORMAT) -> str:
    """
    Convert a user-friendly format like 'DDMMYYYY', 'DD-MM-YYYY' into strftime format.
    Ignores any separator user typed.

    Args:
        sep (str): Separator to use between date parts (e.g., '-', '/', etc.)
        user_format (str): User-specified format indicating order (e.g., 'DDMMYYYY', 'YYMMDD')

    Returns:
        str: strftime-compatible format string
    """
    try:
        # Only fetch label, no delimiters
        tokens = re.findall(r'DD|D|MM|M|YYYY|YY', user_format.upper())

        if not tokens:
            raise ValueError(f"[join_date] Invalid user_format: {user_format}")

        strftime_parts = []
        for token in tokens:
            mapped = FORMAT_CONVERT_MAP.get(token)
            if mapped:
                strftime_parts.append(mapped)
            else:
                raise ValueError(f"[join_date] Unknown token '{token}' in user_format.")

        # Insert delimiters
        return sep.join(strftime_parts)

    except Exception as e:
        print(f"[ERROR] join_date failed: {e}")
        return "%d%m%Y"  # Fallback

def join_time(sep=""):
    return sep.join(["%H", "%M", "%S"])

# Date Time Formats
## Define constants
SEPARATORS = SafeNamespace(
    date     = "-",  # 2025-01-01
    datetime = "_",  # 2025-01-01_12.00.00
    time     = ".",  # 12.00.00
    display  = "/",  # 2025/01/01
)

DATETIME_FORMATS = SafeNamespace(
    csv     = f"{join_date(SEPARATORS.date)}{SEPARATORS.datetime}{join_time()}",                 # 2025-01-01_120000
    log     = f"{join_date(SEPARATORS.date)}{SEPARATORS.datetime}{join_time(SEPARATORS.time)}",  # 2025-01-01_12.00.00
    folder  = join_date(SEPARATORS.date),                                                        # 2025-01-01
    general = f"{join_date(SEPARATORS.display)} {join_time(':')}",                               # 2025/01/01 12:00:00
)
