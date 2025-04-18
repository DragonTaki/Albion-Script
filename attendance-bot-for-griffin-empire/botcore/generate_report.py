# ----- ----- ----- -----
# generate_report.py
# For Albion Online "Griffin Empire" Guild only
# Do not distribute or modify
# Author: DragonTaki (https://github.com/DragonTaki)
# Create Date: 2025/04/18
# Update Date: 2025/04/18
# Version: v1.2 🔴
# ----- ----- ----- -----

import csv
import os
from datetime import datetime

from .config import CacheType, INTERVALS, MAX_CSV_VERSIONS
from .cache import load_from_cache
from .logger import log
from .fetch_guild_members import fetch_guild_members
from .fetch_attendance import fetch_attendance

# Constants for CSV
ATTENDANCE_HEADERS = ["7DaysAttendance", "14DaysAttendance", "28DaysAttendance"]
VIRTUAL_STATS_ALL = "*stats_avg_all"
VIRTUAL_STATS_ACTIVE = "*stats_avg_activeonly"
ATTENDANCE_FIELD_TEMPLATE = "{}DaysAttendance"

# Read required data from cache or fallback
def fetch_required_data():
    player_list = load_from_cache(CacheType.PLAYERS.value)
    if not player_list:
        log("No valid players cache found, attempting to fetch from server...", "w")
        player_list = fetch_guild_members()
        if not player_list:
            log("Failed to retrieve player list.", "e")
            return None, None, None

    attendance_map = load_from_cache(CacheType.ATTENDANCE.value)
    if not attendance_map:
        log("No valid attendance cache found, attempting to fetch from server...", "w")
        attendance_map = fetch_attendance()
        if not attendance_map:
            log("Failed to retrieve attendance data.", "e")
            return None, None, None

    ocr_data = load_from_cache(CacheType.OCR.value)
    if not ocr_data:
        log("No valid OCR cache found, skipping OCR boost.", "w")
        ocr_data = {}

    return player_list, attendance_map, ocr_data

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

# Prepare report from player list + attendance + OCR
def prepare_report_data():
    player_list, attendance_map, ocr_map = fetch_required_data()
    if not player_list or not attendance_map:
        return []

    results = []
    for player in sorted(player_list):
        row = {"Player": player}

        for interval in INTERVALS:
            field = ATTENDANCE_FIELD_TEMPLATE.format(interval)
            row[field] = attendance_map.get(interval, {}).get(player, 0)

        # OCR boost
        if player in ocr_map:
            for interval in INTERVALS:
                row[ATTENDANCE_FIELD_TEMPLATE.format(interval)] += 1

        results.append(row)

    # Add two virtual summary rows: all and active players
    stats_rows = compute_statistics(results)
    results.extend(stats_rows)

    return results

# Save data to CSV and clean up old ones
def write_csv(data_rows):
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"attendance_data_{timestamp_str}.csv"

    fieldnames = ["Player"] + ATTENDANCE_HEADERS

    try:
        with open(filename, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data_rows)
        log(f"Report written to \"{filename}\".")
    except Exception as e:
        log(f"Failed to write CSV: {e}", "e")
        return

    csv_files = sorted(
        [f for f in os.listdir() if f.startswith("attendance_data_") and f.endswith(".csv")],
        key=lambda x: os.path.getmtime(x),
        reverse=True
    )
    for old in csv_files[MAX_CSV_VERSIONS:]:
        os.remove(old)
        log(f"Deleted old CSV file: {old}")
