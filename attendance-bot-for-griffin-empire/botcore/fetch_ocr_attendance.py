# ----- ----- ----- -----
# fetch_ocr_attendance.py
# For Albion Online "Griffin Empire" Guild only
# Do not distribute or modify
# Author: DragonTaki (https://github.com/DragonTaki)
# Create Date: 2025/04/18
# Update Date: 2025/04/18
# Version: v1.0
# ----- ----- ----- -----

import os
from datetime import datetime
from collections import defaultdict
from PIL import Image

from .config import CacheType, DAYS_LOOKBACK, EXTRA_ATTENDANCE_FOLDER, EXTRA_ATTENDANCE_FOLDER_FORMAT, IMAGE_EXTENSIONS
from .cache import save_to_cache
from .logger import log
from .ocr_processing import (
    preprocess_all_versions,
    extract_name_regions_with_opencv, extract_name_regions, 
    save_debug_name_regions,
    get_valid_player_list,
    create_word_list_file,
    perform_ocr_on_versions,
    match_player_names,
    delete_debug_images
)

# Constants
AUTO_DELETE_TEMP_FILE = False  # toggle this to True to clean up debug folder

def parse_screenshots(if_save_to_cache=True):
    today = datetime.today()
    result_by_day = {}
    success_days = 0

    player_list = get_valid_player_list()
    if not player_list:
        log("Cannot continue OCR parsing without player list.", "e")
        return {}

    wordlist_path = create_word_list_file(player_list)
    temp_files = [wordlist_path]

    for folder in os.listdir(EXTRA_ATTENDANCE_FOLDER):
        folder_path = os.path.join(EXTRA_ATTENDANCE_FOLDER, folder)
        if not os.path.isdir(folder_path):
            continue

        try:
            folder_date = datetime.strptime(folder, EXTRA_ATTENDANCE_FOLDER_FORMAT)
        except ValueError:
            continue

        if (today - folder_date).days > DAYS_LOOKBACK:
            continue

        log(f"Processing screenshot folder: {folder}", "i")

        stats = defaultdict(lambda: {"attendance": 0, "versions": set()})
        has_valid_image = False

        for file in os.listdir(folder_path):
            if not file.lower().endswith(IMAGE_EXTENSIONS):
                continue

            full_path = os.path.join(folder_path, file)
            log(f"Processing image: {file}", "d")

            try:
                image = Image.open(full_path)
                version_images = preprocess_all_versions(image)

                image_player_versions = defaultdict(set)

                for version_label, version_image in version_images.items():
                    # name_regions = extract_name_regions_with_opencv(version_image)
                    name_regions = extract_name_regions(version_image)
                    print(f"SS:{name_regions}")
                    save_debug_name_regions(name_regions, full_path, version_label, folder)

                    log(f"[{version_label}] Found {len(name_regions)} name regions", "d")

                    recognized_names = perform_ocr_on_versions(name_regions, wordlist_path)
                    matched_results = match_player_names(recognized_names, player_list, version_label)

                    for name, version in matched_results:
                        image_player_versions[name].add(version)
                        has_valid_image = True

                    log(f"[{version_label}] Matched players: {len(matched_results)}", "d")

                for name, versions in image_player_versions.items():
                    stats[name]["attendance"] += 1
                    stats[name]["versions"].update(versions)

            except Exception as e:
                log(f"OCR parsing failed for {file}: {e}", "e")

        if has_valid_image and stats:
            formatted = []
            for name, data in stats.items():
                formatted.append({
                    "name": name,
                    "attendance": data["attendance"],
                    "ocr": sorted([v.strip("[]") for v in data["versions"]])
                })
            result_by_day[folder] = formatted
            success_days += 1
            log(f"Completed folder {folder} with {len(stats)} player entries", "s")
        else:
            log(f"No valid OCR data found in {folder}", "w")

    # Clean up debug folder if toggle is on
    if AUTO_DELETE_TEMP_FILE:
        delete_debug_images()

    if if_save_to_cache:
        if result_by_day:
            cache_data = {
                "type": CacheType.SCREENSHOT.value,
                "json_data": result_by_day
            }
            save_to_cache(cache_data)
            log(f"OCR parsing done and saved to cache. {success_days} days processed.")
        else:
            log("OCR failed for all images. Nothing saved to cache.", "e")

    return result_by_day
