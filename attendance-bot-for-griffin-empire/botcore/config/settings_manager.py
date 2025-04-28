# ----- ----- ----- -----
# settings_manager.py
# For Albion Online "Griffin Empire" Guild only
# Do not distribute or modify
# Author: DragonTaki (https://github.com/DragonTaki)
# Create Date: 2025/04/27
# Update Date: 2025/04/27
# Version: v1.0
# ----- ----- ----- -----

import os
import json5
from collections import OrderedDict
from shutil import copyfile

from .constant import TEXTFILE_ENCODING
from .static_settings import GUILD_INFO_LIST, USED_DATA, DATE_FORMAT, FOLDER_PATHS, MAX_CSV_VERSIONS, IF_DEBUG_MODE, IF_FORCE_NEW_DAILY_SUMMARY
from botcore.safe_namespace import SafeNamespace

SETTINGS_PATH = "settings.json"

SETTING_KEYS = SafeNamespace(
    guild_info="guild_info",
    used_data="used_data",
    date_format="date_format",
    folder_paths="folder_paths",
    max_csv_versions="max_csv_versions",
    enable_debug_mode="enable_debug_mode",
    force_regenerate_daily_summary="force_regenerate_daily_summary",
)

current_settings = {
    SETTING_KEYS.guild_info: {
        "default": GUILD_INFO_LIST[0]["name"] if GUILD_INFO_LIST else "",
        "list": GUILD_INFO_LIST,
    },
    SETTING_KEYS.used_data: USED_DATA,
    SETTING_KEYS.date_format: DATE_FORMAT,
    SETTING_KEYS.folder_paths: FOLDER_PATHS,
    SETTING_KEYS.max_csv_versions: MAX_CSV_VERSIONS,
    SETTING_KEYS.enable_debug_mode: IF_DEBUG_MODE,
    SETTING_KEYS.force_regenerate_daily_summary: IF_FORCE_NEW_DAILY_SUMMARY,
}

# Settings Object
# ----- ----- ----- -----

class Settings:
    def __init__(self, settings_dict: dict):
        def get_setting(key: str):
            return settings_dict.get(key, current_settings.get(key))

        # Check if SETTING_KEYS is a SafeNamespace instance
        if isinstance(SETTING_KEYS, SafeNamespace):
            setting_keys = SETTING_KEYS.__dict__  # Use the dict if it's SafeNamespace
        else:
            setting_keys = SETTING_KEYS  # Otherwise, use the original dictionary

        # Iterate through the setting keys
        for key, attr_name in setting_keys.items():
            setattr(self, attr_name, self._to_namespace(get_setting(key)))

    def _to_namespace(self, value):
        """ Recursively convert dictionaries into SafeNamespace"""
        if isinstance(value, dict):
            return SafeNamespace(**{k: self._to_namespace(v) for k, v in value.items()})
        return value

    def to_dict(self):
        """Convert the Settings object into a dictionary, including SafeNamespace objects."""
        settings_dict = {}
        for key, value in self.__dict__.items():
            if isinstance(value, SafeNamespace):
                settings_dict[key] = value.to_dict()  # Convert SafeNamespace to dict
            else:
                settings_dict[key] = value
        return settings_dict

# Global settings instance (initialized later)
settings: Settings = None

# ----- ----- ----- -----
# Load & Save Functions
# ----- ----- ----- -----

def safe_load_json5(path):
    """Try load JSON5. If fails, attempt partial load."""
    try:
        with open(path, "r", encoding=TEXTFILE_ENCODING) as f:
            return json5.load(f, object_pairs_hook=OrderedDict)  # Ensure it loads as ordered dict
    except Exception as e:
        print(f"[Warn] Failed to fully load {path}: {e}")
        print("[Info] Trying to recover as much as possible...")
        return recover_partial_json5(path)

def recover_partial_json5(path):
    """Try load parts of JSON5 even if some lines are broken."""
    recovered = {}
    current = ""
    with open(path, "r", encoding=TEXTFILE_ENCODING) as f:
        for line in f:
            try:
                current += line
                partial = json5.loads(f"{{{current}}}")
                recovered = partial
            except Exception:
                continue
    return recovered

def save_setting(key_path: str, value):
    """Update a single setting and save to settings.json.

    Args:
        key_path (str): A dot-separated path to the setting, e.g., "used_data.killboard".
        value: The new value to set.
    """
    keys = key_path.split(".")
    d = current_settings

    # Navigate into nested dict
    for k in keys[:-1]:
        d = d.get(k)
        if d is None:
            raise KeyError(f"Invalid settings path: {key_path}")

    # Set the value
    d[keys[-1]] = value

    # Save the whole settings dict to file
    save_settings(current_settings)

def safe_namespace_default(obj):
    """Custom default method for serializing SafeNamespace."""
    if isinstance(obj, SafeNamespace):
        return obj.to_dict()  # Convert SafeNamespace to dictionary
    raise TypeError(f'{repr(obj)} is not JSON5 serializable')

def save_settings(settings_dict):
    """Save the settings dictionary to the settings.json file."""
    # Convert SafeNamespace objects to dict before saving
    settings_dict = settings_dict.to_dict() if isinstance(settings_dict, SafeNamespace) else settings_dict
    with open(SETTINGS_PATH, "w", encoding=TEXTFILE_ENCODING) as f:
        json5.dump(settings_dict, f, indent=4, ensure_ascii=False, default=safe_namespace_default)

def merge_settings(settings_dict, default_dict):
    """Merge settings with defaults, allowing partial overrides."""
    merged_dict = {}

    for key, value in default_dict.items():
        # Check if settings_dict is an instance of SafeNamespace
        if isinstance(settings_dict, SafeNamespace):
            settings_value = getattr(settings_dict, key, None)
        else:
            settings_value = settings_dict.get(key, None)

        # If value is a SafeNamespace, recursively merge using __dict__
        if isinstance(value, SafeNamespace):
            merged_dict[key] = merge_settings(settings_value or {}, value.__dict__)
        elif isinstance(value, dict):  # Handle normal dictionaries
            merged_dict[key] = merge_settings(settings_value or {}, value)
        else:
            # Regular value, fallback to settings_value if it exists
            merged_dict[key] = settings_value if settings_value is not None else value

    return merged_dict

def load_and_apply_settings():
    """Load settings.json and apply to global settings object."""
    global settings

    if not os.path.exists(SETTINGS_PATH):
        save_settings(current_settings)
        settings_dict = current_settings
    else:
        settings_dict = safe_load_json5(SETTINGS_PATH)
        if not settings_dict:
            print("[Warn] No valid settings found, restoring default settings.")
            copyfile(SETTINGS_PATH, SETTINGS_PATH + ".broken")
            save_settings(current_settings)
            settings_dict = current_settings

        settings_dict = merge_settings(settings_dict, current_settings)
        save_settings(settings_dict)

    settings = Settings(settings_dict)

# Manual Init
if settings is None:
    load_and_apply_settings()
