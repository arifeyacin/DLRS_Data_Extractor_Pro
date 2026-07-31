"""
Database Manager Module for DLRS Data Extractor Pro
Handles SQLite connection, schema creation, PRAGMA performance tuning, and FTS5 full-text indexing.
"""

import os
import sqlite3
from typing import Optional

from app.logger import get_system_logger, get_error_logger

class DatabaseManager:
    """Manages SQLite database connections and schema migrations."""

    def __init__(self, db_path: str = "./Output/SQLite/dlrs_data.db"):
        self.db_path = os.path.abspath(db_path)
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.logger = get_system_logger()
        self.error_logger = get_error_logger()
        self.init_db()

    def get_connection(self) -> sqlite3.Connection:
        """Create and configure a thread-safe SQLite connection."""
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        return conn

    def init_db(self):
        """Initialize relational database tables, indexes, and FTS5 search index."""
        self.logger.info(f"Initializing SQLite database at: {self.db_path}")
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            # 1. Gazettes table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS gazettes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                gazette_number TEXT UNIQUE NOT NULL,
                district TEXT NOT NULL,
                upazila TEXT NOT NULL,
                publication_date TEXT,
                file_name TEXT NOT NULL,
                file_path TEXT NOT NULL,
                source_url TEXT,
                record_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)

            # 2. Land Records table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS land_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                record_id TEXT UNIQUE NOT NULL,
                gazette_number TEXT,
                district TEXT NOT NULL,
                upazila TEXT NOT NULL,
                mouza TEXT NOT NULL,
                khatian TEXT,
                dag TEXT,
                owner_name TEXT NOT NULL,
                publication_date TEXT,
                area TEXT,
                land_type TEXT,
                remarks TEXT,
                source_pdf TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (gazette_number) REFERENCES gazettes (gazette_number) ON DELETE SET NULL
            );
            """)

            # 3. Downloads tracker table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS downloads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE NOT NULL,
                filename TEXT NOT NULL,
                district TEXT,
                upazila TEXT,
                status TEXT NOT NULL,
                file_size INTEGER DEFAULT 0,
                downloaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)

            # 4. Standard B-Tree Indexes for fast relational filtering
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_land_district ON land_records(district);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_land_upazila ON land_records(upazila);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_land_mouza ON land_records(mouza);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_land_khatian ON land_records(khatian);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_land_dag ON land_records(dag);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_land_owner ON land_records(owner_name);")

            # 5. SQLite FTS5 Full-Text Search Virtual Table
            try:
                cursor.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS land_records_fts USING fts5(
                    record_id,
                    district,
                    upazila,
                    mouza,
                    khatian,
                    dag,
                    owner_name,
                    remarks,
                    content='land_records',
                    content_rowid='id'
                );
                """)

                # FTS Triggers for automatic sync
                cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS land_records_ai AFTER INSERT ON land_records BEGIN
                    INSERT INTO land_records_fts(rowid, record_id, district, upazila, mouza, khatian, dag, owner_name, remarks)
                    VALUES (new.id, new.record_id, new.district, new.upazila, new.mouza, new.khatian, new.dag, new.owner_name, new.remarks);
                END;
                """)

                cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS land_records_ad AFTER DELETE ON land_records BEGIN
                    INSERT INTO land_records_fts(land_records_fts, rowid, record_id, district, upazila, mouza, khatian, dag, owner_name, remarks)
                    VALUES('delete', old.id, old.record_id, old.district, old.upazila, old.mouza, old.khatian, old.dag, old.owner_name, old.remarks);
                END;
                """)

                cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS land_records_au AFTER UPDATE ON land_records BEGIN
                    INSERT INTO land_records_fts(land_records_fts, rowid, record_id, district, upazila, mouza, khatian, dag, owner_name, remarks)
                    VALUES('delete', old.id, old.record_id, old.district, old.upazila, old.mouza, old.khatian, old.dag, old.owner_name, old.remarks);
                    INSERT INTO land_records_fts(rowid, record_id, district, upazila, mouza, khatian, dag, owner_name, remarks)
                    VALUES (new.id, new.record_id, new.district, new.upazila, new.mouza, new.khatian, new.dag, new.owner_name, new.remarks);
                END;
                """)
                self.logger.info("SQLite FTS5 full-text search virtual table and sync triggers created.")
            except Exception as fts_err:
                self.error_logger.warning(f"FTS5 initialization warning: {fts_err}. Standard B-Tree queries active.")

            conn.commit()
            self.logger.info("Database schema setup completed successfully.")
        except Exception as e:
            conn.rollback()
            self.error_logger.error(f"Failed to initialize database schema: {e}")
            raise
        finally:
            conn.close()
