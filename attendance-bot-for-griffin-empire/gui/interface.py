# ----- ----- ----- -----
# interface.py
# For Albion Online "Griffin Empire" Guild only
# Do not distribute or modify
# Author: DragonTaki (https://github.com/DragonTaki)
# Create Date: 2025/04/18
# Update Date: 2025/04/22
# Version: v1.2
# ----- ----- ----- -----

import json
import threading
import tkinter as tk
from tkinter import font

# Modular imports
from botcore.fetch_web_attendance import fetch_web_attendance
from botcore.fetch_guild_members import fetch_guild_members
from botcore.fetch_textfile_attendance import fetch_textfile_attendance
from botcore.fetch_ocr_attendance import parse_screenshots
from botcore.generate_report import generate_report
from botcore.cache import load_from_cache, save_to_cache, clear_all_cache_files
from botcore.logger import log, set_external_logger, log_welcome_message

from botcore.ocr_processing import debug_crop_regions_by_template

# Define constant values for configuration
BG_COLOR = "#08192D"
BTN_BG_COLOR = "#0F2540"
BTN_FG_COLOR = "#FCFAF2"
LOGGER_BG_COLOR = "#434343"
LOGGER_FG_COLOR = "#373C38"

# Define cache type constants
CACHE_TYPE_ATTENDANCE = "attendance"

# Constants for buttons
NUM_COLUMNS = 4
LOGGER_ROW_OFFSET = 1

MIN_BTN_W = 350
MIN_BTN_H = 60
MAX_BTN_W = 500
MAX_BTN_H = 120

MIN_LOGGER_W = 700
MIN_LOGGER_H = 200
MAX_LOGGER_W = 1000
MAX_LOGGER_H = 400


def configure_grid_layout(frame, num_buttons):
    num_rows = (num_buttons + NUM_COLUMNS - 1) // NUM_COLUMNS
    total_rows = num_rows + LOGGER_ROW_OFFSET  # +1 for logger
    for r in range(total_rows):
        frame.rowconfigure(r, weight=1)
    for c in range(NUM_COLUMNS):
        frame.columnconfigure(c, weight=1)
    return num_rows  # Return button row count for logger position

class AttendanceBotGUI(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Attendance Bot for Griffin Empire - created by @DragonTaki")
        self.geometry("1280x720")
        self.configure(bg=BG_COLOR)
        self.frame = tk.Frame(self, bg=BG_COLOR)
        self.minsize(900, 600)

        self.frame.pack(fill=tk.BOTH, expand=True)

        set_external_logger(self.log)

        self.create_widgets()
        self.update_sizes()

        log_welcome_message()
    
    def create_widgets(self):
        button_font = font.Font(family="Helvetica", size=12, weight="bold")

        self.buttons_config = [
            {
                "label": "Fetch member list\n(Save as cache)",
                "command": lambda: self.run_with_thread(self.fetch_member_list_task),
            },
            {
                "label": "Fetch attendance\n(Save as cache)",
                "command": lambda: self.run_with_thread(self.fetch_web_attendance_task),
            },
            {
                "label": "Load attendance from textfile\n(Save as cache)",
                "command": lambda: self.run_with_thread(self.fetch_textfile_attendance_task),
            },
            {
                "label": "Load attendance from screenshot\n(Save as cache)",
                "command": lambda: self.run_with_thread(self.not_done_yet_task),
            },
            {
                "label": "Generate report from web only\n[No extra attendance]",
                "command": lambda: self.run_with_thread(self.generate_report_pure_task),
            },
            {
                "label": "Generate report from cache",
                "command": lambda: self.run_with_thread(self.generate_report_from_cache_task),
            },
            {
                "label": "Clear Cache",
                "command": lambda: self.run_with_thread(self.clear_cache_task),
            },
            {
                "label": "Test Button",
                "command": lambda: self.run_with_thread(self.test_task),
            }
        ]

        self.buttons = []
        for i, cfg in enumerate(self.buttons_config):
            row = i // NUM_COLUMNS
            column = i % NUM_COLUMNS
            btn = tk.Button(self.frame, text=cfg["label"], command=cfg["command"],
                            font=button_font, bg=BTN_BG_COLOR, fg=BTN_FG_COLOR, relief="raised")
            btn.grid(row=row, column=column, padx=20, pady=20, sticky="nsew")
            self.buttons.append(btn)

        num_buttons = len(self.buttons_config)
        button_rows = configure_grid_layout(self.frame, num_buttons)

        logger_row = button_rows  # Logger is placed right after last button row

        self.logger = tk.Text(self.frame, height=10, width=70, wrap=tk.WORD,
                            font=("Courier", 10), bg=LOGGER_BG_COLOR, fg=LOGGER_FG_COLOR)
        self.logger.config(state=tk.DISABLED)

        self.scrollbar = tk.Scrollbar(self.frame, command=self.logger.yview, highlightbackground=BG_COLOR)
        self.logger.config(yscrollcommand=self.scrollbar.set)

        self.logger.grid(row=logger_row, column=0, columnspan=NUM_COLUMNS, padx=10, pady=10, sticky="nsew")
        self.scrollbar.grid(row=logger_row, column=NUM_COLUMNS, sticky="ns")

    def log(self, message):
        self.logger.config(state=tk.NORMAL)
        try:
            parsed = json.loads(message)
            if isinstance(parsed, list):
                for entry in parsed:
                    content = entry.get("text", "")
                    tag = entry.get("tag", None)
                    styles = {
                        "foreground": entry.get("color", "white"),
                        "font": ("Courier", 10, ("bold" if entry.get("bold") else "") + (" italic" if entry.get("italic") else ""))
                    }
                    self.logger.insert(tk.END, content, tag)
                    self.logger.tag_config(tag, **styles)
            else:
                content = parsed.get("text", "")
                tag = parsed.get("tag", None)
                styles = {
                    "foreground": parsed.get("color", "white"),
                    "font": ("Courier", 10, ("bold" if parsed.get("bold") else "") + (" italic" if parsed.get("italic") else ""))
                }
                self.logger.insert(tk.END, content + "\n", tag)
                self.logger.tag_config(tag, **styles)
        except Exception:
            self.logger.insert(tk.END, message + "\n")
        self.logger.yview(tk.END)
        self.logger.config(state=tk.DISABLED)

    def update_sizes(self, event=None):
        window_width = self.winfo_width()
        window_height = self.winfo_height()

        button_width = max(MIN_BTN_W, min(MAX_BTN_W, window_width // 4))
        button_height = max(MIN_BTN_H, min(MAX_BTN_H, window_height // 8))

        for btn in self.buttons:
            btn.config(width=button_width // 10, height=button_height // 15)

        logger_width = max(MIN_LOGGER_W, min(MAX_LOGGER_W, window_width - 20))
        logger_height = max(MIN_LOGGER_H, min(MAX_LOGGER_H, window_height // 3))

        self.logger.config(width=logger_width // 10, height=logger_height // 15)

    # New: Generic runner for async tasks
    def run_with_thread(self, task_func):
        def wrapper():
            try:
                task_func()  # Run task in background
            finally:
                self.set_all_buttons_state(tk.NORMAL)  # Unlock all buttons after completion
        self.set_all_buttons_state(tk.DISABLED)       # Lock all buttons before starting
        threading.Thread(target=wrapper, daemon=True).start()
        
    def set_all_buttons_state(self, state):
        for btn in self.buttons:
            btn.config(state=state)

    # Task wrappers (no UI logic here)
    def fetch_member_list_task(self):
        log("Fetching member list and saving to cache...")
        try:
            data = fetch_guild_members()
            if data:
                log("Done.")
        except Exception as e:
            log(f"Failed to fetch and cache: {e}", "e")

    def fetch_web_attendance_task(self):
        log("Fetching attendance from killboard and saving to cache...")
        try:
            data = fetch_web_attendance()
            if data:
                log("Done.")
        except Exception as e:
            log(f"Failed to fetch and cache: {e}", "e")

    def fetch_textfile_attendance_task(self):
        log("Parsing textfile attendance...")
        try:
            result = fetch_textfile_attendance()
            if len(result) > 0:
                log("Done.")
        except Exception as e:
            log(f"Failed to load attendance from file: {e}", "e")

    def fetch_screenshot_attendance_task(self):
        log("Parsing screenshots attendance via OCR...")
        try:
            result = parse_screenshots()
            if len(result) > 0:
                log("Done.")
        except Exception as e:
            log(f"OCR parsing failed: {e}", "e")

    def generate_report_pure_task(self):
        log("Fetching data and generating report...")
        try:
            report = generate_report(True, True)
            log("Done.")
        except Exception as e:
            log(f"Failed to generate report: {e}", "e")

    def generate_report_from_cache_task(self):
        log("Loading data from cache...")
        try:
            report = generate_report(True)
            log("Done.")
        except Exception as e:
            log(f"Failed to generate report from cache: {e}", "e")

    def clear_cache_task(self):
        log("Clearing cache...")
        try:
            deleted = clear_all_cache_files()
            log(f"Cache cleared. Deleted {deleted} files.")
        except Exception as e:
            log(f"Failed to clear cache: {e}", "e")

    def test_task(self):
        log("Testing...")
        try:
            result = debug_crop_regions_by_template()
            log(f"Testing done. Return: {result}.")
        except Exception as e:
            log(f"Testing failed: {e}", "e")

    def not_done_yet_task(self):
        log("This function is not done...")

if __name__ == "__main__":
    app = AttendanceBotGUI()
    app.mainloop()
