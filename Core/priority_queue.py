"""
Livestock Disease Surveillance Network (LDSN) - Priority Queue (Max-Heap)

Emergency Alert Triage using a Max-Heap for priority-based alert management.
Implements O(log n) push/pop operations with Cameroon-specific priority matrix.

Priority Levels:
    P1 (Critical): Anthrax, Highly Pathogenic Avian Influenza - IMMEDIATE RESPONSE
    P2 (High): PPR, FMD, Rabies - URGENT RESPONSE
    P3 (Moderate): CBPP, Newcastle, ASF - PRIORITY RESPONSE
    P4 (Standard): Sheep/Goat Pox - ROUTINE RESPONSE
    P5 (Info): Helminthosis - SURVEILLANCE

Author: LDSN Development Team
Version: 2.0.0
"""

import heapq
import time
from typing import Any, Dict, List, Optional, Tuple
from enum import IntEnum
from dataclasses import dataclass, field


class PriorityLevel(IntEnum):
    """Priority levels for disease alerts (higher value = more critical)."""
    P5_INFO = 5
    P4_STANDARD = 4
    P3_MODERATE = 3
    P2_HIGH = 2
    P1_CRITICAL = 1


# ============================================================================
# Cameroon Priority Matrix - Disease Classifications
# ============================================================================

# Ministry of Livestock, Fisheries and Animal Industries (MINEPIA)
# Priority matrix for automatic P1 classification

CAMEROON_PRIORITY_MATRIX: Dict[str, PriorityLevel] = {
    # P1 - Critical (Zoonotic/Emergency Response)
    "anthrax": PriorityLevel.P1_CRITICAL,
    "highly pathogenic avian influenza": PriorityLevel.P1_CRITICAL,
    "ebola": PriorityLevel.P1_CRITICAL,
    "marburg": PriorityLevel.P1_CRITICAL,
    
    # P2 - High Priority (Urgent Response)
    "peste des petits ruminants": PriorityLevel.P2_HIGH,
    "foot and mouth disease": PriorityLevel.P2_HIGH,
    "rabies": PriorityLevel.P2_HIGH,
    "brucellosis": PriorityLevel.P2_HIGH,
    "rift valley fever": PriorityLevel.P2_HIGH,
    
    # P3 - Moderate Priority (Priority Response)
    "contagious bovine pleuropneumonia": PriorityLevel.P3_MODERATE,
    "newcastle disease": PriorityLevel.P3_MODERATE,
    "african swine fever": PriorityLevel.P3_MODERATE,
    "lumpy skin disease": PriorityLevel.P3_MODERATE,
    
    # P4 - Standard (Routine Response)
    "sheep pox": PriorityLevel.P4_STANDARD,
    "goat pox": PriorityLevel.P4_STANDARD,
    
    # P5 - Informational (Surveillance)
    "helminthosis": PriorityLevel.P5_INFO,
    "tick-borne diseases": PriorityLevel.P5_INFO,
    "nutritional deficiencies": PriorityLevel.P5_INFO,
}


def get_disease_priority(disease_name: str) -> PriorityLevel:
    """
    Get the priority level for a disease.
    
    Args:
        disease_name: Name of the disease (case-insensitive)
        
    Returns:
        PriorityLevel enum value
    """
    normalized = disease_name.lower().strip()
    return CAMEROON_PRIORITY_MATRIX.get(normalized, PriorityLevel.P4_STANDARD)


@dataclass(order=True)
class AlertItem:
    """Priority queue item with ordering based on priority level."""
    priority_level: int = field(init=False, compare=True)
    disease_name: str
    location: str
    reporter_id: str
    timestamp: float = field(default_factory=time.time)
    details: Dict = field(default_factory=dict)
    
    def __post_init__(self):
        """Calculate priority level based on disease."""
        self.priority_level = get_disease_priority(self.disease_name)
    
    def is_critical(self) -> bool:
        """Check if this is a P1 critical alert."""
        return self.priority_level == PriorityLevel.P1_CRITICAL
    
    def to_dict(self) -> Dict:
        """Convert to dictionary representation."""
        return {
            "priority_level": self.priority_level,
            "priority_name": PriorityLevel(self.priority_level).name,
            "disease_name": self.disease_name,
            "location": self.location,
            "reporter_id": self.reporter_id,
            "timestamp": self.timestamp,
            "details": self.details,
        }


class AlertTriage:
    """
    Priority Queue (Max-Heap) for Emergency Alert Triage.
    
    Complexity:
        - push_alert: O(log n)
        - pop_highest_priority: O(log n)
        - peek: O(1)
    
    Python's heapq is a min-heap, so we negate priorities for max-heap behavior.
    
    Attributes:
        heap: Internal heap data structure
    """
    
    def __init__(self) -> None:
        """Initialize an empty alert triage queue."""
        self.heap: List[Tuple[int, float, AlertItem]] = []
        self._counter = 0  # For tie-breaking when priorities are equal
    
    def push_alert(
        self,
        disease_name: str,
        location: str,
        reporter_id: str,
        details: Optional[Dict] = None
    ) -> AlertItem:
        """
        Push a new disease alert onto the queue.
        
        Automatically classifies priority based on Cameroon Priority Matrix.
        
        Args:
            disease_name: Name of the suspected disease
            location: Location of the alert
            reporter_id: ID of the reporting officer
            details: Additional details about the alert
            
        Returns:
            The created AlertItem
        """
        alert = AlertItem(
            disease_name=disease_name,
            location=location,
            reporter_id=reporter_id,
            details=details or {}
        )
        
        # Store as (-priority, timestamp, counter, alert) for max-heap
        # Negative priority because heapq is min-heap
        heapq.heappush(
            self.heap,
            (-alert.priority_level, alert.timestamp, self._counter, alert)
        )
        self._counter += 1
        
        return alert
    
    def pop_highest_priority(self) -> Optional[AlertItem]:
        """
        Extract the most urgent alert from the queue.
        
        Returns:
            AlertItem with highest priority, or None if empty
        """
        if not self.heap:
            return None
        
        _, _, _, alert = heapq.heappop(self.heap)
        return alert
    
    def peek(self) -> Optional[AlertItem]:
        """
        View the highest priority alert without removing it.
        
        Returns:
            AlertItem with highest priority, or None if empty
        """
        if not self.heap:
            return None
        _, _, _, alert = self.heap[0]
        return alert
    
    def get_pending_count(self) -> int:
        """
        Get the number of pending alerts.
        
        Returns:
            Number of alerts in the queue
        """
        return len(self.heap)
    
    def get_critical_count(self) -> int:
        """
        Get the number of P1 critical alerts.
        
        Returns:
            Number of critical alerts
        """
        critical_count = 0
        for neg_priority, _, _, alert in self.heap:
            if -neg_priority == PriorityLevel.P1_CRITICAL:
                critical_count += 1
        return critical_count
    
    def get_alerts_by_priority(self, level: PriorityLevel) -> List[AlertItem]:
        """
        Get all alerts of a specific priority level.
        
        Args:
            level: Priority level to filter by
            
        Returns:
            List of AlertItems with the specified priority
        """
        alerts = []
        for neg_priority, _, _, alert in self.heap:
            if -neg_priority == level:
                alerts.append(alert)
        return alerts
    
    def get_all_alerts(self) -> List[AlertItem]:
        """
        Get all alerts sorted by priority (highest first).
        
        Returns:
            List of all AlertItems sorted by priority
        """
        sorted_heap = sorted(
            self.heap,
            key=lambda x: (-x[0], x[1])  # Sort by priority (desc), then timestamp
        )
        return [alert for _, _, _, alert in sorted_heap]
    
    def clear(self) -> None:
        """Clear all pending alerts."""
        self.heap.clear()
        self._counter = 0
    
    def __len__(self) -> int:
        """Return the number of alerts in the queue."""
        return len(self.heap)
    
    def __bool__(self) -> bool:
        """Return True if there are pending alerts."""
        return len(self.heap) > 0


# ============================================================================
# Validation Models
# ============================================================================

class AlertEntry:
    """Validation model for alert data entries."""
    def __init__(self, disease_name: str, location: str, reporter_id: str, details: Optional[Dict[str, Any]] = None):
        if not disease_name or not disease_name.strip():
            raise ValueError("Disease name cannot be empty")
        if not location or not location.strip():
            raise ValueError("Location cannot be empty")
        if not reporter_id or not reporter_id.strip():
            raise ValueError("Reporter ID cannot be empty")
        
        self.disease_name = disease_name.strip()
        self.location = location.strip()
        self.reporter_id = reporter_id.strip()
        self.details = details or {}


def validate_alert_entry(entry: Dict) -> AlertEntry:
    """
    Validate an alert entry dictionary using native validation.

    Args:
        entry: Dictionary containing alert data

    Returns:
        Validated AlertEntry object

    Raises:
        ValueError: If entry fails validation
    """
    return AlertEntry(**entry)


# ============================================================================
# Convenience Functions
# ============================================================================

def create_critical_alert(
    disease_name: str,
    location: str,
    reporter_id: str,
    details: Optional[Dict] = None
) -> AlertItem:
    """
    Create a P1 critical alert for immediate response.
    
    Args:
        disease_name: Name of the critical disease
        location: Location of the alert
        reporter_id: ID of the reporting officer
        details: Additional details
        
    Returns:
        AlertItem with P1 critical priority
    """
    alert = AlertItem(
        disease_name=disease_name,
        location=location,
        reporter_id=reporter_id,
        details=details or {}
    )
    # Override to ensure P1 critical
    alert.priority_level = PriorityLevel.P1_CRITICAL
    return alert


def process_alert_queue(triage: AlertTriage, max_alerts: int = 10) -> List[AlertItem]:
    """
    Process alerts from the queue.
    
    Args:
        triage: AlertTriage instance
        max_alerts: Maximum number of alerts to process
        
    Returns:
        List of processed AlertItems
    """
    processed = []
    for _ in range(min(max_alerts, len(triage))):
        alert = triage.pop_highest_priority()
        if alert:
            processed.append(alert)
    return processed

