# ----- ----- ----- -----
# interface.py
# For Albion Online "Griffin Empire" Guild only
# Do not distribute or modify
# Author: DragonTaki (https://github.com/DragonTaki)
# Create Date: 2025/04/18
# Update Date: 2025/04/18
# Version: v1.0
# ----- ----- ----- -----

import tkinter as tk
from tkinter import font
import os
from datetime import datetime
import json

# Modular imports
from botcore.fetch_attendance import fetch_attendance_data
from botcore.report import prepare_report_data, write_csv
from botcore.cache import load_from_cache, save_to_cache, clear_all_cache_files  # Updated
from botcore.logger import log, set_external_logger, log_welcome_message
from botcore.screenshot_ocr import parse_screenshots

# Define constant values for configuration
BG_COLOR = "#2E2E2E"
BTN_BG_COLOR = "#5C5C5C"
BTN_FG_COLOR = "white"
LOGGER_BG_COLOR = "#333333"
LOGGER_FG_COLOR = "white"
TIMESTAMP_FORMAT = "%Y/%m/%d %H:%M:%S"

# Define cache type constants
CACHE_TYPE_ATTENDANCE = "attendance"

MIN_BTN_W = 350
MIN_BTN_H = 60
MAX_BTN_W = 500
MAX_BTN_H = 120

MIN_LOGGER_W = 700
MIN_LOGGER_H = 200
MAX_LOGGER_W = 1000
MAX_LOGGER_H = 400

class AttendanceBotGUI(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Attendance Bot for Griffin Empire - created by @DragonTaki")
        self.geometry("1280x720")
        self.configure(bg=BG_COLOR)
        self.minsize(900, 600)

        self.frame = tk.Frame(self)
        self.frame.pack(fill=tk.BOTH, expand=True)

        set_external_logger(self.log)

        self.create_widgets()
        self.update_sizes()

        log_welcome_message()

    def create_widgets(self):
        button_font = font.Font(family="Helvetica", size=12, weight="bold")

        self.buttons_config = [
            {
                "label": "Fetch attendance\nTHAN\nStored as cache",
                "command": self.fetch_and_cache,
                "row": 0, "column": 0
            },
            {
                "label": "Load extra attendance\nTHAN\nStored as cache",
                "command": self.generate_ocr_attendance,
                "row": 0, "column": 1
            },
            {
                "label": "Fetch Attendance\nTHAN\nGenerate report directly\n(No need extra count attendance)",
                "command": self.fetch_and_generate_report,
                "row": 1, "column": 0
            },
            {
                "label": "Generate report from cache",
                "command": self.load_from_cache_and_generate_report,
                "row": 1, "column": 1
            },
            {
                "label": "Clear Cache",
                "command": self.clear_cache,
                "row": 2, "column": 0,
                "columnspan": 2
            }
        ]

        self.buttons = []
        for cfg in self.buttons_config:
            btn = tk.Button(self.frame, text=cfg["label"], command=cfg["command"],
                            font=button_font, bg=BTN_BG_COLOR, fg=BTN_FG_COLOR, relief="raised")
            columnspan = cfg.get("columnspan", 1)
            btn.grid(row=cfg["row"], column=cfg["column"], columnspan=columnspan,
                     padx=20, pady=20, sticky="nsew")
            self.buttons.append(btn)

        self.logger = tk.Text(self.frame, height=10, width=70, wrap=tk.WORD,
                              font=("Courier", 10), bg=LOGGER_BG_COLOR, fg=LOGGER_FG_COLOR)
        self.logger.config(state=tk.DISABLED)
        self.scrollbar = tk.Scrollbar(self.frame, command=self.logger.yview)
        self.logger.config(yscrollcommand=self.scrollbar.set)

        self.logger.grid(row=3, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")
        self.scrollbar.grid(row=3, column=2, sticky="ns")

        for r in range(4):
            self.frame.rowconfigure(r, weight=1)
        for c in range(2):
            self.frame.columnconfigure(c, weight=1)

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

    def fetch_and_cache(self):
        log("Fetching data and saving to cache...")
        try:
            data = fetch_attendance_data()
            save_to_cache({
                "type": CACHE_TYPE_ATTENDANCE,
                "json_data": data
            })
            log("Data fetched and cached.")
        except Exception as e:
            log(f"Failed to fetch and cache: {e}", "e")

    def fetch_and_generate_report(self):
        log("Fetching data and generating report...")
        try:
            data = fetch_attendance_data()
            save_to_cache({
                "type": CACHE_TYPE_ATTENDANCE,
                "json_data": data
            })
            report = prepare_report_data(data)
            write_csv(report)
            log("Report generated.")
        except Exception as e:
            log(f"Failed to generate report: {e}", "e")

    def load_from_cache_and_generate_report(self):
        log("Loading data from cache...")
        try:
            cached_data = load_from_cache(CACHE_TYPE_ATTENDANCE)
            if cached_data:
                report = prepare_report_data(cached_data)
                write_csv(report)
                log("Report generated from cache.")
            else:
                log("No valid cache found.", "w")
        except Exception as e:
            log(f"Failed to generate report from cache: {e}", "e")

    def clear_cache(self):
        log("Clearing cache...")
        try:
            deleted = clear_all_cache_files()
            log(f"Cache cleared. Deleted {deleted} files.")
        except Exception as e:
            log(f"Failed to clear cache: {e}", "e")

    def generate_ocr_attendance(self):
        log("Parsing screenshots via OCR...")
        try:
            result = parse_screenshots()
            log(f"OCR parsing done. {len(result)} days processed.")
        except Exception as e:
            log(f"OCR parsing failed: {e}", "e")

if __name__ == "__main__":
    app = AttendanceBotGUI()
    app.mainloop()
