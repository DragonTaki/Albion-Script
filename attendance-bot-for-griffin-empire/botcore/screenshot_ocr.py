# ----- ----- ----- -----
# screenshot_ocr.py
# For Albion Online "Griffin Empire" Guild only
# Do not distribute or modify
# Author: DragonTaki (https://github.com/DragonTaki)
# Create Date: 2025/04/18
# Update Date: 2025/04/18
# Version: v1.0
# ----- ----- ----- -----

import os
import sys
from datetime import datetime

import pytesseract
from PIL import Image

from .config import DATE_FORMAT, SCREENSHOT_FOLDER
from .cache import save_to_cache
from .logger import log

# Constants for OCR
DAYS_LOOKBACK = 28
IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg")

# Set up Tesseract OCR path
if getattr(sys, 'frozen', False):
    BASE_PATH = sys._MEIPASS
else:
    BASE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "tesseract"))

# Specify tesseract executable and language data path
TESSERACT_DIR = os.path.join(os.path.dirname(__file__), "..", "third-party", "tesseract")
TESSERACT_EXEC = os.path.join(TESSERACT_DIR, "tesseract.exe")
TESSDATA_DIR = os.path.join(TESSERACT_DIR, "tessdata")

pytesseract.pytesseract.tesseract_cmd = TESSERACT_EXEC
os.environ["TESSDATA_PREFIX"] = TESSDATA_DIR

# OCR function: extract text from image
def extract_text_from_image(image_path):
    try:
        image = Image.open(image_path)
        return pytesseract.image_to_string(image)
    except Exception as e:
        log(f"Failed to OCR image: {image_path} => {e}", "e")
        return ""

# Main function to parse screenshots
def parse_screenshots(if_save_to_cache=True):
    today = datetime.today()
    result_by_day = {}
    success_days = 0

    for folder in os.listdir(SCREENSHOT_FOLDER):
        folder_path = os.path.join(SCREENSHOT_FOLDER, folder)
        if not os.path.isdir(folder_path):
            continue

        try:
            folder_date = datetime.strptime(folder, DATE_FORMAT)
        except ValueError:
            continue

        if (today - folder_date).days > DAYS_LOOKBACK:
            continue

        daily_names = set()
        has_valid_image = False

        for file in os.listdir(folder_path):
            if not file.lower().endswith(IMAGE_EXTENSIONS):
                continue
            full_path = os.path.join(folder_path, file)
            raw_text = extract_text_from_image(full_path)
            if not raw_text.strip():
                continue
            has_valid_image = True
            lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
            for name in lines:
                daily_names.add(name)

        if has_valid_image:
            result_by_day[folder] = sorted(list(daily_names))
            success_days += 1

    if if_save_to_cache:
        if result_by_day:
            cache_data = {
                "type": "ocr",
                "json_data": result_by_day
            }
            save_to_cache(cache_data)
            log(f"OCR parsing done and saved to cache. {success_days} days processed.")
        else:
            log("OCR failed for all images. Nothing saved to cache.", "e")

    return result_by_day
