"""
Multi-Format Asset Finder Module for DLRS Data Extractor Pro v2.0
Discovers and categorizes URLs for PDF, HTML, PNG/JPG Images, and Office Documents.
"""

import os
import re
from urllib.parse import urljoin, unquote
from bs4 import BeautifulSoup
from dataclasses import dataclass, asdict
from typing import List, Dict, Set, Optional

from app.scraper.web_analyzer import WebAnalyzer, PageAnalysisResult
from app.logger import get_system_logger, get_error_logger

SUPPORTED_EXTENSIONS = {
    "pdf": [".pdf"],
    "html": [".html", ".htm", ".xhtml"],
    "image": [".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".webp", ".gif"],
    "document": [".xlsx", ".xls", ".csv", ".doc", ".docx", ".txt"]
}

@dataclass
class AssetItem:
    url: str
    filename: str
    format_type: str  # 'pdf', 'html', 'image', 'document'
    extension: str
    district: str
    upazila: str
    title: str
    source_page: str
    file_size_bytes: int = 0
    selected: bool = True

class AssetFinder:
    """Discovers multi-format asset files (PDF, HTML, Images, Documents) from web content."""

    def __init__(self, analyzer: Optional[WebAnalyzer] = None):
        self.analyzer = analyzer or WebAnalyzer()
        self.logger = get_system_logger()
        self.error_logger = get_error_logger()

    def discover_assets(
        self,
        target_url: str,
        allowed_formats: Optional[List[str]] = None
    ) -> List[AssetItem]:
        """Scrape target URL and discover assets matching specified format types."""
        allowed_formats = [f.lower() for f in (allowed_formats or ["pdf", "html", "image", "document"])]
        analysis = self.analyzer.fetch_and_analyze(target_url)

        items = self._extract_from_html(analysis.raw_html, analysis.decoded_content, target_url, allowed_formats)

        # Deduplicate by URL
        unique_items = []
        seen_urls: Set[str] = set()
        for item in items:
            if item.url not in seen_urls:
                seen_urls.add(item.url)
                unique_items.append(item)

        self.logger.info(f"Discovered {len(unique_items)} unique asset files matching formats {allowed_formats}")
        return unique_items

    def _extract_from_html(
        self,
        raw_html: str,
        decoded_content: str,
        source_url: str,
        allowed_formats: List[str]
    ) -> List[AssetItem]:
        asset_items: List[AssetItem] = []
        html_sources = [raw_html]
        if decoded_content:
            html_sources.append(decoded_content)

        for content in html_sources:
            soup = BeautifulSoup(content, "lxml")

            # 1. Inspect table cells for links & District metadata
            for table in soup.find_all("table"):
                current_district = "General"

                for row in table.find_all("tr"):
                    cells = row.find_all(["td", "th"])
                    if not cells:
                        continue

                    if len(cells) >= 2:
                        possible_dist = cells[1].get_text(strip=True)
                        if possible_dist and not possible_dist.isdigit() and len(possible_dist) > 1:
                            current_district = possible_dist

                    for cell in cells:
                        for a in cell.find_all("a", href=True):
                            href = a["href"].strip()
                            item = self._create_asset_item(href, a.get_text(strip=True), current_district, source_url, allowed_formats)
                            if item:
                                asset_items.append(item)

            # 2. Inspect standalone <a> tags
            for a in soup.find_all("a", href=True):
                href = a["href"].strip()
                item = self._create_asset_item(href, a.get_text(strip=True), "General", source_url, allowed_formats)
                if item and not any(i.url == item.url for i in asset_items):
                    asset_items.append(item)

            # 3. If image format is enabled, inspect <img> tags
            if "image" in allowed_formats:
                for img in soup.find_all("img", src=True):
                    src = img["src"].strip()
                    item = self._create_asset_item(src, img.get("alt", ""), "General", source_url, allowed_formats)
                    if item and not any(i.url == item.url for i in asset_items):
                        asset_items.append(item)

        return asset_items

    def _create_asset_item(
        self,
        url_path: str,
        text: str,
        district: str,
        source_url: str,
        allowed_formats: List[str]
    ) -> Optional[AssetItem]:
        full_url = urljoin(source_url, url_path)
        path_lower = url_path.split("?")[0].lower()
        _, ext = os.path.splitext(path_lower)

        matched_format = None
        for fmt, exts in SUPPORTED_EXTENSIONS.items():
            if ext in exts:
                matched_format = fmt
                break

        if not matched_format and "/pdf/" in path_lower:
            matched_format = "pdf"
            ext = ".pdf"

        if not matched_format or matched_format not in allowed_formats:
            return None

        clean_text = text.strip() or os.path.basename(path_lower)
        filename = self._clean_filename(clean_text, url_path, ext)
        upazila = self._extract_upazila_from_text(clean_text, filename)

        return AssetItem(
            url=full_url,
            filename=filename,
            format_type=matched_format,
            extension=ext,
            district=district,
            upazila=upazila,
            title=clean_text,
            source_page=source_url
        )

    def _clean_filename(self, link_text: str, href: str, default_ext: str) -> str:
        raw_name = unquote(os.path.basename(href.split("?")[0]))
        if not any(raw_name.lower().endswith(e) for exts in SUPPORTED_EXTENSIONS.values() for e in exts):
            raw_name += default_ext

        cleaned = link_text if link_text and len(link_text) > 2 else raw_name
        cleaned = re.sub(r'[\\/*?:"<>|]', "_", cleaned)
        if not cleaned.lower().endswith(default_ext):
            cleaned += default_ext
        return cleaned

    def _extract_upazila_from_text(self, text: str, filename: str) -> str:
        base = text if text else filename
        base = re.sub(r'\.[a-zA-Z0-9]+$', '', base).replace("_", " ").strip()
        parts = base.split()
        return parts[0] if parts else "Unknown"
