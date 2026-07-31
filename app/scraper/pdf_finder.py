"""
PDF Finder & Extractor Module for DLRS Data Extractor Pro
Extracts PDF URLs along with District, Upazila, and Gazette metadata.
"""

import os
import re
from urllib.parse import urljoin, unquote
from bs4 import BeautifulSoup
from dataclasses import dataclass, asdict
from typing import List, Dict, Set, Optional

from app.scraper.web_analyzer import WebAnalyzer, PageAnalysisResult
from app.logger import get_system_logger, get_error_logger

@dataclass
class PDFItem:
    url: str
    filename: str
    district: str
    upazila: str
    title: str
    source_page: str
    file_size_bytes: int = 0

class PDFFinder:
    """Discovers and extracts PDF files and metadata from DLRS web content."""

    def __init__(self, analyzer: Optional[WebAnalyzer] = None):
        self.analyzer = analyzer or WebAnalyzer()
        self.logger = get_system_logger()
        self.error_logger = get_error_logger()

    def discover_pdfs(self, target_url: str) -> List[PDFItem]:
        """Scrape target URL and return all discovered PDF items with metadata."""
        analysis = self.analyzer.fetch_and_analyze(target_url)

        if analysis.requires_playwright:
            self.logger.info("Static fetch yielded 0 PDFs. Attempting Playwright dynamic extraction...")
            pdf_items = self._extract_with_playwright(target_url)
        else:
            pdf_items = self._extract_from_html(analysis.raw_html, analysis.decoded_content, target_url)

        # Remove duplicate PDF URLs
        unique_items = []
        seen_urls: Set[str] = set()
        for item in pdf_items:
            if item.url not in seen_urls:
                seen_urls.add(item.url)
                unique_items.append(item)

        self.logger.info(f"Discovered {len(unique_items)} unique PDF files from {target_url}")
        return unique_items

    def _extract_from_html(self, raw_html: str, decoded_content: str, source_url: str) -> List[PDFItem]:
        """Extract PDF URLs and District/Upazila metadata from HTML & base64 decoded tables."""
        pdf_items: List[PDFItem] = []
        html_sources = [raw_html]
        if decoded_content:
            html_sources.append(decoded_content)

        for content in html_sources:
            soup = BeautifulSoup(content, "lxml")

            # 1. Parse tables for structured District/Upazila metadata
            for table in soup.find_all("table"):
                current_district = "General"

                for row in table.find_all("tr"):
                    cells = row.find_all(["td", "th"])
                    if not cells:
                        continue

                    row_text = row.get_text(separator=" ", strip=True)

                    # Check if first/second cell denotes a District (e.g. ঢাকা, গাজীপুর)
                    if len(cells) >= 2:
                        possible_district = cells[1].get_text(strip=True)
                        if possible_district and not possible_district.isdigit() and len(possible_district) > 1:
                            current_district = possible_district

                    for cell in cells:
                        for a in cell.find_all("a", href=True):
                            href = a["href"].strip()
                            if href.lower().endswith(".pdf") or ".pdf?" in href.lower() or "/pdf/" in href.lower():
                                full_url = urljoin(source_url, href)
                                link_text = a.get_text(strip=True) or os.path.basename(href)
                                filename = self._clean_filename(link_text, href)
                                upazila = self._extract_upazila_from_text(link_text, filename)

                                pdf_items.append(PDFItem(
                                    url=full_url,
                                    filename=filename,
                                    district=current_district,
                                    upazila=upazila,
                                    title=link_text,
                                    source_page=source_url
                                ))

            # 2. Parse standalone <a> tags outside tables
            for a in soup.find_all("a", href=True):
                href = a["href"].strip()
                if href.lower().endswith(".pdf") or ".pdf?" in href.lower() or "/pdf/" in href.lower():
                    full_url = urljoin(source_url, href)
                    link_text = a.get_text(strip=True) or os.path.basename(href)
                    filename = self._clean_filename(link_text, href)

                    # Avoid adding if already parsed from table
                    if not any(item.url == full_url for item in pdf_items):
                        pdf_items.append(PDFItem(
                            url=full_url,
                            filename=filename,
                            district="General",
                            upazila=self._extract_upazila_from_text(link_text, filename),
                            title=link_text,
                            source_page=source_url
                        ))

        return pdf_items

    def _extract_with_playwright(self, source_url: str) -> List[PDFItem]:
        """Fallback extraction using Playwright browser engine."""
        pdf_items: List[PDFItem] = []
        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(source_url, wait_until="networkidle", timeout=45000)

                content = page.content()
                browser.close()

                # Process rendered HTML content
                analyzer_res = PageAnalysisResult(
                    url=source_url, title=page.title(), has_rt_renderer=False,
                    decoded_content="", raw_html=content, pdf_count_estimate=0,
                    requires_playwright=False, status_code=200
                )
                pdf_items = self._extract_from_html(content, "", source_url)
        except Exception as e:
            self.error_logger.error(f"Playwright extraction failed for {source_url}: {e}")

        return pdf_items

    def _clean_filename(self, link_text: str, href: str) -> str:
        """Derive a clean, safe filename."""
        raw_name = unquote(os.path.basename(href.split("?")[0]))
        if not raw_name.lower().endswith(".pdf"):
            raw_name += ".pdf"

        if link_text and link_text.strip().lower().endswith(".pdf"):
            cleaned = link_text.strip()
        else:
            cleaned = raw_name

        cleaned = re.sub(r'[\\/*?:"<>|]', "_", cleaned)
        return cleaned

    def _extract_upazila_from_text(self, text: str, filename: str) -> str:
        """Infer Upazila name from link text or filename."""
        base = text if text else filename
        base = base.replace(".pdf", "").replace("_", " ").strip()
        parts = base.split()
        return parts[0] if parts else "Unknown"
