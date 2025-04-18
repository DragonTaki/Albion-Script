# ----- ----- ----- -----
# ocr_utils.py
# For Albion Online "Griffin Empire" Guild only
# Do not distribute or modify
# Author: DragonTaki (https://github.com/DragonTaki)
# Create Date: 2025/04/18
# Update Date: 2025/04/18
# Version: v1.0
# ----- ----- ----- -----

import os
import numpy as np

import cv2
import pytesseract
from PIL import Image

from .config import CacheType
from .cache import load_from_cache
from .logger import log
from .fetch_guild_members import fetch_guild_members

# Constants for image
IMAGE_SIZE_LIMITS = {
    "min_width": 40,
    "max_width": 400,
    "min_height": 15,
    "max_height": 60,
    "min_aspect_ratio": 0.5,
    "max_aspect_ratio": 5.0
}

V4_EDGE_THRESHOLD = 100
LEFT_COLUMN_MAX_X = 500
DEBUG_FOLDER = "debug_ocr_versions"
WORDLIST_TEMP_FILE = "temp_wordlist.txt"

# Tesseract setup
TESSERACT_DIR = os.path.join(os.path.dirname(__file__), "..", "third-party", "tesseract")
TESSERACT_EXEC = os.path.join(TESSERACT_DIR, "tesseract.exe")
TESSDATA_DIR = os.path.join(TESSERACT_DIR, "tessdata")
pytesseract.pytesseract.tesseract_cmd = TESSERACT_EXEC
os.environ["TESSDATA_PREFIX"] = TESSDATA_DIR


# Image conversions
def pil_to_cv(image: Image.Image):
    return cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

def cv_to_pil(image_cv):
    return Image.fromarray(cv2.cvtColor(image_cv, cv2.COLOR_BGR2RGB))


# Extract name regions from image using OpenCV
def extract_name_regions_with_opencv(image: Image.Image):
    img_cv = pil_to_cv(image)
    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)

    thresh = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
        cv2.THRESH_BINARY_INV, 15, 8
    )

    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    name_regions = []
    img_width, img_height = image.size

    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)

        if not (IMAGE_SIZE_LIMITS["min_width"] < w < IMAGE_SIZE_LIMITS["max_width"]
                and IMAGE_SIZE_LIMITS["min_height"] < h < IMAGE_SIZE_LIMITS["max_height"]):
            continue

        aspect_ratio = w / h
        if not (IMAGE_SIZE_LIMITS["min_aspect_ratio"] <= aspect_ratio <= IMAGE_SIZE_LIMITS["max_aspect_ratio"]):
            continue

        if x + w > img_width or y + h > img_height:
            continue

        name_regions.append((x, y, w, h))

    name_regions.sort(key=lambda tup: (tup[0] // LEFT_COLUMN_MAX_X, tup[1]))

    return [image.crop((x, y, x + w, y + h)) for (x, y, w, h) in name_regions]


# Save name region debug images
def save_debug_name_regions(regions, original_image_path, version_label, folder_date):
    image_name = os.path.basename(original_image_path).split(".")[0]
    output_folder = os.path.join(DEBUG_FOLDER, folder_date)
    os.makedirs(output_folder, exist_ok=True)

    for idx, region in enumerate(regions, 1):
        filename = f"{image_name}-{version_label}-{idx:02d}.png"
        save_path = os.path.join(output_folder, filename)
        region.save(save_path)


# Load or fetch player list
def get_valid_player_list():
    player_list = load_from_cache(CacheType.PLAYERS.value)
    if not player_list:
        log("No valid players cache found, attempting to fetch from server...", "w")
        player_list = fetch_guild_members()
        if player_list:
            log("Fetched and cached player list.")
        else:
            log("Failed to retrieve player list.", "e")
    return player_list or []


# Create Tesseract-compatible word list file
def create_word_list_file(player_list):
    with open(WORDLIST_TEMP_FILE, "w", encoding="utf-8") as f:
        for name in player_list:
            f.write(name + "\n")
    return WORDLIST_TEMP_FILE


# OCR execution on regions
def perform_ocr_on_versions(name_images, whitelist_path):
    config = f'--psm 7 --user-words {whitelist_path}'
    return [pytesseract.image_to_string(img, config=config).strip() for img in name_images if img]


# Match recognized names to official player list
def match_player_names(recognized_names, player_list, version_label):
    return [(name, version_label) for name in recognized_names if name in player_list]

##### Testing functions #####
# Apply V1~V4 preprocessing variants
def preprocess_all_versions(image: Image.Image):
    img_cv = pil_to_cv(image)
    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)

    # V1: grayscale
    v1 = gray.copy()

    # V2: binary threshold
    _, v2 = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)

    # V3: sharpen
    kernel_sharpen = np.array([[0, -1, 0], [-1, 5,-1], [0, -1, 0]])
    v3 = cv2.filter2D(gray, -1, kernel_sharpen)

    # V4: Canny edge
    v4 = cv2.Canny(gray, threshold1=V4_EDGE_THRESHOLD, threshold2=V4_EDGE_THRESHOLD * 2)

    return {
        "v1": Image.fromarray(v1),
        "v2": Image.fromarray(v2),
        "v3": Image.fromarray(v3),
        "v4": Image.fromarray(v4)
    }
