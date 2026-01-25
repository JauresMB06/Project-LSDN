from typing import Dict, List, Optional, Set


class UnionFindConfig:
    """Configuration model for Union-Find initialization."""
    def __init__(self, locations: List[str], validate_locations: bool = True):
        if not locations:
            raise ValueError("Locations list cannot be empty")
        if not isinstance(locations, list):
            raise ValueError("Locations must be a list")
        
        self.locations = locations
        self.validate_locations = validate_locations


class OutbreakCluster:
    """
    Disjoint Set Union (DSU) for Epidemiological Cluster Detection.
    
    Complexity:
        - Find: O(α(n)) - inverse Ackermann function (near-constant)
        - Union: O(α(n)) - with Union by Rank
        - Connected: O(α(n))
    
    Uses Path Compression and Union by Rank optimizations.
    
    This class implements the Data Layer for the 3-Tier Architecture:
        - Receives cluster requests from Service Layer (LDSNService)
        - Returns cluster membership and connections
        - Hides DSU algorithmic complexity
    
    Attributes:
        parent: Maps each element to its parent
        rank: Used for Union by Rank
        cluster_size: Tracks size of each cluster
        _num_clusters: Current number of clusters
    
    Author: LDSN Development Team
    Version: 3.0.0
    """
    
    # Class-level constants
    MIN_LOCATIONS = 1
    MAX_LOCATIONS = 1_000_000  # 1 million locations
    
    def __init__(self, locations: Optional[List[str]] = None) -> None:
        """
        Initialize the Union-Find data structure.
        
        Args:
            locations: Optional list of initial locations/elements
            
        Raises:
            ValueError: If locations list is empty or contains duplicates
        """
        self.parent: Dict[str, str] = {}
        self.rank: Dict[str, int] = {}
        self.cluster_size: Dict[str, int] = {}
        self._num_clusters: int = 0
        
        if locations:
            self.initialize_locations(locations)
    
    def initialize_locations(self, locations: List[str]) -> None:
        """
        Initialize the data structure with a list of locations.
        
        Args:
            locations: List of location identifiers
            
        Raises:
            ValueError: If locations list is invalid
        """
        if not locations:
            raise ValueError("Locations list cannot be empty")
        
        if len(locations) > self.MAX_LOCATIONS:
            raise ValueError(
                f"Locations count ({len(locations)}) exceeds maximum ({self.MAX_LOCATIONS})"
            )
        
        seen: Set[str] = set()
        for loc in locations:
            if loc in seen:
                raise ValueError(f"Duplicate location found: {loc}")
            seen.add(loc)
            self.parent[loc] = loc
            self.rank[loc] = 0
            self.cluster_size[loc] = 1
            self._num_clusters += 1
    
    def add_location(self, location: str) -> None:
        """
        Add a new location to the data structure.
        
        Args:
            location: New location identifier to add
            
        Raises:
            ValueError: If location already exists
        """
        if location in self.parent:
            raise ValueError(f"Location already exists: {location}")
        
        self.parent[location] = location
        self.rank[location] = 0
        self.cluster_size[location] = 1
        self._num_clusters += 1
    
    def find(self, location: str) -> str:
        """
        Finds the root of the cluster with Path Compression.
        
        Args:
            location: The location to find the root for
            
        Returns:
            The root location of the cluster
            
        Raises:
            KeyError: If location is not in the data structure
        """
        if location not in self.parent:
            raise KeyError(f"Location not found: {location}")
        
        # Path compression: make every node point directly to root
        # This gives O(α(n)) amortized time complexity
        if self.parent[location] != location:
            self.parent[location] = self.find(self.parent[location])
        
        return self.parent[location]
    
    def union(self, loc_a: str, loc_b: str) -> bool:
        """
        Merges two clusters based on shared resources.
        
        Used to detect epidemiological connections (e.g., shared water points,
        common markets, transhumance corridors).
        
        Args:
            loc_a: First location
            loc_b: Second location
            
        Returns:
            True if clusters were merged, False if already in same cluster
            
        Raises:
            KeyError: If either location is not in the data structure
        """
        root_a = self.find(loc_a)
        root_b = self.find(loc_b)
        
        if root_a == root_b:
            return False  # Already in the same cluster
        
        # Union by Rank - attach shorter tree to taller tree
        if self.rank[root_a] < self.rank[root_b]:
            self.parent[root_a] = root_b
            self.cluster_size[root_b] += self.cluster_size[root_a]
        elif self.rank[root_a] > self.rank[root_b]:
            self.parent[root_b] = root_a
            self.cluster_size[root_a] += self.cluster_size[root_b]
        else:
            # Equal rank - arbitrarily choose one and increment rank
            self.parent[root_a] = root_b
            self.rank[root_b] += 1
            self.cluster_size[root_b] += self.cluster_size[root_a]
        
        self._num_clusters -= 1
        return True
    
    def connected(self, loc_a: str, loc_b: str) -> bool:
        """
        Check if two locations are in the same cluster.
        
        Args:
            loc_a: First location
            loc_b: Second location
            
        Returns:
            True if locations are in the same cluster, False otherwise
        """
        return self.find(loc_a) == self.find(loc_b)
    
    def get_cluster(self, location: str) -> Set[str]:
        """
        Get all locations in the same cluster as the given location.
        
        Args:
            location: The location to find cluster for
            
        Returns:
            Set of all locations in the cluster
        """
        root = self.find(location)
        cluster = set()
        for loc in self.parent.keys():
            if self.find(loc) == root:
                cluster.add(loc)
        return cluster
    
    def get_clusters(self) -> List[Set[str]]:
        """
        Get all clusters in the data structure.
        
        Returns:
            List of sets, each representing a cluster
        """
        cluster_map: Dict[str, Set[str]] = {}
        for loc in self.parent.keys():
            root = self.find(loc)
            if root not in cluster_map:
                cluster_map[root] = set()
            cluster_map[root].add(loc)
        return list(cluster_map.values())
    
    def get_cluster_size(self, location: str) -> int:
        """
        Get the size of the cluster containing the location.
        
        Args:
            location: The location to check
            
        Returns:
            Number of locations in the cluster
        """
        root = self.find(location)
        return self.cluster_size[root]
    
    def get_num_clusters(self) -> int:
        """
        Get the current number of clusters.
        
        Returns:
            Number of clusters
        """
        return self._num_clusters
    
    def get_all_locations(self) -> List[str]:
        """
        Get all locations in the data structure.
        
        Returns:
            List of all location names
        """
        return list(self.parent.keys())
    
    def __len__(self) -> int:
        """Return the number of elements in the data structure."""
        return len(self.parent)
    
    def __contains__(self, location: str) -> bool:
        """Check if a location exists in the data structure."""
        return location in self.parent
    
    def __repr__(self) -> str:
        """Return string representation."""
        return f"OutbreakCluster(locations={len(self)}, clusters={self._num_clusters})"


# ============================================================================
# Cameroon Cluster Detection Utilities
# ============================================================================

# Regional connections for Cameroon
# These represent epidemiological links between regions
# Location names use proper accents (Ngaoundéré, Mbé, Yaoundé)

ADAMAWA_CONNECTIONS = [
    ("Ngaoundéré", "Tibati"),
    ("Ngaoundéré", "Mbé"),
    ("Tibati", "Mbé"),
]

FAR_NORTH_CONNECTIONS = [
    ("Maroua", "Kousseri"),
    ("Maroua", "Mora"),
    ("Kousseri", "Mora"),
    ("Mora", "Mindif"),
    ("Logone Floodplain", "Mindif"),
    ("Maroua", "Logone Floodplain"),
]

WEST_REGION_CONNECTIONS = [
    ("Bafoussam", "Bamenda"),
    ("Bafoussam", "Dschang"),
    ("Bamenda", "Dschang"),
    ("Bafoussam", "Bamendjou"),
]

CENTRE_CONNECTIONS = [
    ("Yaoundé", "Edea"),
]

CROSS_REGION_CONNECTIONS = [
    ("Ngaoundéré", "Maroua"),    # Adamawa to Far North
    ("Ngaoundéré", "Garoua"),    # Adamawa to North
    ("Bafoussam", "Yaoundé"),    # West to Centre
    ("Garoua", "Maroua"),        # North to Far North
    ("Bertoua", "Yaoundé"),      # East to Centre
    ("Bertoua", "Ngaoundéré"),   # East to Adamawa
]


def create_cameroon_outbreak_clusters(
    initial_locations: Optional[List[str]] = None
) -> OutbreakCluster:
    """
    Create a Union-Find structure pre-configured for Cameroon regions.
    
    This factory function creates an OutbreakCluster with:
        - All major livestock hub locations
        - Regional epidemiological connections
        - Cross-regional transhumance corridors
    
    Args:
        initial_locations: Optional list of additional locations to include
        
    Returns:
        Configured OutbreakCluster instance
    
    Service Layer Integration:
        - Used by LDSNService.__init__()
        - Provides cluster detection for alert priority escalation
    
    Author: LDSN Development Team
    Version: 3.0.0
    """
    # Default locations if none provided
    if initial_locations is None:
        initial_locations = []
    
    # Add all known Cameroon locations with proper accents
    locations = set(initial_locations)
    
    # Adamawa Region
    locations.update(["Ngaoundéré", "Tibati", "Mbé"])
    
    # Far North Region
    locations.update(["Maroua", "Kousseri", "Mora", "Mindif", "Logone Floodplain", "Maga"])
    
    # West Region
    locations.update(["Bafoussam", "Dschang", "Bamendjou"])
    
    # Northwest Region
    locations.update(["Bamenda"])
    
    # Centre Region
    locations.update(["Yaoundé", "Edea"])
    
    # North Region
    locations.update(["Garoua"])
    
    # East Region
    locations.update(["Bertoua"])
    
    # Create the cluster
    cluster = OutbreakCluster(list(locations))
    
    # Add regional connections
    for loc_a, loc_b in (
        ADAMAWA_CONNECTIONS + 
        FAR_NORTH_CONNECTIONS + 
        WEST_REGION_CONNECTIONS +
        CENTRE_CONNECTIONS +
        CROSS_REGION_CONNECTIONS
    ):
        cluster.union(loc_a, loc_b)
    
    return cluster


# ============================================================================
# Cluster Analysis Utilities
# ============================================================================

def get_cluster_risk_score(
    cluster: OutbreakCluster,
    risk_data: Dict[str, float]
) -> float:
    """
    Calculate the total risk score for a cluster.
    
    Args:
        cluster: OutbreakCluster instance
        risk_data: Dict mapping locations to risk scores
        
    Returns:
        Total risk score for the cluster
    """
    total_risk = 0.0
    for location in cluster.get_all_locations():
        total_risk += risk_data.get(location, 0.0)
    return total_risk


def find_connected_zvscc_stations(
    cluster: OutbreakCluster,
    location: str
) -> List[str]:
    """
    Find all ZVSCC stations connected to a location.
    
    Used for emergency response routing.
    
    Args:
        cluster: OutbreakCluster instance
        location: Starting location
        
    Returns:
        List of connected ZVSCC station names
    """
    connected_cluster = cluster.get_cluster(location)
    zvscc_stations = []
    
    # ZVSCC stations (hardcoded for now, could be from config)
    zvscc_locations = {
        "Ngaoundéré", "Maroua", "Kousseri", "Yaoundé",
        "Bafoussam", "Bamenda", "Dschang", "Garoua", "Bertoua"
    }
    
    for loc in connected_cluster:
        if loc in zvscc_locations:
            zvscc_stations.append(loc)
    
    return zvscc_stations


# ============================================================================
# Validation Models
# ============================================================================

class ClusterConnection:
    """Validation model for cluster connection data."""
    def __init__(self, location_a: str, location_b: str):
        if not location_a or not location_a.strip():
            raise ValueError("Location A cannot be empty")
        if not location_b or not location_b.strip():
            raise ValueError("Location B cannot be empty")

        self.location_a = location_a.strip()
        self.location_b = location_b.strip()


def validate_cluster_connection(entry: dict) -> ClusterConnection:
    """
    Validate a cluster connection dictionary using native validation.

    Args:
        entry: Dictionary containing connection data

    Returns:
        Validated ClusterConnection object

    Raises:
        ValueError: If entry fails validation
    """
    return ClusterConnection(**entry)


def detect_outbreak_clusters(
    connections: List[ClusterConnection],
    locations: List[str]
) -> OutbreakCluster:
    """
    Detect outbreak clusters from connection data.
    
    Args:
        connections: List of validated connections
        locations: List of all locations
        
    Returns:
        OutbreakCluster with all connections applied
    """
    cluster = OutbreakCluster(locations)
    for conn in connections:
        cluster.union(conn.location_a, conn.location_b)
    return cluster


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("LDSN Cameroon - Outbreak Cluster Detection Demo")
    print("=" * 60)
    
    # Create Cameroon outbreak clusters
    clusters = create_cameroon_outbreak_clusters()
    
    print(f"\n✓ Cluster system initialized")
    print(f"✓ Total locations: {len(clusters)}")
    print(f"✓ Active clusters: {clusters.get_num_clusters()}")
    
    # Display clusters
    print("\n--- Current Outbreak Clusters ---")
    all_clusters = clusters.get_clusters()
    for i, cluster in enumerate(all_clusters, 1):
        print(f"Cluster {i}: {sorted(cluster)}")
    
    # Check connectivity
    print("\n--- Epidemiological Connections ---")
    print(f"Ngaoundéré ↔ Maroua: {clusters.connected('Ngaoundéré', 'Maroua')}")
    print(f"Bafoussam ↔ Yaoundé: {clusters.connected('Bafoussam', 'Yaoundé')}")
    print(f"Tibati ↔ Mbé: {clusters.connected('Tibati', 'Mbé')}")
    
    # Cluster size
    print("\n--- Cluster Sizes ---")
    print(f"Ngaoundéré cluster: {clusters.get_cluster_size('Ngaoundéré')} locations")
    print(f"Maroua cluster: {clusters.get_cluster_size('Maroua')} locations")
    print(f"Bafoussam cluster: {clusters.get_cluster_size('Bafoussam')} locations")

