"""
Resilient Multi-Threaded PDF Downloader Engine for DLRS Data Extractor Pro
Supports parallel threads, auto-resume, retry, pause/resume/cancel, and folder organization.
"""

import os
import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import List, Dict, Callable, Optional

from app.scraper.pdf_finder import PDFItem
from app.logger import get_download_logger, get_error_logger

@dataclass
class DownloadProgress:
    total_files: int
    completed_files: int
    failed_files: int
    skipped_files: int
    current_file: str
    bytes_downloaded: int
    total_bytes: int
    speed_kbps: float
    status: str

class ResilientDownloader:
    """Enterprise multi-threaded stream downloader for PDF gazettes."""

    def __init__(
        self,
        output_dir: str = "./Output/PDFs",
        max_threads: int = 4,
        max_retries: int = 3,
        timeout: int = 30,
        chunk_size: int = 8192,
        user_agent: Optional[str] = None
    ):
        self.output_dir = os.path.abspath(output_dir)
        self.max_threads = max_threads
        self.max_retries = max_retries
        self.timeout = timeout
        self.chunk_size = chunk_size
        self.user_agent = user_agent or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0 Safari/537.36"

        self.download_logger = get_download_logger()
        self.error_logger = get_error_logger()

        # Control flags for desktop GUI interaction
        self.is_paused = False
        self.is_cancelled = False

        # Statistics
        self.completed_count = 0
        self.failed_count = 0
        self.skipped_count = 0

    def pause(self):
        """Pause downloading threads."""
        self.is_paused = True
        self.download_logger.info("Download process PAUSED.")

    def resume(self):
        """Resume downloading threads."""
        self.is_paused = False
        self.download_logger.info("Download process RESUMED.")

    def cancel(self):
        """Cancel downloading tasks."""
        self.is_cancelled = True
        self.download_logger.info("Download process CANCELLED.")

    def download_batch(
        self,
        items: List[PDFItem],
        progress_callback: Optional[Callable[[DownloadProgress], None]] = None
    ) -> Dict[str, List[str]]:
        """Execute parallel batch downloading of PDF items."""
        self.is_paused = False
        self.is_cancelled = False
        self.completed_count = 0
        self.failed_count = 0
        self.skipped_count = 0

        total_files = len(items)
        successful_paths = []
        failed_urls = []

        self.download_logger.info(f"Starting batch download for {total_files} files using {self.max_threads} threads.")

        with ThreadPoolExecutor(max_workers=self.max_threads) as executor:
            future_to_item = {
                executor.submit(self._download_single_file, item, progress_callback, total_files): item
                for item in items
            }

            for future in as_completed(future_to_item):
                item = future_to_item[future]
                if self.is_cancelled:
                    self.download_logger.warning("Batch download cancelled by user.")
                    break

                try:
                    result_path = future.result()
                    if result_path:
                        if result_path == "SKIPPED":
                            self.skipped_count += 1
                        else:
                            successful_paths.append(result_path)
                            self.completed_count += 1
                    else:
                        failed_urls.append(item.url)
                        self.failed_count += 1
                except Exception as e:
                    self.error_logger.error(f"Execution error for {item.url}: {e}")
                    failed_urls.append(item.url)
                    self.failed_count += 1

        self.download_logger.info(
            f"Batch Download Finished: Completed={self.completed_count}, Skipped={self.skipped_count}, Failed={self.failed_count}"
        )

        return {
            "success": successful_paths,
            "failed": failed_urls
        }

    def _download_single_file(
        self,
        item: PDFItem,
        progress_callback: Optional[Callable[[DownloadProgress], None]],
        total_files: int
    ) -> Optional[str]:
        """Download single PDF with auto-resume, retry logic, and subfolder organization."""
        # Sanitize folder and filename
        safe_district = "".join(c for c in item.district if c.isalnum() or c in (" ", "_", "-")).strip() or "General"
        target_folder = os.path.join(self.output_dir, safe_district)
        os.makedirs(target_folder, exist_ok=True)

        target_file_path = os.path.join(target_folder, item.filename)

        # Check existing file for duplicate skip / auto-resume
        existing_size = 0
        if os.path.exists(target_file_path):
            existing_size = os.path.getsize(target_file_path)

        for attempt in range(1, self.max_retries + 1):
            if self.is_cancelled:
                return None

            while self.is_paused:
                time.sleep(0.5)
                if self.is_cancelled:
                    return None

            try:
                headers = {"User-Agent": self.user_agent}

                # Check server content length via HEAD request with SSL fallback
                try:
                    head_resp = requests.head(item.url, headers=headers, timeout=self.timeout, allow_redirects=True, verify=True)
                except requests.exceptions.SSLError:
                    head_resp = requests.head(item.url, headers=headers, timeout=self.timeout, allow_redirects=True, verify=False)

                total_bytes = int(head_resp.headers.get("Content-Length", 0))

                # Skip if already fully downloaded
                if existing_size > 0 and total_bytes > 0 and existing_size >= total_bytes:
                    self.download_logger.info(f"[SKIP] Existing file matches size: {target_file_path}")
                    return "SKIPPED"

                # Auto-resume support via Range header
                if existing_size > 0 and total_bytes > existing_size:
                    headers["Range"] = f"bytes={existing_size}-"
                    mode = "ab"
                    downloaded_bytes = existing_size
                    self.download_logger.info(f"[RESUME] Resuming {item.filename} from byte {existing_size}")
                else:
                    mode = "wb"
                    downloaded_bytes = 0

                start_time = time.time()
                try:
                    resp = requests.get(item.url, headers=headers, stream=True, timeout=self.timeout, verify=True)
                except requests.exceptions.SSLError:
                    resp = requests.get(item.url, headers=headers, stream=True, timeout=self.timeout, verify=False)

                with resp:
                    resp.raise_for_status()

                    with open(target_file_path, mode) as f:
                        for chunk in resp.iter_content(chunk_size=self.chunk_size):
                            if self.is_cancelled:
                                return None

                            while self.is_paused:
                                time.sleep(0.5)
                                if self.is_cancelled:
                                    return None

                            if chunk:
                                f.write(chunk)
                                downloaded_bytes += len(chunk)
                                elapsed = time.time() - start_time
                                speed_kbps = (downloaded_bytes / 1024) / (elapsed if elapsed > 0 else 1)

                                if progress_callback:
                                    progress_callback(DownloadProgress(
                                        total_files=total_files,
                                        completed_files=self.completed_count,
                                        failed_files=self.failed_count,
                                        skipped_files=self.skipped_count,
                                        current_file=item.filename,
                                        bytes_downloaded=downloaded_bytes,
                                        total_bytes=total_bytes or downloaded_bytes,
                                        speed_kbps=speed_kbps,
                                        status=f"Downloading {item.filename} ({attempt}/{self.max_retries})"
                                    ))

                self.download_logger.info(f"[SUCCESS] Downloaded: {target_file_path}")
                return target_file_path

            except Exception as e:
                self.error_logger.warning(
                    f"Download attempt {attempt}/{self.max_retries} failed for {item.url}: {e}"
                )
                time.sleep(attempt * 2)  # Exponential backoff

        self.error_logger.error(f"[FAILED] Permanent failure for {item.url} after {self.max_retries} attempts.")
        return None
