

import heapq
import time
from typing import Dict, List, Optional, Tuple
from enum import IntEnum
from dataclasses import dataclass, field
# Removed pydantic dependency to avoid import issues


class PriorityLevel(IntEnum):
    """Priority levels (1=Critical, 5=Info)."""
    P5_INFO = 5
    P4_STANDARD = 4
    P3_MODERATE = 3
    P2_HIGH = 2
    P1_CRITICAL = 1


CAMEROON_PRIORITY_MATRIX: Dict[str, PriorityLevel] = {
    "anthrax": PriorityLevel.P1_CRITICAL,
    "highly pathogenic avian influenza": PriorityLevel.P1_CRITICAL,
    "ebola": PriorityLevel.P1_CRITICAL,
    "peste des petits ruminants": PriorityLevel.P2_HIGH,
    "foot and mouth disease": PriorityLevel.P2_HIGH,
    "rabies": PriorityLevel.P2_HIGH,
    "contagious bovine pleuropneumonia": PriorityLevel.P3_MODERATE,
    "newcastle disease": PriorityLevel.P3_MODERATE,
    "sheep pox": PriorityLevel.P4_STANDARD,
    "helminthosis": PriorityLevel.P5_INFO,
}


def get_disease_priority(disease_name: str) -> PriorityLevel:
    normalized = disease_name.lower().strip()
    return CAMEROON_PRIORITY_MATRIX.get(normalized, PriorityLevel.P4_STANDARD)


@dataclass
class Alert:
    disease_name: str
    location: str
    reporter_id: str
    priority_level: int
    priority_name: str
    cluster_boost: int = 0
    timestamp: float = 0.0
    details: Dict = field(default_factory=dict)

    @classmethod
    def create_from_disease(cls, disease_name: str, location: str, reporter_id: str,
                           cluster_boost: int = 0, details: Optional[Dict] = None):
        priority_value = get_disease_priority(disease_name)
        if cluster_boost > 0:
            priority_value = max(1, priority_value - 1)

        return cls(
            disease_name=disease_name,
            location=location,
            reporter_id=reporter_id,
            priority_level=priority_value,
            priority_name=PriorityLevel(priority_value).name,
            cluster_boost=cluster_boost,
            details=details or {},
        )

    def is_critical(self):
        return self.priority_level == PriorityLevel.P1_CRITICAL

    def to_alert_item(self):
        return AlertItem(
            priority_level=self.priority_level,
            disease_name=self.disease_name,
            location=self.location,
            reporter_id=self.reporter_id,
            priority_name=self.priority_name,
            cluster_boost=self.cluster_boost,
            timestamp=self.timestamp,
            details=self.details,
        )


@dataclass(order=True)
class AlertItem:
    priority_level: int = field(compare=True)
    disease_name: str
    location: str
    reporter_id: str
    priority_name: str = ""
    cluster_boost: int = 0
    timestamp: float = field(default_factory=time.time)
    details: Dict = field(default_factory=dict)

    def __post_init__(self):
        self.priority_level = int(self.priority_level)
    
    def is_critical(self):
        return self.priority_level == PriorityLevel.P1_CRITICAL


class AlertTriageEngine:
    """
    Priority Queue with correct max-heap behavior for alert triage.
    
    P1 (Critical) alerts are always returned first.
    """
    
    def __init__(self):
        self.heap = []
        self._counter = 0
        self.alerts_db = {}
    
    def push_alert(self, disease_name: str, location: str, reporter_id: str,
                   cluster_boost: int = 0, details: Optional[Dict] = None) -> AlertItem:
        alert = Alert.create_from_disease(disease_name, location, reporter_id, cluster_boost, details)
        alert_item = alert.to_alert_item()

        # FIXED: Use priority_level directly as heap key (P1=1, P5=5)
        # Since heapq is min-heap, smaller priority numbers (higher priority) are popped first
        heap_key = alert_item.priority_level

        heapq.heappush(self.heap, (heap_key, alert_item.timestamp, self._counter, alert_item))
        self._counter += 1
        self.alerts_db[alert_item.timestamp] = alert_item
        return alert_item
    
    def pop_highest_priority(self) -> Optional[AlertItem]:
        if not self.heap:
            return None
        _, _, _, alert = heapq.heappop(self.heap)
        self.alerts_db.pop(alert.timestamp, None)
        return alert
    
    def peek(self) -> Optional[AlertItem]:
        if not self.heap:
            return None
        return self.heap[0][3]
    
    def get_pending_count(self) -> int:
        return len(self.heap)
    
    def get_critical_count(self) -> int:
        return sum(1 for _, _, _, a in self.heap if a.priority_level == 1)
    
    def get_all_alerts(self) -> List[AlertItem]:
        return [a[3] for a in sorted(self.heap, key=lambda x: (-x[0], x[1]))]
    
    def get_critical_alerts(self) -> List[AlertItem]:
        return [a[3] for _, _, _, a in self.heap if a.priority_level == 1]
    
    def clear(self):
        self.heap.clear()
        self.alerts_db.clear()
        self._counter = 0
    
    def __len__(self):
        return len(self.heap)
    
    def __bool__(self):
        return len(self.heap) > 0


class AlertTriage(AlertTriageEngine):
    pass


if __name__ == "__main__":
    triage = AlertTriage()
    
    # Test: Push P5, P1, P3 - should pop P1 first
    triage.push_alert("helminthosis", "Yaoundé", "VET-001")  # P5
    triage.push_alert("anthrax", "Maroua", "VET-002")  # P1 (should pop first!)
    triage.push_alert("newcastle disease", "Bafoussam", "VET-003")  # P3
    
    alert = triage.pop_highest_priority()
    print(f"Popped: {alert.disease_name} (Priority: {alert.priority_level})")
    
    assert alert.priority_level == 1, f"Expected P1, got P{alert.priority_level}"
    print("SUCCESS: Max-heap working correctly!")
