"""
Dashboard Tab Module for DLRS Data Extractor Pro Desktop GUI
Contains URL input, Start/Pause/Resume/Cancel controls, progress bar, stats counters, and live log stream.
"""

import customtkinter as ctk
from typing import Callable, Optional

class DashboardTab(ctk.CTkFrame):
    """Main Operational Dashboard View."""

    def __init__(
        self,
        master,
        on_start: Callable[[str], None],
        on_pause: Callable[[], None],
        on_resume: Callable[[], None],
        on_cancel: Callable[[], None],
        initial_url: str = "https://dlrs.gov.bd/pages/static-pages/অর্পিত-সম্পত্তির-গ্যাজেট-তালিকা-ldsoay-6994019afcf25ca2d10077ca"
    ):
        super().__init__(master, corner_radius=10)
        self.on_start_cb = on_start
        self.on_pause_cb = on_pause
        self.on_resume_cb = on_resume
        self.on_cancel_cb = on_cancel

        self._build_ui(initial_url)

    def _build_ui(self, initial_url: str):
        self.grid_columnconfigure(0, weight=1)

        # 1. Title Header
        title_frame = ctk.CTkFrame(self, fg_color="transparent")
        title_frame.pack(fill="x", padx=20, pady=(15, 5))
        
        lbl_title = ctk.CTkLabel(
            title_frame,
            text="DLRS Data Extraction Control Center",
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold")
        )
        lbl_title.pack(side="left")

        # 2. Target URL Input Section & Format Selector
        url_frame = ctk.CTkFrame(self, corner_radius=8)
        url_frame.pack(fill="x", padx=20, pady=8)
        url_frame.grid_columnconfigure(1, weight=1)

        lbl_url = ctk.CTkLabel(url_frame, text="Target URL:", font=ctk.CTkFont(size=12, weight="bold"))
        lbl_url.grid(row=0, column=0, padx=(15, 5), pady=(12, 4))

        self.url_entry = ctk.CTkEntry(url_frame, font=ctk.CTkFont(size=11), placeholder_text="Enter DLRS Page URL...")
        self.url_entry.insert(0, initial_url)
        self.url_entry.grid(row=0, column=1, padx=5, pady=(12, 4), sticky="ew")

        # Checkbox Format Filter Bar
        fmt_bar = ctk.CTkFrame(url_frame, fg_color="transparent")
        fmt_bar.grid(row=1, column=1, padx=5, pady=(0, 10), sticky="w")

        ctk.CTkLabel(fmt_bar, text="Target Formats to Download:", font=ctk.CTkFont(size=11, weight="bold"), text_color="gray70").pack(side="left", padx=(0, 8))

        self.var_fmt_pdf = ctk.BooleanVar(value=True)
        self.var_fmt_html = ctk.BooleanVar(value=True)
        self.var_fmt_img = ctk.BooleanVar(value=True)
        self.var_fmt_doc = ctk.BooleanVar(value=False)

        ctk.CTkCheckBox(fmt_bar, text="PDF (.pdf)", variable=self.var_fmt_pdf, width=18).pack(side="left", padx=6)
        ctk.CTkCheckBox(fmt_bar, text="HTML Pages", variable=self.var_fmt_html, width=18).pack(side="left", padx=6)
        ctk.CTkCheckBox(fmt_bar, text="Images (PNG/JPG)", variable=self.var_fmt_img, width=18).pack(side="left", padx=6)
        ctk.CTkCheckBox(fmt_bar, text="Spreadsheets/Docs", variable=self.var_fmt_doc, width=18).pack(side="left", padx=6)

        # 3. Control Buttons Panel
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=5)

        self.btn_start = ctk.CTkButton(
            btn_frame, text="▶ Start Extraction", fg_color="#00A63E", hover_color="#008532",
            font=ctk.CTkFont(size=13, weight="bold"), height=36, command=self._handle_start
        )
        self.btn_start.pack(side="left", padx=(0, 8))

        self.btn_pause = ctk.CTkButton(
            btn_frame, text="⏸ Pause", fg_color="#FF6600", hover_color="#D95700",
            font=ctk.CTkFont(size=13, weight="bold"), height=36, state="disabled", command=self._handle_pause
        )
        self.btn_pause.pack(side="left", padx=8)

        self.btn_resume = ctk.CTkButton(
            btn_frame, text="⏯ Resume", fg_color="#1568B2", hover_color="#104E85",
            font=ctk.CTkFont(size=13, weight="bold"), height=36, state="disabled", command=self._handle_resume
        )
        self.btn_resume.pack(side="left", padx=8)

        self.btn_cancel = ctk.CTkButton(
            btn_frame, text="⏹ Cancel", fg_color="#DC2626", hover_color="#B91C1C",
            font=ctk.CTkFont(size=13, weight="bold"), height=36, state="disabled", command=self._handle_cancel
        )
        self.btn_cancel.pack(side="left", padx=8)

        # 4. Progress Indicator & Status Label
        prog_frame = ctk.CTkFrame(self, corner_radius=8)
        prog_frame.pack(fill="x", padx=20, pady=10)

        self.lbl_status = ctk.CTkLabel(prog_frame, text="Status: Ready", font=ctk.CTkFont(size=12))
        self.lbl_status.pack(anchor="w", padx=15, pady=(10, 2))

        self.progress_bar = ctk.CTkProgressBar(prog_frame, height=14)
        self.progress_bar.set(0.0)
        self.progress_bar.pack(fill="x", padx=15, pady=(2, 10))

        # 5. Live Download Statistics Panel
        stats_frame = ctk.CTkFrame(self, fg_color="transparent")
        stats_frame.pack(fill="x", padx=20, pady=5)
        stats_frame.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="stat")

        self.card_pdfs = self._create_stat_card(stats_frame, 0, "Discovered PDFs", "0")
        self.card_dl = self._create_stat_card(stats_frame, 1, "Downloaded", "0")
        self.card_parsed = self._create_stat_card(stats_frame, 2, "Parsed Records", "0")
        self.card_speed = self._create_stat_card(stats_frame, 3, "Current Speed", "0 KB/s")

        # 6. Real-Time Console Log Viewer
        log_frame = ctk.CTkFrame(self, corner_radius=8)
        log_frame.pack(fill="both", expand=True, padx=20, pady=(10, 15))

        lbl_log_title = ctk.CTkLabel(log_frame, text="Live Operation Log Stream", font=ctk.CTkFont(size=12, weight="bold"))
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

    def _handle_start(self):
        url = self.url_entry.get().strip()
        if url:
            self.btn_start.configure(state="disabled")
            self.btn_pause.configure(state="normal")
            self.btn_cancel.configure(state="normal")
            self.on_start_cb(url)

    def _handle_pause(self):
        self.btn_pause.configure(state="disabled")
        self.btn_resume.configure(state="normal")
        self.on_pause_cb()

    def _handle_resume(self):
        self.btn_resume.configure(state="disabled")
        self.btn_pause.configure(state="normal")
        self.on_resume_cb()

    def _handle_cancel(self):
        self.btn_start.configure(state="normal")
        self.btn_pause.configure(state="disabled")
        self.btn_resume.configure(state="disabled")
        self.btn_cancel.configure(state="disabled")
        self.on_cancel_cb()

    def update_status(self, text: str, progress: float = 0.0):
        self.lbl_status.configure(text=f"Status: {text}")
        self.progress_bar.set(max(0.0, min(progress, 1.0)))

    def update_stats(self, pdfs: int = 0, downloaded: int = 0, parsed: int = 0, speed_kbps: float = 0.0):
        self.card_pdfs.configure(text=str(pdfs))
        self.card_dl.configure(text=str(downloaded))
        self.card_parsed.configure(text=str(parsed))
        self.card_speed.configure(text=f"{speed_kbps:.1f} KB/s")

    def append_log(self, message: str, level: str = "INFO"):
        self.log_textbox.insert("end", f"{message}\n")
        self.log_textbox.see("end")

    def reset_buttons(self):
        self.btn_start.configure(state="normal")
        self.btn_pause.configure(state="disabled")
        self.btn_resume.configure(state="disabled")
        self.btn_cancel.configure(state="disabled")
