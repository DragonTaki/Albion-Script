# ----- ----- ----- -----
# generate_report.py
# For Albion Online "Griffin Empire" Guild only
# Do not distribute or modify
# Author: DragonTaki (https://github.com/DragonTaki)
# Create Date: 2025/04/18
# Update Date: 2025/04/25
# Version: v1.6
# ----- ----- ----- -----

import csv
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from botcore.config.constant import EXTENSIONS, DATETIME_FORMATS, INTERVALS, TEXTFILE_ENCODING
from botcore.config.settings import MAX_CSV_VERSIONS, FOLDER_PATHS
from .cache import CacheType, load_from_cache
from .logger import LogLevel, log
from .fetch_daily_attendance import fetch_daily_attendance
from .fetch_guild_members import fetch_guild_members
from .fetch_web_attendance import fetch_web_attendance
from .utils import get_relative_path_to_target, ensure_folder_exists

# Constants
CSV_REPORT_PREFIX = "attendance_data_"
ATTENDANCE_HEADERS = ["7DaysAttendance", "14DaysAttendance", "28DaysAttendance"]
VIRTUAL_STATS_ALL = "*stats_avg_all"
VIRTUAL_STATS_ACTIVE = "*stats_avg_activeonly"
ATTENDANCE_FIELD_TEMPLATE = "{}DaysAttendance"

# Helper function to fetch required data from cache or fallback sources
def fetch_required_data(
    use_web: bool = True,
    use_textfile: bool = True,
    use_screenshot: bool = True
) -> Tuple[Optional[Dict[str, int]], Optional[Dict[str, int]], Optional[Dict[str, int]], Optional[Dict[str, int]]]:
    """
    Fetches necessary attendance data. Tries to load from cache, otherwise fetches from appropriate sources.

    Args:
        use_web (bool): Whether to load web attendance.
        use_textfile (bool): Whether to load textfile attendance.
        use_screenshot (bool): Whether to load screenshot attendance.

    Returns:
        Tuple containing player list, web attendance map, textfile attendance map, screenshot attendance map.
        If any required data cannot be fetched, returns None for that part.
    """
    try:
        player_list = load_from_cache(CacheType.MEMBERLIST.value)
        if not player_list:
            log(f"No valid {CacheType.MEMBERLIST.value} cache found, attempting to fetch from server...", LogLevel.WARN)
            player_list = fetch_guild_members()
            if not player_list:
                log("Failed to retrieve player list.", LogLevel.ERROR)
                return None, None, None, None
        
        attendance_map = load_from_cache(CacheType.ATTENDANCE.value) if use_web else {}
        if not attendance_map and use_web:
            log(f"No valid {CacheType.ATTENDANCE.value} cache found, attempting to fetch from server...", LogLevel.WARN)
            attendance_map = fetch_web_attendance()
        
        textfile_data = load_from_cache(CacheType.TEXTFILE.value) if use_textfile else {}
        if not textfile_data and use_textfile:
            log(f"No valid {CacheType.TEXTFILE.value} cache found, attempting to launch calculation function...", LogLevel.WARN)
            textfile_data = fetch_daily_attendance("TEXTFILE", CacheType.TEXTFILE)

        screenshot_data = load_from_cache(CacheType.SCREENSHOT.value) if use_screenshot else {}
        if not screenshot_data and use_screenshot:
            log(f"No valid {CacheType.SCREENSHOT.value} cache found, attempting to launch calculation function...", LogLevel.WARN)
            screenshot_data = fetch_daily_attendance("SCREENSHOT", CacheType.SCREENSHOT)

        return player_list, attendance_map, textfile_data, screenshot_data
    
    except Exception as e:
        log(f"Error fetching required data: {e}", LogLevel.ERROR)
        return None, None, None, None

# Function to check if a player is active based on attendance data
def is_active_player(row: Dict[str, int]) -> bool:
    """
    Determines whether a player is active by checking their attendance across all intervals.

    Args:
        row (dict): A dictionary containing player's attendance data.

    Returns:
        bool: True if the player has non-zero attendance, False otherwise.
    """
    return any(row[ATTENDANCE_FIELD_TEMPLATE.format(interval)] > 0 for interval in INTERVALS)

# Function to compute statistics (average attendance) for all players or only active players
def compute_statistics(data_rows: List[Dict[str, int]]) -> List[Dict[str, int]]:
    """
    Computes statistics for attendance data, including averages for all players and active players.

    Args:
        data_rows (list): A list of dictionaries containing attendance data for each player.

    Returns:
        list: A list of dictionaries containing computed statistics for all and active players.
    """
    stats_rows = []

    for label, filter_func in [
        (VIRTUAL_STATS_ALL, lambda r: True),  # All players
        (VIRTUAL_STATS_ACTIVE, is_active_player)  # Only active players
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

# Main function to generate the attendance report
def generate_report(save_to_csv: bool = False, pure_report: bool = False) -> List[Dict[str, int]]:
    """
    Generates an attendance report based on the available data (web, textfile, screenshot).

    Args:
        save_to_csv (bool): Whether to save the generated report to a CSV file.
        pure_report (bool): Whether to include only web attendance in the report (exclude textfile and screenshot boosts).

    Returns:
        list: A list of dictionaries representing the generated report.
    """
    try:
        player_list, web_attendance_map, textfile_attendance_map, screenshot_attendance_map = fetch_required_data(pure_report)

        if not player_list or not web_attendance_map:
            log("Insufficient data to generate report.", LogLevel.ERROR)
            return []

        results = []
        for player in sorted(player_list):
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

    except Exception as e:
        log(f"Error generating report: {e}", LogLevel.ERROR)
        return []

# Function to write the report data to a CSV file
def write_csv(data_rows: List[Dict[str, int]]) -> None:
    """
    Writes the report data to a CSV file and cleans up old CSV files.

    Args:
        data_rows (list): A list of dictionaries containing the report data to be written to the CSV file.
    """
    try:
        timestamp_str = datetime.now().strftime(DATETIME_FORMATS.csv)
        filename = f"{CSV_REPORT_PREFIX}{timestamp_str}{EXTENSIONS.csv}"
        report_dir = os.path.abspath(FOLDER_PATHS.report)
        ensure_folder_exists(report_dir)
        filepath = os.path.join(report_dir, filename)

        fieldnames = ["Player"] + ATTENDANCE_HEADERS

        with open(filepath, mode="w", newline="", encoding=TEXTFILE_ENCODING) as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data_rows)
        
        relative_path = get_relative_path_to_target(filepath)
        log(f"Report written to \"{relative_path}\".")

        # Cleanup old CSVs
        delete_old_csvs(report_dir)

    except Exception as e:
        log(f"Failed to write CSV: {e}", LogLevel.ERROR)

# Function to delete old CSV files, keeping only the most recent N versions
def delete_old_csvs(report_dir: str) -> None:
    """
    Deletes old CSV files in the report directory, keeping only the most recent N versions.

    Args:
        report_dir (str): The directory where the CSV files are stored.
    """
    try:
        csv_files = sorted(
            [f for f in os.listdir(report_dir) if f.startswith(CSV_REPORT_PREFIX) and f.endswith(EXTENSIONS.csv)],
            key=lambda x: os.path.getmtime(os.path.join(report_dir, x)),
            reverse=True
        )

        for oldfile in csv_files[MAX_CSV_VERSIONS:]:
            abs_filepath = os.path.abspath(os.path.join(report_dir, oldfile))
            os.remove(abs_filepath)
            relative_path = get_relative_path_to_target(abs_filepath)
            log(f"Deleted old report: \"{relative_path}\".", LogLevel.WARN)

    except Exception as e:
        log(f"Failed to delete old reports: {e}", LogLevel.ERROR)
