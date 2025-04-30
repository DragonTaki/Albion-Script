# ----- ----- ----- -----
# main_interface.py
# For Albion Online "Griffin Empire" Guild only
# Do not distribute or modify
# Author: DragonTaki (https://github.com/DragonTaki)
# Create Date: 2025/04/18
# Update Date: 2025/04/26
# Version: v2.0
# ----- ----- ----- -----

import json
import threading
import tkinter as tk
from tkinter import font

from botcore.safe_namespace import SafeNamespace
from botcore.config.settings_manager import settings, save_setting
from botcore.core.fetch_killboard_attendance import fetch_killboard_attendance
from botcore.core.fetch_guild_members import fetch_guild_members
from botcore.core.generate_report import generate_report
from botcore.core.cache import clear_all_cache_files
from botcore.core.daily_summary import DAILY_SUMMARY, clear_all_daily_summary_files
from botcore.logging.app_logger import LogLevel, log, set_external_logger, log_welcome_message
from botcore.logging.log_file_manager import append_runtime_log, save_log, save_all_logs, clear_log

# Constants for UI objects
UI = SafeNamespace(
    FRAME={
        "COLOR": {
            "BACKGROUND": "#08192D",
        }
    },
    BUTTON={
        "WIDTH": (250, 500),
        "HEIGHT": (20, 120),
        "COLOR": {
            "BACKGROUND": "#0F2540",
            "FOREGROUND": "#FCFAF2",
        },
        "FONT": lambda: font.Font(family="Helvetica", size=11, weight="bold"),
    },
    LOGGER={
        "WIDTH": (100, 1000),
        "HEIGHT": (100, 400),
        "COLOR": {
            "BACKGROUND": "#434343",
            "FOREGROUND": "#FCFAF2",
        },
        "FONT": lambda: font.Font(family="Courier", size=10),
    },
    SWITCH={
        "WIDTH": (250, 500),
        "HEIGHT": (20, 120),
    },
    RIGHTCLICK_MENU={
        "FONT": lambda: font.Font(family="Cascadia Mono", size=9),
    },
)

class AttendanceBotGUI(tk.Frame):
    def __init__(self, root):
        super().__init__(root)
        self.root = root
        self.configure(bg=UI.FRAME.COLOR.BACKGROUND)
        self.grid(sticky="nsew")

        self.bind("<Configure>", self.update_sizes)
        set_external_logger(self.log)

        self.create_widgets()
        log_welcome_message()

    def create_widgets(self):
        """Create and organize all widgets in the GUI."""
        self.buttons = []
        self.switches = {}

        # Create left and right frames
        self.left_frame = self.create_frame(self, 0, 0)
        self.right_frame = self.create_frame(self, 0, 1)

        # Initialize row counter
        r = 0

        # Helper function to create a button with an optional switch
        self.create_button_with_action(r, "Fetch member list", self.fetch_member_list_task)
        r += 1
        self.create_switch_button(r, "Fetch attendance - killboard", self.fetch_killboard_attendance_task, "killboard", settings.used_data.killboard)
        r += 1
        self.create_switch_button(r, "Fetch attendance - textfile", self.fetch_textfile_attendance_task, "textfile", settings.used_data.textfile)
        r += 1
        self.create_switch_button(r, "Fetch attendance - screenshot", self.fetch_screenshot_attendance_task, "screenshot", settings.used_data.screenshot)
        r += 1

        self.create_button_with_action(r, "Generate report", self.generate_report_from_cache_task)
        r += 1
        self.create_button_with_action(r, "Clear All Cache", self.clear_all_cache_task)
        r += 1
        self.create_button_with_action(r, "Clear Attendance Cache", self.clear_attendance_cache_task)
        r += 1
        self.create_button_with_action(r, "Clear Daily Summary Cache", self.clear_daily_summary_task)

        # Create the logger area and configure right-click menu and keyboard shortcuts
        self.logger = self.create_logger_area(self.right_frame)
        self.create_right_click_menu(self.logger)
        self.configure_shortcuts(self.logger)

    def create_frame(self, parent, row, column):
        """Helper function to create frames."""
        frame = tk.Frame(parent, bg=UI.FRAME.COLOR.BACKGROUND)
        frame.grid(row=row, column=column, sticky="nsew", padx=10, pady=10)
        return frame

    def create_switch_button(self, row, button_text, task, switch_key, initial_state):
        """Create a button with an optional toggle switch for data input."""
        row_frame = self.create_frame(self.left_frame, row, 0)
        btn = self.create_button(row_frame, button_text, lambda: self.run_with_thread(task))
        btn.pack(side="left", padx=5, pady=5)
        self.buttons.append(btn)
        switch = self.create_switch(
            row_frame, 
            switch_key, 
            initial_state,
            command=lambda: self.toggle_switch(switch_key)
        )
        
        self.switches[switch_key] = switch  # Store switch reference for later updates

    def create_button_with_action(self, row, button_text, action):
        """Create a simple button that runs an action when clicked."""
        row_frame = self.create_frame(self.left_frame, row, 0)
        btn = self.create_button(
            row_frame,
            button_text,
            lambda: self.run_with_thread(action)
        )
        btn.pack(side="left", padx=5, pady=5)
        self.buttons.append(btn)

    def create_button(self, parent, text, command):
        """Helper function to create a button."""
        width = UI.BUTTON.WIDTH.MIN // 10
        height = UI.BUTTON.HEIGHT.MIN // 20
        return tk.Button(parent, text=text, font=UI.BUTTON.FONT(), command=command,
                         bg=UI.BUTTON.COLOR.BACKGROUND, fg=UI.BUTTON.COLOR.FOREGROUND,
                         width=width, height=height,)

    def create_switch(self, parent, key, initial_state, command=None):
        """Helper function to create a switch (Checkbutton)."""
        var = tk.BooleanVar(value=initial_state)
        chk = tk.Checkbutton(parent, text="Use this data", font=UI.BUTTON.FONT(), variable=var, command=command,
                             bg=UI.FRAME.COLOR.BACKGROUND, fg=UI.BUTTON.COLOR.FOREGROUND,
                             selectcolor=UI.FRAME.COLOR.BACKGROUND)
        chk.var = var
        chk.pack(side="left")
        return var

    def create_logger_area(self, parent):
        """Create and configure the logger area on the right frame."""
        logger = tk.Text(parent, wrap=tk.WORD, height=20, font=UI.LOGGER.FONT(),
                         bg=UI.LOGGER.COLOR.BACKGROUND, fg=UI.LOGGER.COLOR.FOREGROUND)
        logger.config(state=tk.DISABLED)
        logger.pack(fill="both", expand=True, side="left")

        scrollbar = tk.Scrollbar(parent, command=logger.yview)
        logger.config(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        return logger

    def create_right_click_menu(self, logger):
        """Create the right-click context menu for the logger."""
        self.logger_menu = tk.Menu(logger, font=UI.RIGHTCLICK_MENU.FONT(), tearoff=0)

        def format_menu_item(label_text: str, shortcut_text: str, total_width: int = 40) -> str:
            padding = total_width - len(label_text) - len(shortcut_text)
            return f"{label_text}{' ' * max(padding, 1)}{shortcut_text}"

        menu_items = [
            ("Copy", "Ctrl + C", lambda: logger.event_generate("<<Copy>>")),
            ("Select All", "Ctrl + A", lambda: logger.event_generate("<<SelectAll>>")),
        ]

        for label, shortcut, command in menu_items:
            self.logger_menu.add_command(label=format_menu_item(label, shortcut), command=command)

        self.logger_menu.add_separator()  # Separator

        more_items = [
            ("Save As", "Ctrl + S", lambda: self.save_log(self.get_selected_log_lines())),
            ("Save All As", "Ctrl + Shift + S", lambda: self.save_all_logs()),
            ("Clear Log", "Ctrl + L", lambda: self.clear_log())
        ]

        for label, shortcut, command in more_items:
            self.logger_menu.add_command(label=format_menu_item(label, shortcut), command=command)

        logger.bind("<Button-3>", self.show_logger_context_menu)

    def configure_shortcuts(self, logger):
        """Configure keyboard shortcuts for the logger."""
        logger.bind("<Control-c>", lambda e: logger.event_generate("<<Copy>>"))
        logger.bind("<Control-a>", lambda e: logger.event_generate("<<SelectAll>>"))
        logger.bind("<Control-s>", lambda e: self.save_log())
        logger.bind("<Control-S>", lambda e: self.save_all_logs())
        logger.bind("<Control-l>", lambda e: self.clear_log())

    def toggle_switch(self, switch_key):
        """Update the switch value and save to settings."""
        new_value = self.switches[switch_key].get()
        setattr(settings.used_data, switch_key, new_value)
        save_setting(switch_key, new_value)

    def update_switches(self):
        """Update the UI switches to reflect the current settings."""
        self.switches["killboard"].set(settings.used_data.killboard)
        self.switches["textfile"].set(settings.used_data.textfile)
        self.switches["screenshot"].set(settings.used_data.screenshot)

    # Generic runner for async tasks
    def run_with_thread(self, task_func):
        def wrapper():
            try:
                task_func()  # Run task in background
            finally:
                self.set_all_buttons_state(tk.NORMAL)  # Unlock all buttons after completion
        self.set_all_buttons_state(tk.DISABLED)        # Lock all buttons before starting
        threading.Thread(target=wrapper, daemon=True).start()
        
    def set_all_buttons_state(self, state):
        for btn in self.buttons:
            btn.config(state=state)

    def show_logger_context_menu(self, event):
        try:
            self.logger_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.logger_menu.grab_release()

    # Logger functions
    def log(self, message):
        self.logger.config(state=tk.NORMAL)
        full_plain_text = ""
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
                    full_plain_text += content
            else:
                content = parsed.get("text", "")
                tag = parsed.get("tag", None)
                styles = {
                    "foreground": parsed.get("color", "white"),
                    "font": ("Courier", 10, ("bold" if parsed.get("bold") else "") + (" italic" if parsed.get("italic") else ""))
                }
                self.logger.insert(tk.END, content + "\n", tag)
                self.logger.tag_config(tag, **styles)
                full_plain_text += content
        except Exception:
            self.logger.insert(tk.END, message + "\n")
            full_plain_text = message
        self.logger.yview(tk.END)
        self.logger.config(state=tk.DISABLED)
        append_runtime_log(full_plain_text.strip())

    # Logger actions
    def get_selected_log_lines(self):
        selected_text = self.logger.get(self.logger.index(tk.INSERT) + " linestart", self.logger.index(tk.INSERT) + " lineend")
        return selected_text.splitlines()

    def save_log(self, selected_log_lines=None):
        lines = selected_log_lines or self.get_selected_log_lines()
        saved_log_path = save_log(lines)
        log(f"Log saved at \"{saved_log_path}\".")

    def save_all_logs(self):
        saved_log_path = save_all_logs(self.logger.get("1.0", tk.END))
        log(f"Log saved at \"{saved_log_path}\".")

    def clear_log(self):
        clear_log(self.logger)
        log_welcome_message()

    # Auto update sizes of buttons and frames on window resize
    def update_sizes(self, event=None):
        window_width = self.master.winfo_width()
        window_height = self.master.winfo_height()

        # Calculate button size for left frame
        button_width = max(UI.BUTTON.WIDTH.MIN, min(UI.BUTTON.WIDTH.MAX, window_width // 4))
        button_height = max(UI.BUTTON.HEIGHT.MIN, min(UI.BUTTON.HEIGHT.MAX, window_height // 15))

        button_area_height = len(self.buttons) * button_height + (len(self.buttons) - 1) * 10

        available_height = window_height - button_area_height - 50

        # Update button sizes in left_frame
        for btn in self.buttons:
            btn.config(width=button_width // 10, height=button_height // 15)

        # Update left_frame size
        self.left_frame.config(width=window_width // 2, height=available_height)

        # Update right_frame size (for logger)
        logger_width = max(UI.LOGGER.WIDTH.MIN, min(UI.LOGGER.WIDTH.MAX, window_width // 2 - 20))
        logger_height = max(UI.LOGGER.HEIGHT.MIN, min(UI.LOGGER.HEIGHT.MAX, window_height - 100))
        
        self.logger.config(width=logger_width // 10, height=logger_height // 15)
        self.right_frame.config(width=window_width // 2, height=available_height)

    # Task wrappers (no UI logic here)
    def fetch_member_list_task(self):
        log("Fetching member list and saving to cache...")
        try:
            data = fetch_guild_members()
            if data:
                log("Done.")
        except Exception as e:
            log(f"Failed to fetch and cache: {e}", LogLevel.ERROR)

    def fetch_killboard_attendance_task(self):
        log("Fetching attendance from killboard and saving to cache...")
        try:
            data = fetch_killboard_attendance()
            if data:
                log("Done.")
        except Exception as e:
            log(f"Failed to fetch and cache: {e}", LogLevel.ERROR)

    def fetch_textfile_attendance_task(self):
        from botcore.core.fetch_daily_attendance import fetch_daily_attendance
        log("Parsing textfile attendance...")
        try:
            result = fetch_daily_attendance(DAILY_SUMMARY.TEXTFILE)
            if len(result) > 0:
                log("Done.")
        except Exception as e:
            log(f"Failed to load attendance from file: {e}", LogLevel.ERROR)

    def fetch_screenshot_attendance_task(self):
        from botcore.core.fetch_daily_attendance import fetch_daily_attendance
        log("Parsing screenshots attendance via OCR...")
        try:
            result = fetch_daily_attendance(DAILY_SUMMARY.SCREENSHOT)
            if len(result) > 0:
                log("Done.")
        except Exception as e:
            log(f"OCR parsing failed: {e}", LogLevel.ERROR)


    def generate_report_from_cache_task(self):
        log("Loading data from cache...")
        try:
            report = generate_report(settings.used_data.killboard, settings.used_data.textfile, settings.used_data.screenshot, True)
            log("Done.")
        except Exception as e:
            log(f"Failed to generate report from cache: {e}", LogLevel.ERROR)

    def clear_all_cache_task(self):
        log("Clearing all cache...")
        try:
            deleted = clear_all_cache_files()
            deleted += clear_all_daily_summary_files()
            log(f"Cache cleared. Deleted {deleted} files.")
        except Exception as e:
            log(f"Failed to clear all cache: {e}", LogLevel.ERROR)

    def clear_attendance_cache_task(self):
        log("Clearing cache...")
        try:
            deleted = clear_all_cache_files()
            log(f"Cache cleared. Deleted {deleted} files.")
        except Exception as e:
            log(f"Failed to clear cache: {e}", LogLevel.ERROR)

    def clear_daily_summary_task(self):
        log("Clearing daily summary task...")
        try:
            deleted = clear_all_daily_summary_files()
            log(f"Cache cleared. Deleted {deleted} files.")
        except Exception as e:
            log(f"Failed to clear daily summary file: {e}", LogLevel.ERROR)

    def test_task(self):
        log("Testing...")
        try:
            result = None
            log(f"Testing done. Return: {result}.")
        except Exception as e:
            log(f"Testing failed: {e}", LogLevel.ERROR)

    def not_done_yet_task(self):
        log("This function is not done...")

'''
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Attendance Bot for Griffin Empire - created by @DragonTaki")
    root.geometry("1280x720")
    app = AttendanceBotGUI(root)
    app.pack(fill="both", expand=True)
    root.mainloop()
'''
