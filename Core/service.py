"""
Livestock Disease Surveillance Network (LDSN) - Service Layer

3-Tier Architecture Gateway that perfectly decouples algorithmic logic
from the Presentation Layer (CLI/Web).

Tiers:
    1. Presentation Layer: CLI, Web UI, Mobile App
    2. Service Layer: LDSNService (this module)
    3. Data Layer: Core algorithms + Persistence

Author: LDSN Development Team
Version: 2.0.0
"""

from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime

# Core Algorithm Imports
from .Trie import SymptomTrie, get_trained_trie, CAMEROON_PRIORITY_DISEASES
from .Transhumance import (
    TranshumanceGraph,
    get_cameroon_network,
    SeasonType,
    analyze_seasonal_impact,
)
from .union_find import OutbreakCluster, create_cameroon_outbreak_clusters
from .priority_queue import (
    AlertTriage,
    AlertItem,
    PriorityLevel,
    CAMEROON_PRIORITY_MATRIX,
)
from .segment_tree import MortalitySegmentTree, CameroonMortalityTracker

# Persistence Layer
from .data_persistence import (
    StoreAndForwardManager,
    get_persistence_manager,
    validate_report_data,
    validate_alert_data,
    ReportModel,
    AlertModel,
)


# ============================================================================
# Data Transfer Objects (DTOs)
# ============================================================================

class SymptomResult:
    """DTO for symptom autocomplete results."""
    def __init__(self, matches: List[str], prefix: str):
        self.matches = matches
        self.prefix = prefix
        self.count = len(matches)
        self.timestamp = datetime.utcnow().isoformat()


class RouteResult:
    """DTO for route calculation results."""
    def __init__(
        self,
        path: List[str],
        total_weight: float,
        is_rainy_season: bool,
        season_name: str,
    ):
        self.path = path
        self.total_weight = total_weight
        self.is_rainy_season = is_rainy_season
        self.season_name = season_name
        self.timestamp = datetime.utcnow().isoformat()
        self.num_stops = len(path) - 1 if len(path) > 1 else 0


class AlertResult:
    """DTO for alert processing results."""
    def __init__(self, alert: AlertItem, action_taken: str):
        self.alert = alert
        self.action_taken = action_taken
        self.priority_level = alert.priority_level
        self.priority_name = PriorityLevel(alert.priority_level).name
        self.timestamp = datetime.utcnow().isoformat()


class ClusterResult:
    """DTO for cluster detection results."""
    def __init__(self, cluster_id: str, locations: List[str], size: int):
        self.cluster_id = cluster_id
        self.locations = locations
        self.size = size
        self.timestamp = datetime.utcnow().isoformat()


class MortalityResult:
    """DTO for mortality tracking results."""
    def __init__(
        self,
        dry_season_total: int,
        rainy_season_total: int,
        total: int,
    ):
        self.dry_season_total = dry_season_total
        self.rainy_season_total = rainy_season_total
        self.total = total
        self.timestamp = datetime.utcnow().isoformat()


class ServiceStats:
    """DTO for service statistics."""
    def __init__(self, persistence_stats: Dict, algorithm_stats: Dict):
        self.persistence = persistence_stats
        self.algorithms = algorithm_stats
        self.timestamp = datetime.utcnow().isoformat()


# ============================================================================
# LDSN Service Gateway
# ============================================================================

class LDSNService:
    """
    Primary Service Gateway for the Livestock Disease Surveillance Network.
    
    This class implements the 3-Tier Architecture by:
        1. Providing a clean API to the Presentation Layer
        2. Orchestrating core algorithmic components
        3. Managing data persistence
    
    All algorithmic complexity is hidden behind this interface.
    
    Attributes:
        trie: SymptomTrie for autocomplete
        network: TranshumanceGraph for routing
        clusters: OutbreakCluster for cluster detection
        triage: AlertTriage for priority management
        mortality: MortalitySegmentTree for tracking
        persistence: StoreAndForwardManager for offline storage
    """
    
    def __init__(
        self,
        persistence_manager: Optional[StoreAndForwardManager] = None,
    ) -> None:
        """
        Initialize the LDSN Service.
        
        Args:
            persistence_manager: Optional custom persistence manager
        """
        # Initialize Core Algorithms
        self.trie = get_trained_trie()
        self.network = get_cameroon_network()
        self.clusters = create_cameroon_outbreak_clusters()
        self.triage = AlertTriage()
        self.mortality = CameroonMortalityTracker()
        
        # Initialize Persistence
        self.persistence = persistence_manager or get_persistence_manager()
        
        # Cache for loaded disease terms
        self._disease_cache: Optional[List[str]] = None
    
    # -------------------------------------------------------------------------
    # Symptom Autocomplete Services
    # -------------------------------------------------------------------------
    
    def autocomplete_symptoms(self, prefix: str) -> SymptomResult:
        """
        Autocomplete disease symptoms using the Trie.
        
        Args:
            prefix: The prefix to search for
            
        Returns:
            SymptomResult with matching terms
            
        Raises:
            ValueError: If prefix is None or empty
        """
        if not prefix or not prefix.strip():
            raise ValueError("Prefix cannot be empty")
        
        matches = self.trie.autocomplete(prefix.strip())
        return SymptomResult(matches=matches, prefix=prefix)
    
    def search_symptoms(self, term: str) -> bool:
        """
        Search for an exact symptom term.
        
        Args:
            term: Term to search for
            
        Returns:
            True if term exists, False otherwise
        """
        return self.trie.search(term)
    
    def get_all_symptoms(self) -> List[str]:
        """Get all loaded symptom terms."""
        if self._disease_cache is None:
            self._disease_cache = CAMEROON_PRIORITY_DISEASES
        return self._disease_cache
    
    # -------------------------------------------------------------------------
    # Route Calculation Services
    # -------------------------------------------------------------------------
    
    def calculate_route(
        self,
        start: str,
        end: str,
        is_rainy_season: bool = False,
    ) -> RouteResult:
        """
        Calculate the safest transhumance route.
        
        Args:
            start: Starting location
            end: Destination location
            is_rainy_season: Whether it's the rainy season
            
        Returns:
            RouteResult with path and weight
            
        Raises:
            KeyError: If start or end location doesn't exist
        """
        path, weight = self.network.calculate_safe_route(
            start=start,
            end=end,
            is_rainy_season=is_rainy_season,
        )
        
        season_name = "Rainy (Duumol)" if is_rainy_season else "Dry"
        
        return RouteResult(
            path=path,
            total_weight=weight,
            is_rainy_season=is_rainy_season,
            season_name=season_name,
        )
    
    def analyze_route_seasonal_impact(
        self,
        start: str,
        end: str,
    ) -> Dict[str, Any]:
        """
        Analyze how seasonal conditions affect a route.
        
        Args:
            start: Starting location
            end: Destination location
            
        Returns:
            Dictionary with dry and rainy season analysis
        """
        return analyze_seasonal_impact(self.network, start, end)
    
    def update_location_risk(self, location: str, risk: float) -> None:
        """
        Update risk score for a location.
        
        Used when cluster detection identifies an outbreak.
        
        Args:
            location: Location name
            risk: New risk score
        """
        self.network.update_location_risk(location, risk)
    
    def get_all_locations(self) -> List[str]:
        """Get all available locations."""
        return self.network.get_all_locations()
    
    # -------------------------------------------------------------------------
    # Cluster Detection Services
    # -------------------------------------------------------------------------
    
    def detect_clusters(self) -> List[ClusterResult]:
        """
        Detect all current outbreak clusters.
        
        Returns:
            List of ClusterResult objects
        """
        clusters = self.clusters.get_clusters()
        results = []
        
        for i, cluster in enumerate(clusters):
            results.append(
                ClusterResult(
                    cluster_id=f"CLUSTER-{i+1:03d}",
                    locations=list(cluster),
                    size=len(cluster),
                )
            )
        
        return results
    
    def connect_locations(
        self,
        location_a: str,
        location_b: str,
        connection_type: str = "shared_resource",
    ) -> bool:
        """
        Create a connection between two locations.
        
        Used to link locations that share resources (water, markets, etc.).
        
        Args:
            location_a: First location
            location_b: Second location
            connection_type: Type of connection
            
        Returns:
            True if a new cluster was formed, False if already connected
        """
        return self.clusters.union(location_a, location_b)
    
    def check_cluster_connected(self, loc_a: str, loc_b: str) -> bool:
        """
        Check if two locations are in the same cluster.
        
        Args:
            loc_a: First location
            loc_b: Second location
            
        Returns:
            True if locations are in the same cluster
        """
        return self.clusters.connected(loc_a, loc_b)
    
    def get_cluster_size(self, location: str) -> int:
        """
        Get the size of the cluster containing a location.
        
        Args:
            location: Location to check
            
        Returns:
            Number of locations in the cluster
        """
        return self.clusters.get_cluster_size(location)
    
    # -------------------------------------------------------------------------
    # Alert Triage Services
    # -------------------------------------------------------------------------
    
    def submit_alert(
        self,
        disease_name: str,
        location: str,
        reporter_id: str,
        details: Optional[Dict] = None,
    ) -> AlertResult:
        """
        Submit a disease alert for triage.
        
        Automatically prioritizes based on Cameroon Priority Matrix.
        
        Args:
            disease_name: Name of the suspected disease
            location: Location of the alert
            reporter_id: ID of the reporting officer
            details: Additional details
            
        Returns:
            AlertResult with priority and action taken
        """
        alert = self.triage.push_alert(
            disease_name=disease_name,
            location=location,
            reporter_id=reporter_id,
            details=details,
        )
        
        # Determine action based on priority
        if alert.is_critical():
            action = "IMMEDIATE_RESPONSE_REQUIRED"
        elif alert.priority_level == PriorityLevel.P2_HIGH:
            action = "URGENT_RESPONSE_SCHEDULED"
        else:
            action = "QUEUED_FOR_INVESTIGATION"
        
        # Persist the alert
        self.persistence.save_alert(
            disease_name=disease_name,
            location=location,
            priority_level=alert.priority_level,
            reporter_id=reporter_id,
            details=details,
        )
        
        return AlertResult(alert=alert, action_taken=action)
    
    def process_next_alert(self) -> Optional[AlertResult]:
        """
        Process the highest priority alert.
        
        Returns:
            AlertResult for the processed alert, or None if queue is empty
        """
        alert = self.triage.pop_highest_priority()
        if alert:
            return AlertResult(
                alert=alert,
                action_taken="DISPATCHED_TO_FIELD_TEAM",
            )
        return None
    
    def get_pending_alerts(self) -> List[AlertItem]:
        """Get all pending alerts sorted by priority."""
        return self.triage.get_all_alerts()
    
    def get_critical_alert_count(self) -> int:
        """Get count of P1 critical alerts."""
        return self.triage.get_critical_count()
    
    # -------------------------------------------------------------------------
    # Mortality Tracking Services
    # -------------------------------------------------------------------------
    
    def record_mortality(self, day: int, count: int, location: Optional[str] = None) -> None:
        """
        Record mortality data for a specific day.
        
        Args:
            day: Day number (0-based)
            count: Number of deaths
            location: Optional location for metadata
        """
        self.mortality.record_mortality(day, count)
    
    def get_mortality_statistics(self) -> MortalityResult:
        """
        Get mortality statistics by season.
        
        Returns:
            MortalityResult with dry and rainy season totals
        """
        return MortalityResult(
            dry_season_total=self.mortality.get_dry_season_mortality(),
            rainy_season_total=self.mortality.get_rainy_season_mortality(),
            total=self.mortality.get_total_mortality(),
        )
    
    # -------------------------------------------------------------------------
    # Persistence Services
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
        return self.persistence.save_report(
            report_type=report_type,
            location=location,
            reporter_id=reporter_id,
            **kwargs,
        )
    
    def get_pending_data(self, limit: int = 100) -> Dict[str, List[Dict]]:
        """
        Get all pending data for synchronization.
        
        Args:
            limit: Maximum number of items to retrieve
            
        Returns:
            Dictionary with 'reports' and 'alerts' lists
        """
        return {
            "reports": self.persistence.get_pending_reports(limit),
            "alerts": self.persistence.get_pending_alerts(limit),
        }
    
    def mark_data_synced(self, report_ids: List[int], alert_ids: List[int]) -> None:
        """
        Mark data as successfully synced.
        
        Args:
            report_ids: List of report IDs
            alert_ids: List of alert IDs
        """
        self.persistence.mark_reports_synced(report_ids)
        self.persistence.mark_alerts_synced(alert_ids)
    
    def get_service_stats(self) -> ServiceStats:
        """
        Get comprehensive service statistics.
        
        Returns:
            ServiceStats with persistence and algorithm metrics
        """
        persistence_stats = self.persistence.get_stats()
        
        algorithm_stats = {
            "symptom_count": self.trie.get_word_count(),
            "location_count": len(self.network),
            "cluster_count": self.clusters.get_num_clusters(),
            "pending_alerts": len(self.triage),
            "critical_alerts": self.triage.get_critical_count(),
        }
        
        return ServiceStats(
            persistence_stats=persistence_stats,
            algorithm_stats=algorithm_stats,
        )
    
    # -------------------------------------------------------------------------
    # Health Check
    # -------------------------------------------------------------------------
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check on all service components.
        
        Returns:
            Dictionary with health status of each component
        """
        return {
            "status": "healthy",
            "components": {
                "trie": self.trie.get_word_count() > 0,
                "network": len(self.network) > 0,
                "clusters": len(self.clusters) > 0,
                "persistence": True,
            },
            "timestamp": datetime.utcnow().isoformat(),
        }


# ============================================================================
# Service Factory
# ============================================================================

def get_ldsn_service() -> LDSNService:
    """
    Create and return the LDSN Service instance.
    
    This is the recommended way to access the service layer.
    
    Returns:
        Configured LDSNService instance
    """
    return LDSNService()


# ============================================================================
# Presentation Layer Examples
# ============================================================================

# Example usage for CLI
def cli_example():
    """Example of CLI usage."""
    service = get_ldsn_service()
    
    # Autocomplete symptoms
    result = service.autocomplete_symptoms("pes")
    print(f"Symptoms matching 'pes': {result.matches}")
    
    # Calculate route
    route = service.calculate_route("Ngaoundere", "Maroua", is_rainy_season=True)
    print(f"Route: {route.path}")
    print(f"Weight: {route.total_weight}")
    
    # Submit alert
    alert = service.submit_alert(
        disease_name="anthrax",
        location="Maroua",
        reporter_id="VET-001",
    )
    print(f"Alert Priority: {alert.priority_name}")


# Example usage for API
def api_example():
    """Example of API endpoint usage."""
    service = get_ldsn_service()
    
    return {
        "symptoms": service.autocomplete_symptoms("highly"),
        "route": service.calculate_route("Bafoussam", "Yaounde"),
        "clusters": service.detect_clusters(),
        "health": service.health_check(),
    }


if __name__ == "__main__":
    print("LDSN Service Layer initialized.")
    print("Use get_ldsn_service() to access the service gateway.")

