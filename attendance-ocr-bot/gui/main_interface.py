# ----- ----- ----- -----
# main_interface.py
# For Albion Online "Griffin Empire" Guild only
# Do not distribute or modify
# Author: DragonTaki (https://github.com/DragonTaki)
# Create Date: 2025/04/18
# Update Date: 2025/05/01
# Version: v2.1
# ----- ----- ----- -----

import json
import threading
import tkinter as tk
from tkinter import font

from botcore.safe_namespace import SafeNamespace
from botcore.config.settings_manager import get_settings, save_setting
settings = get_settings()
from botcore.core.fetch_killboard_attendance import fetch_killboard_attendance
from botcore.core.fetch_guild_members import fetch_guild_members
from botcore.core.generate_report import generate_report
from botcore.core.cache import clear_all_cache_files
from botcore.core.daily_summary import DAILY_SUMMARY, clear_all_daily_summary_files
from botcore.logging.app_logger import LogLevel, log, set_external_logger
from botcore.logging.log_file_manager import append_runtime_log, save_log, save_all_logs, clear_log


# ----- Constants for UI objects ----- #
UI = SafeNamespace(
    FRAME={
        "COLOR": {
            "BACKGROUND": "#08192D",
        }
    },
    BUTTON={
        "WIDTH": (240, 500),
        "HEIGHT": (50, 120),
        "RWIDTH": 0.7,
        "RHEIGHT": 0.1,
        "COLOR": {
            "BACKGROUND": "#0F2540",
            "FOREGROUND": "#FCFAF2",
        },
        "FONT": lambda: font.Font(family="Helvetica", size=11, weight="bold"),
    },
    SWITCH={
        "WIDTH": (180, 500),
        "HEIGHT": (30, 120),
    },
    LABEL={
        "WIDTH": (240, 500),
        "HEIGHT": (30, 120),
        "RWIDTH": 1.0,
        "RHEIGHT": 0.05,
        "COLOR": {
            "BACKGROUND": "#0F2540",
            "FOREGROUND": "#FCFAF2",
        },
        "FONT": lambda: font.Font(family="Helvetica", size=11, weight="bold"),
    },
    LOGGER={
        "WIDTH": (420, 1000),
        "HEIGHT": (100, 400),
        "COLOR": {
            "BACKGROUND": "#434343",
            "FOREGROUND": "#FCFAF2",
        },
        "FONT": lambda: font.Font(family="Courier", size=10),
    },
    SCROLLBAR={
        "WIDTH": 15,
    },
    RIGHTCLICK_MENU={
        "FONT": lambda: font.Font(family="Cascadia Mono", size=9),
    },
    PADDING=10,
    FULL={
        "RWIDTH": 1.0,
        "RHEIGHT": 1.0,
    },
)

class AttendanceBotGUI(tk.Frame):
    def __init__(self, root, show_welcome: bool = False):
        super().__init__(root)
        self.root = root

        self.button_row_configs = [
            ("Step 1: Get database"),
            ("Fetch member list", self.fetch_member_list_task),
            ("Step 2: Choose attendance source"),
            ("Calculate attendance - killboard", self.fetch_killboard_attendance_task, "killboard", settings.used_data.killboard),
            ("Calculate attendance - textfile", self.fetch_textfile_attendance_task, "textfile", settings.used_data.textfile),
            ("Calculate attendance - screenshot", self.fetch_screenshot_attendance_task, "screenshot", settings.used_data.screenshot),
            ("Step 3: Generate report file"),
            ("Generate report", self.generate_report_from_cache_task),
            ("Other options"),
            ("Clear All Cache", self.clear_all_cache_task),
            ("Clear Attendance Cache", self.clear_attendance_cache_task),
            ("Clear Daily Summary Cache", self.clear_daily_summary_task),
        ]

        self.configure(bg=UI.FRAME.COLOR.BACKGROUND)
        self.place(x=0, y=0, relwidth=1, relheight=1)

        """Calculate window min size"""
        row_total_height = 0
        for config in self.button_row_configs:
            if isinstance(config, str):
                row_total_height += UI.LABEL.HEIGHT.MIN
            else:
                row_total_height += UI.BUTTON.HEIGHT.MIN
        root_min_width = UI.BUTTON.WIDTH.MIN + UI.SWITCH.WIDTH.MIN + UI.LOGGER.WIDTH.MIN + UI.SCROLLBAR.WIDTH + UI.PADDING * 3
        root_min_height = row_total_height + UI.PADDING * 2
        self.root.minsize(root_min_width, root_min_height)

        self.bind("<Configure>", self.update_sizes)
        self.create_widgets()
        set_external_logger(self.log)
        if show_welcome:
            from botcore.logging.app_logger import log_welcome_message
            log_welcome_message()


    def create_widgets(self):
        """Create and organize all widgets in the GUI."""
        self.buttons = []
        self.switches = {}

        # Create left and right frames
        self.left_frame = self.create_frame(self)
        self.right_frame = self.create_frame(self)

        # Create the logger area and configure right-click menu and keyboard shortcuts
        self.logger, self.logger_scrollbar = self.create_logger_area(self.right_frame)
        self.create_right_click_menu(self.logger)
        self.configure_shortcuts(self.logger)

        # Initialize row counter
        self.button_rows = []
        row_y = 0.0

        for config in self.button_row_configs:
            if isinstance(config, str):
                """Label only"""
                text = config
                self.create_label_row(row_y, text)
                row_y += 0.04
            elif len(config) == 2:
                """Button only"""
                text, task = config
                self.create_button_with_action(row_y, text, task)
                row_y += 0.1
            else:
                """Button with switch"""
                text, task, key, initial = config
                self.create_switch_button(row_y, text, task, key, initial)
                row_y += 0.1


    def create_frame(self, parent):
        """Helper function to create frames."""
        frame = tk.Frame(parent, bg=UI.FRAME.COLOR.BACKGROUND)
        return frame

    def create_switch_button(self, row_y, button_text, task, switch_key, initial_state):
        """Create a button with an optional toggle switch for data input."""
        row_frame = self.create_frame(self.left_frame)
        row_frame.place(relx=0.0, rely=row_y, relwidth=UI.FULL.RWIDTH, relheight=UI.BUTTON.RHEIGHT)

        btn = self.create_button(row_frame, button_text, lambda: self.run_with_thread(task))
        btn.place(relx=0.005, rely=0.1, relwidth=0.7, relheight=0.8)

        switch = self.create_switch(
            row_frame,
            switch_key,
            initial_state,
            command=lambda: self.toggle_switch(switch_key)
        )
        switch_widget = switch["widget"]
        switch_widget.place(relx=0.72, rely=0.2, relwidth=0.25, relheight=0.6)

        self.buttons.append(btn)
        self.switches[switch_key] = switch["var"]  # Store switch reference for later updates
        self.button_rows.append(row_frame)

    def create_button_with_action(self, row_y, button_text, action):
        """Create a simple button that runs an action when clicked."""
        row_frame = self.create_frame(self.left_frame)
        row_frame.place(relx=0.005, rely=row_y, relwidth=UI.BUTTON.RWIDTH, relheight=UI.BUTTON.RHEIGHT)
        
        btn = self.create_button(
            row_frame,
            button_text,
            lambda: self.run_with_thread(action)
        )
        btn.place(relx=0.0, rely=0.1, relwidth=1.0, relheight=0.8)

        self.buttons.append(btn)
        self.button_rows.append(row_frame)

    def create_button(self, parent, text, command):
        """Helper function to create a button."""
        return tk.Button(
            parent, text=text, font=UI.BUTTON.FONT(), command=command,
            bg=UI.BUTTON.COLOR.BACKGROUND,
            fg=UI.BUTTON.COLOR.FOREGROUND,
            borderwidth=2, relief="solid"
        )

    def create_switch(self, parent, key, initial_state, command=None):
        var = tk.BooleanVar(value=initial_state)
        chk = tk.Checkbutton(
            parent, text="Use this data", variable=var, command=command,
            font=UI.BUTTON.FONT(),
            bg=UI.FRAME.COLOR.BACKGROUND,
            fg=UI.BUTTON.COLOR.FOREGROUND,
            selectcolor=UI.FRAME.COLOR.BACKGROUND
        )
        return {"var": var, "widget": chk}
    
    def create_label_row(self, row_y, text):
        """Create a label row to group related buttons visually."""
        row_frame = self.create_frame(self.left_frame)
        row_frame.place(relx=0.01, rely=row_y, relwidth=UI.LABEL.RWIDTH, relheight=UI.LABEL.RHEIGHT)

        label = tk.Label(
            row_frame,
            text=text,
            font=UI.LABEL.FONT(),
            bg=UI.FRAME.COLOR.BACKGROUND,
            fg=UI.LABEL.COLOR.FOREGROUND,
            anchor="w"
        )
        label.place(relx=0.02, rely=0.1, relwidth=0.96, relheight=0.8)
        self.button_rows.append(row_frame)

    def create_logger_area(self, parent):
        """Create and configure the logger area on the right frame."""
        logger = tk.Text(parent, wrap=tk.WORD, font=UI.LOGGER.FONT(),
                         bg=UI.LOGGER.COLOR.BACKGROUND, fg=UI.LOGGER.COLOR.FOREGROUND)
        logger.config(state=tk.DISABLED)

        scrollbar = tk.Scrollbar(parent, command=logger.yview)
        logger.config(yscrollcommand=scrollbar.set)

        return logger, scrollbar

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
        save_setting(f"used_data.{switch_key}", new_value)

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
        from botcore.logging.app_logger import log_welcome_message
        log_welcome_message()

    # Auto update sizes of buttons and frames on window resize
    def update_sizes(self, event=None):
        width = self.root.winfo_width()
        height = self.root.winfo_height()

        # Calculate left and right fame width
        min_left_width = UI.BUTTON.WIDTH.MIN + UI.SWITCH.WIDTH.MIN + UI.PADDING * 4
        left_width = max(width * 0.4 - UI.PADDING * 2, min_left_width)
        right_width = width - left_width - UI.PADDING * 2

        self.left_frame.place(
            x=UI.PADDING,
            y=UI.PADDING,
            width=left_width,
            height=height
        )
        self.right_frame.place(
            x=UI.PADDING + left_width,
            y=UI.PADDING,
            width=right_width,
            height=height
        )

        self.logger.place(
            x=0,
            y=0,
            width=right_width - UI.SCROLLBAR.WIDTH,
            height=height - UI.PADDING * 2
        )
        self.logger_scrollbar.place(
            x=right_width - UI.SCROLLBAR.WIDTH,
            y=0,
            width=UI.SCROLLBAR.WIDTH,
            height=height - UI.PADDING * 2
        )

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
