"""
Web Analyzer Module for DLRS Data Extractor Pro
Analyzes target website HTML, Base64 components (<rt-renderer>), and dynamic JS content.
"""

import base64
import requests
from bs4 import BeautifulSoup
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple

from app.logger import get_system_logger, get_error_logger

@dataclass
class PageAnalysisResult:
    url: str
    title: str
    has_rt_renderer: bool
    decoded_content: str
    raw_html: str
    pdf_count_estimate: int
    requires_playwright: bool
    status_code: int

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class WebAnalyzer:
    """Analyzes DLRS website structure and decodes embedded content components."""

    def __init__(self, user_agent: Optional[str] = None, timeout: int = 30):
        self.headers = {
            "User-Agent": user_agent or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "bn,en-US;q=0.9,en;q=0.8",
        }
        self.timeout = timeout
        self.logger = get_system_logger()
        self.error_logger = get_error_logger()

    def fetch_and_analyze(self, url: str) -> PageAnalysisResult:
        """Fetch target web page and analyze HTML structure & base64 dynamic components."""
        self.logger.info(f"Analyzing target web page: {url}")
        try:
            try:
                response = requests.get(url, headers=self.headers, timeout=self.timeout, verify=True)
            except requests.exceptions.SSLError:
                self.logger.warning(f"SSL certificate verification failed for {url}. Falling back to verify=False.")
                response = requests.get(url, headers=self.headers, timeout=self.timeout, verify=False)

            response.raise_for_status()
            raw_html = response.text
            status_code = response.status_code
        except Exception as e:
            self.error_logger.error(f"Failed to fetch page {url}: {e}")
            return PageAnalysisResult(
                url=url,
                title="",
                has_rt_renderer=False,
                decoded_content="",
                raw_html="",
                pdf_count_estimate=0,
                requires_playwright=True,
                status_code=0
            )

        soup = BeautifulSoup(raw_html, "lxml")
        title = soup.title.string.strip() if soup.title and soup.title.string else "DLRS Portal"

        # Check for Base64 encoded component <rt-renderer encoded-content="...">
        rt_renderers = soup.find_all("rt-renderer")
        has_rt_renderer = len(rt_renderers) > 0
        decoded_content_chunks = []

        for elem in rt_renderers:
            encoded_str = elem.get("encoded-content", "")
            if encoded_str:
                try:
                    decoded = base64.b64decode(encoded_str).decode("utf-8", errors="ignore")
                    decoded_content_chunks.append(decoded)
                except Exception as b64_err:
                    self.error_logger.warning(f"Base64 decode warning: {b64_err}")

        combined_decoded = "\n".join(decoded_content_chunks)
        full_text_to_search = raw_html + "\n" + combined_decoded

        # Estimate PDF count
        pdf_count = full_text_to_search.lower().count(".pdf")

        # Determine if Playwright is strictly required
        requires_playwright = (pdf_count == 0 and "javascript" in raw_html.lower())

        self.logger.info(f"Page Analysis Complete: Title='{title}', PDFs Found={pdf_count}, Has Base64 RT-Renderer={has_rt_renderer}")

        return PageAnalysisResult(
            url=url,
            title=title,
            has_rt_renderer=has_rt_renderer,
            decoded_content=combined_decoded,
            raw_html=raw_html,
            pdf_count_estimate=pdf_count,
            requires_playwright=requires_playwright,
            status_code=status_code
        )
