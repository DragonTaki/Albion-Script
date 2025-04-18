# ----- ----- ----- -----
# generate_report.py
# For Albion Online "Griffin Empire" Guild only
# Do not distribute or modify
# Author: DragonTaki (https://github.com/DragonTaki)
# Create Date: 2025/04/18
# Update Date: 2025/04/18
# Version: v1.0
# ----- ----- ----- -----

import csv
import os
from datetime import datetime
from .config import INTERVALS, CSV_HEADERS, MAX_CSV_VERSIONS
from .logger import log

def prepare_report_data(fetched_data):
    all_players = set()
    for interval in INTERVALS:
        all_players.update(fetched_data[interval].keys())

    results = []
    for player in sorted(all_players):
        row = {
            "Player": player,
            "7DaysAttendance": fetched_data[7].get(player, 0),
            "14DaysAttendance": fetched_data[14].get(player, 0),
            "28DaysAttendance": fetched_data[28].get(player, 0),
        }
        results.append(row)
    return results

def write_csv(data_rows):
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"attendance_data_{timestamp_str}.csv"
    try:
        with open(filename, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=CSV_HEADERS)
            writer.writeheader()
            writer.writerows(data_rows)
        log(f"Report written to \"{filename}\".")
    except Exception as e:
        log(f"Failed to write CSV: {e}", "e")
        return

    csv_files = sorted([f for f in os.listdir() if f.startswith("attendance_data_") and f.endswith(".csv")],
                        key=lambda x: os.path.getmtime(x), reverse=True)
    for old in csv_files[MAX_CSV_VERSIONS:]:
        os.remove(old)
        log(f"Deleted old CSV file: {old}")
