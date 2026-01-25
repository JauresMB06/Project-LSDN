
import json
import sqlite3
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Type, TypeVar
from contextlib import contextmanager
from pathlib import Path
from pydantic import BaseModel


# ============================================================================
# Configuration
# ============================================================================

T = TypeVar("T", bound=BaseModel)

# Default paths for data storage
DEFAULT_DB_PATH = "ldsn_data.db"
DEFAULT_CACHE_DIR = "cache"


# ============================================================================
# JSON Cache Manager
# ============================================================================

class JSONCacheManager:
    """
    Lightweight JSON-based cache for offline data storage.
    
    Used for storing reports and alerts when SQLite is unavailable.
    
    Attributes:
        cache_dir: Directory for cache files
    """
    
    def __init__(self, cache_dir: str = DEFAULT_CACHE_DIR) -> None:
        """
        Initialize the JSON cache manager.
        
        Args:
            cache_dir: Directory to store cache files
        """
        self.cache_dir = Path(cache_dir)
        self._ensure_cache_dir()
    
    def _ensure_cache_dir(self) -> None:
        """Create cache directory if it doesn't exist."""
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_cache_path(self, name: str) -> Path:
        """Get the path for a cache file."""
        return self.cache_dir / f"{name}.json"
    
    def save(self, name: str, data: List[Dict]) -> None:
        """
        Save data to cache file.
        
        Args:
            name: Name of the cache
            data: List of dictionaries to save
        """
        cache_path = self._get_cache_path(name)
        cache_data = {
            "updated_at": datetime.utcnow().isoformat(),
            "items": data,
        }
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, indent=2, ensure_ascii=False)
    
    def load(self, name: str) -> Optional[List[Dict]]:
        """
        Load data from cache file.
        
        Args:
            name: Name of the cache
            
        Returns:
            List of cached items, or None if cache doesn't exist
        """
        cache_path = self._get_cache_path(name)
        if not cache_path.exists():
            return None
        
        with open(cache_path, "r", encoding="utf-8") as f:
            cache_data = json.load(f)
        return cache_data.get("items", [])
    
    def append(self, name: str, item: Dict) -> None:
        """
        Append a single item to cache.
        
        Args:
            name: Name of the cache
            item: Item to append
        """
        data = self.load(name) or []
        data.append(item)
        self.save(name, data)
    
    def clear(self, name: str) -> None:
        """
        Clear a cache.
        
        Args:
            name: Name of the cache to clear
        """
        cache_path = self._get_cache_path(name)
        if cache_path.exists():
            cache_path.unlink()
    
    def list_caches(self) -> List[str]:
        """List all available caches."""
        return [
            f.stem for f in self.cache_dir.glob("*.json")
        ]


# ============================================================================
# SQLite Database Manager
# ============================================================================

class SQLiteManager:
    """
    SQLite database manager for structured data persistence.
    
    Provides Store-and-Forward capability for remote ZVSCC stations.
    
    Attributes:
        db_path: Path to SQLite database file
    """
    
    # SQL statements for table creation
    SCHEMA = """
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_type TEXT NOT NULL,
            location TEXT NOT NULL,
            reporter_id TEXT NOT NULL,
            disease_suspected TEXT,
            symptom_terms TEXT,
            mortality_count INTEGER,
            latitude REAL,
            longitude REAL,
            timestamp TEXT NOT NULL,
            synced INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            disease_name TEXT NOT NULL,
            location TEXT NOT NULL,
            priority_level INTEGER NOT NULL,
            reporter_id TEXT NOT NULL,
            details TEXT,
            timestamp TEXT NOT NULL,
            synced INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS cluster_connections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            location_a TEXT NOT NULL,
            location_b TEXT NOT NULL,
            connection_type TEXT,
            timestamp TEXT NOT NULL,
            synced INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_reports_synced ON reports(synced);
        CREATE INDEX IF NOT EXISTS idx_alerts_synced ON alerts(synced);
        CREATE INDEX IF NOT EXISTS idx_connections_synced ON cluster_connections(synced);
    """
    
    def __init__(self, db_path: str = DEFAULT_DB_PATH) -> None:
        """
        Initialize the SQLite manager.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self._ensure_db()
        self._create_schema()
    
    def _ensure_db(self) -> None:
        """Create database file if it doesn't exist."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
    
    def _create_schema(self) -> None:
        """Create database tables."""
        with self._get_connection() as conn:
            conn.executescript(self.SCHEMA)
    
    @contextmanager
    def _get_connection(self):
        """Context manager for database connection."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def insert_report(
        self,
        report_type: str,
        location: str,
        reporter_id: str,
        disease_suspected: Optional[str] = None,
        symptom_terms: Optional[str] = None,
        mortality_count: Optional[int] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        timestamp: Optional[str] = None,
    ) -> int:
        """
        Insert a disease report.
        
        Args:
            report_type: Type of report (symptom, mortality, cluster)
            location: Location of the report
            reporter_id: ID of the reporting officer
            disease_suspected: Suspected disease
            symptom_terms: Comma-separated symptom terms
            mortality_count: Number of mortalities
            latitude: GPS latitude
            longitude: GPS longitude
            timestamp: ISO format timestamp
            
        Returns:
            ID of the inserted report
        """
        if timestamp is None:
            timestamp = datetime.utcnow().isoformat()
        
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO reports (
                    report_type, location, reporter_id, disease_suspected,
                    symptom_terms, mortality_count, latitude, longitude, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    report_type, location, reporter_id, disease_suspected,
                    symptom_terms, mortality_count, latitude, longitude, timestamp
                ),
            )
            return cursor.lastrowid
    
    def insert_alert(
        self,
        disease_name: str,
        location: str,
        priority_level: int,
        reporter_id: str,
        details: Optional[Dict] = None,
        timestamp: Optional[str] = None,
    ) -> int:
        """
        Insert an alert.
        
        Args:
            disease_name: Name of the disease
            location: Location of the alert
            priority_level: Priority level (1-5)
            reporter_id: ID of the reporting officer
            details: Additional details as JSON
            timestamp: ISO format timestamp
            
        Returns:
            ID of the inserted alert
        """
        if timestamp is None:
            timestamp = datetime.utcnow().isoformat()
        
        details_json = json.dumps(details) if details else None
        
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO alerts (
                    disease_name, location, priority_level, reporter_id, details, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (disease_name, location, priority_level, reporter_id, details_json, timestamp),
            )
            return cursor.lastrowid
    
    def insert_cluster_connection(
        self,
        location_a: str,
        location_b: str,
        connection_type: Optional[str] = None,
        timestamp: Optional[str] = None,
    ) -> int:
        """
        Insert a cluster connection.
        
        Args:
            location_a: First location
            location_b: Second location
            connection_type: Type of connection
            timestamp: ISO format timestamp
            
        Returns:
            ID of the inserted connection
        """
        if timestamp is None:
            timestamp = datetime.utcnow().isoformat()
        
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO cluster_connections (
                    location_a, location_b, connection_type, timestamp
                ) VALUES (?, ?, ?, ?)
                """,
                (location_a, location_b, connection_type, timestamp),
            )
            return cursor.lastrowid
    
    def get_unsynced_reports(self, limit: int = 100) -> List[Dict]:
        """Get reports that haven't been synced."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM reports WHERE synced = 0 LIMIT ?",
                (limit,),
            )
            return [dict(row) for row in cursor.fetchall()]
    
    def get_unsynced_alerts(self, limit: int = 100) -> List[Dict]:
        """Get alerts that haven't been synced."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM alerts WHERE synced = 0 LIMIT ?",
                (limit,),
            )
            return [dict(row) for row in cursor.fetchall()]
    
    def mark_synced(self, table: str, ids: List[int]) -> None:
        """Mark records as synced."""
        if not ids:
            return
        
        placeholders = ",".join("?" * len(ids))
        with self._get_connection() as conn:
            conn.execute(
                f"UPDATE {table} SET synced = 1 WHERE id IN ({placeholders})",
                ids,
            )
    
    def get_report_count(self) -> int:
        """Get total number of reports."""
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM reports")
            return cursor.fetchone()[0]
    
    def get_alert_count(self) -> int:
        """Get total number of alerts."""
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM alerts")
            return cursor.fetchone()[0]
    
    def close(self) -> None:
        """Close database connection (for cleanup)."""
        pass  # Connection is closed automatically via context manager


# ============================================================================
# Store-and-Forward Manager
# ============================================================================

class StoreAndForwardManager:
    """
    Unified Store-and-Forward manager for offline data persistence.
    
    Combines SQLite and JSON caching for robust offline capability.
    Designed for remote ZVSCC stations in Cameroon's Far North Region.
    
    Attributes:
        db: SQLite database manager
        cache: JSON cache manager
    """
    
    def __init__(
        self,
        db_path: str = DEFAULT_DB_PATH,
        cache_dir: str = DEFAULT_CACHE_DIR,
    ) -> None:
        """
        Initialize the Store-and-Forward manager.
        
        Args:
            db_path: Path to SQLite database
            cache_dir: Directory for JSON cache
        """
        self.db = SQLiteManager(db_path)
        self.cache = JSONCacheManager(cache_dir)
    
    # -------------------------------------------------------------------------
    # Report Operations
    # -------------------------------------------------------------------------
    
    def save_report(
        self,
        report_type: str,
        location: str,
        reporter_id: str,
        **kwargs,
    ) -> int:
        """
        Save a disease report (Store-and-Forward).
        
        Args:
            report_type: Type of report
            location: Location of the report
            reporter_id: ID of reporting officer
            **kwargs: Additional report fields
            
        Returns:
            ID of the saved report
        """
        report_id = self.db.insert_report(
            report_type=report_type,
            location=location,
            reporter_id=reporter_id,
            **kwargs,
        )
        
        # Also cache for offline access
        self.cache.append("pending_reports", {
            "id": report_id,
            "report_type": report_type,
            "location": location,
            "reporter_id": reporter_id,
            **kwargs,
        })
        
        return report_id
    
    def get_pending_reports(self, limit: int = 100) -> List[Dict]:
        """Get pending reports for synchronization."""
        # Try database first
        reports = self.db.get_unsynced_reports(limit)
        if reports:
            return reports
        
        # Fallback to cache
        return self.cache.load("pending_reports") or []
    
    def mark_reports_synced(self, report_ids: List[int]) -> None:
        """Mark reports as synced."""
        self.db.mark_synced("reports", report_ids)

        # Also clear the cache since reports are now synced
        # In a real implementation, we might want to update the cache instead of clearing it
        self.cache.clear("pending_reports")
    
    # -------------------------------------------------------------------------
    # Alert Operations
    # -------------------------------------------------------------------------
    
    def save_alert(
        self,
        disease_name: str,
        location: str,
        priority_level: int,
        reporter_id: str,
        **kwargs,
    ) -> int:
        """
        Save an alert (Store-and-Forward).
        
        Args:
            disease_name: Name of the disease
            location: Location of the alert
            priority_level: Priority level (1-5)
            reporter_id: ID of reporting officer
            **kwargs: Additional alert fields
            
        Returns:
            ID of the saved alert
        """
        alert_id = self.db.insert_alert(
            disease_name=disease_name,
            location=location,
            priority_level=priority_level,
            reporter_id=reporter_id,
            **kwargs,
        )
        
        self.cache.append("pending_alerts", {
            "id": alert_id,
            "disease_name": disease_name,
            "location": location,
            "priority_level": priority_level,
            "reporter_id": reporter_id,
            **kwargs,
        })
        
        return alert_id
    
    def get_pending_alerts(self, limit: int = 100) -> List[Dict]:
        """Get pending alerts for synchronization."""
        alerts = self.db.get_unsynced_alerts(limit)
        if alerts:
            return alerts
        return self.cache.load("pending_alerts") or []
    
    def mark_alerts_synced(self, alert_ids: List[int]) -> None:
        """Mark alerts as synced."""
        self.db.mark_synced("alerts", alert_ids)
    
    # -------------------------------------------------------------------------
    # Statistics
    # -------------------------------------------------------------------------
    
    def get_stats(self) -> Dict[str, int]:
        """
        Get statistics about stored data.
        
        Returns:
            Dictionary with counts of stored items
        """
        return {
            "reports": self.db.get_report_count(),
            "alerts": self.db.get_alert_count(),
            "pending_reports": len(self.cache.load("pending_reports") or []),
            "pending_alerts": len(self.cache.load("pending_alerts") or []),
        }
    
    def clear_all(self) -> None:
        """Clear all stored data (use with caution)."""
        self.cache.clear("pending_reports")
        self.cache.clear("pending_alerts")
        # Note: SQLite data is not cleared as it represents historical records


# ============================================================================
# Validation Models
# ============================================================================

class ReportModel:
    """Validation model for report data."""
    def __init__(
        self,
        report_type: str,
        location: str,
        reporter_id: str,
        disease_suspected: Optional[str] = None,
        symptom_terms: Optional[str] = None,
        mortality_count: Optional[int] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
    ):
        if not report_type or not report_type.strip():
            raise ValueError("Report type cannot be empty")
        if not location or not location.strip():
            raise ValueError("Location cannot be empty")
        if not reporter_id or not reporter_id.strip():
            raise ValueError("Reporter ID cannot be empty")
        
        self.report_type = report_type.strip()
        self.location = location.strip()
        self.reporter_id = reporter_id.strip()
        self.disease_suspected = disease_suspected.strip() if disease_suspected else None
        self.symptom_terms = symptom_terms.strip() if symptom_terms else None
        self.mortality_count = mortality_count
        self.latitude = latitude
        self.longitude = longitude


class AlertModel:
    """Validation model for alert data."""
    def __init__(
        self,
        disease_name: str,
        location: str,
        priority_level: int,
        reporter_id: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        if not disease_name or not disease_name.strip():
            raise ValueError("Disease name cannot be empty")
        if not location or not location.strip():
            raise ValueError("Location cannot be empty")
        if not reporter_id or not reporter_id.strip():
            raise ValueError("Reporter ID cannot be empty")
        if priority_level < 1 or priority_level > 5:
            raise ValueError("Priority level must be between 1 and 5")
        
        self.disease_name = disease_name.strip()
        self.location = location.strip()
        self.priority_level = priority_level
        self.reporter_id = reporter_id.strip()
        self.details = details or {}


def validate_report_data(data: Dict) -> ReportModel:
    """Validate report data using native validation."""
    return ReportModel(**data)


def validate_alert_data(data: Dict) -> AlertModel:
    """Validate alert data using native validation."""
    return AlertModel(**data)


# ============================================================================
# Factory Functions
# ============================================================================

def get_persistence_manager(
    db_path: str = DEFAULT_DB_PATH,
    cache_dir: str = DEFAULT_CACHE_DIR,
) -> StoreAndForwardManager:
    """
    Create a Store-and-Forward manager with default settings.
    
    Args:
        db_path: Path to SQLite database
        cache_dir: Directory for JSON cache
        
    Returns:
        Configured StoreAndForwardManager instance
    """
    return StoreAndForwardManager(db_path=db_path, cache_dir=cache_dir)

