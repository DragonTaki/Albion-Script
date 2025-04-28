# ----- ----- ----- -----
# process_screenshot.py
# For Albion Online "Griffin Empire" Guild only
# Do not distribute or modify
# Author: DragonTaki (https://github.com/DragonTaki)
# Create Date: 2025/04/18
# Update Date: 2025/04/25
# Version: v2.1
# ----- ----- ----- -----

import os
import numpy as np
from datetime import datetime
from collections import defaultdict
from PIL import Image
from fuzzywuzzy import fuzz
from enum import Enum

import cv2
import pytesseract
import shutil
from PIL import Image, ImageOps, ImageFilter

from botcore.config.constant import CacheType, EXTENSIONS, DATETIME_FORMATS, DAYS_LOOKBACK, TEXTFILE_ENCODING
from botcore.config.settings_manager import settings
from botcore.logging.app_logger import LogLevel, log
from .cache import load_from_cache
from .fetch_guild_members import fetch_guild_members
from .utils import get_file_checksum, get_path, ensure_folder_exists

# Settings for Screenshot Processing
## Sys paths
APP_DATA_FOLDER = "app_data"
THIRD_PARTY_FOLDER = "third-party"

## Debug mode
AUTO_DELETE_TEMP_FILE = False  # Toggle this to `True` to clean up debug folder

## Screenshot preprossing step 1: enlarge image
SCALE_FACTOR = 2.0  # Scale factor for enlarging the image

## Screenshot preprossing step 2: matching area
min_scale = 0.7
max_scale = 1.9
step = 0.1
MATCH_SCALES = np.arange(min_scale, max_scale + step, step).round(2).tolist()

class NameRegion:
    class Offset:
        X = -166
        Y = 0

    class Size:
        Width = 163
        Height = 35

class MergeStrategy(Enum):
    LEFTMOST = "left"
    MIDDLE = "middle"
    RIGHTMOST = "right"

## Screenshot preprossing step 3: image preprocessing
SHARPEN_KERNEL = np.array([
    [0, -0.2, 0],
    [-0.2, 2.5, -0.2],
    [0, -0.2, 0]
])

## Matching option
FUZZY_MATCH_THRESHOLD = 75

def enlarge_image(image: Image.Image):
    enlarged_size = (int (image.width * SCALE_FACTOR), int (image.height * SCALE_FACTOR))
    image = image.resize(enlarged_size, Image.LANCZOS)
    return image

def pil_to_cv2_gray(image: Image.Image):
    """
    Convert a PIL image to a grayscale OpenCV image.
    
    Args:
        image (PIL.Image): Input image.

    Returns:
        np.ndarray: Grayscale image in OpenCV format.
    """
    rgb = np.array(image)
    bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    return gray

# Constants
WORDLIST_TEMP_FILENAME = "temp_wordlist.txt"
WORDLIST_TEMP_FILE = os.path.join(settings.folder_paths.temp, WORDLIST_TEMP_FILENAME)
ensure_folder_exists(settings.folder_paths.temp)
BUTTON_TEMPLATE_FILENAME = "button.png"
BUTTON_TEMPLATE_PATH = get_path(APP_DATA_FOLDER, BUTTON_TEMPLATE_FILENAME, use_meipass=True)
BUTTON_TEMPLATE_ORIG = Image.open(BUTTON_TEMPLATE_PATH)
BUTTON_TEMPLATE_ENLARGED = enlarge_image(BUTTON_TEMPLATE_ORIG)
BUTTON_TEMPLATE_CV2 = pil_to_cv2_gray(BUTTON_TEMPLATE_ENLARGED)
MAX_VERTICAL_DIFF = 3

# Tesseract setup
TESSERACT_DIR = os.path.join(os.path.dirname(__file__), "..", "..", THIRD_PARTY_FOLDER, "tesseract")
TESSERACT_EXEC = os.path.join(TESSERACT_DIR, "tesseract.exe")
TESSDATA_DIR = os.path.join(TESSERACT_DIR, "tessdata")
pytesseract.pytesseract.tesseract_cmd = TESSERACT_EXEC
os.environ["TESSDATA_PREFIX"] = TESSDATA_DIR

def create_word_list_file(player_list):
    with open(WORDLIST_TEMP_FILE, "w", encoding=TEXTFILE_ENCODING) as f:
        for name in player_list:
            f.write(name + "\n")
    return WORDLIST_TEMP_FILE

def get_valid_player_list():
    """
    Fetch the player list from the cache or API.
    """
    player_list = load_from_cache(CacheType.MEMBERLIST)
    if player_list is None:
        log("Fetching guild members from API.")
        player_list = fetch_guild_members()
        if not player_list:
            log("Failed to fetch guild members. Cannot continue OCR parsing without member list.", LogLevel.ERROR)
            return []
        log(f"Fetched {len(player_list)} guild members.")
    else:
        log(f"Loaded {len(player_list)} guild members from cache.")

    return player_list

def save_debug_pictures(images, original_filename, prefix, subfolder=None):
    """
    Save debug images to disk only if DEBUG_MODE is enabled.

    Args:
        images: A single PIL.Image or a list of PIL.Images.
        prefix: Filename prefix to identify image purpose, e.g., 'v0_enlarged'.
        subfolder: Optional. Save to a subfolder under DEBUG_FOLDER if specified.
    """
    if not settings.enable_debug_mode:
        return

    # Check and strip known image extensions
    base_name, ext = os.path.splitext(original_filename)
    if ext.lower() in EXTENSIONS.image:
        name_without_ext = base_name
    else:
        name_without_ext = original_filename

    # Prepare folder path
    folder_path = os.path.join(settings.folder_paths.debug, subfolder) if subfolder else settings.folder_paths.debug
    os.makedirs(folder_path, exist_ok=True)

    # Ensure images is a list
    if not isinstance(images, list):
        images = [images]

    for idx, img in enumerate(images):
        if not isinstance(img, Image.Image):
            continue  # skip if not a PIL image

        filename = f"{name_without_ext}_{prefix}_{idx}.png"
        save_path = os.path.join(folder_path, filename)

        try:
            img.save(save_path)
        except Exception as e:
            log(f"Failed to save image \"{filename}\": {e}", LogLevel.ERROR)

def clear_debug_folder():
    """
    Clear all generated debug images in the DEBUG_FOLDER. 
    If subfolders are empty after deletion, remove them as well.
    """
    # Check if the DEBUG_FOLDER exists
    if not os.path.exists(settings.folder_paths.debug):
        log(f"DEBUG_FOLDER \"{settings.folder_paths.debug}\" does not exist.", LogLevel.WARN)
        return
    
    # Iterate over all items in the DEBUG_FOLDER
    for root, dirs, files in os.walk(settings.folder_paths.debug, topdown=False):  # Walk in reverse to delete files first
        for file in files:
            # Only delete image files
            if file.lower().endswith(EXTENSIONS.image):
                file_path = os.path.join(root, file)
                try:
                    os.remove(file_path)
                    log(f"Deleted image: \"{file_path}\".", LogLevel.DEBUG)
                except Exception as e:
                    log(f"Failed to delete image \"{file_path}\": {e}.", LogLevel.ERROR)

        # After files are deleted, check if the folder is empty, and remove it if so
        for dir_name in dirs:
            dir_path = os.path.join(root, dir_name)
            if not os.listdir(dir_path):  # Check if directory is empty
                try:
                    shutil.rmtree(dir_path)
                    log(f"Deleted empty folder: \"{dir_path}\".", LogLevel.DEBUG)
                except Exception as e:
                    log(f"Failed to delete folder \"{dir_path}\": {e}.", LogLevel.ERROR)

def extract_name_regions(image: Image.Image):
    """
    Extracts name regions from the image using OpenCV and returns them as PIL images.
    """
    # Use the minus button detection method to crop name regions
    return crop_name_regions_by_minus_buttons(image)

# New: crop name regions using minus button positions
def crop_name_regions_by_minus_buttons(enlarged_image: Image.Image, tolerance: int = 5) -> list[Image.Image]:
    """
    Crop name regions by detecting minus buttons in an already enlarged image.

    Args:
        enlarged_image (PIL.Image): Pre-enlarged image.

    Returns:
        List[PIL.Image]: Cropped name regions.
    """
    try:
        image_cv2 = pil_to_cv2_gray(enlarged_image)

        matched_points_with_scale = match_template(image_cv2, BUTTON_TEMPLATE_CV2, MATCH_SCALES, threshold=0.8)
        if not matched_points_with_scale:
            log("No area matched with template.", LogLevel.WARN)
            return []

        # Group matched y-values into rows
        matched_points_with_scale.sort(key=lambda pt: pt[1])
        grouped_rows = []
        current_row = [matched_points_with_scale[0]]

        for pt in matched_points_with_scale[1:]:
            if abs(pt[1] - current_row[-1][1]) <= MAX_VERTICAL_DIFF:
                current_row.append(pt)
            else:
                grouped_rows.append(current_row)
                current_row = [pt]
        grouped_rows.append(current_row)

        processed_regions = []
        name_regions = []
        for row in grouped_rows:
            row.sort(key=lambda pt: pt[0])  # sort left to right
            for (x, y, scale) in row:
                left = max(int(x + NameRegion.Offset.X * scale), 0)
                top = max(int(y + NameRegion.Offset.Y * scale), 0)
                right = left + int(NameRegion.Size.Width * scale)
                bottom = top + int(NameRegion.Size.Height * scale)

                # Check if the region is already processed using tolerance
                region = (left, top, right, bottom)
                
                # Check if there is a previously processed region with a similar location within tolerance
                is_duplicate = False
                for processed in processed_regions:
                    (prev_left, prev_top, prev_right, prev_bottom) = processed
                    if abs(prev_left - left) <= tolerance and abs(prev_top - top) <= tolerance:
                        is_duplicate = True
                        break
                
                if not is_duplicate:
                    cropped = enlarged_image.crop((left, top, right, bottom))
                    name_regions.append(cropped)
                    processed_regions.append(region)

        return name_regions

    except Exception as e:
        log(f"Failed to extract name regions: {e}", LogLevel.ERROR)
        return []

def match_template(
    image_gray: np.ndarray,
    template_gray: np.ndarray,
    scales: list[float],
    threshold: float = 0.8
) -> list[tuple[int, int]]:
    """
    Match a grayscale template within a grayscale image, with optional scaling.

    Args:
        image_gray: The target image in grayscale.
        template_gray: The template image in grayscale.
        threshold: Matching threshold between 0 and 1.
        scales: A list of scale factors to resize the template.

    Returns:
        A list of (x, y) coordinates where matches were found.
    """
    matched_points = []

    for scale in scales:
        if scale != 1.0:
            resized_template = cv2.resize(template_gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
        else:
            resized_template = template_gray

        result = cv2.matchTemplate(image_gray, resized_template, cv2.TM_CCOEFF_NORMED)
        loc = np.where(result >= threshold)
        points = list(zip(*loc[::-1]))  # (x, y)

        # Optional: remove duplicates from overlapping scale matches
        matched_points.extend([(x, y, scale) for (x, y) in points])
        matched_points = deduplicate_matches(matched_points, tolerance=10)

    return matched_points

def deduplicate_matches(points: list[tuple[int, int, float]], tolerance: int = 10,
                        strategy: MergeStrategy = MergeStrategy.MIDDLE) -> list[tuple[int, int, float]]:
    """
    Merge nearby matching points (possibly from different scales) into unique points.

    Args:
        points: List of (x, y, scale) match points.
        tolerance: Pixel distance within which to merge points.
        strategy: Strategy to choose representative point from a group.

    Returns:
        List of deduplicated (x, y, scale) points.
    """
    clusters = []

    for x, y, scale in points:
        added = False
        for cluster in clusters:
            cx, cy, _ = cluster[0]
            if abs(x - cx) <= tolerance and abs(y - cy) <= tolerance:
                cluster.append((x, y, scale))
                added = True
                break
        if not added:
            clusters.append([(x, y, scale)])

    # Select representative point from each cluster
    result = []
    for cluster in clusters:
        if strategy == MergeStrategy.LEFTMOST:
            representative = min(cluster, key=lambda pt: pt[0])  # 最左邊 x 最小
        elif strategy == MergeStrategy.RIGHTMOST:
            representative = max(cluster, key=lambda pt: pt[0])  # 最右邊 x 最大
        elif strategy == MergeStrategy.MIDDLE:
            sorted_cluster = sorted(cluster, key=lambda pt: pt[0])
            representative = sorted_cluster[len(sorted_cluster) // 2]
        else:
            representative = cluster[0]  # 預設 fallback

        result.append(representative)

    return result

def preprocess_v1(image: Image.Image) -> Image.Image:
    # Convert to grayscale, and optionally increase contrast slightly
    gray = image.convert("L")
    contrast = ImageOps.autocontrast(gray, cutoff=10)  # Apply slight contrast enhancement
    return contrast

# New V2: Contrast enhancement and moderate sharpening
def preprocess_v2(image: Image.Image) -> Image.Image:
    gray = image.convert("L")
    # Enhance contrast (slightly higher cutoff to preserve more details)
    enhanced = ImageOps.autocontrast(gray, cutoff=15)
    # Apply sharpening filter
    sharpened = enhanced.filter(ImageFilter.UnsharpMask(radius=1, percent=150, threshold=3))
    return sharpened

# New V3: Moderate sharpening with a customized kernel
def preprocess_v3(image: Image.Image) -> Image.Image:
    gray = np.array(image.convert("L"))
    # Custom sharpening kernel (slightly less aggressive)
    sharpened = cv2.filter2D(gray, -1, SHARPEN_KERNEL)
    return Image.fromarray(sharpened)

# New V4: CLAHE (Contrast Limited Adaptive Histogram Equalization) with optimized parameters
def preprocess_v4(image: Image.Image) -> Image.Image:
    gray = np.array(image.convert("L"))
    # Apply CLAHE with moderate clipping limit and a larger grid size for better general contrast
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(16, 16))  # Reduced clipLimit, increased gridSize
    equalized = clahe.apply(gray)
    return Image.fromarray(equalized)

def preprocess_all_versions(image: Image.Image) -> dict[str, Image.Image]:
    """
    Apply multiple preprocessing versions to the input image.
    
    Returns:
        A dictionary with version names as keys and processed PIL.Images as values.
    """
    return {
        "v1": preprocess_v1(image),
        "v2": preprocess_v2(image),
        "v3": preprocess_v3(image),
        "v4": preprocess_v4(image),
    }
    
def perform_ocr_on_versions(name_images, whitelist_path):
    config = f"--psm 7"
    
    ocr_results = []
    for img in name_images:
        if img:
            try:
                result = pytesseract.image_to_string(img, config=config).strip()
                if result:
                    ocr_results.append(result)
                else:
                    #log(f"Empty OCR result for image \"{img}\".", LogLevel.DEBUG)
                    continue
            except Exception as e:
                log(f"Error during OCR processing: {e}.", LogLevel.ERROR)
        else:
            log("Skipping empty image...", LogLevel.WARNING)
    
    return ocr_results

def match_player_names(recognized_names, player_list, version_label):
    matched = []

    # Normalize player list to lowercase
    lowered_player_list = [player.lower() for player in player_list]

    for name in recognized_names:
        try:
            lowered_name = name.lower()

            # Fuzzy match using original (lowercased) names
            best_match = max(
                player_list,
                key=lambda player: fuzz.ratio(lowered_name, player.lower()),
            )
            best_score = fuzz.ratio(lowered_name, best_match.lower())
            # log(f"[{version_label}] Matching \"{name}\" against \"{best_match}\" (score: {best_score})")

            if best_score > FUZZY_MATCH_THRESHOLD:
                matched.append((best_match, version_label))
            else:
                # log(f"[{version_label}] No match above threshold for \"{name}\" (score: {best_score}).", LogLevel.DEBUG)
                continue

        except Exception as e:
            log(f"[{version_label}] Failed to match \"{name}\": {e}.", LogLevel.DEBUG)

    return matched

def parse_screenshot_file(folder_name: str, player_list, wordlist_path):
    today = datetime.today()

    ensure_folder_exists(settings.folder_paths.attendance)
    folder_path = os.path.join(settings.folder_paths.attendance, folder_name)
    try:
        folder_date = datetime.strptime(folder_name, DATETIME_FORMATS.folder)
    except ValueError:
        return None, None

    if (today - folder_date).days > DAYS_LOOKBACK:
        return None, None

    log(f"Processing screenshot folder: \"{folder_name}\".")

    stats = defaultdict(lambda: {"attendance": 0, "versions": set()})
    has_valid_image = False

    for file in os.listdir(folder_path):
        if not file.lower().endswith(EXTENSIONS.image):
            continue

        full_path = os.path.join(folder_path, file)
        log(f"Processing image: \"{file}\".")

        try:
            image = Image.open(full_path)

            # Step 1: Enlarge the image first
            enlarged_image = enlarge_image(image)
            save_debug_pictures(enlarged_image, file, "s0_enlarged", folder_name)

            # Step 2: Detect name regions
            name_region_images = extract_name_regions(enlarged_image)
            save_debug_pictures(name_region_images, file, "s1_extracted", folder_name)

            image_matched_players = set()

            # Step 3: For each name region, preprocess into multiple versions and OCR
            for idx, region in enumerate(name_region_images):
                version_images = preprocess_all_versions(region)
                save_debug_pictures(version_images.values(), file, f"s2_preprocessed_{idx}", folder_name)

                region_matched_players = set()

                for version_label, version_image in version_images.items():
                    recognized_names = perform_ocr_on_versions([version_image], wordlist_path)
                    #log(f"[Region {idx}][{version_label}] OCR recognized: {recognized_names}", LogLevel.DEBUG)

                    matched_results = match_player_names(recognized_names, player_list, version_label)
                    #log(f"[Region {idx}][{version_label}] Matched results: {matched_results}", LogLevel.DEBUG)

                    for name, version in matched_results:
                        if name not in region_matched_players:
                            stats[name]["attendance"] += 1
                            region_matched_players.add(name)
                        stats[name]["versions"].add(version)
                        has_valid_image = True
                        image_matched_players.add(name)

                if region_matched_players:
                    for name in region_matched_players:
                        log(f"[Region {idx}] Matched player name: \"{name}\", total matched players: {len(image_matched_players)}.", LogLevel.DEBUG)
                else:
                    log(f"[Region {idx}] No matched player.", LogLevel.DEBUG)

            log(f"Matched players from image \"{file}\": {sorted(image_matched_players)}", LogLevel.DEBUG)

        except Exception as e:
            log(f"OCR parsing failed for \"{file}\": {str(e)}.", LogLevel.ERROR)

    if has_valid_image and stats:
        formatted = [
            {
                "name": name,
                "attendance": data["attendance"],
                "ocr": sorted([v.strip("[]") for v in data["versions"]])
            }
            for name, data in stats.items()
        ]

        log(f"Final formatted summary: {formatted}", LogLevel.DEBUG)

        if not formatted:
            log(f"No valid data found in folder \"{folder_name}\". Skipping.", LogLevel.WARN)
            return None, None

        log(f"Completed folder \"{folder_name}\" with {len(formatted)} player entries.")

        meta = {
            f: get_file_checksum(os.path.abspath(os.path.join(folder_path, f)))
            for f in os.listdir(folder_path)
            if f.lower().endswith(EXTENSIONS.image)
        }

        attendance_list = [
            {"name": entry["name"], "attendance": entry["attendance"], "versions": entry["ocr"]}
            for entry in formatted
        ]

        return attendance_list, meta
    else:
        return None, None

clear_debug_folder()