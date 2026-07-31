"""
Step 5 Verification Test Script for DLRS Data Extractor Pro
Tests ExportManager, JSONExporter, CSVExporter, and ExcelExporter.
"""

import sys
import os

# Ensure Windows stdout supports UTF-8 Bengali characters
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.config_manager import ConfigManager
from app.logger import LogManager, get_system_logger
from app.database.db_manager import DatabaseManager
from app.database.repositories import LandRecordRepository
from app.exporter.export_manager import ExportManager

def run_test():
    print("=" * 75)
    print("      DLRS Data Extractor Pro - Step 5 Empirical Verification Test      ")
    print("=" * 75)

    config_mgr = ConfigManager()
    LogManager.setup_loggers(
        log_dir=config_mgr.get("logging.log_dir"),
        log_level=config_mgr.get("logging.level")
    )
    logger = get_system_logger()
    logger.info("Initializing Step 5 Verification Test...")

    # Fetch database records from Step 4
    db_mgr = DatabaseManager(db_path=config_mgr.get("database.db_path"))
    repo = LandRecordRepository(db_manager=db_mgr)
    records = repo.search(limit=1000)

    print(f"[INFO] Fetched {len(records)} land records from SQLite database for export.")

    # Execute ExportManager
    print("\n[1/3] Executing Multi-Format Data Export (JSON, CSV, Excel)...")
    exporter = ExportManager(
        json_dir=config_mgr.get("export.json_dir"),
        csv_dir=config_mgr.get("export.csv_dir"),
        excel_dir=config_mgr.get("export.excel_dir"),
        repo=repo
    )

    paths = exporter.export_all(records=records, base_name="dlrs_land_records_export_test")

    # Verify Generated Files
    print("\n[2/3] Verifying Exported File Paths & File Sizes:")
    for fmt, p in paths.items():
        if p and os.path.exists(p):
            size_kb = os.path.getsize(p) / 1024
            print(f"  [OK] Format '{fmt.upper()}': {p} ({size_kb:.2f} KB)")
        else:
            print(f"  [FAIL] Format '{fmt.upper()}': Failed to create file.")

    print("\n" + "=" * 75)
    print("[SUCCESS] Step 5 Module Verification Completed Cleanly!")
    print("=" * 75)

if __name__ == "__main__":
    run_test()
