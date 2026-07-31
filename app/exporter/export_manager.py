"""
Export Manager Module for DLRS Data Extractor Pro
Unified coordinator exporting land records to JSON, CSV, and Excel formats simultaneously.
"""

from typing import List, Dict, Any, Optional

from app.exporter.json_exporter import JSONExporter
from app.exporter.csv_exporter import CSVExporter
from app.exporter.excel_exporter import ExcelExporter
from app.database.repositories import LandRecordRepository
from app.logger import get_system_logger

class ExportManager:
    """Coordinates multi-format data exports."""

    def __init__(
        self,
        json_dir: str = "./Output/JSON",
        csv_dir: str = "./Output/CSV",
        excel_dir: str = "./Output/Excel",
        repo: Optional[LandRecordRepository] = None
    ):
        self.json_exporter = JSONExporter(output_dir=json_dir)
        self.csv_exporter = CSVExporter(output_dir=csv_dir)
        self.excel_exporter = ExcelExporter(output_dir=excel_dir)
        self.repo = repo or LandRecordRepository()
        self.logger = get_system_logger()

    def export_all(
        self,
        records: Optional[List[Dict[str, Any]]] = None,
        base_name: str = "dlrs_land_records"
    ) -> Dict[str, str]:
        """Export dataset to JSON, CSV, and Excel formats simultaneously."""
        if records is None:
            records = self.repo.search(limit=100000)

        self.logger.info(f"Initiating unified export of {len(records)} records across JSON, CSV, and Excel...")

        json_path = self.json_exporter.export(records, f"{base_name}.json")
        csv_path = self.csv_exporter.export(records, f"{base_name}.csv")
        excel_path = self.excel_exporter.export(records, f"{base_name}.xlsx")

        return {
            "json": json_path,
            "csv": csv_path,
            "excel": excel_path
        }
