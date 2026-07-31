"""
CSV Exporter Module for DLRS Data Extractor Pro
Exports land records to UTF-8 BOM formatted CSV files compatible with Excel and database tools.
"""

import os
import pandas as pd
from typing import List, Dict, Any

from app.logger import get_system_logger, get_error_logger

class CSVExporter:
    """Exports land records to CSV dataset files."""

    def __init__(self, output_dir: str = "./Output/CSV"):
        self.output_dir = os.path.abspath(output_dir)
        os.makedirs(self.output_dir, exist_ok=True)
        self.logger = get_system_logger()
        self.error_logger = get_error_logger()

    def export(self, records: List[Dict[str, Any]], filename: str = "dlrs_land_records.csv") -> str:
        """Export records list to CSV file with UTF-8 BOM encoding for proper Bengali text display."""
        if not filename.endswith(".csv"):
            filename += ".csv"

        target_path = os.path.join(self.output_dir, filename)
        self.logger.info(f"Exporting {len(records)} records to CSV dataset: {target_path}")

        try:
            df = pd.DataFrame(records)
            # Write with utf-8-sig to preserve Bengali script in Microsoft Excel
            df.to_csv(target_path, index=False, encoding="utf-8-sig")
            self.logger.info(f"CSV export completed successfully: {target_path}")
            return target_path
        except Exception as e:
            self.error_logger.error(f"Failed to export CSV file {target_path}: {e}")
            return ""
