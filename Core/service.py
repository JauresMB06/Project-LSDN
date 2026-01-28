
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
    AlertTriageEngine,
    AlertItem,
    Alert,
    PriorityLevel,
    CAMEROON_PRIORITY_MATRIX,
)
from .segment_tree import MortalitySegmentTree, CameroonMortalityTracker

# Persistence Layer - Using SQLAlchemy (unified persistence)
from .database_manager import (
    DatabaseManager,
    get_database_manager,
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
    def __init__(self, alert: AlertItem, action_taken: str, alert_id: int = None):
        self.alert = alert
        self.action_taken = action_taken
        self.priority_level = alert.priority_level
        self.priority_name = PriorityLevel(alert.priority_level).name
        self.alert_id = alert_id
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
# Alert Manager (Cluster-Aware)
# ============================================================================

class AlertManager:
    """
    Manages alerts with cluster awareness for priority escalation.
    
    When multiple reports of the same disease are submitted in the same
    Union-Find cluster, the priority level is escalated to ensure
    faster response.
    
    Service Layer Component:
        - Integrates Priority Queue with Union-Find
        - Applies cluster-based priority escalation
        - Coordinates with Persistence Layer for storage
    """
    
    def __init__(
        self,
        triage: AlertTriageEngine,
        clusters: OutbreakCluster,
        db: DatabaseManager,
    ):
        self.triage = triage
        self.clusters = clusters
        self.db = db
        # Track report counts per (disease, cluster) for escalation
        self._report_counts: Dict[str, int] = {}
    
    def _get_cluster_key(self, disease: str, location: str) -> str:
        """Generate a unique key for tracking disease reports per cluster."""
        try:
            cluster_id = self.clusters.find(location)
        except KeyError:
            # Add location to Union-Find as a new singleton cluster
            self.clusters.add_location(location)
            cluster_id = location
        return f"{disease.lower()}:{cluster_id}"
    
    def submit_report(
        self,
        disease: str,
        location: str,
        reporter_id: str,
        mortality: Optional[int] = None,
    ) -> AlertResult:
        """
        Submit a disease report and automatically create an alert.
        
        Args:
            disease: Name of the disease
            location: Location of the report
            reporter_id: ID of the reporter
            mortality: Number of deaths (optional)
            
        Returns:
            AlertResult with alert details
        """
        # Get cluster boost for priority escalation
        cluster_key = self._get_cluster_key(disease, location)
        previous_count = self._report_counts.get(cluster_key, 0)
        cluster_boost = previous_count
        
        # Update report count
        self._report_counts[cluster_key] = previous_count + 1
        
        # Push to priority queue with cluster awareness
        alert = self.triage.push_alert(
            disease_name=disease,
            location=location,
            reporter_id=reporter_id,
            cluster_boost=cluster_boost,
            details={"mortality_count": mortality, "cluster_boost": cluster_boost}
        )
        
        # Persist the alert using SQLAlchemy
        alert_id = self.db.save_alert(
            disease_name=alert.disease_name,
            location=alert.location,
            priority_level=alert.priority_level,
            reporter_id=alert.reporter_id,
            details={"mortality_count": mortality, "cluster_boost": cluster_boost},
        )
        
        # Determine action based on priority
        if alert.is_critical():
            action = "IMMEDIATE_RESPONSE_REQUIRED"
        elif alert.priority_level == PriorityLevel.P2_HIGH:
            action = "URGENT_RESPONSE_SCHEDULED"
        else:
            action = "QUEUED_FOR_INVESTIGATION"
        
        return AlertResult(alert=alert, action_taken=action, alert_id=alert_id)
    
    def get_pending_alerts(self) -> List[AlertItem]:
        """Get all pending alerts sorted by priority."""
        return self.triage.get_all_alerts()
    
    def get_critical_count(self) -> int:
        """Get count of P1 critical alerts."""
        return self.triage.get_critical_count()


# ============================================================================
# LDSN Service Gateway
# ============================================================================

class LDSNService:
    """
    Primary Service Gateway for the Livestock Disease Surveillance Network.
    
    This class implements the 3-Tier Architecture by:
        1. Providing a clean API to the Presentation Layer (CLI/Web)
        2. Orchestrating core algorithmic components
        3. Managing data persistence via SQLAlchemy
    
    All algorithmic complexity is hidden behind this interface.
    
    Attributes:
        trie: SymptomTrie for autocomplete (O(L))
        network: TranshumanceGraph for routing (O(E log V))
        clusters: OutbreakCluster for cluster detection (O(α(n)))
        triage: AlertTriageEngine for priority management (O(log n))
        mortality: MortalitySegmentTree for tracking (O(log n))
        db: DatabaseManager for persistence (SQLAlchemy)
        alert_manager: AlertManager for cluster-aware alert handling
    
    Service Layer Responsibilities:
        - Data standardization using Trie
        - Cluster detection using Union-Find
        - Route optimization using Dijkstra's
        - Priority triage using Max-Heap
        - Temporal analytics using Segment Tree
        - Persistence via SQLAlchemy
    
    Author: LDSN Development Team
    Version: 3.0.0
    """
    
    def __init__(
        self,
        db: Optional[DatabaseManager] = None,
    ) -> None:
        """
        Initialize the LDSN Service with lazy loading.

        Heavy components are loaded only when first accessed to improve startup time.

        Args:
            db: Optional custom database manager (uses SQLAlchemy)
        """
        # Initialize Persistence (SQLAlchemy) - lightweight, keep eager
        self.db = db or get_database_manager()

        # Cache for loaded disease terms
        self._disease_cache: Optional[List[str]] = None

        # Lazy-loaded components (initialized as None)
        self._trie: Optional[SymptomTrie] = None
        self._network: Optional[TranshumanceGraph] = None
        self._clusters: Optional[OutbreakCluster] = None
        self._triage: Optional[AlertTriageEngine] = None
        self._mortality: Optional[CameroonMortalityTracker] = None
        self._alert_manager: Optional[AlertManager] = None

    # -------------------------------------------------------------------------
    # Lazy Loading Properties
    # -------------------------------------------------------------------------

    @property
    def trie(self) -> SymptomTrie:
        """Lazy-loaded SymptomTrie for disease autocomplete."""
        if self._trie is None:
            self._trie = get_trained_trie()
        return self._trie

    @property
    def network(self) -> TranshumanceGraph:
        """Lazy-loaded TranshumanceGraph for route calculations."""
        if self._network is None:
            self._network = get_cameroon_network()
        return self._network

    @property
    def clusters(self) -> OutbreakCluster:
        """Lazy-loaded OutbreakCluster for epidemiological cluster detection."""
        if self._clusters is None:
            self._clusters = create_cameroon_outbreak_clusters()
        return self._clusters

    @property
    def triage(self) -> AlertTriageEngine:
        """Lazy-loaded AlertTriageEngine for priority queue management."""
        if self._triage is None:
            self._triage = AlertTriageEngine()
        return self._triage

    @property
    def mortality(self) -> CameroonMortalityTracker:
        """Lazy-loaded CameroonMortalityTracker for seasonal mortality statistics."""
        if self._mortality is None:
            self._mortality = CameroonMortalityTracker()
        return self._mortality

    @property
    def alert_manager(self) -> AlertManager:
        """Lazy-loaded AlertManager for cluster-aware alert processing."""
        if self._alert_manager is None:
            self._alert_manager = AlertManager(
                triage=self.triage,
                clusters=self.clusters,
                db=self.db,
            )
        return self._alert_manager

    # -------------------------------------------------------------------------
    # Symptom Autocomplete Services (Trie)
    # -------------------------------------------------------------------------
    
    def autocomplete_symptoms(self, prefix: str) -> SymptomResult:
        """
        Autocomplete disease symptoms using the Trie.

        Complexity: O(L) where L is the prefix length

        Args:
            prefix: The prefix to search for

        Returns:
            SymptomResult with matching terms

        Notes:
            If prefix is empty, returns top priority diseases from Cameroon context
        """
        if not prefix or not prefix.strip():
            # Return top priority diseases for empty prefix
            matches = CAMEROON_PRIORITY_DISEASES[:20]  # Limit to 20 suggestions
            return SymptomResult(matches=matches, prefix="")

        matches = self.trie.autocomplete(prefix.strip().lower())
        return SymptomResult(matches=matches, prefix=prefix)
    
    def search_symptoms(self, term: str) -> bool:
        """
        Search for an exact symptom term.
        
        Complexity: O(L)
        
        Args:
            term: Term to search for
            
        Returns:
            True if term exists, False otherwise
        """
        return self.trie.search(term.lower())
    
    def get_all_symptoms(self) -> List[str]:
        """Get all loaded symptom terms."""
        if self._disease_cache is None:
            self._disease_cache = CAMEROON_PRIORITY_DISEASES
        return self._disease_cache
    
    # -------------------------------------------------------------------------
    # Route Calculation Services (Dijkstra's)
    # -------------------------------------------------------------------------
    
    def calculate_route(
        self,
        start: str,
        end: str,
        is_rainy_season: bool = False,
    ) -> RouteResult:
        """
        Calculate the safest transhumance route.
        
        Complexity: O(E log V) using Dijkstra's algorithm
        
        Applies 2.5× penalty for unpaved Adamawa tracks during Duumol (rainy season).
        
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
    
    def get_zvscc_stations(self) -> List[str]:
        """Get all ZVSCC stations."""
        return self.network.get_zvscc_locations()
    
    # -------------------------------------------------------------------------
    # Cluster Detection Services (Union-Find)
    # -------------------------------------------------------------------------
    
    def detect_clusters(self) -> List[ClusterResult]:
        """
        Detect all current outbreak clusters.
        
        Complexity: O(α(n)) for Union-Find operations
        
        Returns:
            List of ClusterResult objects
        """
        clusters = self.clusters.get_clusters()
        results = []
        
        for i, cluster in enumerate(clusters):
            results.append(
                ClusterResult(
                    cluster_id=f"CLUSTER-{i+1:03d}",
                    locations=sorted(list(cluster)),
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
        
        Complexity: O(α(n))
        
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
        
        Complexity: O(α(n))
        
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
    
    def get_cluster_members(self, location: str) -> List[str]:
        """
        Get all members of the cluster containing a location.
        
        Args:
            location: Location to check
            
        Returns:
            List of all locations in the cluster
        """
        return sorted(list(self.clusters.get_cluster(location)))
    
    # -------------------------------------------------------------------------
    # Alert Triage Services (Priority Queue)
    # -------------------------------------------------------------------------
    
    def submit_alert(
        self,
        disease_name: str,
        location: str,
        reporter_id: str,
        details: Optional[Dict] = None,
    ) -> AlertResult:
        """
        Submit a disease alert for triage with cluster awareness.
        
        Automatically prioritizes based on Cameroon Priority Matrix.
        Applies priority escalation when multiple reports exist in the same cluster.
        
        Args:
            disease_name: Name of the suspected disease
            location: Location of the alert
            reporter_id: ID of the reporting officer
            details: Additional details
            
        Returns:
            AlertResult with priority and action taken
        """
        return self.alert_manager.submit_report(
            disease=disease_name,
            location=location,
            reporter_id=reporter_id,
        )
    
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
    
    def get_critical_alerts(self) -> List[AlertItem]:
        """Get all P1 critical alerts."""
        return self.triage.get_critical_alerts()
    
    def get_critical_alert_count(self) -> int:
        """Get count of P1 critical alerts."""
        return self.triage.get_critical_count()
    
    # -------------------------------------------------------------------------
    # Mortality Tracking Services (Segment Tree)
    # -------------------------------------------------------------------------
    
    def record_mortality(self, day: int, count: int, location: Optional[str] = None) -> None:
        """
        Record mortality data for a specific day.
        
        Complexity: O(log n)
        
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

    def get_species_mortality_data(self) -> List[Dict[str, Any]]:
        """
        Get species-specific mortality data from Segment Tree.

        Returns:
            List of dictionaries with species mortality data
        """
        return self.mortality.get_all_species_data()
    
    # -------------------------------------------------------------------------
    # Persistence Services (SQLAlchemy)
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
        return self.db.save_report(
            report_type=report_type,
            location=location,
            reporter_id=reporter_id,
            **kwargs,
        )
    
    def get_unsynced_reports(self, limit: int = 100) -> List[Dict]:
        """
        Get reports that haven't been synced.
        
        Args:
            limit: Maximum number of reports to retrieve
            
        Returns:
            List of unsynced report dictionaries
        """
        reports = self.db.get_unsynced_reports(limit)
        return [r.to_dict() for r in reports]
    
    def get_unsynced_alerts(self, limit: int = 100) -> List[Dict]:
        """
        Get alerts that haven't been synced.
        
        Args:
            limit: Maximum number of alerts to retrieve
            
        Returns:
            List of unsynced alert dictionaries
        """
        alerts = self.db.get_unsynced_alerts(limit)
        return [a.to_dict() for a in alerts]
    
    def mark_reports_synced(self, report_ids: List[int]) -> None:
        """
        Mark reports as successfully synced.
        
        Args:
            report_ids: List of report IDs
        """
        self.db.mark_reports_synced(report_ids)
    
    def mark_alerts_synced(self, alert_ids: List[int]) -> None:
        """
        Mark alerts as successfully synced.
        
        Args:
            alert_ids: List of alert IDs
        """
        self.db.mark_alerts_synced(alert_ids)
    
    def get_service_stats(self) -> ServiceStats:
        """
        Get comprehensive service statistics.
        
        Returns:
            ServiceStats with persistence and algorithm metrics
        """
        persistence_stats = self.db.get_stats()
        
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
                "database": self.db is not None,
            },
            "zvscc_stations": len(self.get_zvscc_stations()),
            "timestamp": datetime.utcnow().isoformat(),
        }


# ============================================================================
# Service Factory
# ============================================================================

# Global service instance (lazy initialization)
_service_instance: Optional[LDSNService] = None


def get_ldsn_service() -> LDSNService:
    """
    Create and return the LDSN Service instance.
    
    This is the recommended way to access the service layer.
    Uses singleton pattern for efficiency.
    
    Returns:
        Configured LDSNService instance
    
    Usage:
        >>> from Core.service import get_ldsn_service
        >>> service = get_ldsn_service()
        >>> route = service.calculate_route("Ngaoundéré", "Maroua", is_rainy_season=True)
    """
    global _service_instance
    if _service_instance is None:
        _service_instance = LDSNService()
    return _service_instance


def reset_service() -> None:
    """Reset the service instance (useful for testing)."""
    global _service_instance
    _service_instance = None


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
    route = service.calculate_route("Ngaoundéré", "Maroua", is_rainy_season=True)
    print(f"Route: {route.path}")
    print(f"Weight: {route.total_weight}")
    
    # Submit alert with cluster awareness
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
        "route": service.calculate_route("Bafoussam", "Yaoundé"),
        "clusters": service.detect_clusters(),
        "health": service.health_check(),
    }


if __name__ == "__main__":
    print("LDSN Service Layer v3.0.0")
    print("Use get_ldsn_service() to access the service gateway.")
    print("\nExample: Calculating route during Duumol (rainy season)...")
    
    service = get_ldsn_service()
    route = service.calculate_route("Ngaoundéré", "Maroua", is_rainy_season=True)
    print(f"Route: {' → '.join(route.path)}")
    print(f"Total Weight: {route.total_weight:.2f}")
    print(f"Season: {route.season_name}")

