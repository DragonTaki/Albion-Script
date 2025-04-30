# ----- ----- ----- -----
# fetch_daily_attendance.py
# For Albion Online "Griffin Empire" Guild only
# Do not distribute or modify
# Author: DragonTaki (https://github.com/DragonTaki)
# Create Date: 2025/04/22
# Update Date: 2025/04/26
# Version: v1.3
# ----- ----- ----- -----

from types import SimpleNamespace

from botcore.logging.app_logger import LogLevel, log
from .cache import save_to_cache_if_needed
from .daily_summary import collect_all_daily_attendance, calculate_interval_summary


def fetch_daily_attendance(
    data_type: SimpleNamespace,
    if_save_to_cache: bool = True
) -> dict:
    """
    Process daily attendance records for a given data source (textfiles or screenshots),
    and optionally save the interval summary to cache.

    Args:
        data_type (SimpleNamespace): One of the entries from DAILY_SUMMARY (e.g., DAILY_SUMMARY.TEXTFILE).
        if_save_to_cache (bool, optional): Whether to persist the interval summary to the cache. Default is True.

    Returns:
        dict: A dictionary with keys like "7d", "14d", "28d", each mapping to
            another dictionary of player names and their attendance counts.
    """

    cache_type = data_type.cache_type # Mapping back to cache_type

    result_by_day = collect_all_daily_attendance(data_type)
    summary_by_interval = calculate_interval_summary(data_type, result_by_day)

    if summary_by_interval:
        save_to_cache_if_needed(
            cache_type,
            summary_by_interval,
            if_save_to_cache,
            f"{data_type.cache_type.name.capitalize()} attendance data"
        )
    else:
        log(
            f"No valid {data_type.cache_type.name} attendance data found. Nothing saved.",
            LogLevel.ERROR
        )

    return summary_by_interval
