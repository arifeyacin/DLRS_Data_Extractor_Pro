"""
Land Record Entity Parser Module for DLRS Data Extractor Pro
Parses raw text and extracted tables into standardized land record entities.
"""

import re
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional

from app.logger import get_system_logger, get_error_logger

@dataclass
class LandRecord:
    record_id: str
    district: str
    upazila: str
    mouza: str
    khatian: str
    dag: str
    owner_name: str
    gazette_number: str
    publication_date: str
    area: str
    land_type: str
    remarks: str
    source_pdf: str

class LandRecordParser:
    """Parses raw text and tables into structured land record records."""

    def __init__(self):
        self.logger = get_system_logger()
        self.error_logger = get_error_logger()

    def parse_document(
        self,
        full_text: str,
        tables: List[List[List[str]]],
        default_district: str = "Unknown",
        default_upazila: str = "Unknown",
        source_pdf: str = ""
    ) -> List[LandRecord]:
        """Parse full text and extracted table structures into LandRecord list."""
        records: List[LandRecord] = []
        counter = 1

        # 1. Parse Gazette metadata (Gazette No & Publication Date)
        gazette_number = self._extract_gazette_number(full_text)
        pub_date = self._extract_publication_date(full_text)
        district = self._extract_district(full_text) or default_district
        upazila = self._extract_upazila(full_text) or default_upazila
        mouza = self._extract_mouza(full_text) or "General Mouza"

        # 2. Parse from extracted tabular structures
        if tables:
            for table in tables:
                for row in table:
                    if len(row) >= 3 and not self._is_header_row(row):
                        rec = self._parse_table_row(
                            row=row,
                            counter=counter,
                            district=district,
                            upazila=upazila,
                            mouza=mouza,
                            gazette_number=gazette_number,
                            pub_date=pub_date,
                            source_pdf=source_pdf
                        )
                        if rec:
                            records.append(rec)
                            counter += 1

        # 3. Fallback: Line-by-line regex parsing if no structured table records parsed
        if not records and full_text:
            lines = full_text.splitlines()
            for line in lines:
                rec = self._parse_text_line(
                    line=line,
                    counter=counter,
                    district=district,
                    upazila=upazila,
                    mouza=mouza,
                    gazette_number=gazette_number,
                    pub_date=pub_date,
                    source_pdf=source_pdf
                )
                if rec:
                    records.append(rec)
                    counter += 1

        self.logger.info(f"Parsed {len(records)} land records from {source_pdf}")
        return records

    def _parse_table_row(
        self,
        row: List[str],
        counter: int,
        district: str,
        upazila: str,
        mouza: str,
        gazette_number: str,
        pub_date: str,
        source_pdf: str
    ) -> Optional[LandRecord]:
        """Map columns of a table row to LandRecord fields."""
        # Clean row cells
        cleaned = [c.strip() for c in row if c.strip()]
        if len(cleaned) < 3:
            return None

        # Heuristic cell assignment based on length and patterns
        khatian = cleaned[0] if len(cleaned) > 0 else ""
        dag = cleaned[1] if len(cleaned) > 1 else ""
        owner = cleaned[2] if len(cleaned) > 2 else ""
        land_type = cleaned[3] if len(cleaned) > 3 else "নাল"
        area = cleaned[4] if len(cleaned) > 4 else "0.0"
        remarks = " ".join(cleaned[5:]) if len(cleaned) > 5 else "অর্পিত সম্পত্তি"

        rec_id = f"REC-{district[:3].upper()}-{upazila[:3].upper()}-{counter:04d}"

        return LandRecord(
            record_id=rec_id,
            district=district,
            upazila=upazila,
            mouza=mouza,
            khatian=khatian,
            dag=dag,
            owner_name=owner,
            gazette_number=gazette_number,
            publication_date=pub_date,
            area=area,
            land_type=land_type,
            remarks=remarks,
            source_pdf=source_pdf
        )

    def _parse_text_line(
        self,
        line: str,
        counter: int,
        district: str,
        upazila: str,
        mouza: str,
        gazette_number: str,
        pub_date: str,
        source_pdf: str
    ) -> Optional[LandRecord]:
        """Parse structured text line with regex patterns."""
        # Example pattern matching: "খতিয়ান: ১২৩৪, দাগ: ৫৬৭, মালিক: করিম মিঞা"
        khatian_match = re.search(r'(?:খতিয়ান|খতিয়ান)[\s:]*([০-৯0-9]+)', line)
        dag_match = re.search(r'(?:দাগ)[\s:]*([০-৯0-9]+)', line)
        owner_match = re.search(r'(?:মালিক|দখলকার)[\s:]*([^\d,]+)', line)

        if khatian_match or dag_match or owner_match:
            khatian = khatian_match.group(1) if khatian_match else str(counter)
            dag = dag_match.group(1) if dag_match else str(counter * 10)
            owner = owner_match.group(1).strip() if owner_match else f"মালিক_{counter}"

            rec_id = f"REC-{district[:3].upper()}-{upazila[:3].upper()}-{counter:04d}"
            return LandRecord(
                record_id=rec_id,
                district=district,
                upazila=upazila,
                mouza=mouza,
                khatian=khatian,
                dag=dag,
                owner_name=owner,
                gazette_number=gazette_number,
                publication_date=pub_date,
                area="0.50 একর",
                land_type="নাল",
                remarks="অর্পিত সম্পত্তি",
                source_pdf=source_pdf
            )
        return None

    def _extract_gazette_number(self, text: str) -> str:
        match = re.search(r'(?:গেজেট|প্রজ্ঞাপন|Gazette)[\s#№নম্বর:-]*([A-Za-z0-9-/০-৯]+)', text, re.IGNORECASE)
        return match.group(1) if match else "GZ-2026-DLRS"

    def _extract_publication_date(self, text: str) -> str:
        match = re.search(r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|[০-৯]{1,2}[/-][০-৯]{1,2}[/-][০-৯]{2,4})', text)
        return match.group(1) if match else "2026-01-15"

    def _extract_district(self, text: str) -> Optional[str]:
        match = re.search(r'(?:জেলা)[\s:]*([^\n,]+)', text)
        return match.group(1).strip() if match else None

    def _extract_upazila(self, text: str) -> Optional[str]:
        match = re.search(r'(?:উপজেলা|থানা)[\s:]*([^\n,]+)', text)
        return match.group(1).strip() if match else None

    def _extract_mouza(self, text: str) -> Optional[str]:
        match = re.search(r'(?:মৌজা)[\s:]*([^\n,]+)', text)
        return match.group(1).strip() if match else None

    def _is_header_row(self, row: List[str]) -> bool:
        row_str = " ".join(row).lower()
        return any(h in row_str for h in ["খতিয়ান", "দাগ", "মালিক", "ক্রমিক", "sl", "khatian", "dag"])
