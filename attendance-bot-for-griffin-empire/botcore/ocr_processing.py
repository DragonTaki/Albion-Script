# ----- ----- ----- -----
# ocr_processing.py
# For Albion Online "Griffin Empire" Guild only
# Do not distribute or modify
# Author: DragonTaki (https://github.com/DragonTaki)
# Create Date: 2025/04/18
# Update Date: 2025/04/21
# Version: v1.1
# ----- ----- ----- -----

import os
import numpy as np

import cv2
import pytesseract
import shutil
from PIL import Image

from .config import CacheType, TEMP_FOLDER, DEBUG_FOLDER
from .cache import load_from_cache
from .logger import log
from .fetch_guild_members import fetch_guild_members

# Constants
WORDLIST_TEMP_FILENAME = "temp_wordlist.txt"
WORDLIST_TEMP_FILE = TEMP_FOLDER + os.sep + WORDLIST_TEMP_FILENAME

IMAGE_SIZE_LIMITS = {
    "min_width": 40,
    "max_width": 400,
    "min_height": 15,
    "max_height": 60,
    "min_aspect_ratio": 0.5,
    "max_aspect_ratio": 5.0
}
LEFT_COLUMN_MAX_X = 500
V4_EDGE_THRESHOLD = 100
NAME_REGION_Y_MIN = 50
NAME_REGION_Y_MAX = 700

VERTICAL_DENSITY_THRESHOLD_MIN = 0.03
VERTICAL_DENSITY_THRESHOLD_MAX = 0.55

# Expected background color under player names (BGR)
PLAYER_NAME_BG_COLOR = (191, 161, 133)
COLOR_DIFF_THRESHOLD = 20

# Constants for minus button detection
MINUS_TEMPLATE_COORDS = {"x": 250, "y": 140, "w": 24, "h": 24}
MINUS_MATCH_THRESHOLD = 0.85
MINUS_REGION_WIDTH = 200
MINUS_REGION_HEIGHT = 30
MINUS_LEFT_OFFSET = 230
MINUS_TOP_OFFSET = 8
MINUS_MIN_DISTANCE_Y = 10

# 🔴 Adjusted constants for minus button cropping [🔴]
MINUS_CROP_TEMPLATE_WIDTH = MINUS_TEMPLATE_COORDS["w"]    # 24
MINUS_CROP_TEMPLATE_HEIGHT = MINUS_TEMPLATE_COORDS["h"]     # 24
MINUS_CROP_REGION_WIDTH = MINUS_REGION_WIDTH              # 200
MINUS_CROP_REGION_HEIGHT = MINUS_REGION_HEIGHT            # 30
MINUS_CROP_OFFSET_X = MINUS_LEFT_OFFSET                   # Horizontal offset from minus button center to crop region left boundary
MINUS_CROP_OFFSET_Y = MINUS_TOP_OFFSET                    # Vertical offset from minus button center to crop region top boundary

# 🔴 New: use external template image instead of hardcoded region [🔴]
MINUS_TEMPLATE_PATH = os.path.join("data", "button.png")  # 🔴 Template source for minus button

# 🔴 Updated: extract minus button template from image file [🔴]
def load_minus_template_from_file():
    """
    Loads the minus button template from external file and converts it to grayscale.
    Matches the same preprocessing as screenshot input for consistency.
    """
    if not os.path.exists(MINUS_TEMPLATE_PATH):
        log(f"Minus template file not found at {MINUS_TEMPLATE_PATH}", "e")
        return None

    template_color = cv2.imread(MINUS_TEMPLATE_PATH)
    if template_color is None:
        log(f"Failed to read minus template image.", "e")
        return None

    template_gray = cv2.cvtColor(template_color, cv2.COLOR_BGR2GRAY)
    return template_gray

# Tesseract setup
TESSERACT_DIR = os.path.join(os.path.dirname(__file__), "..", "third-party", "tesseract")
TESSERACT_EXEC = os.path.join(TESSERACT_DIR, "tesseract.exe")
TESSDATA_DIR = os.path.join(TESSERACT_DIR, "tessdata")
pytesseract.pytesseract.tesseract_cmd = TESSERACT_EXEC
os.environ["TESSDATA_PREFIX"] = TESSDATA_DIR

def is_similar_color(color1, color2, threshold=COLOR_DIFF_THRESHOLD):
    return all(abs(int(a) - int(b)) <= threshold for a, b in zip(color1, color2))

def pil_to_cv(image: Image.Image):
    return cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

def cv_to_pil(image_cv):
    return Image.fromarray(cv2.cvtColor(image_cv, cv2.COLOR_BGR2RGB))

def detect_columns_and_split(name_regions, image_width):
    midpoint = image_width // 2
    left_column = []
    right_column = []

    print(f"detect_columns_and_split{name_regions}")
    for region in name_regions:
        x, y, w, h = region
        if x + w // 2 < midpoint:
            left_column.append(region)
        else:
            right_column.append(region)

    left_column.sort(key=lambda r: r[1])
    right_column.sort(key=lambda r: r[1])
    return left_column + right_column

def is_valid_name_box(gray_img, x, y, w, h):
    if not (NAME_REGION_Y_MIN <= y <= NAME_REGION_Y_MAX):
        return False

    cropped = gray_img[y:y + h, x:x + w]
    nonzero_ratio = np.count_nonzero(cropped) / (w * h)
    if not (VERTICAL_DENSITY_THRESHOLD_MIN < nonzero_ratio < VERTICAL_DENSITY_THRESHOLD_MAX):
        return False

    sample_x = x + w // 2
    sample_y = y + h // 2
    try:
        pixel_color = gray_img[sample_y, sample_x]
        pixel_bgr = (int(pixel_color), int(pixel_color), int(pixel_color))
        if not is_similar_color(pixel_bgr, PLAYER_NAME_BG_COLOR):
            return False
    except IndexError:
        return False

    return True

def extract_name_regions_with_opencv(image: Image.Image):
    img_cv = pil_to_cv(image)
    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)

    thresh = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
        cv2.THRESH_BINARY_INV, 15, 8
    )

    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    raw_regions = []
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

        if not is_valid_name_box(gray, x, y, w, h):
            continue

        raw_regions.append((x, y, w, h))

    sorted_regions = detect_columns_and_split(raw_regions, img_width)

    return [image.crop((x, y, x + w, y + h)) for (x, y, w, h) in sorted_regions]

# 🔴 New: fallback OCR name region extractor using minus button detection
def extract_name_regions(image: Image.Image):
    name_regions = []

    try:
        name_regions = crop_name_regions_by_minus_buttons(image)
        if not name_regions:
            log("No name regions detected via minus buttons.", "w")
    except Exception as e:
        log(f"Failed to extract name regions: {e}", "e")

    print(f"extract_name_regions{name_regions}")
    return name_regions
'''    try:
        name_regions = extract_name_regions_with_opencv(image)
        if name_regions:
            return name_regions
    except Exception as e:
        log(f"OpenCV region extraction failed: {e}", "w")

    log("Fallback: Using minus button detection for name regions.", "d")
    return crop_name_regions_by_minus_buttons(image)'''

# 🔴 New: crop name regions using minus button positions
def crop_name_regions_by_minus_buttons(image_pil):
    gray_image = image_pil_to_gray(image_pil)  # 🔴 Use helper function for safety
    template = load_minus_template_from_file()
    minus_locations = find_minus_buttons(gray_image, template)

    name_regions = []
    for (x, y) in minus_locations:
        crop_box = calculate_crop_box(x, y)
        name_regions.append(image_pil.crop(crop_box))

    return name_regions

# 🔴 New: helper function to calculate crop box from detected minus button position [🔴]
def calculate_crop_box(btn_x, btn_y):
    center_x = btn_x + MINUS_CROP_TEMPLATE_WIDTH // 2
    center_y = btn_y + MINUS_CROP_TEMPLATE_HEIGHT // 2
    crop_x = max(center_x - MINUS_CROP_OFFSET_X, 0)
    crop_y = max(center_y - MINUS_CROP_OFFSET_Y, 0)
    return (crop_x, crop_y, crop_x + MINUS_CROP_REGION_WIDTH, crop_y + MINUS_CROP_REGION_HEIGHT)

# 🔴 New: extract minus button template from known coordinates
def extract_minus_template_from_screenshot(image_gray):
    x = MINUS_TEMPLATE_COORDS["x"]
    y = MINUS_TEMPLATE_COORDS["y"]
    w = MINUS_TEMPLATE_COORDS["w"]
    h = MINUS_TEMPLATE_COORDS["h"]
    return image_gray[y:y + h, x:x + w]

# 🔴 Updated: match minus buttons using template matching
def find_minus_buttons(gray_image, template, threshold=MINUS_MATCH_THRESHOLD):
    if template is None:
        log("Failed to load template.", "e")
        return []

    result = cv2.matchTemplate(gray_image, template, cv2.TM_CCOEFF_NORMED)
    locations = np.where(result >= threshold)
    matches = list(zip(*locations[::-1]))

    matches.sort(key=lambda pt: pt[1])
    filtered_matches = []
    last_y = -999

    for (x, y) in matches:
        if abs(y - last_y) >= MINUS_MIN_DISTANCE_Y:
            filtered_matches.append((x, y))
            last_y = y
    print(filtered_matches)
    return filtered_matches

def save_debug_name_regions(regions, original_image_path, version_label, folder_date):
    image_name = os.path.basename(original_image_path).split(".")[0]
    output_folder = os.path.join(DEBUG_FOLDER, folder_date)
    os.makedirs(output_folder, exist_ok=True)

    for idx, region in enumerate(regions, 1):
        filename = f"{image_name}-{version_label}-{idx:02d}.png"
        save_path = os.path.join(output_folder, filename)
        region.save(save_path)

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

def create_word_list_file(player_list):
    with open(WORDLIST_TEMP_FILE, "w", encoding="utf-8") as f:
        for name in player_list:
            f.write(name + "\n")
    return WORDLIST_TEMP_FILE

def perform_ocr_on_versions(name_images, whitelist_path):
    config = f'--psm 7 --user-words {whitelist_path}'
    return [pytesseract.image_to_string(img, config=config).strip() for img in name_images if img]

def match_player_names(recognized_names, player_list, version_label):
    return [(name, version_label) for name in recognized_names if name in player_list]

def delete_debug_images():
    if os.path.exists(DEBUG_FOLDER):
        try:
            shutil.rmtree(DEBUG_FOLDER)
            log(f"Debug images folder \"{DEBUG_FOLDER}\" deleted.", "d")
        except Exception as e:
            log(f"Failed to delete debug folder: {e}.", "e")

def preprocess_all_versions(image: Image.Image):
    SCALE_FACTOR = 2
    THRESHOLD_BINARY = 127
    MAX_VALUE = 255
    V4_EDGE_THRESHOLD = 100
    SHARPEN_KERNEL = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])

    enlarged_size = (int (image.width * SCALE_FACTOR), int (image.height * SCALE_FACTOR))
    image = image.resize(enlarged_size, Image.LANCZOS)

    img_cv = pil_to_cv(image)
    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)

    v1 = gray.copy()
    _, v2 = cv2.threshold(gray, THRESHOLD_BINARY, MAX_VALUE, cv2.THRESH_BINARY)
    v3 = cv2.filter2D(gray, -1, SHARPEN_KERNEL)
    v4 = cv2.Canny(gray, threshold1=V4_EDGE_THRESHOLD, threshold2=V4_EDGE_THRESHOLD * 2)

    return {
        "v1": Image.fromarray(v1),
        "v2": Image.fromarray(v2),
        "v3": Image.fromarray(v3),
        "v4": Image.fromarray(v4)
    }

def image_pil_to_gray(image_pil):
    """
    Converts a PIL image (RGB or grayscale) to a grayscale OpenCV format.
    """
    img_array = np.array(image_pil)
    if len(img_array.shape) == 3 and img_array.shape[2] == 3:
        return cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    elif len(img_array.shape) == 2:  # already grayscale
        return img_array
    else:
        raise ValueError("Unsupported image format for grayscale conversion.")
    
# 🔴 Debug constants for crop test [🔴]
DEBUG_CROP_VERSION_LABEL = "template-crop"
DEBUG_TEMPLATE_CROP_FOLDER = DEBUG_FOLDER  # reuse debug folder path

# 🔴 New: debug crop from screenshot using external minus button template [🔴]
def debug_crop_regions_by_template(image_pil: Image.Image, original_image_path: str, folder_date: str):
    """
    This debug function uses the external minus button template (button.png)
    to detect minus positions in a screenshot and crops name regions accordingly.
    Resulting cropped images will be saved to the debug folder for inspection.
    """
    gray_image = image_pil_to_gray(image_pil)
    template = load_minus_template_from_file()

    if template is None:
        log("Template not found. Aborting crop debug.", "e")
        return

    matches = find_minus_buttons(gray_image, template)
    if not matches:
        log("No minus buttons found during debug crop.", "w")
        return

    image_name = os.path.basename(original_image_path).split(".")[0]
    output_folder = os.path.join(DEBUG_TEMPLATE_CROP_FOLDER, folder_date)
    os.makedirs(output_folder, exist_ok=True)

    for idx, (x, y) in enumerate(matches, 1):
        crop_box = calculate_crop_box(x, y)
        cropped_region = image_pil.crop(crop_box)

        filename = f"{image_name}-{DEBUG_CROP_VERSION_LABEL}-{idx:02d}.png"
        save_path = os.path.join(output_folder, filename)
        cropped_region.save(save_path)
        log(f"Saved debug crop #{idx} to {save_path}", "d")
