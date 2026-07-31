# Master AI Prompt & Project Specification Blueprint

> Copy and paste the prompt below into any AI Assistant (such as Antigravity, Claude, ChatGPT, or Cursor) to reproduce, extend, or build **DLRS Data Extractor Pro** from scratch.

---

```markdown
# Role
You are a Senior Python Software Engineer, Web Scraping Expert, Data Engineer, OCR Specialist, and Desktop Application Developer.

# Objective
Build a production-ready Windows desktop application (and web application backend) named **DLRS Data Extractor Pro** that automatically scrapes, downloads, extracts, OCR processes, indexes, and exports all Vested Property Gazette (অর্পিত সম্পত্তির গ্যাজেট) PDF files from the official Bangladesh **Department of Land Records and Surveys (DLRS)** portal.

Target Website:
https://dlrs.gov.bd/pages/static-pages/অর্পিত-সম্পত্তির-গ্যাজেট-তালিকা-ldsoay-6994019afcf25ca2d10077ca

---

# Architecture & Module Breakdown

1. **Scraper Subsystem** (`app/scraper/`):
   - `web_analyzer.py`: HTML analyzer supporting static HTML, Base64 `<rt-renderer>` components, and SSL verification fallback (`verify=False`).
   - `pdf_finder.py`: Discovers PDF gazette links and maps them to District (জেলা) and Upazila (উপজেলা) metadata.
   - `downloader.py`: Multi-threaded stream downloader with auto-resume (`Range: bytes=`), retries, duplicate check, and pause/resume/cancel flags.

2. **PDF Processing & Bengali OCR Subsystem** (`app/pdf_processor/`):
   - `pdf_detector.py`: Scans PDFs to classify as `TEXT_PDF`, `SCANNED_PDF`, or `HYBRID_PDF`.
   - `text_extractor.py`: Fast PyMuPDF (`fitz`) and `pdfplumber` text/table extraction with Bengali Unicode normalization.
   - `ocr_engine.py`: High DPI (300 DPI) rendering, Pillow image preprocessing (grayscale, contrast, binarization, sharpening), and Tesseract OCR (`ben+eng`).
   - `parser.py`: Regex & entity parser extracting District, Upazila, Mouza, Khatian, Dag, Owner Name, Gazette Number, Publication Date, Area, Land Type, and Remarks.

3. **SQLite Database & FTS5 Search Engine** (`app/database/`):
   - `db_manager.py`: SQLite connection pool in WAL mode (`journal_mode=WAL`), normalized relational tables (`gazettes`, `land_records`, `downloads`), FTS5 virtual table (`land_records_fts`), and automatic sync triggers.
   - `repositories.py`: Thread-safe batch transaction layer (`insert_batch`) and multi-field + FTS5 full-text queries.

4. **Multi-Format Export Subsystem** (`app/exporter/`):
   - `json_exporter.py`: Standardized backend-ready JSON (Laravel, Next.js, React, Node.js, PHP, REST/GraphQL APIs).
   - `csv_exporter.py`: UTF-8 BOM CSV dataset generator.
   - `excel_exporter.py`: Styled OpenPyXL Excel workbook generator with auto-width columns and custom headers.
   - `export_manager.py`: Unified multi-format exporter coordinator.

5. **CustomTkinter Desktop GUI** (`app/gui/`):
   - `main_window.py`: Core window with sidebar navigation, theme switcher (Light/Dark), and background worker thread manager.
   - `dashboard_tab.py`: Control panel (Start/Pause/Resume/Cancel), animated progress bar, live stats cards, and log streamer console.
   - `search_tab.py`: Structured & FTS5 full-text search GUI with scrollable tabular viewer.
   - `settings_tab.py`: Output folder selector, thread count, retry count, and Tesseract CMD path configuration.

6. **Executable Compiler**:
   - `DLRS_Data_Extractor.spec` & `build.bat`: PyInstaller standalone executable compilation.

---

# Execution Steps
1. Step 1: Initialize project structure, `requirements.txt`, `config.json`, `install.bat`, `build.bat`, and `README.md`.
2. Step 2: Implement logging and scraping downloader subsystem (`web_analyzer.py`, `pdf_finder.py`, `downloader.py`).
3. Step 3: Implement PDF processing, PyMuPDF text/table extractor, Bengali OCR engine, and entity parser.
4. Step 4: Implement SQLite database schema, WAL mode, FTS5 virtual table, and DAO repositories.
5. Step 5: Implement multi-format dataset exporters (JSON, CSV, Excel).
6. Step 6: Build CustomTkinter Desktop GUI interface.
7. Step 7: Compile standalone `DLRS_Data_Extractor.exe` executable binary and verify output datasets.
```
