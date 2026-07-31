"""
Bengali Tesseract OCR Subsystem for DLRS Data Extractor Pro
Renders PDF pages to high-DPI images, performs image pre-processing, and runs Tesseract OCR.
"""

import os
import io
import fitz  # PyMuPDF
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract
from dataclasses import dataclass
from typing import List, Optional

from app.logger import get_ocr_logger, get_error_logger

@dataclass
class OCRPageResult:
    page_number: int
    text: str
    confidence: float
    image_width: int
    image_height: int

class OCREngine:
    """High-performance Bengali + English OCR processing engine."""

    def __init__(
        self,
        tesseract_cmd: str = "C:\\Program Files\\Tesseract-OCR\\tesseract.exe",
        lang: str = "ben+eng",
        psm: int = 6,
        oem: int = 3,
        dpi: int = 300,
        ocr_cache_dir: str = "./Output/OCR"
    ):
        self.tesseract_cmd = tesseract_cmd
        self.lang = lang
        self.psm = psm
        self.oem = oem
        self.dpi = dpi
        self.ocr_cache_dir = os.path.abspath(ocr_cache_dir)
        os.makedirs(self.ocr_cache_dir, exist_ok=True)

        self.ocr_logger = get_ocr_logger()
        self.error_logger = get_error_logger()

        self._configure_tesseract()

    def _configure_tesseract(self):
        """Set Tesseract executable path if available."""
        if os.path.exists(self.tesseract_cmd):
            pytesseract.pytesseract.tesseract_cmd = self.tesseract_cmd
            self.ocr_logger.info(f"Tesseract executable configured: {self.tesseract_cmd}")
        else:
            self.ocr_logger.warning(
                f"Tesseract executable not found at {self.tesseract_cmd}. OCR will attempt default system PATH."
            )

    def process_pdf(self, pdf_path: str) -> List[OCRPageResult]:
        """Perform high-DPI rendering, image preprocessing, and OCR page by page."""
        self.ocr_logger.info(f"Starting OCR processing for PDF: {pdf_path}")
        results: List[OCRPageResult] = []
        base_name = os.path.splitext(os.path.basename(pdf_path))[0]

        try:
            doc = fitz.open(pdf_path)
            total_pages = len(doc)

            for page_num in range(total_pages):
                cache_file = os.path.join(self.ocr_cache_dir, f"{base_name}_p{page_num + 1}.txt")

                # Check OCR cache first
                if os.path.exists(cache_file):
                    with open(cache_file, "r", encoding="utf-8") as f:
                        cached_text = f.read()
                    self.ocr_logger.info(f"Loaded OCR cache for page {page_num + 1}/{total_pages}")
                    results.append(OCRPageResult(
                        page_number=page_num + 1,
                        text=cached_text,
                        confidence=100.0,
                        image_width=0,
                        image_height=0
                    ))
                    continue

                page = doc[page_num]
                # High DPI rendering matrix (300 DPI = 300/72 = 4.166 multiplier)
                zoom = self.dpi / 72.0
                mat = fitz.Matrix(zoom, zoom)
                pix = page.get_pixmap(matrix=mat, alpha=False)

                img_data = pix.tobytes("png")
                image = Image.open(io.BytesIO(img_data))

                # Image Preprocessing
                processed_img = self._preprocess_image(image)

                # Execute Tesseract OCR
                config = f"--psm {self.psm} --oem {self.oem}"
                try:
                    ocr_text = pytesseract.image_to_string(processed_img, lang=self.lang, config=config)
                except Exception as ocr_err:
                    self.error_logger.warning(f"Bengali language pack missing or Tesseract error on page {page_num+1}: {ocr_err}. Retrying with 'eng' fallback.")
                    ocr_text = pytesseract.image_to_string(processed_img, lang="eng", config=config)

                # Save cache
                with open(cache_file, "w", encoding="utf-8") as f:
                    f.write(ocr_text)

                self.ocr_logger.info(f"OCR Page {page_num+1}/{total_pages} Completed ({len(ocr_text)} characters extracted)")

                results.append(OCRPageResult(
                    page_number=page_num + 1,
                    text=ocr_text,
                    confidence=85.0,
                    image_width=image.width,
                    image_height=image.height
                ))

            doc.close()
        except Exception as e:
            self.error_logger.error(f"OCR failure for {pdf_path}: {e}")

        return results

    def _preprocess_image(self, img: Image.Image) -> Image.Image:
        """Apply grayscale, contrast enhancement, and noise reduction."""
        # 1. Convert to grayscale
        gray = img.convert("L")

        # 2. Enhance contrast
        enhancer = ImageEnhance.Contrast(gray)
        contrast = enhancer.enhance(2.0)

        # 3. Simple thresholding / binarization
        threshold = 180
        binarized = contrast.point(lambda p: 255 if p > threshold else 0)

        # 4. Sharpen
        sharpened = binarized.filter(ImageFilter.SHARPEN)
        return sharpened
