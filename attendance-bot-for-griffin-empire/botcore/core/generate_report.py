# ----- ----- ----- -----
# generate_report.py
# For Albion Online "Griffin Empire" Guild only
# Do not distribute or modify
# Author: DragonTaki (https://github.com/DragonTaki)
# Create Date: 2025/04/18
# Update Date: 2025/04/25
# Version: v1.5
# ----- ----- ----- -----

import csv
import os
from datetime import datetime

from .config.constant import INTERVALS
from .config.settings import MAX_CSV_VERSIONS, REPORT_FOLDER, CSV_REPORT_PREFIX, CSV_TIMESTAMP_FORMAT, CSV_EXTENSION
from .cache import CacheType, load_from_cache
from .logger import LogLevel, log
from .fetch_guild_members import fetch_guild_members
from .fetch_web_attendance import fetch_web_attendance
from .utils import get_relative_path_to_target, ensure_folder_exists

# Constants for CSV
ATTENDANCE_HEADERS = ["7DaysAttendance", "14DaysAttendance", "28DaysAttendance"]
VIRTUAL_STATS_ALL = "*stats_avg_all"
VIRTUAL_STATS_ACTIVE = "*stats_avg_activeonly"
ATTENDANCE_FIELD_TEMPLATE = "{}DaysAttendance"

# Read required data from cache or fallback
def fetch_required_data(pure_report=False):
    player_list = load_from_cache(CacheType.MEMBERLIST.value)
    if not player_list:
        log(f"No valid {CacheType.MEMBERLIST.value} cache found, attempting to fetch from server...", LogLevel.WARN)
        player_list = fetch_guild_members()
        if not player_list:
            log("Failed to retrieve player list.", LogLevel.ERROR)
            return None, None, None, None

    attendance_map = load_from_cache(CacheType.ATTENDANCE.value)
    if not attendance_map:
        log(f"No valid {CacheType.ATTENDANCE.value} cache found, attempting to fetch from server...", LogLevel.WARN)
        attendance_map = fetch_web_attendance()
        if not attendance_map:
            log("Failed to retrieve attendance data.", LogLevel.ERROR)
            return None, None, None, None

    textfile_data = {}
    screenshot_data = {}
    if not pure_report:
        textfile_data = load_from_cache(CacheType.TEXTFILE.value)
        if not textfile_data:
            log(f"No valid {CacheType.TEXTFILE.value} cache found, skipping {CacheType.TEXTFILE.value} attendance calculate.", LogLevel.WARN)
            textfile_data = {}

        screenshot_data = load_from_cache(CacheType.SCREENSHOT.value)
        if not screenshot_data:
            log(f"No valid {CacheType.SCREENSHOT.value} cache found, skipping {CacheType.SCREENSHOT.value} attendance calculate.", LogLevel.WARN)
            screenshot_data = {}

    return player_list, attendance_map, textfile_data, screenshot_data

# Determine whether a player is active (has non-zero attendance)
def is_active_player(row):
    return any(row[ATTENDANCE_FIELD_TEMPLATE.format(interval)] > 0 for interval in INTERVALS)

# Compute statistics for all and active players
def compute_statistics(data_rows):
    stats_rows = []

    for label, filter_func in [
        (VIRTUAL_STATS_ALL, lambda r: True),                # all players
        (VIRTUAL_STATS_ACTIVE, is_active_player)            # active only
    ]:
        filtered = list(filter(filter_func, data_rows))
        num_players = len(filtered)

        stats_row = {"Player": label}
        for interval in INTERVALS:
            field = ATTENDANCE_FIELD_TEMPLATE.format(interval)
            total = sum(row[field] for row in filtered)
            stats_row[field] = round(total / num_players, 2) if num_players else 0

        stats_rows.append(stats_row)

    return stats_rows

# Generate report from member_list + web_attendance + textfile_attendance + screenshot_attendance
def generate_report(save_to_csv=False, pure_report=False):
    member_list, web_attendance_map, textfile_attendance_map, screenshot_attendance_map = fetch_required_data(pure_report)
    if not member_list or not web_attendance_map:
        return []

    results = []
    for player in sorted(member_list):
        row = {"Player": player}

        for interval in INTERVALS:
            field = ATTENDANCE_FIELD_TEMPLATE.format(interval)
            base_count = web_attendance_map.get(interval, {}).get(player, 0)
            
            # Only add the textfile and screenshot boosts if pure_report is False
            if not pure_report:
                textfile_boost = textfile_attendance_map.get(interval, {}).get(player, 0)
                screenshot_boost = screenshot_attendance_map.get(interval, {}).get(player, 0)
                row[field] = base_count + textfile_boost + screenshot_boost
            else:
                row[field] = base_count

        results.append(row)

    # Add two virtual summary rows: all and active players
    stats_rows = compute_statistics(results)
    results.extend(stats_rows)

    # If save_to_csv is True, generate the CSV file
    if save_to_csv:
        write_csv(results)

    return results

# Save data to CSV and clean up old ones
def write_csv(data_rows):
    timestamp_str = datetime.now().strftime(CSV_TIMESTAMP_FORMAT)
    filename = f"{CSV_REPORT_PREFIX}{timestamp_str}{CSV_EXTENSION}"
    report_dir = os.path.abspath(os.path.join(REPORT_FOLDER))
    ensure_folder_exists(report_dir)
    filepath = os.path.join(report_dir, filename)

    fieldnames = ["Player"] + ATTENDANCE_HEADERS

    try:
        with open(filepath, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data_rows)
        relative_path = get_relative_path_to_target(filepath)
        log(f"Report written to \"{relative_path}\".")
    except Exception as e:
        log(f"Failed to write CSV: \"{e}\".", LogLevel.ERROR)
        return

    # Cleanup old CSVs
    delete_old_csvs(report_dir)

def delete_old_csvs(report_dir):
    """Delete old CSV files in the report directory, keeping only the most recent N versions"""
    try:
        csv_files = sorted(
            [f for f in os.listdir(report_dir) if f.startswith(CSV_REPORT_PREFIX) and f.endswith(CSV_EXTENSION)],
            key=lambda x: os.path.getmtime(os.path.join(report_dir, x)),
            reverse=True
        )

        for oldfile in csv_files[MAX_CSV_VERSIONS:]:
            abs_filepath = os.path.abspath(os.path.join(report_dir, oldfile))
            os.remove(abs_filepath)
            relative_path = get_relative_path_to_target(abs_filepath)
            log(f"Deleted old report: \"{relative_path}\".", LogLevel.WARN)
    except Exception as e:
        log(f"Failed to delete old reports: \"{e}\".", LogLevel.ERROR)
