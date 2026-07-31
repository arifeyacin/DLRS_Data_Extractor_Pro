"""
Configuration Manager Module for DLRS Data Extractor Pro
Handles loading, saving, and schema validation for config.json.
"""

import os
import json
from typing import Dict, Any, List

DEFAULT_CONFIG: Dict[str, Any] = {
    "app_name": "DLRS Data Extractor Pro",
    "version": "1.0.0",
    "theme": "Dark",
    "language": "en",
    "target_urls": [
        "https://dlrs.gov.bd/pages/static-pages/অর্পিত-সম্পত্তির-গ্যাজেট-তালিকা-ldsoay-6994019afcf25ca2d10077ca"
    ],
    "download": {
        "output_dir": "./Output",
        "pdf_dir": "./Output/PDFs",
        "threads": 4,
        "max_retries": 3,
        "timeout_seconds": 30,
        "chunk_size": 8192,
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "auto_resume": True,
        "skip_existing": True
    },
    "ocr": {
        "enabled": True,
        "tesseract_cmd": "C:\\Program Files\\Tesseract-OCR\\tesseract.exe",
        "language": "ben+eng",
        "psm": 6,
        "oem": 3,
        "dpi": 300,
        "output_dir": "./Output/OCR"
    },
    "database": {
        "db_path": "./Output/SQLite/dlrs_data.db",
        "fts_enabled": True,
        "batch_size": 100
    },
    "export": {
        "json_dir": "./Output/JSON",
        "csv_dir": "./Output/CSV",
        "excel_dir": "./Output/Excel",
        "formats": ["json", "csv", "excel", "sqlite"]
    },
    "logging": {
        "log_dir": "./Output/Logs",
        "level": "INFO",
        "files": {
            "download": "download.log",
            "error": "error.log",
            "ocr": "ocr.log",
            "system": "system.log"
        }
    }
}

class ConfigManager:
    """Manages application configurations."""

    def __init__(self, config_path: str = "config.json"):
        self.config_path = os.path.abspath(config_path)
        self.config: Dict[str, Any] = {}
        self.load()

    def load(self) -> Dict[str, Any]:
        """Load configuration from JSON file or create with default values."""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    self.config = self._deep_merge(DEFAULT_CONFIG.copy(), loaded)
            except Exception as e:
                print(f"[WARNING] Failed to parse {self.config_path}: {e}. Falling back to default.")
                self.config = DEFAULT_CONFIG.copy()
        else:
            self.config = DEFAULT_CONFIG.copy()
            self.save()

        self._ensure_directories()
        return self.config

    def save(self) -> bool:
        """Save current configuration to JSON file."""
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"[ERROR] Failed to save config to {self.config_path}: {e}")
            return False

    def get(self, key_path: str, default: Any = None) -> Any:
        """Get nested configuration using dot notation e.g. 'download.threads'."""
        keys = key_path.split(".")
        val = self.config
        for k in keys:
            if isinstance(val, dict) and k in val:
                val = val[k]
            else:
                return default
        return val

    def set(self, key_path: str, value: Any) -> bool:
        """Set nested configuration using dot notation."""
        keys = key_path.split(".")
        d = self.config
        for k in keys[:-1]:
            if k not in d or not isinstance(d[k], dict):
                d[k] = {}
            d = d[k]
        d[keys[-1]] = value
        self._ensure_directories()
        return self.save()

    def _ensure_directories(self):
        """Ensure all required output directories exist on disk."""
        dirs = [
            self.get("download.output_dir", "./Output"),
            self.get("download.pdf_dir", "./Output/PDFs"),
            self.get("ocr.output_dir", "./Output/OCR"),
            os.path.dirname(self.get("database.db_path", "./Output/SQLite/dlrs_data.db")),
            self.get("export.json_dir", "./Output/JSON"),
            self.get("export.csv_dir", "./Output/CSV"),
            self.get("export.excel_dir", "./Output/Excel"),
            self.get("logging.log_dir", "./Output/Logs"),
        ]
        for d in dirs:
            if d:
                os.makedirs(os.path.abspath(d), exist_ok=True)

    def _deep_merge(self, base: dict, override: dict) -> dict:
        """Recursively merge dictionaries."""
        for k, v in override.items():
            if isinstance(v, dict) and k in base and isinstance(base[k], dict):
                base[k] = self._deep_merge(base[k], v)
            else:
                base[k] = v
        return base
