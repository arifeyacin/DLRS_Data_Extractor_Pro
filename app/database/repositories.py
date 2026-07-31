"""
Repositories & Data Access Object (DAO) Layer for DLRS Data Extractor Pro
Provides thread-safe operations for LandRecords, Gazettes, Downloads, and FTS5 Queries.
"""

import sqlite3
from typing import List, Dict, Any, Optional

from app.database.db_manager import DatabaseManager
from app.pdf_processor.parser import LandRecord
from app.logger import get_system_logger, get_error_logger

class LandRecordRepository:
    """Repository handling CRUD operations and search for land records."""

    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        self.db_mgr = db_manager or DatabaseManager()
        self.logger = get_system_logger()
        self.error_logger = get_error_logger()

    def insert_batch(self, records: List[LandRecord]) -> int:
        """Insert a batch of LandRecord items inside a single high-speed transaction."""
        if not records:
            return 0

        self.logger.info(f"Inserting batch of {len(records)} land records into SQLite database...")
        conn = self.db_mgr.get_connection()
        cursor = conn.cursor()

        try:
            # 1. Upsert parent gazette entries to satisfy Foreign Key constraints
            gazette_map = {}
            for r in records:
                if r.gazette_number and r.gazette_number not in gazette_map:
                    gazette_map[r.gazette_number] = (
                        r.gazette_number, r.district, r.upazila,
                        r.publication_date or "2026-01-15",
                        r.source_pdf or "unknown.pdf",
                        r.source_pdf or ""
                    )

            for gz_data in gazette_map.values():
                cursor.execute("""
                INSERT OR IGNORE INTO gazettes (
                    gazette_number, district, upazila, publication_date, file_name, file_path
                ) VALUES (?, ?, ?, ?, ?, ?);
                """, gz_data)

            # 2. Insert land records
            sql = """
            INSERT OR REPLACE INTO land_records (
                record_id, gazette_number, district, upazila, mouza, khatian, dag,
                owner_name, publication_date, area, land_type, remarks, source_pdf
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """

            data = [
                (
                    r.record_id, r.gazette_number, r.district, r.upazila, r.mouza,
                    r.khatian, r.dag, r.owner_name, r.publication_date, r.area,
                    r.land_type, r.remarks, r.source_pdf
                )
                for r in records
            ]

            cursor.executemany(sql, data)
            conn.commit()
            inserted_count = cursor.rowcount
            self.logger.info(f"Successfully inserted {inserted_count} land records into database.")
            return len(records)
        except Exception as e:
            conn.rollback()
            self.error_logger.error(f"Failed to batch insert land records: {e}")
            return 0
        finally:
            conn.close()

    def search(
        self,
        keyword: str = "",
        district: str = "",
        upazila: str = "",
        mouza: str = "",
        khatian: str = "",
        dag: str = "",
        owner: str = "",
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Perform flexible search across Land Records using FTS5 and/or SQL filters."""
        conn = self.db_mgr.get_connection()
        cursor = conn.cursor()

        conditions = []
        params = []

        if keyword:
            # FTS5 full-text search match if enabled
            conditions.append("""
            id IN (
                SELECT rowid FROM land_records_fts WHERE land_records_fts MATCH ?
            )
            """)
            params.append(f'"{keyword}"*')

        if district:
            conditions.append("district LIKE ?")
            params.append(f"%{district}%")
        if upazila:
            conditions.append("upazila LIKE ?")
            params.append(f"%{upazila}%")
        if mouza:
            conditions.append("mouza LIKE ?")
            params.append(f"%{mouza}%")
        if khatian:
            conditions.append("khatian LIKE ?")
            params.append(f"%{khatian}%")
        if dag:
            conditions.append("dag LIKE ?")
            params.append(f"%{dag}%")
        if owner:
            conditions.append("owner_name LIKE ?")
            params.append(f"%{owner}%")

        where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""

        sql = f"""
        SELECT record_id, gazette_number, district, upazila, mouza, khatian, dag,
               owner_name, publication_date, area, land_type, remarks, source_pdf
        FROM land_records
        {where_clause}
        ORDER BY id ASC
        LIMIT ? OFFSET ?;
        """
        params.extend([limit, offset])

        try:
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            results = [dict(row) for row in rows]
            return results
        except Exception as e:
            self.error_logger.error(f"Search query error: {e}")
            return []
        finally:
            conn.close()

    def get_stats(self) -> Dict[str, Any]:
        """Return total record count and breakdown stats."""
        conn = self.db_mgr.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT COUNT(*) FROM land_records;")
            total_records = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(DISTINCT district) FROM land_records;")
            total_districts = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(DISTINCT upazila) FROM land_records;")
            total_upazilas = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(DISTINCT gazette_number) FROM land_records;")
            total_gazettes = cursor.fetchone()[0]

            return {
                "total_records": total_records,
                "total_districts": total_districts,
                "total_upazilas": total_upazilas,
                "total_gazettes": total_gazettes
            }
        except Exception as e:
            self.error_logger.error(f"Failed to fetch stats: {e}")
            return {"total_records": 0, "total_districts": 0, "total_upazilas": 0, "total_gazettes": 0}
        finally:
            conn.close()

class DownloadRepository:
    """Repository tracking download operations."""

    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        self.db_mgr = db_manager or DatabaseManager()

    def record_download(self, url: str, filename: str, district: str, upazila: str, status: str, file_size: int = 0):
        conn = self.db_mgr.get_connection()
        cursor = conn.cursor()
        sql = """
        INSERT OR REPLACE INTO downloads (url, filename, district, upazila, status, file_size)
        VALUES (?, ?, ?, ?, ?, ?);
        """
        try:
            cursor.execute(sql, (url, filename, district, upazila, status, file_size))
            conn.commit()
        finally:
            conn.close()

    def is_downloaded(self, url: str) -> bool:
        conn = self.db_mgr.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT 1 FROM downloads WHERE url = ? AND status = 'COMPLETED';", (url,))
            return cursor.fetchone() is not None
        finally:
            conn.close()
