"""
PDF Type Detector Module for DLRS Data Extractor Pro
Determines whether a PDF is a Searchable/Vector Text PDF, Scanned Image PDF, or Hybrid PDF.
"""

import fitz  # PyMuPDF
from enum import Enum
from dataclasses import dataclass
from typing import Optional

from app.logger import get_system_logger, get_error_logger

class PDFType(Enum):
    TEXT_PDF = "TEXT_PDF"
    SCANNED_PDF = "SCANNED_PDF"
    HYBRID_PDF = "HYBRID_PDF"
    CORRUPTED = "CORRUPTED"

@dataclass
class PDFDetectionResult:
    file_path: str
    pdf_type: PDFType
    total_pages: int
    text_page_count: int
    image_page_count: int
    total_char_count: int
    avg_chars_per_page: float
    requires_ocr: bool

class PDFDetector:
    """Detects structure and text density of PDF files."""

    def __init__(self, min_chars_per_page: int = 50):
        self.min_chars_per_page = min_chars_per_page
        self.logger = get_system_logger()
        self.error_logger = get_error_logger()

    def detect(self, pdf_path: str) -> PDFDetectionResult:
        """Analyze PDF file and return detection metrics and classification."""
        try:
            doc = fitz.open(pdf_path)
        except Exception as e:
            self.error_logger.error(f"Failed to open PDF file {pdf_path}: {e}")
            return PDFDetectionResult(
                file_path=pdf_path,
                pdf_type=PDFType.CORRUPTED,
                total_pages=0,
                text_page_count=0,
                image_page_count=0,
                total_char_count=0,
                avg_chars_per_page=0.0,
                requires_ocr=False
            )

        total_pages = len(doc)
        text_pages = 0
        image_pages = 0
        total_chars = 0

        for page_num in range(total_pages):
            page = doc[page_num]
            text = page.get_text("text").strip()
            char_count = len(text)
            total_chars += char_count

            images = page.get_images()

            if char_count >= self.min_chars_per_page:
                text_pages += 1
            else:
                image_pages += 1

        doc.close()

        avg_chars = (total_chars / total_pages) if total_pages > 0 else 0.0

        if text_pages == total_pages:
            pdf_type = PDFType.TEXT_PDF
            requires_ocr = False
        elif image_pages == total_pages or avg_chars < self.min_chars_per_page:
            pdf_type = PDFType.SCANNED_PDF
            requires_ocr = True
        else:
            pdf_type = PDFType.HYBRID_PDF
            requires_ocr = True

        self.logger.info(
            f"PDF Detection for {pdf_path}: Type={pdf_type.value}, Pages={total_pages}, "
            f"TextPages={text_pages}, ImagePages={image_pages}, AvgChars={avg_chars:.1f}, RequiresOCR={requires_ocr}"
        )

        return PDFDetectionResult(
            file_path=pdf_path,
            pdf_type=pdf_type,
            total_pages=total_pages,
            text_page_count=text_pages,
            image_page_count=image_pages,
            total_char_count=total_chars,
            avg_chars_per_page=avg_chars,
            requires_ocr=requires_ocr
        )
