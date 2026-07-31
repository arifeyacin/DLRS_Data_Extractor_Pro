# DLRS Data Extractor Pro

An enterprise-grade Windows desktop application built with Python 3.12, CustomTkinter, Playwright, PyMuPDF, pdfplumber, Tesseract OCR, SQLite, and Pandas. Automatically scrapes, extracts, OCR processes, indexes, and exports all Vested Property Gazette (অর্পিত সম্পত্তির গ্যাজেট) PDF files from the official Bangladesh **Department of Land Records and Surveys (DLRS)** website.

---

## Technical Analysis of DLRS Target Portal

- **Target URL**: `https://dlrs.gov.bd/pages/static-pages/অর্পিত-সম্পত্তির-গ্যাজেট-তালিকা-ldsoay-6994019afcf25ca2d10077ca`
- **Data Source Structure**:
  - The DLRS page embeds district-wise gazette links inside an HTML table rendered via static HTML and custom component markup (`<rt-renderer encoded-content="...">`).
  - Gazette PDFs are served directly via Oracle Cloud Object Storage (`https://objectstorage.ap-dcc-gazipur-1.oraclecloud15.com/n/axvjbnqprylg/b/V2Ministry/...`).
- **Extraction Strategy**:
  1. Direct HTTP parsing via `requests` + `BeautifulSoup` for optimal speed and low memory usage.
  2. Base64 HTML decoding for embedded table data.
  3. Playwright browser engine fallback for dynamic page interactions and lazy-loaded items.
  4. Multi-threaded resilient stream downloading with auto-resume, checksum duplicate prevention, and retry mechanisms.

---

## Enterprise Architecture & Folder Structure

```
DLRS_Data_Extractor_Pro/
│
├── config.json                 # System & application configuration file
├── requirements.txt             # Locked Python dependencies
├── install.bat                 # One-click environment setup script
├── build.bat                   # One-click PyInstaller executable compiler
├── DLRS_Data_Extractor.spec    # PyInstaller build specification file
├── main.py                     # Main application entry point
├── README.md                   # Complete system documentation
│
├── app/                        # Main Application Package
│   ├── __init__.py
│   ├── config_manager.py       # Configuration loading, validation & saving
│   ├── logger.py               # Multi-channel logger setup (Download, Error, OCR, System)
│   │
│   ├── gui/                    # CustomTkinter Desktop Interface
│   │   ├── __init__.py
│   │   ├── main_window.py      # Core window layout & navigation sidebar
│   │   ├── dashboard_tab.py    # URL control, progress bar, live statistics & status log
│   │   ├── search_tab.py       # Full-text & field search engine GUI
│   │   └── settings_tab.py     # Application settings & theme switcher
│   │
│   ├── scraper/                # Web Scraping & PDF Detection Engine
│   │   ├── __init__.py
│   │   ├── web_analyzer.py     # HTML & JavaScript endpoint detector
│   │   ├── pdf_finder.py       # Gazette PDF link & metadata extractor
│   │   └── downloader.py       # Multi-threaded resilient async downloader
│   │
│   ├── pdf_processor/          # PDF Extraction & OCR Subsystem
│   │   ├── __init__.py
│   │   ├── pdf_detector.py     # Vector/Text PDF vs Scanned Image PDF detector
│   │   ├── text_extractor.py   # PyMuPDF & pdfplumber structured extraction
│   │   ├── ocr_engine.py       # Tesseract OCR engine (Bengali + English support)
│   │   └── parser.py           # Standardized land record entity extractor
│   │
│   ├── database/               # Relational Storage & Indexing Engine
│   │   ├── __init__.py
│   │   ├── db_manager.py       # SQLite connection manager & schema migrations
│   │   └── repositories.py     # SQLite Full-Text Search (FTS) & CRUD query handlers
│   │
│   └── exporter/               # Multi-Format Backend Export Pipeline
│       ├── __init__.py
│       ├── json_exporter.py    # Standardized backend-ready JSON schema
│       ├── csv_exporter.py     # CSV export module
│       ├── excel_exporter.py   # OpenPyXL Excel spreadsheet generator
│       └── export_manager.py   # Unified export coordinator
│
└── Output/                     # Organized Data Pipeline Directories
    ├── PDFs/                   # Raw downloaded PDF files grouped by district
    ├── JSON/                   # Standardized JSON export files
    ├── CSV/                    # CSV dataset files
    ├── Excel/                  # Formatted Excel workbooks
    ├── SQLite/                 # Production SQLite database (`dlrs_data.db`)
    ├── Logs/                   # Logging output files
    └── OCR/                    # OCR extracted text cache
```

---

## Installation & Setup Guide

### System Requirements
- **OS**: Windows 10 / Windows 11 (64-bit)
- **Python**: Version 3.12 or higher
- **Tesseract OCR**: Recommended for scanned PDFs (installed with Bengali `ben.traineddata` language pack).

### Automated Setup (`install.bat`)
Run `install.bat` from Windows File Explorer or Command Prompt:

```cmd
install.bat
```

This script automatically:
1. Verifies Python 3.12+ installation.
2. Creates a isolated virtual environment (`venv`).
3. Upgrades `pip` and installs all dependencies listed in `requirements.txt`.
4. Installs Playwright Chromium binaries (`playwright install chromium`).
5. Generates the standard `Output/` folder structure.
6. Verifies Tesseract OCR availability.

---

## Building Standalone Binary Executable (`build.bat`)

To produce a single, standalone Windows executable (`DLRS_Data_Extractor.exe`):

```cmd
build.bat
```

The resulting executable and associated bundles will be placed in the `dist\` folder:
`dist\DLRS_Data_Extractor.exe`

---

## Standardized JSON Output Schema (Backend Ready)

The exported JSON is specifically structured for immediate integration with web backend frameworks like **Laravel, Next.js, React, Node.js, PHP, REST APIs, or GraphQL**:

```json
{
  "gazette_meta": {
    "district": "Dhaka",
    "upazila": "Dhamrai",
    "gazette_number": "GZ-2026-104",
    "publication_date": "2026-01-15",
    "source_url": "https://objectstorage.ap-dcc-gazipur-1.oraclecloud15.com/n/axvjbnqprylg/b/V2Ministry/o/office-dlrs/2026/1/88446923-7705-49f7-8937-56dbafb89c48.pdf"
  },
  "records": [
    {
      "record_id": "REC-DHAK-DHAM-0001",
      "mouza": "Dhamrai Town",
      "khatian": "1042",
      "dag": "512",
      "owner_name": "আব্দুর রহমান",
      "area_acres": 0.45,
      "land_type": "কৃষি (Agricultural)",
      "remarks": "অর্পিত সম্পত্তি ক-তফসিল"
    }
  ]
}
```

---

## Logging Subsystem

The application maintains isolated log outputs inside `Output/Logs/`:
- `download.log`: Download progress, retry attempts, HTTP status codes, and file speeds.
- `error.log`: Diagnostic stack traces and unhandled operational errors.
- `ocr.log`: Image pre-processing steps, Tesseract execution times, and confidence scores.
- `system.log`: General application lifecycle and GUI events.

---

## License & Developer Information

Developed for production web scraping, automated land record data extraction, and backend database compilation.
