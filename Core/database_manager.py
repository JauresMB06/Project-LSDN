
import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Type, TypeVar
from contextlib import contextmanager
from pathlib import Path
from dataclasses import dataclass, field

from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool

T = TypeVar("T", bound=declarative_base)

# ============================================================================
# SQLAlchemy Base
# ============================================================================

Base = declarative_base()

# ============================================================================
# Database Models
# ============================================================================

class ReportModel(Base):
    """SQLAlchemy model for disease reports."""
    __tablename__ = "reports"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    report_type = Column(String(50), nullable=False)
    location = Column(String(100), nullable=False)
    reporter_id = Column(String(50), nullable=False)
    disease_suspected = Column(String(100), nullable=True)
    symptom_terms = Column(Text, nullable=True)
    mortality_count = Column(Integer, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    synced = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    offline_created = Column(Boolean, default=False)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "report_type": self.report_type,
            "location": self.location,
            "reporter_id": self.reporter_id,
            "disease_suspected": self.disease_suspected,
            "symptom_terms": self.symptom_terms,
            "mortality_count": self.mortality_count,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "synced": self.synced,
            "offline_created": self.offline_created,
        }


class AlertModel(Base):
    """SQLAlchemy model for alerts."""
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    disease_name = Column(String(100), nullable=False)
    location = Column(String(100), nullable=False)
    priority_level = Column(Integer, nullable=False)
    reporter_id = Column(String(50), nullable=False)
    details = Column(Text, nullable=True)  # JSON string
    timestamp = Column(DateTime, default=datetime.utcnow)
    synced = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "disease_name": self.disease_name,
            "location": self.location,
            "priority_level": self.priority_level,
            "reporter_id": self.reporter_id,
            "details": json.loads(self.details) if self.details else {},
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "synced": self.synced,
        }


class ClusterConnectionModel(Base):
    """SQLAlchemy model for cluster connections."""
    __tablename__ = "cluster_connections"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    location_a = Column(String(100), nullable=False)
    location_b = Column(String(100), nullable=False)
    connection_type = Column(String(50), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    synced = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "location_a": self.location_a,
            "location_b": self.location_b,
            "connection_type": self.connection_type,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "synced": self.synced,
        }


class MortalityRecordModel(Base):
    """SQLAlchemy model for mortality records."""
    __tablename__ = "mortality_records"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    location = Column(String(100), nullable=False)
    day = Column(Integer, nullable=False)
    mortality_count = Column(Integer, nullable=False)
    disease_suspected = Column(String(100), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "location": self.location,
            "day": self.day,
            "mortality_count": self.mortality_count,
            "disease_suspected": self.disease_suspected,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }


# ============================================================================
# Database Manager
# ============================================================================

class DatabaseManager:
    """
    SQLAlchemy-based Database Manager with Store-and-Forward capability.
    
    Provides:
    - SQLite persistence with SQLAlchemy ORM
    - Store-and-Forward for offline connectivity
    - Automatic sync tracking
    
    Attributes:
        db_path: Path to SQLite database file
        offline_mode: Whether to operate in offline mode
        engine: SQLAlchemy engine
        Session: SQLAlchemy session factory
    """
    
    def __init__(
        self,
        db_path: str = "ldsn_data.db",
        offline_mode: bool = False,
    ) -> None:
        """
        Initialize the Database Manager.
        
        Args:
            db_path: Path to SQLite database file
            offline_mode: Whether to operate in offline mode
        """
        self.db_path = Path(db_path)
        self.offline_mode = offline_mode
        
        # Create engine with connection pooling for performance
        self.engine = create_engine(
            f"sqlite:///{self.db_path}",
            poolclass=QueuePool,
            pool_size=5,
            max_overflow=10,
            pool_timeout=30,
        )
        
        # Create session factory
        self.Session = sessionmaker(bind=self.engine)
        
        # Create tables
        self._create_schema()
        
        # Initialize offline cache
        self._offline_cache: List[Dict] = []
        
    def _create_schema(self) -> None:
        """Create database tables if they don't exist."""
        Base.metadata.create_all(self.engine)
    
    @contextmanager
    def get_session(self) -> Session:
        """Context manager for database sessions."""
        session = self.Session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    # -------------------------------------------------------------------------
    # Report Operations
    # -------------------------------------------------------------------------
    
    def save_report(
        self,
        report_type: str,
        location: str,
        reporter_id: str,
        disease_suspected: Optional[str] = None,
        symptom_terms: Optional[str] = None,
        mortality_count: Optional[int] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        timestamp: Optional[datetime] = None,
    ) -> int:
        """
        Save a disease report.
        
        Args:
            report_type: Type of report (symptom, mortality, cluster)
            location: Location of the report
            reporter_id: ID of the reporting officer
            disease_suspected: Suspected disease
            symptom_terms: Comma-separated symptom terms
            mortality_count: Number of mortalities
            latitude: GPS latitude
            longitude: GPS longitude
            timestamp: Report timestamp
            
        Returns:
            ID of the saved report
        """
        report = ReportModel(
            report_type=report_type,
            location=location,
            reporter_id=reporter_id,
            disease_suspected=disease_suspected,
            symptom_terms=symptom_terms,
            mortality_count=mortality_count,
            latitude=latitude,
            longitude=longitude,
            timestamp=timestamp or datetime.utcnow(),
            offline_created=self.offline_mode,
        )
        
        with self.get_session() as session:
            session.add(report)
            session.flush()
            report_id = report.id
        
        # Store for sync if offline
        if self.offline_mode:
            self._offline_cache.append({
                "type": "report",
                "data": {
                    "report_type": report_type,
                    "location": location,
                    "reporter_id": reporter_id,
                    "disease_suspected": disease_suspected,
                    "mortality_count": mortality_count,
                    "latitude": latitude,
                    "longitude": longitude,
                }
            })
        
        return report_id
    
    def get_unsynced_reports(self, limit: int = 100) -> List[ReportModel]:
        """Get reports that haven't been synced."""
        with self.get_session() as session:
            return (
                session.query(ReportModel)
                .filter(ReportModel.synced == False)
                .limit(limit)
                .all()
            )
    
    def mark_reports_synced(self, report_ids: List[int]) -> None:
        """Mark reports as synced."""
        if not report_ids:
            return
        
        with self.get_session() as session:
            session.query(ReportModel).filter(
                ReportModel.id.in_(report_ids)
            ).update(
                {ReportModel.synced: True},
                synchronize_session=False
            )
    
    # -------------------------------------------------------------------------
    # Alert Operations
    # -------------------------------------------------------------------------
    
    def save_alert(
        self,
        disease_name: str,
        location: str,
        priority_level: int,
        reporter_id: str,
        details: Optional[Dict] = None,
        timestamp: Optional[datetime] = None,
    ) -> int:
        """
        Save an alert.
        
        Args:
            disease_name: Name of the disease
            location: Location of the alert
            priority_level: Priority level (1-5)
            reporter_id: ID of the reporting officer
            details: Additional details as dictionary
            timestamp: Alert timestamp
            
        Returns:
            ID of the saved alert
        """
        alert = AlertModel(
            disease_name=disease_name,
            location=location,
            priority_level=priority_level,
            reporter_id=reporter_id,
            details=json.dumps(details) if details else None,
            timestamp=timestamp or datetime.utcnow(),
        )
        
        with self.get_session() as session:
            session.add(alert)
            session.flush()
            alert_id = alert.id
        
        return alert_id
    
    def get_unsynced_alerts(self, limit: int = 100) -> List[AlertModel]:
        """Get alerts that haven't been synced."""
        with self.get_session() as session:
            return (
                session.query(AlertModel)
                .filter(AlertModel.synced == False)
                .limit(limit)
                .all()
            )
    
    def mark_alerts_synced(self, alert_ids: List[int]) -> None:
        """Mark alerts as synced."""
        if not alert_ids:
            return
        
        with self.get_session() as session:
            session.query(AlertModel).filter(
                AlertModel.id.in_(alert_ids)
            ).update(
                {AlertModel.synced: True},
                synchronize_session=False
            )
    
    # -------------------------------------------------------------------------
    # Mortality Operations
    # -------------------------------------------------------------------------
    
    def save_mortality(
        self,
        location: str,
        day: int,
        mortality_count: int,
        disease_suspected: Optional[str] = None,
        timestamp: Optional[datetime] = None,
    ) -> int:
        """
        Save a mortality record.
        
        Args:
            location: Location of mortality
            day: Day number (0-364)
            mortality_count: Number of deaths
            disease_suspected: Suspected disease
            timestamp: Record timestamp
            
        Returns:
            ID of the saved record
        """
        record = MortalityRecordModel(
            location=location,
            day=day,
            mortality_count=mortality_count,
            disease_suspected=disease_suspected,
            timestamp=timestamp or datetime.utcnow(),
        )
        
        with self.get_session() as session:
            session.add(record)
            session.flush()
            return record.id
    
    def get_mortality_by_range(
        self,
        start_day: int,
        end_day: int,
        location: Optional[str] = None,
    ) -> List[MortalityRecordModel]:
        """
        Get mortality records for a range of days.
        
        Args:
            start_day: Start day (inclusive)
            end_day: End day (inclusive)
            location: Optional location filter
            
        Returns:
            List of mortality records
        """
        with self.get_session() as session:
            query = session.query(MortalityRecordModel).filter(
                MortalityRecordModel.day >= start_day,
                MortalityRecordModel.day <= end_day,
            )
            
            if location:
                query = query.filter(MortalityRecordModel.location == location)
            
            return query.all()
    
    # -------------------------------------------------------------------------
    # Statistics
    # -------------------------------------------------------------------------
    
    def get_stats(self) -> Dict[str, int]:
        """
        Get statistics about stored data.
        
        Returns:
            Dictionary with counts of stored items
        """
        with self.get_session() as session:
            return {
                "reports": session.query(ReportModel).count(),
                "alerts": session.query(AlertModel).count(),
                "mortality_records": session.query(MortalityRecordModel).count(),
                "pending_reports": session.query(ReportModel).filter(
                    ReportModel.synced == False
                ).count(),
                "pending_alerts": session.query(AlertModel).filter(
                    AlertModel.synced == False
                ).count(),
            }
    
    # -------------------------------------------------------------------------
    # Offline Mode
    # -------------------------------------------------------------------------
    
    def set_offline_mode(self, offline: bool) -> None:
        """Enable or disable offline mode."""
        self.offline_mode = offline
    
    def get_offline_cache(self) -> List[Dict]:
        """Get all items in the offline cache."""
        return self._offline_cache.copy()
    
    def clear_offline_cache(self) -> None:
        """Clear the offline cache."""
        self._offline_cache.clear()
    
    def sync_offline_data(self) -> Dict[str, int]:
        """
        Sync offline data when coming back online.
        
        Returns:
            Dictionary with sync results
        """
        if not self.offline_mode:
            return {"synced": 0, "failed": 0}
        
        synced_count = 0
        failed_count = 0
        
        for item in self._offline_cache:
            try:
                if item["type"] == "report":
                    data = item["data"]
                    self.save_report(
                        report_type=data["report_type"],
                        location=data["location"],
                        reporter_id=data["reporter_id"],
                        disease_suspected=data.get("disease_suspected"),
                        mortality_count=data.get("mortality_count"),
                        latitude=data.get("latitude"),
                        longitude=data.get("longitude"),
                    )
                    synced_count += 1
            except Exception:
                failed_count += 1
        
        self.clear_offline_cache()
        
        return {
            "synced": synced_count,
            "failed": failed_count,
        }
    
    # -------------------------------------------------------------------------
    # Utility Methods
    # -------------------------------------------------------------------------
    
    def close(self) -> None:
        """Close database connections."""
        self.engine.dispose()
    
    def drop_all(self) -> None:
        """Drop all tables (use with caution)."""
        Base.metadata.drop_all(self.engine)


# ============================================================================
# Factory Function
# ============================================================================

def get_database_manager(
    db_path: str = "ldsn_data.db",
    offline_mode: bool = False,
) -> DatabaseManager:
    """
    Create a Database Manager instance.
    
    Args:
        db_path: Path to SQLite database
        offline_mode: Whether to operate in offline mode
        
    Returns:
        Configured DatabaseManager instance
    """
    return DatabaseManager(db_path=db_path, offline_mode=offline_mode)

