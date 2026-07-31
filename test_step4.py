"""
Step 4 Verification Test Script for DLRS Data Extractor Pro
Tests DatabaseManager, LandRecordRepository, DownloadRepository, and SQLite FTS5 Full-Text Search.
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
from app.database.repositories import LandRecordRepository, DownloadRepository
from app.pdf_processor.pdf_detector import PDFDetector
from app.pdf_processor.text_extractor import TextExtractor
from app.pdf_processor.parser import LandRecordParser

def run_test():
    print("=" * 75)
    print("      DLRS Data Extractor Pro - Step 4 Empirical Verification Test      ")
    print("=" * 75)

    config_mgr = ConfigManager()
    LogManager.setup_loggers(
        log_dir=config_mgr.get("logging.log_dir"),
        log_level=config_mgr.get("logging.level")
    )
    logger = get_system_logger()
    logger.info("Initializing Step 4 Verification Test...")

    # 1. Test Database Initialization & Table Creation
    print("\n[1/4] Testing DatabaseManager & SQLite Schema Initialization...")
    db_mgr = DatabaseManager(db_path=config_mgr.get("database.db_path"))
    print(f"  [OK] Database active at: {db_mgr.db_path}")

    # 2. Extract & Parse Land Records from test PDF
    pdf_dir = config_mgr.get("download.pdf_dir")
    found_pdfs = []
    for root, _, files in os.walk(pdf_dir):
        for f in files:
            if f.lower().endswith(".pdf"):
                found_pdfs.append(os.path.join(root, f))

    if not found_pdfs:
        print("[WARNING] No PDF files found for testing.")
        return

    test_pdf = found_pdfs[0]
    print(f"\n[2/4] Parsing Land Records from PDF: {os.path.basename(test_pdf)}")
    extractor = TextExtractor()
    doc_content = extractor.extract(test_pdf)

    parser = LandRecordParser()
    parsed_records = parser.parse_document(
        full_text=doc_content.full_text,
        tables=doc_content.all_tables,
        default_district="ঢাকা",
        default_upazila="ডেমরা",
        source_pdf=os.path.basename(test_pdf)
    )

    print(f"  --> Parsed {len(parsed_records)} Land Records for database insertion.")

    # 3. Bulk Insert into SQLite Database
    print("\n[3/4] Testing Bulk Batch Insertion into SQLite Database...")
    repo = LandRecordRepository(db_manager=db_mgr)
    inserted = repo.insert_batch(parsed_records)
    print(f"  [OK] Bulk inserted {inserted} records into SQLite.")

    # Check Database Statistics
    stats = repo.get_stats()
    print(f"  --> DB Stats: Total Records={stats['total_records']}, Districts={stats['total_districts']}, Upazilas={stats['total_upazilas']}, Gazettes={stats['total_gazettes']}")

    # 4. Test SQLite FTS5 Full-Text & Field Search
    print("\n[4/4] Testing SQLite FTS5 & Relational Field Search Queries...")
    
    # Query 1: Filter by District & Upazila
    results_field = repo.search(district="ঢাকা", upazila="ডেমরা", limit=5)
    print(f"  --> Field Search (District='ঢাকা', Upazila='ডেমরা'): Returned {len(results_field)} matches.")
    if results_field:
        sample = results_field[0]
        print(f"      Sample Result: [{sample['record_id']}] District={sample['district']}, Upazila={sample['upazila']}, Khatian={sample['khatian']}, Owner={sample['owner_name']}")

    # Query 2: FTS5 Full-text search keyword match
    results_fts = repo.search(keyword="ঢাকা", limit=5)
    print(f"  --> FTS5 Full-Text Match (Keyword='ঢাকা'): Returned {len(results_fts)} matches.")

    print("\n" + "=" * 75)
    print("[SUCCESS] Step 4 Module Verification Completed Cleanly!")
    print("=" * 75)

if __name__ == "__main__":
    run_test()
