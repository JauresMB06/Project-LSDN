"""
Livestock Disease Surveillance Network (LDSN) - Union-Find (Disjoint Set)

Outbreak cluster detection using Disjoint Set Union (DSU) data structure.
Implements Path Compression and Union by Rank for O(α(n)) near-constant time.

Designed for epidemiological cluster detection across Cameroon's regions.

Author: LDSN Development Team
Version: 2.0.0
"""

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
    
    Attributes:
        parent: Maps each element to its parent
        rank: Used for Union by Rank
        cluster_size: Tracks size of each cluster
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
        
        # Union by Rank
        if self.rank[root_a] < self.rank[root_b]:
            self.parent[root_a] = root_b
            self.cluster_size[root_b] += self.cluster_size[root_a]
        elif self.rank[root_a] > self.rank[root_b]:
            self.parent[root_b] = root_a
            self.cluster_size[root_a] += self.cluster_size[root_b]
        else:
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
    
    def __len__(self) -> int:
        """Return the number of elements in the data structure."""
        return len(self.parent)
    
    def __contains__(self, location: str) -> bool:
        """Check if a location exists in the data structure."""
        return location in self.parent


# ============================================================================
# Cameroon Cluster Detection Utilities
# ============================================================================

# Regional connections for Cameroon
# These represent epidemiological links between regions

ADAMawa_CONNECTIONS = [
    ("Ngaoundere", "Tibati"),
    ("Ngaoundere", "Mbere"),
    ("Tibati", "Mbere"),
]

FAR_NORTH_CONNECTIONS = [
    ("Maroua", "Kousseri"),
    ("Maroua", "Mora"),
    ("Kousseri", "Mora"),
    ("Mora", "Mindif"),
]

WEST_REGION_CONNECTIONS = [
    ("Bafoussam", "Bamenda"),
    ("Bafoussam", "Dschang"),
    ("Bamenda", "Dschang"),
]

CROSS_REGION_CONNECTIONS = [
    ("Ngaoundere", "Maroua"),  # Adamawa to Far North
    ("Bafoussam", "Yaounde"),  # West to Centre
]


def create_cameroon_outbreak_clusters(
    initial_locations: Optional[List[str]] = None
) -> OutbreakCluster:
    """
    Create a Union-Find structure pre-configured for Cameroon regions.
    
    Args:
        initial_locations: Optional list of additional locations to include
        
    Returns:
        Configured OutbreakCluster instance
    """
    # Default locations if none provided
    if initial_locations is None:
        initial_locations = []
    
    # Add all known Cameroon locations
    locations = set(initial_locations)
    locations.update(["Ngaoundere", "Maroua", "Yaounde", "Bafoussam", "Bamenda"])
    locations.update(["Tibati", "Mbere", "Kousseri", "Mora", "Mindif", "Dschang"])
    
    cluster = OutbreakCluster(list(locations))
    
    # Add regional connections
    for loc_a, loc_b in (
        ADAMawa_CONNECTIONS + 
        FAR_NORTH_CONNECTIONS + 
        WEST_REGION_CONNECTIONS + 
        CROSS_REGION_CONNECTIONS
    ):
        cluster.union(loc_a, loc_b)
    
    return cluster


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

