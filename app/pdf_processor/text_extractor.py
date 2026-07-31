"""
Text & Table Extractor Module for DLRS Data Extractor Pro
Extracts structured text, tables, and page content from vector PDFs using PyMuPDF & pdfplumber.
"""

import fitz  # PyMuPDF
import pdfplumber
import unicodedata
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

from app.logger import get_system_logger, get_error_logger

@dataclass
class ExtractedPageContent:
    page_number: int
    raw_text: str
    tables: List[List[List[str]]]
    char_count: int

@dataclass
class ExtractedDocumentContent:
    file_path: str
    total_pages: int
    pages: List[ExtractedPageContent]
    full_text: str
    all_tables: List[List[List[str]]]

class TextExtractor:
    """Extracts text and tabular data from PDF files."""

    def __init__(self):
        self.logger = get_system_logger()
        self.error_logger = get_error_logger()

    def extract(self, pdf_path: str) -> ExtractedDocumentContent:
        """Extract text and tables page by page from target PDF."""
        self.logger.info(f"Extracting text and tables from PDF: {pdf_path}")
        pages_content: List[ExtractedPageContent] = []
        full_text_list: List[str] = []
        all_tables_list: List[List[List[str]]] = []

        # 1. PyMuPDF fast text extraction
        try:
            doc = fitz.open(pdf_path)
            total_pages = len(doc)

            for page_idx in range(total_pages):
                page = doc[page_idx]
                raw_text = page.get_text("text")
                normalized_text = self._normalize_bengali_text(raw_text)

                pages_content.append(ExtractedPageContent(
                    page_number=page_idx + 1,
                    raw_text=normalized_text,
                    tables=[],
                    char_count=len(normalized_text)
                ))
                full_text_list.append(normalized_text)
            doc.close()
        except Exception as e:
            self.error_logger.error(f"PyMuPDF text extraction error for {pdf_path}: {e}")
            total_pages = 0

        # 2. Extract tables via pdfplumber
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for idx, page in enumerate(pdf.pages):
                    if idx < len(pages_content):
                        tables = page.extract_tables()
                        clean_tables = []
                        for table in tables:
                            clean_table = [
                                [self._normalize_bengali_text(cell or "") for cell in row]
                                for row in table
                            ]
                            clean_tables.append(clean_table)
                            all_tables_list.append(clean_table)
                        pages_content[idx].tables = clean_tables
        except Exception as table_err:
            self.logger.warning(f"pdfplumber table extraction warning for {pdf_path}: {table_err}")

        combined_full_text = "\n\n--- Page Break ---\n\n".join(full_text_list)

        return ExtractedDocumentContent(
            file_path=pdf_path,
            total_pages=total_pages,
            pages=pages_content,
            full_text=combined_full_text,
            all_tables=all_tables_list
        )

    def _normalize_bengali_text(self, text: str) -> str:
        """Clean and normalize Bengali unicode characters."""
        if not text:
            return ""
        normalized = unicodedata.normalize("NFC", text)
        lines = [line.strip() for line in normalized.splitlines() if line.strip()]
        return "\n".join(lines)
