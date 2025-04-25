# ----- ----- ----- -----
# fetch_textfile_attendance.py
# For Albion Online "Griffin Empire" Guild only
# Do not distribute or modify
# Author: DragonTaki (https://github.com/DragonTaki)
# Create Date: 2025/04/22
# Update Date: 2025/04/23
# Version: v1.1
# ----- ----- ----- -----

from .config.constant import LogLevel
from .cache import CacheType, save_to_cache_if_needed
from .daily_summary import DAILY_SUMMARY, collect_all_daily_attendance, calculate_interval_summary
from .logger import log

# Main function: call externally
def fetch_textfile_attendance(if_save_to_cache=True):
    result_by_day = collect_all_daily_attendance(DAILY_SUMMARY.TEXTFILE)
    summary_by_interval = calculate_interval_summary(DAILY_SUMMARY.TEXTFILE, result_by_day)

    if summary_by_interval:
        save_to_cache_if_needed(CacheType.TEXTFILE, summary_by_interval, if_save_to_cache, "Textfile attendance data")
    else:
        log("No valid extra attendance data found. Nothing saved.", LogLevel.ERROR)

    return summary_by_interval
