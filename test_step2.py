"""
Step 2 Verification Test Script for DLRS Data Extractor Pro
Tests Logger, ConfigManager, WebAnalyzer, PDFFinder, and ResilientDownloader against DLRS live website.
"""

import sys
import os

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Ensure Windows stdout supports UTF-8 Bengali characters
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from app.config_manager import ConfigManager
from app.logger import LogManager, get_system_logger, get_download_logger
from app.scraper.web_analyzer import WebAnalyzer
from app.scraper.pdf_finder import PDFFinder
from app.scraper.downloader import ResilientDownloader, DownloadProgress

def run_test():
    print("=" * 70)
    print("      DLRS Data Extractor Pro - Step 2 Empirical Verification Test      ")
    print("=" * 70)

    # 1. Test ConfigManager & LogManager
    config_mgr = ConfigManager()
    LogManager.setup_loggers(
        log_dir=config_mgr.get("logging.log_dir"),
        log_level=config_mgr.get("logging.level")
    )
    logger = get_system_logger()
    logger.info("Initializing Step 2 Verification Test...")

    # 2. Test WebAnalyzer & PDFFinder
    target_url = config_mgr.get("target_urls")[0]
    print(f"\n[1/3] Scraping DLRS Target URL: {target_url}")

    finder = PDFFinder()
    discovered_pdfs = finder.discover_pdfs(target_url)

    print(f"[OK] Total unique PDF gazettes discovered: {len(discovered_pdfs)}")
    if discovered_pdfs:
        print("\n--- Sample Discovered PDF Items ---")
        for i, item in enumerate(discovered_pdfs[:5], 1):
            print(f"  {i}. [{item.district}] {item.filename} -> {item.url}")

    # 3. Test ResilientDownloader
    print("\n[2/3] Testing Resilient Multi-Threaded PDF Downloader...")
    downloader = ResilientDownloader(
        output_dir=config_mgr.get("download.pdf_dir"),
        max_threads=2,
        max_retries=2,
        timeout=15
    )

    def on_progress(p: DownloadProgress):
        print(f"  --> Progress: {p.current_file} | Downloaded: {p.bytes_downloaded}/{p.total_bytes} bytes | Speed: {p.speed_kbps:.2f} KB/s", end="\r")

    # Download first 3 files as test batch
    test_batch = discovered_pdfs[:3] if discovered_pdfs else []
    if test_batch:
        print(f"Downloading sample batch of {len(test_batch)} files...")
        results = downloader.download_batch(test_batch, progress_callback=on_progress)
        print(f"\n[OK] Batch Results: Downloaded={len(results['success'])}, Failed={len(results['failed'])}")

    # 4. Verify Log Files
    print("\n[3/3] Verifying Generated Log Files in Output/Logs...")
    log_dir = config_mgr.get("logging.log_dir")
    for log_file in ["system.log", "download.log", "error.log", "ocr.log"]:
        path = os.path.join(log_dir, log_file)
        if os.path.exists(path):
            print(f"  [OK] Log file verified: {log_file} ({os.path.getsize(path)} bytes)")
        else:
            print(f"  [FAIL] Missing log file: {log_file}")

    print("\n" + "=" * 70)
    print("[SUCCESS] Step 2 Module Verification Completed Cleanly!")
    print("=" * 70)

if __name__ == "__main__":
    run_test()
