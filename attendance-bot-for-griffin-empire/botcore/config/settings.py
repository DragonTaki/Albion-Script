# ----- ----- ----- -----
# settings.py
# For Albion Online "Griffin Empire" Guild only
# Do not distribute or modify
# Author: DragonTaki (https://github.com/DragonTaki)
# Create Date: 2025/04/18
# Update Date: 2025/04/25
# Version: v2.0
# ----- ----- ----- -----

from botcore.safe_namespace import SafeNamespace

# Guild Info Lists
GUILD_INFO_LIST = [
    {"name":"Griffin Empire", "id":"sAFfW_tPSkuU_49gvg4sZQ", "tag":"GE"},
]

# Date Time Main Format
DATE_ORDER = ["%d", "%m", "%Y"]

# Folder Paths
FOLDER_PATHS = SafeNamespace(
    app        = "app_data",
    attendance = "attendance_data",
    cache      = "cache",
    debug      = "temp_debug",
    log        = "log",
    report     = "report",
    temp       = "temp"
)

# CSV Settings
MAX_CSV_VERSIONS = 3

# Debug Settings
IF_DEBUG_MODE = True
IF_FORCE_NEW_DAILY_SUMMARY = False

# Limit Version
IF_TRIAL_VERSION = True
TRIAL_DATE = 7
EXPIRE_DATE = "2025-04-30"
