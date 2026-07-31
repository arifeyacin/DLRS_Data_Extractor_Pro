"""
Settings Tab Module for DLRS Data Extractor Pro Desktop GUI
Provides settings configuration for output paths, threading, retries, theme, and Tesseract path.
"""

import os
import customtkinter as ctk
from tkinter import filedialog
from typing import Callable, Dict, Any

from app.config_manager import ConfigManager

class SettingsTab(ctk.CTkFrame):
    """Configuration & Application Settings View."""

    def __init__(self, master, config_mgr: ConfigManager, on_save: Callable[[], None], on_theme_change: Callable[[str], None]):
        super().__init__(master, corner_radius=10)
        self.config_mgr = config_mgr
        self.on_save_cb = on_save
        self.on_theme_change_cb = on_theme_change

        self._build_ui()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)

        # 1. Header
        lbl_title = ctk.CTkLabel(
            self,
            text="System Settings & Preferences",
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold")
        )
        lbl_title.pack(anchor="w", padx=20, pady=(15, 10))

        # 2. Settings Form Container
        form_frame = ctk.CTkScrollableFrame(self, corner_radius=8)
        form_frame.pack(fill="both", expand=True, padx=20, pady=(0, 15))
        form_frame.grid_columnconfigure(1, weight=1)

        row = 0

        # Output Folder
        ctk.CTkLabel(form_frame, text="Output Directory:", font=ctk.CTkFont(size=12, weight="bold")).grid(row=row, column=0, padx=12, pady=10, sticky="w")
        self.entry_out_dir = ctk.CTkEntry(form_frame)
        self.entry_out_dir.insert(0, self.config_mgr.get("download.output_dir", "./Output"))
        self.entry_out_dir.grid(row=row, column=1, padx=8, pady=10, sticky="ew")

        btn_browse_out = ctk.CTkButton(form_frame, text="Browse...", width=90, command=self._browse_output_dir)
        btn_browse_out.grid(row=row, column=2, padx=12, pady=10)
        row += 1

        # Download Threads
        ctk.CTkLabel(form_frame, text="Download Threads:", font=ctk.CTkFont(size=12, weight="bold")).grid(row=row, column=0, padx=12, pady=10, sticky="w")
        self.opt_threads = ctk.CTkOptionMenu(form_frame, values=["1", "2", "4", "8", "16"])
        self.opt_threads.set(str(self.config_mgr.get("download.threads", 4)))
        self.opt_threads.grid(row=row, column=1, padx=8, pady=10, sticky="w")
        row += 1

        # Retry Count
        ctk.CTkLabel(form_frame, text="Max Retries:", font=ctk.CTkFont(size=12, weight="bold")).grid(row=row, column=0, padx=12, pady=10, sticky="w")
        self.opt_retries = ctk.CTkOptionMenu(form_frame, values=["1", "2", "3", "5", "10"])
        self.opt_retries.set(str(self.config_mgr.get("download.max_retries", 3)))
        self.opt_retries.grid(row=row, column=1, padx=8, pady=10, sticky="w")
        row += 1

        # Theme Switcher
        ctk.CTkLabel(form_frame, text="Application Theme:", font=ctk.CTkFont(size=12, weight="bold")).grid(row=row, column=0, padx=12, pady=10, sticky="w")
        self.opt_theme = ctk.CTkOptionMenu(form_frame, values=["Dark", "Light", "System"], command=self._handle_theme_change)
        self.opt_theme.set(self.config_mgr.get("theme", "Dark"))
        self.opt_theme.grid(row=row, column=1, padx=8, pady=10, sticky="w")
        row += 1

        # Tesseract OCR Command Path
        ctk.CTkLabel(form_frame, text="Tesseract OCR Path:", font=ctk.CTkFont(size=12, weight="bold")).grid(row=row, column=0, padx=12, pady=10, sticky="w")
        self.entry_tesseract = ctk.CTkEntry(form_frame)
        self.entry_tesseract.insert(0, self.config_mgr.get("ocr.tesseract_cmd", "C:\\Program Files\\Tesseract-OCR\\tesseract.exe"))
        self.entry_tesseract.grid(row=row, column=1, padx=8, pady=10, sticky="ew")

        btn_browse_tess = ctk.CTkButton(form_frame, text="Browse...", width=90, command=self._browse_tesseract)
        btn_browse_tess.grid(row=row, column=2, padx=12, pady=10)
        row += 1

        # Save Button
        btn_save = ctk.CTkButton(
            form_frame, text="💾 Save Configuration", fg_color="#00A63E", hover_color="#008532",
            font=ctk.CTkFont(size=13, weight="bold"), height=36, command=self._save_settings
        )
        btn_save.grid(row=row, column=1, padx=8, pady=25, sticky="w")

    def _browse_output_dir(self):
        folder = filedialog.askdirectory(title="Select Output Directory")
        if folder:
            self.entry_out_dir.delete(0, "end")
            self.entry_out_dir.insert(0, folder)

    def _browse_tesseract(self):
        file_path = filedialog.askopenfilename(
            title="Select Tesseract Executable",
            filetypes=[("Executable Files", "*.exe"), ("All Files", "*.*")]
        )
        if file_path:
            self.entry_tesseract.delete(0, "end")
            self.entry_tesseract.insert(0, file_path)

    def _handle_theme_change(self, choice: str):
        self.on_theme_change_cb(choice)

    def _save_settings(self):
        self.config_mgr.set("download.output_dir", self.entry_out_dir.get().strip())
        self.config_mgr.set("download.threads", int(self.opt_threads.get()))
        self.config_mgr.set("download.max_retries", int(self.opt_retries.get()))
        self.config_mgr.set("theme", self.opt_theme.get())
        self.config_mgr.set("ocr.tesseract_cmd", self.entry_tesseract.get().strip())

        self.on_save_cb()
