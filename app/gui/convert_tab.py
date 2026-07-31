"""
Stage 2 Conversion & Data Extraction Tab for DLRS Data Extractor Pro v2.0
Executes text extraction, Bengali OCR, SQLite indexing, and JSON/CSV/Excel exporting for selected files.
"""

import customtkinter as ctk
from typing import Callable, List, Optional

class ConvertTab(ctk.CTkFrame):
    """Stage 2 Processing Dashboard View."""

    def __init__(self, master, on_start_convert: Callable[[List[str]], None], on_cancel_convert: Callable[[], None]):
        super().__init__(master, corner_radius=10)
        self.on_start_convert_cb = on_start_convert
        self.on_cancel_convert_cb = on_cancel_convert
        self.queued_files: List[str] = []

        self._build_ui()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)

        # 1. Title Header
        title_frame = ctk.CTkFrame(self, fg_color="transparent")
        title_frame.pack(fill="x", padx=20, pady=(15, 5))

        lbl_title = ctk.CTkLabel(
            title_frame,
            text="Stage 2: Conversion & Data Extraction Engine",
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold")
        )
        lbl_title.pack(side="left")

        # 2. Queue Status Bar
        queue_frame = ctk.CTkFrame(self, corner_radius=8)
        queue_frame.pack(fill="x", padx=20, pady=8)

        self.lbl_queue_status = ctk.CTkLabel(
            queue_frame,
            text="Queued Files: 0 selected files ready for conversion.",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.lbl_queue_status.pack(side="left", padx=15, pady=10)

        self.btn_convert_start = ctk.CTkButton(
            queue_frame, text="▶ Start Conversion", fg_color="#00A63E", hover_color="#008532",
            font=ctk.CTkFont(size=13, weight="bold"), height=36, command=self._handle_start
        )
        self.btn_convert_start.pack(side="right", padx=10, pady=8)

        # 3. Progress Bar & Active File Status
        prog_frame = ctk.CTkFrame(self, corner_radius=8)
        prog_frame.pack(fill="x", padx=20, pady=8)

        self.lbl_file_status = ctk.CTkLabel(prog_frame, text="Current Task: Idle", font=ctk.CTkFont(size=11))
        self.lbl_file_status.pack(anchor="w", padx=15, pady=(8, 2))

        self.convert_prog_bar = ctk.CTkProgressBar(prog_frame, height=14)
        self.convert_prog_bar.set(0.0)
        self.convert_prog_bar.pack(fill="x", padx=15, pady=(2, 10))

        # 4. Conversion Statistics Cards
        stats_frame = ctk.CTkFrame(self, fg_color="transparent")
        stats_frame.pack(fill="x", padx=20, pady=5)
        stats_frame.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="cstat")

        self.card_queue = self._create_stat_card(stats_frame, 0, "Queued Files", "0")
        self.card_done = self._create_stat_card(stats_frame, 1, "Converted Files", "0")
        self.card_records = self._create_stat_card(stats_frame, 2, "Land Records", "0")
        self.card_chars = self._create_stat_card(stats_frame, 3, "Chars Extracted", "0")

        # 5. Conversion Log Viewer
        log_frame = ctk.CTkFrame(self, corner_radius=8)
        log_frame.pack(fill="both", expand=True, padx=20, pady=(10, 15))

        lbl_log_title = ctk.CTkLabel(log_frame, text="Stage 2 Conversion Log", font=ctk.CTkFont(size=12, weight="bold"))
        lbl_log_title.pack(anchor="w", padx=12, pady=(8, 4))

        self.log_textbox = ctk.CTkTextbox(log_frame, font=ctk.CTkFont(family="Consolas", size=10), wrap="word")
        self.log_textbox.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def _create_stat_card(self, parent, col: int, title: str, value: str) -> ctk.CTkLabel:
        card = ctk.CTkFrame(parent, corner_radius=8)
        card.grid(row=0, column=col, padx=4, pady=4, sticky="ew")

        lbl_t = ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=10, weight="bold"), text_color="gray70")
        lbl_t.pack(pady=(8, 0))

        lbl_v = ctk.CTkLabel(card, text=value, font=ctk.CTkFont(size=16, weight="bold"), text_color="#00A63E")
        lbl_v.pack(pady=(0, 8))
        return lbl_v

    def set_queued_files(self, file_paths: List[str]):
        self.queued_files = file_paths
        self.lbl_queue_status.configure(text=f"Queued Files: {len(file_paths)} selected files ready for conversion.")
        self.card_queue.configure(text=str(len(file_paths)))

    def _handle_start(self):
        if self.queued_files:
            self.btn_convert_start.configure(state="disabled")
            self.on_start_convert_cb(self.queued_files)

    def update_progress(self, status: str, progress: float):
        self.lbl_file_status.configure(text=status)
        self.convert_prog_bar.set(max(0.0, min(progress, 1.0)))

    def update_stats(self, queued: int, done: int, records: int, chars: int):
        self.card_queue.configure(text=str(queued))
        self.card_done.configure(text=str(done))
        self.card_records.configure(text=str(records))
        self.card_chars.configure(text=str(chars))

    def append_log(self, text: str):
        self.log_textbox.insert("end", f"{text}\n")
        self.log_textbox.see("end")

    def reset_controls(self):
        self.btn_convert_start.configure(state="normal")
