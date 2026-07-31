"""
Main Window & Navigation Subsystem for DLRS Data Extractor Pro Desktop GUI
Manages sidebar navigation, background threads, theme toggling, and module orchestration.
"""

import os
import threading
import customtkinter as ctk
from typing import Dict, Any, List

from app.config_manager import ConfigManager
from app.logger import LogManager, get_system_logger
from app.scraper.pdf_finder import PDFFinder, PDFItem
from app.scraper.downloader import ResilientDownloader, DownloadProgress
from app.pdf_processor.pdf_detector import PDFDetector
from app.pdf_processor.text_extractor import TextExtractor
from app.pdf_processor.ocr_engine import OCREngine
from app.pdf_processor.parser import LandRecordParser, LandRecord
from app.database.db_manager import DatabaseManager
from app.database.repositories import LandRecordRepository, DownloadRepository
from app.exporter.export_manager import ExportManager

from app.gui.dashboard_tab import DashboardTab
from app.gui.search_tab import SearchTab
from app.gui.settings_tab import SettingsTab

class MainWindow(ctk.CTk):
    """Main Desktop Application Window."""

    def __init__(self):
        super().__init__()
        self.config_mgr = ConfigManager()

        # Set appearance theme
        theme = self.config_mgr.get("theme", "Dark")
        ctk.set_appearance_mode(theme)
        ctk.set_default_color_theme("green")

        self.title("DLRS Data Extractor Pro v1.0.0")
        self.geometry("1100 x 720")
        self.minsize(950, 600)

        # Setup Logging
        LogManager.setup_loggers(
            log_dir=self.config_mgr.get("logging.log_dir"),
            log_level=self.config_mgr.get("logging.level"),
            gui_callback=self._on_gui_log_received
        )
        self.logger = get_system_logger()

        # Database & Repositories
        self.db_mgr = DatabaseManager(db_path=self.config_mgr.get("database.db_path"))
        self.land_repo = LandRecordRepository(db_manager=self.db_mgr)
        self.download_repo = DownloadRepository(db_manager=self.db_mgr)
        self.export_mgr = ExportManager(repo=self.land_repo)

        # Worker control flags
        self.downloader: Optional[ResilientDownloader] = None
        self.worker_thread: Optional[threading.Thread] = None

        self._build_ui()

    def _build_ui(self):
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # 1. Sidebar Frame
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(4, weight=1)

        lbl_logo = ctk.CTkLabel(
            self.sidebar_frame,
            text="DLRS Extractor",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        lbl_logo.grid(row=0, column=0, padx=20, pady=(20, 20))

        self.btn_nav_dash = ctk.CTkButton(
            self.sidebar_frame, text="📊 Dashboard", fg_color="transparent", text_color=("gray10", "gray90"),
            hover_color=("gray70", "gray30"), anchor="w", command=lambda: self._select_tab("dashboard")
        )
        self.btn_nav_dash.grid(row=1, column=0, padx=10, pady=5, sticky="ew")

        self.btn_nav_search = ctk.CTkButton(
            self.sidebar_frame, text="🔍 Search & Explore", fg_color="transparent", text_color=("gray10", "gray90"),
            hover_color=("gray70", "gray30"), anchor="w", command=lambda: self._select_tab("search")
        )
        self.btn_nav_search.grid(row=2, column=0, padx=10, pady=5, sticky="ew")

        self.btn_nav_settings = ctk.CTkButton(
            self.sidebar_frame, text="⚙️ Settings", fg_color="transparent", text_color=("gray10", "gray90"),
            hover_color=("gray70", "gray30"), anchor="w", command=lambda: self._select_tab("settings")
        )
        self.btn_nav_settings.grid(row=3, column=0, padx=10, pady=5, sticky="ew")

        # 2. Main Content Container
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        self.content_frame.grid_rowconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(0, weight=1)

        # Tab Views
        self.tab_dashboard = DashboardTab(
            self.content_frame,
            on_start=self._start_extraction_pipeline,
            on_pause=self._pause_extraction,
            on_resume=self._resume_extraction,
            on_cancel=self._cancel_extraction,
            initial_url=self.config_mgr.get("target_urls")[0]
        )

        self.tab_search = SearchTab(
            self.content_frame,
            on_search=self._handle_search_query,
            on_export=self._handle_export_from_search
        )

        self.tab_settings = SettingsTab(
            self.content_frame,
            config_mgr=self.config_mgr,
            on_save=self._on_settings_saved,
            on_theme_change=self._on_theme_changed
        )

        # Show default tab
        self._select_tab("dashboard")

    def _select_tab(self, tab_name: str):
        self.tab_dashboard.grid_forget()
        self.tab_search.grid_forget()
        self.tab_settings.grid_forget()

        self.btn_nav_dash.configure(fg_color="transparent")
        self.btn_nav_search.configure(fg_color="transparent")
        self.btn_nav_settings.configure(fg_color="transparent")

        if tab_name == "dashboard":
            self.tab_dashboard.grid(row=0, column=0, sticky="nsew")
            self.btn_nav_dash.configure(fg_color=("gray75", "gray25"))
        elif tab_name == "search":
            self.tab_search.grid(row=0, column=0, sticky="nsew")
            self.btn_nav_search.configure(fg_color=("gray75", "gray25"))
        elif tab_name == "settings":
            self.tab_settings.grid(row=0, column=0, sticky="nsew")
            self.btn_nav_settings.configure(fg_color=("gray75", "gray25"))

    def _on_gui_log_received(self, msg: str, level: str):
        """Thread-safe UI logger callback."""
        self.after(0, lambda: self.tab_dashboard.append_log(msg, level))

    def _start_extraction_pipeline(self, target_url: str):
        """Launch background worker thread for scraping, downloading, OCR, & DB insertion."""
        self.worker_thread = threading.Thread(target=self._run_pipeline_worker, args=(target_url,), daemon=True)
        self.worker_thread.start()

    def _run_pipeline_worker(self, target_url: str):
        try:
            self.logger.info("=== DLRS Pipeline Worker Started ===")
            self._ui_status("Discovering PDF gazettes from website...", 0.1)

            finder = PDFFinder()
            pdf_items = finder.discover_pdfs(target_url)

            self._ui_stats(pdfs=len(pdf_items))
            self.logger.info(f"Discovered {len(pdf_items)} gazette PDFs.")

            if not pdf_items:
                self._ui_status("No PDF files discovered on page.", 1.0)
                self.after(0, self.tab_dashboard.reset_buttons)
                return

            # Initialize Downloader
            self.downloader = ResilientDownloader(
                output_dir=self.config_mgr.get("download.pdf_dir"),
                max_threads=self.config_mgr.get("download.threads", 4),
                max_retries=self.config_mgr.get("download.max_retries", 3)
            )

            self._ui_status("Downloading PDF gazettes...", 0.3)

            def on_progress(p: DownloadProgress):
                prog = 0.3 + (0.4 * (p.completed_files / p.total_files if p.total_files > 0 else 0))
                self._ui_status(p.status, prog)
                self._ui_stats(pdfs=p.total_files, downloaded=p.completed_files, speed_kbps=p.speed_kbps)

            download_res = self.downloader.download_batch(pdf_items, progress_callback=on_progress)
            successful_files = download_res["success"]

            # Process PDFs (Extract & OCR)
            self._ui_status("Extracting text and parsing land records...", 0.7)
            detector = PDFDetector()
            extractor = TextExtractor()
            ocr_engine = OCREngine(
                tesseract_cmd=self.config_mgr.get("ocr.tesseract_cmd"),
                lang=self.config_mgr.get("ocr.language"),
                ocr_cache_dir=self.config_mgr.get("ocr.output_dir")
            )
            parser = LandRecordParser()

            total_parsed = 0
            for idx, item in enumerate(pdf_items):
                safe_district = "".join(c for c in item.district if c.isalnum() or c in (" ", "_", "-")).strip() or "General"
                pdf_path = os.path.join(self.config_mgr.get("download.pdf_dir"), safe_district, item.filename)

                if os.path.exists(pdf_path):
                    detection = detector.detect(pdf_path)
                    doc_content = extractor.extract(pdf_path)

                    full_text = doc_content.full_text
                    if detection.requires_ocr:
                        ocr_res = ocr_engine.process_pdf(pdf_path)
                        ocr_text = "\n".join(r.text for r in ocr_res)
                        full_text += "\n" + ocr_text

                    records = parser.parse_document(
                        full_text=full_text,
                        tables=doc_content.all_tables,
                        default_district=item.district,
                        default_upazila=item.upazila,
                        source_pdf=item.filename
                    )

                    if records:
                        self.land_repo.insert_batch(records)
                        total_parsed += len(records)
                        self._ui_stats(parsed=total_parsed)

            # Auto Multi-Format Export
            self._ui_status("Exporting datasets (JSON, CSV, Excel)...", 0.9)
            self.export_mgr.export_all()

            self._ui_status("Pipeline Completed Successfully!", 1.0)
            self.logger.info("=== DLRS Pipeline Completed Successfully ===")
        except Exception as e:
            self.logger.error(f"Pipeline error: {e}")
            self._ui_status(f"Error: {e}", 0.0)
        finally:
            self.after(0, self.tab_dashboard.reset_buttons)

    def _pause_extraction(self):
        if self.downloader:
            self.downloader.pause()

    def _resume_extraction(self):
        if self.downloader:
            self.downloader.resume()

    def _cancel_extraction(self):
        if self.downloader:
            self.downloader.cancel()

    def _ui_status(self, status: str, prog: float):
        self.after(0, lambda: self.tab_dashboard.update_status(status, prog))

    def _ui_stats(self, pdfs: int = 0, downloaded: int = 0, parsed: int = 0, speed_kbps: float = 0.0):
        self.after(0, lambda: self.tab_dashboard.update_stats(pdfs, downloaded, parsed, speed_kbps))

    def _handle_search_query(self, **kwargs) -> List[Dict[str, Any]]:
        return self.land_repo.search(**kwargs)

    def _handle_export_from_search(self):
        paths = self.export_mgr.export_all()
        self.logger.info(f"Manual Export Created: JSON={paths['json']}, CSV={paths['csv']}, Excel={paths['excel']}")

    def _on_settings_saved(self):
        self.logger.info("Settings saved to config.json.")

    def _on_theme_changed(self, theme: str):
        ctk.set_appearance_mode(theme)
