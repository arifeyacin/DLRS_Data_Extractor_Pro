"""
Main Window & 2-Stage Workflow Navigation Subsystem for DLRS Data Extractor Pro v2.0
Manages decoupled Stage 1 (Download), File Manager, Stage 2 (Convert & Extract), and Search tabs.
"""

import os
import threading
import customtkinter as ctk
from typing import Dict, Any, List, Optional

from app.config_manager import ConfigManager
from app.logger import LogManager, get_system_logger
from app.scraper.asset_finder import AssetFinder, AssetItem
from app.scraper.downloader import ResilientDownloader, DownloadProgress
from app.pdf_processor.pdf_detector import PDFDetector
from app.pdf_processor.text_extractor import TextExtractor
from app.pdf_processor.ocr_engine import OCREngine
from app.pdf_processor.parser import LandRecordParser, LandRecord
from app.database.db_manager import DatabaseManager
from app.database.repositories import LandRecordRepository, DownloadRepository
from app.exporter.export_manager import ExportManager

from app.gui.dashboard_tab import DashboardTab
from app.gui.file_manager_tab import FileManagerTab
from app.gui.convert_tab import ConvertTab
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

        self.title("DLRS Data Extractor Pro v2.0 - High Performance 2-Stage Engine")
        self.geometry("1150 x 750")
        self.minsize(980, 640)

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

        # 1. Sidebar Navigation Frame
        self.sidebar_frame = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(6, weight=1)

        lbl_logo = ctk.CTkLabel(
            self.sidebar_frame,
            text="DLRS Extractor v2.0",
            font=ctk.CTkFont(size=17, weight="bold")
        )
        lbl_logo.grid(row=0, column=0, padx=15, pady=(20, 15))

        self.btn_nav_dash = ctk.CTkButton(
            self.sidebar_frame, text="📥 Stage 1: Download", fg_color="transparent", text_color=("gray10", "gray90"),
            hover_color=("gray70", "gray30"), anchor="w", command=lambda: self._select_tab("dashboard")
        )
        self.btn_nav_dash.grid(row=1, column=0, padx=10, pady=4, sticky="ew")

        self.btn_nav_files = ctk.CTkButton(
            self.sidebar_frame, text="📂 File Selection Manager", fg_color="transparent", text_color=("gray10", "gray90"),
            hover_color=("gray70", "gray30"), anchor="w", command=lambda: self._select_tab("files")
        )
        self.btn_nav_files.grid(row=2, column=0, padx=10, pady=4, sticky="ew")

        self.btn_nav_convert = ctk.CTkButton(
            self.sidebar_frame, text="⚡ Stage 2: Convert & Extract", fg_color="transparent", text_color=("gray10", "gray90"),
            hover_color=("gray70", "gray30"), anchor="w", command=lambda: self._select_tab("convert")
        )
        self.btn_nav_convert.grid(row=3, column=0, padx=10, pady=4, sticky="ew")

        self.btn_nav_search = ctk.CTkButton(
            self.sidebar_frame, text="🔍 Search & Explore", fg_color="transparent", text_color=("gray10", "gray90"),
            hover_color=("gray70", "gray30"), anchor="w", command=lambda: self._select_tab("search")
        )
        self.btn_nav_search.grid(row=4, column=0, padx=10, pady=4, sticky="ew")

        self.btn_nav_settings = ctk.CTkButton(
            self.sidebar_frame, text="⚙️ Settings", fg_color="transparent", text_color=("gray10", "gray90"),
            hover_color=("gray70", "gray30"), anchor="w", command=lambda: self._select_tab("settings")
        )
        self.btn_nav_settings.grid(row=5, column=0, padx=10, pady=4, sticky="ew")

        # 2. Main Content Container
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        self.content_frame.grid_rowconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(0, weight=1)

        # Tab Views
        self.tab_dashboard = DashboardTab(
            self.content_frame,
            on_start=self._start_stage1_download,
            on_pause=self._pause_extraction,
            on_resume=self._resume_extraction,
            on_cancel=self._cancel_extraction,
            initial_url=self.config_mgr.get("target_urls")[0]
        )

        self.tab_files = FileManagerTab(
            self.content_frame,
            on_start_conversion=self._switch_to_stage2_convert,
            output_root_dir=self.config_mgr.get("download.output_dir", "./Output")
        )

        self.tab_convert = ConvertTab(
            self.content_frame,
            on_start_convert=self._start_stage2_conversion,
            on_cancel_convert=self._cancel_extraction
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
        self.tab_files.grid_forget()
        self.tab_convert.grid_forget()
        self.tab_search.grid_forget()
        self.tab_settings.grid_forget()

        for btn in [self.btn_nav_dash, self.btn_nav_files, self.btn_nav_convert, self.btn_nav_search, self.btn_nav_settings]:
            btn.configure(fg_color="transparent")

        if tab_name == "dashboard":
            self.tab_dashboard.grid(row=0, column=0, sticky="nsew")
            self.btn_nav_dash.configure(fg_color=("gray75", "gray25"))
        elif tab_name == "files":
            self.tab_files.refresh_file_list()
            self.tab_files.grid(row=0, column=0, sticky="nsew")
            self.btn_nav_files.configure(fg_color=("gray75", "gray25"))
        elif tab_name == "convert":
            self.tab_convert.grid(row=0, column=0, sticky="nsew")
            self.btn_nav_convert.configure(fg_color=("gray75", "gray25"))
        elif tab_name == "search":
            self.tab_search.grid(row=0, column=0, sticky="nsew")
            self.btn_nav_search.configure(fg_color=("gray75", "gray25"))
        elif tab_name == "settings":
            self.tab_settings.grid(row=0, column=0, sticky="nsew")
            self.btn_nav_settings.configure(fg_color=("gray75", "gray25"))

    def _on_gui_log_received(self, msg: str, level: str):
        """Thread-safe UI logger callback."""
        self.after(0, lambda: self.tab_dashboard.append_log(msg, level))
        self.after(0, lambda: self.tab_convert.append_log(msg))

    def _start_stage1_download(self, target_url: str):
        """Stage 1: Multi-format download worker thread."""
        allowed_formats = []
        if self.tab_dashboard.var_fmt_pdf.get(): allowed_formats.append("pdf")
        if self.tab_dashboard.var_fmt_html.get(): allowed_formats.append("html")
        if self.tab_dashboard.var_fmt_img.get(): allowed_formats.append("image")
        if self.tab_dashboard.var_fmt_doc.get(): allowed_formats.append("document")

        self.worker_thread = threading.Thread(
            target=self._run_stage1_worker,
            args=(target_url, allowed_formats),
            daemon=True
        )
        self.worker_thread.start()

    def _run_stage1_worker(self, target_url: str, allowed_formats: List[str]):
        try:
            self.logger.info("=== Stage 1 Download Worker Started ===")
            self._ui_status("Discovering asset files from portal...", 0.1)

            finder = AssetFinder()
            assets = finder.discover_assets(target_url, allowed_formats=allowed_formats)

            self._ui_stats(pdfs=len(assets))
            self.logger.info(f"Discovered {len(assets)} target assets matching {allowed_formats}.")

            if not assets:
                self._ui_status("No assets matching selected formats found.", 1.0)
                self.after(0, self.tab_dashboard.reset_buttons)
                return

            # Initialize Downloader
            self.downloader = ResilientDownloader(
                output_dir=self.config_mgr.get("download.output_dir", "./Output"),
                max_threads=self.config_mgr.get("download.threads", 4),
                max_retries=self.config_mgr.get("download.max_retries", 3)
            )

            self._ui_status("Downloading files...", 0.3)

            # Convert AssetItem list to PDFItem-compatible objects for downloader
            from app.scraper.pdf_finder import PDFItem
            pdf_items = [
                PDFItem(url=a.url, filename=a.filename, district=a.district, upazila=a.upazila, title=a.title, source_page=a.source_page)
                for a in assets
            ]

            def on_progress(p: DownloadProgress):
                prog = 0.3 + (0.7 * (p.completed_files / p.total_files if p.total_files > 0 else 0))
                self._ui_status(p.status, prog)
                self._ui_stats(pdfs=p.total_files, downloaded=p.completed_files, speed_kbps=p.speed_kbps)

            res = self.downloader.download_batch(pdf_items, progress_callback=on_progress)
            self._ui_status("Stage 1 Download Completed! Switch to File Selection Manager.", 1.0)
            self.logger.info(f"Stage 1 Download Finished: {len(res['success'])} files ready.")
            self.after(0, lambda: self._select_tab("files"))
        except Exception as e:
            self.logger.error(f"Stage 1 Download error: {e}")
            self._ui_status(f"Error: {e}", 0.0)
        finally:
            self.after(0, self.tab_dashboard.reset_buttons)

    def _switch_to_stage2_convert(self, selected_paths: List[str]):
        """Pass user-selected files from File Manager to Stage 2 Convert Tab."""
        self.tab_convert.set_queued_files(selected_paths)
        self._select_tab("convert")

    def _start_stage2_conversion(self, file_paths: List[str]):
        """Stage 2: Conversion & Extraction worker thread."""
        self.worker_thread = threading.Thread(
            target=self._run_stage2_worker,
            args=(file_paths,),
            daemon=True
        )
        self.worker_thread.start()

    def _run_stage2_worker(self, file_paths: List[str]):
        try:
            self.logger.info("=== Stage 2 Conversion & Extraction Worker Started ===")
            detector = PDFDetector()
            extractor = TextExtractor()
            ocr_engine = OCREngine(
                tesseract_cmd=self.config_mgr.get("ocr.tesseract_cmd"),
                lang=self.config_mgr.get("ocr.language"),
                ocr_cache_dir=self.config_mgr.get("ocr.output_dir")
            )
            parser = LandRecordParser()

            total_files = len(file_paths)
            converted_files = 0
            total_records = 0
            total_chars = 0

            for idx, f_path in enumerate(file_paths):
                if not os.path.exists(f_path):
                    continue

                filename = os.path.basename(f_path)
                status_str = f"Processing ({idx+1}/{total_files}): {filename}"
                prog = (idx + 1) / total_files
                self.after(0, lambda s=status_str, p=prog: self.tab_convert.update_progress(s, p))

                ext = os.path.splitext(filename)[1].lower()
                full_text = ""
                tables = []

                if ext == ".pdf":
                    detection = detector.detect(f_path)
                    doc_content = extractor.extract(f_path)
                    full_text = doc_content.full_text
                    tables = doc_content.all_tables

                    if detection.requires_ocr:
                        ocr_res = ocr_engine.process_pdf(f_path)
                        full_text += "\n" + "\n".join(r.text for r in ocr_res)
                elif ext in [".html", ".htm"]:
                    with open(f_path, "r", encoding="utf-8", errors="ignore") as hf:
                        from bs4 import BeautifulSoup
                        soup = BeautifulSoup(hf.read(), "lxml")
                        full_text = soup.get_text(separator=" ", strip=True)

                total_chars += len(full_text)

                # Parse entities
                records = parser.parse_document(
                    full_text=full_text,
                    tables=tables,
                    default_district="General",
                    default_upazila="General",
                    source_pdf=filename
                )

                if records:
                    self.land_repo.insert_batch(records)
                    total_records += len(records)

                converted_files += 1
                self.after(0, lambda q=total_files, d=converted_files, r=total_records, c=total_chars: self.tab_convert.update_stats(q, d, r, c))

            # Multi-format Exports
            self.after(0, lambda: self.tab_convert.update_progress("Generating JSON, CSV, and Excel exports...", 0.95))
            self.export_mgr.export_all()

            self.after(0, lambda: self.tab_convert.update_progress("Stage 2 Conversion Completed Successfully!", 1.0))
            self.logger.info(f"Stage 2 Conversion Finished: {converted_files} files processed, {total_records} land records extracted.")
        except Exception as e:
            self.logger.error(f"Stage 2 error: {e}")
            self.after(0, lambda: self.tab_convert.update_progress(f"Error: {e}", 0.0))
        finally:
            self.after(0, self.tab_convert.reset_controls)

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
