"""
Backend-Ready JSON Exporter Module for DLRS Data Extractor Pro
Produces standardized JSON structured for Laravel, Next.js, React, Node.js, PHP, REST, and GraphQL APIs.
"""

import os
import json
from typing import List, Dict, Any, Optional

from app.logger import get_system_logger, get_error_logger

class JSONExporter:
    """Exports land records to standardized backend-compatible JSON."""

    def __init__(self, output_dir: str = "./Output/JSON"):
        self.output_dir = os.path.abspath(output_dir)
        os.makedirs(self.output_dir, exist_ok=True)
        self.logger = get_system_logger()
        self.error_logger = get_error_logger()

    def export(self, records: List[Dict[str, Any]], filename: str = "dlrs_land_records.json") -> str:
        """Export list of land record dictionaries to JSON file."""
        if not filename.endswith(".json"):
            filename += ".json"

        target_path = os.path.join(self.output_dir, filename)
        self.logger.info(f"Exporting {len(records)} records to backend JSON: {target_path}")

        payload = {
            "meta": {
                "system": "DLRS Data Extractor Pro",
                "version": "1.0.0",
                "total_records": len(records),
                "export_format": "standardized_backend_v1",
                "supported_backends": ["Laravel", "Next.js", "React", "Node.js", "PHP", "REST API", "GraphQL"]
            },
            "data": records
        }

        try:
            with open(target_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2, ensure_ascii=False)
            self.logger.info(f"JSON export completed successfully: {target_path}")
            return target_path
        except Exception as e:
            self.error_logger.error(f"Failed to export JSON file {target_path}: {e}")
            return ""
