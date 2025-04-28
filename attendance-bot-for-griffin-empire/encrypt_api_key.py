# ----- ----- ----- -----
# encrypt_api_key.py
# For Albion Online "Griffin Empire" Guild only
# Do not distribute or modify
# Author: DragonTaki (https://github.com/DragonTaki)
# Create Date: 2025/04/27
# Update Date: 2025/04/27
# Version: v2.0
# ----- ----- ----- -----

import json
import hashlib
from typing import Dict, Any

API_KEY_FILE_RAW = "api_keys_raw.json"
API_KEY_FILE = "api_keys.json"

class AuthConfig:
    USERS_CLASS_NAME = "users"
    USERNAME_FIELD = "username"  # Username
    KEY_FIELD = "key"            # Password

# ----- Utility Functions -----
def get_hash(key: str, username: str) -> str:
    """
    Generate a SHA-256 hash using the user's key and username as salt.

    Args:
        key (str): The API key or password to hash.
        username (str): The username to use as salt.

    Returns:
        str: Hexadecimal string of the hashed value.
    """
    salt = username.encode()
    hashed = hashlib.pbkdf2_hmac(
        'sha256',
        key.encode(),
        salt,
        100000  # Iterations for strengthening
    )
    return hashed.hex()

def load_raw_keys(file_path: str = API_KEY_FILE_RAW) -> Dict[str, Any]:
    """
    Load raw API keys from a JSON file.

    Args:
        file_path (str): Path to the raw API key JSON file.

    Returns:
        Dict[str, Any]: Dictionary containing the raw user API keys.
    """
    try:
        with open(file_path, "r") as file:
            raw_api_keys = json.load(file)
        if AuthConfig.USERS_CLASS_NAME not in raw_api_keys:
            raise ValueError("Invalid format: 'users' key missing.")
        return raw_api_keys
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        exit()
    except json.JSONDecodeError:
        print(f"Error: File '{file_path}' is not a valid JSON.")
        exit()
    except Exception as e:
        print(f"Error loading raw API keys: {e}")
        exit()

def save_encrypted_keys(encrypted_data: Dict[str, Any], file_path: str = API_KEY_FILE) -> None:
    """
    Save encrypted (hashed) API keys to a JSON file.

    Args:
        encrypted_data (Dict[str, Any]): Dictionary containing users with hashed API keys.
        file_path (str): Destination path to save the encrypted API keys.

    Returns:
        None
    """
    try:
        with open(file_path, "w") as file:
            json.dump({AuthConfig.USERS_CLASS_NAME: encrypted_data[AuthConfig.USERS_CLASS_NAME]}, file, indent=4)
        print(f"✅ API keys hashed and saved to '{file_path}'.")
    except Exception as e:
        print(f"Error saving encrypted API keys: {e}")
        exit()

def encrypt_file() -> None:
    """
    Encrypt (hash) all API keys in the raw file and save them to a secure file.

    Returns:
        None
    """
    raw_api_keys = load_raw_keys()

    for user in raw_api_keys[AuthConfig.USERS_CLASS_NAME]:
        username = user.get(AuthConfig.USERNAME_FIELD)
        api_key = user.get(AuthConfig.KEY_FIELD)

        if not username or not api_key:
            print("Error: Missing 'username' or 'key' field in a user entry.")
            continue

        hashed_key = get_hash(api_key, username)
        user[AuthConfig.KEY_FIELD] = hashed_key

    save_encrypted_keys(raw_api_keys)


# ----- Main Entrypoint -----
if __name__ == "__main__":
    encrypt_file()
