# ----- ----- ----- -----
# generate_key.py
# For Albion Online "Griffin Empire" Guild only
# Do not distribute or modify
# Author: DragonTaki (https://github.com/DragonTaki)
# Create Date: 2025/04/27
# Update Date: 2025/04/27
# Version: v1.0
# ----- ----- ----- -----

import os
from cryptography.fernet import Fernet

KEY_FILE = "secret.key"


# ----- Utility Functions -----
def generate_random_key() -> bytes:
    """
    Generate a random key using Fernet.

    Returns:
        bytes: Randomly generated key.
    """
    return Fernet.generate_key()

def save_key(key: bytes, file_path: str = KEY_FILE) -> None:
    """
    Save the generated key into a file.

    Args:
        key (bytes): The key to be saved.
        file_path (str): The path to the key file.

    Returns:
        None
    """
    try:
        with open(file_path, "wb") as key_file:
            key_file.write(key)
        print(f"✅ New key generated and saved to '{file_path}'.")
    except Exception as e:
        print(f"Error saving the key: {e}")
        exit()

def check_key_file(file_path: str = KEY_FILE) -> bool:
    """
    Check if the key file exists and contains data.

    Args:
        file_path (str): The path to the key file.

    Returns:
        bool: True if key exists and is non-empty, False otherwise.
    """
    if os.path.exists(file_path):
        if os.path.getsize(file_path) > 0:
            print(f"Key file '{file_path}' already exists and is valid. No new key will be generated.")
            return True
        else:
            print(f"Key file '{file_path}' exists but is empty. A new key will be generated.")
            return False
    return False

def generate_key() -> None:
    """
    Generate and save a new key if the key file does not exist or is empty.

    Returns:
        None
    """
    if not check_key_file():
        key = generate_random_key()
        save_key(key)
    else:
        # Do nothing if the file already contains a valid key
        pass


# ----- Main Entrypoint -----
if __name__ == "__main__":
    generate_key()
