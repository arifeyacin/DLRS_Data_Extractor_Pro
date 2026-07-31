"""
Step 3 Verification Test Script for DLRS Data Extractor Pro
Tests PDFDetector, TextExtractor, OCREngine, and LandRecordParser on downloaded PDF files.
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
from app.pdf_processor.pdf_detector import PDFDetector, PDFType
from app.pdf_processor.text_extractor import TextExtractor
from app.pdf_processor.ocr_engine import OCREngine
from app.pdf_processor.parser import LandRecordParser

def run_test():
    print("=" * 75)
    print("      DLRS Data Extractor Pro - Step 3 Empirical Verification Test      ")
    print("=" * 75)

    config_mgr = ConfigManager()
    LogManager.setup_loggers(
        log_dir=config_mgr.get("logging.log_dir"),
        log_level=config_mgr.get("logging.level")
    )
    logger = get_system_logger()
    logger.info("Initializing Step 3 Verification Test...")

    # Locate downloaded test PDF files from Step 2
    pdf_dir = config_mgr.get("download.pdf_dir")
    found_pdfs = []
    for root, _, files in os.walk(pdf_dir):
        for f in files:
            if f.lower().endswith(".pdf"):
                found_pdfs.append(os.path.join(root, f))

    print(f"[INFO] Discovered {len(found_pdfs)} PDF files in output directory.")
    if not found_pdfs:
        print("[WARNING] No PDF files found in Output/PDFs/. Make sure Step 2 was executed.")
        return

    test_pdf = found_pdfs[0]
    print(f"\n[1/4] Testing PDF Type Detection on: {os.path.basename(test_pdf)}")
    detector = PDFDetector()
    detection_res = detector.detect(test_pdf)

    print(f"  --> PDF Type: {detection_res.pdf_type.value}")
    print(f"  --> Total Pages: {detection_res.total_pages}")
    print(f"  --> Text Pages: {detection_res.text_page_count} | Image Pages: {detection_res.image_page_count}")
    print(f"  --> Average Chars/Page: {detection_res.avg_chars_per_page:.1f}")
    print(f"  --> Requires OCR: {detection_res.requires_ocr}")

    # 2. Test Text Extraction
    print(f"\n[2/4] Testing PyMuPDF & pdfplumber Text/Table Extractor...")
    extractor = TextExtractor()
    doc_content = extractor.extract(test_pdf)

    print(f"  --> Extracted {len(doc_content.full_text)} characters across {doc_content.total_pages} pages.")
    print(f"  --> Total Table Structures Found: {len(doc_content.all_tables)}")

    # 3. Test OCR Subsystem
    print(f"\n[3/4] Testing Bengali Tesseract OCR Engine...")
    ocr_engine = OCREngine(
        tesseract_cmd=config_mgr.get("ocr.tesseract_cmd"),
        lang=config_mgr.get("ocr.language"),
        ocr_cache_dir=config_mgr.get("ocr.output_dir")
    )

    ocr_results = ocr_engine.process_pdf(test_pdf)
    print(f"  --> OCR Processed Pages: {len(ocr_results)}")

    # 4. Test Entity Parsing into LandRecords
    print(f"\n[4/4] Testing Land Record Entity Parser...")
    parser = LandRecordParser()
    records = parser.parse_document(
        full_text=doc_content.full_text,
        tables=doc_content.all_tables,
        default_district="ঢাকা",
        default_upazila="ডেমরা",
        source_pdf=os.path.basename(test_pdf)
    )

    print(f"  --> Total Parsed Land Records: {len(records)}")
    if records:
        print("\n--- Sample Parsed Land Record Entity ---")
        sample = records[0]
        print(f"  Record ID: {sample.record_id}")
        print(f"  District: {sample.district} | Upazila: {sample.upazila} | Mouza: {sample.mouza}")
        print(f"  Khatian: {sample.khatian} | Dag: {sample.dag}")
        print(f"  Owner Name: {sample.owner_name}")
        print(f"  Gazette No: {sample.gazette_number} | Pub Date: {sample.publication_date}")
        print(f"  Land Type: {sample.land_type} | Area: {sample.area}")

    print("\n" + "=" * 75)
    print("[SUCCESS] Step 3 Module Verification Completed Cleanly!")
    print("=" * 75)

if __name__ == "__main__":
    run_test()
