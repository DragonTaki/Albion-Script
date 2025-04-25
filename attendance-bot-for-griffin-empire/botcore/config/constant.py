# ----- ----- ----- -----
# constant.py
# For Albion Online "Griffin Empire" Guild only
# Do not distribute or modify
# Author: DragonTaki (https://github.com/DragonTaki)
# Create Date: 2025/04/25
# Update Date: 2025/04/25
# Version: v1.0
# ----- ----- ----- -----

from botcore.safe_namespace import SafeNamespace
from .settings import DATE_ORDER

# CSV Headers
CSV_HEADERS = ["Player", "7DaysAttendance", "14DaysAttendance", "28DaysAttendance"]

# Attendance Days
INTERVALS = [7, 14, 28]
DAYS_LOOKBACK = max(INTERVALS)

# File Formats
TEXTFILE_ENCODING = "utf-8"

EXTENSIONS = SafeNamespace(
    csv   = ".csv",
    cache = ".cache",
    log   = ".log",
    text  = (".txt",),
    image = (".jpg", ".jpeg", ".png")
)

# Date Time Formats
## Combination functions
def join_date(sep="", order=DATE_ORDER):
    return sep.join(order)

def join_time(sep=""):
    return sep.join(["%H", "%M", "%S"])

# Safe Constants
## Define constants
SEPARATORS = SafeNamespace(
    date     = "-",  # 2025-01-01
    datetime = "_",  # 2025-01-01_12.00.00
    time     = ".",  # 12.00.00
    display  = "/"   # 2025/01/01
)

DATETIME_FORMATS = SafeNamespace(
    csv     = f"{join_date(SEPARATORS.date)}{SEPARATORS.datetime}{join_time()}",                 # 2025-01-01_120000
    log     = f"{join_date(SEPARATORS.date)}{SEPARATORS.datetime}{join_time(SEPARATORS.time)}",  # 2025-01-01_12.00.00
    folder  = join_date(SEPARATORS.date),                                                        # 2025-01-01
    general = f"{join_date(SEPARATORS.display)} {join_time(':')}"                                # 2025/01/01 12:00:00
)
