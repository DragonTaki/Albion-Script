# ----- ----- ----- -----
# screenshot_ocr.py
# For Albion Online "Griffin Empire" Guild only
# Do not distribute or modify
# Author: DragonTaki (https://github.com/DragonTaki)
# Create Date: 2025/04/18
# Update Date: 2025/04/18
# Version: v1.1  🔴
# ----- ----- ----- -----

import os
from datetime import datetime, timedelta
from PIL import Image
import pytesseract
from rapidfuzz import process
from botcore.cache import load_from_cache, save_to_cache  # 🔴 use new cache API
from botcore.logger import log  # 🔴 log errors
import sys

# Get base path for current mode (dev or bundled)
if getattr(sys, 'frozen', False):
    BASE_PATH = sys._MEIPASS
else:
    BASE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "tesseract"))

# 🔴 Set pytesseract's executable path
pytesseract.pytesseract.tesseract_cmd = os.path.join(BASE_PATH, "tesseract.exe")
# 🔴 Specify tesseract executable path relative to project directory
TESSERACT_PATH = os.path.join(os.path.dirname(__file__), "..", "tesseract", "tesseract.exe")
pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

# 🔴 constants
SCREENSHOT_FOLDER = "screenshot"
DATE_FORMAT = "%d-%m-%Y"
DAYS_LOOKBACK = 30

# 🔴 load known names from players cache
def load_known_names():
    data = load_from_cache("players")  # 🔴 specify type
    return [entry["name"] for entry in data] if data else []

# 🔴 fuzzy match helper
def correct_name(raw_name, known_names, threshold=80):
    match, score, _ = process.extractOne(raw_name, known_names)
    return match if score >= threshold else raw_name

# 🔴 extract text from image
def extract_text_from_image(image_path):
    try:
        image = Image.open(image_path)
        return pytesseract.image_to_string(image)
    except Exception as e:
        log(f"Failed to OCR image: {image_path} => {e}", "e")
        return ""

# 🔴 main OCR and parsing function
def parse_screenshots():
    known_names = load_known_names()
    today = datetime.today()
    result_by_day = {}

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
        for file in os.listdir(folder_path):
            if not file.lower().endswith((".png", ".jpg", ".jpeg")):
                continue
            full_path = os.path.join(folder_path, file)
            raw_text = extract_text_from_image(full_path)
            lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
            for line in lines:
                corrected = correct_name(line, known_names)
                daily_names.add(corrected)

        result_by_day[folder] = sorted(list(daily_names))

    # 🔴 Save to structured binary cache
    save_to_cache({
        "type": "ocr",
        "json_data": result_by_day
    })

    return result_by_day
