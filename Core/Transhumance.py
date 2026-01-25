
import heapq
import math
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class SeasonType(Enum):
    """Season types for Cameroon transhumance routing."""
    DRY = "dry"
    RAINY = "rainy"  # Duumol: July-September
    TRANSITION = "transition"


# ============================================================================
# Cameroon Seasonal Configuration
# ============================================================================

# Cameroon Ministry of Transport and MINEPIA
# Seasonal multipliers for unpaved tracks

SEASONAL_MULTIPLIERS: Dict[SeasonType, float] = {
    SeasonType.DRY: 1.0,          # Standard weights
    SeasonType.RAINY: 2.5,        # 2.5× penalty for duumol (rainy season)
    SeasonType.TRANSITION: 1.2,   # Light penalty during transition
}

# Regional risk factors
REGIONAL_RISK_FACTORS: Dict[str, float] = {
    "Adamawa": 1.0,        # Base region for transhumance
    "Far North": 1.2,      # Higher risk due to border activity
    "West": 0.8,           # Lower risk, better infrastructure
    "Centre": 1.0,         # Standard risk
    "North": 1.1,          # Moderate risk
    "Northwest": 0.9,      # Good infrastructure
    "East": 1.0,           # Standard risk
    "South": 0.9,          # Lower risk
}

# Adamawa unpaved track segments (high impact during rainy season)
ADAMAWA_UNPAVED_TRACKS: List[Tuple[str, str]] = [
    ("Ngaoundéré", "Tibati"),
    ("Ngaoundéré", "Mbé"),
    ("Tibati", "Mbé"),
]


@dataclass(order=True)
class RouteSegment:
    """
    Represents a segment of a transhumance route.
    
    Attributes:
        origin: Starting location
        destination: Ending location
        distance_km: Distance in kilometers
        is_paved: Whether track is paved
        region: Administrative region
        risk_score: Outbreak risk score
    """
    origin: str
    destination: str
    distance_km: float
    is_paved: bool = False
    region: str = "Adamawa"
    risk_score: float = 0.0
    
    def effective_weight(self, season: SeasonType = SeasonType.DRY) -> float:
        """
        Calculate effective weight based on season and track conditions.
        
        Args:
            season: Current season type
            
        Returns:
            Effective weight for routing
        """
        base_weight = self.distance_km
        
        # Apply seasonal multiplier
        multiplier = SEASONAL_MULTIPLIERS[season]
        
        # Additional penalty for unpaved tracks in Adamawa
        if not self.is_paved and self.region == "Adamawa":
            multiplier *= 1.5
        
        return base_weight * multiplier + self.risk_score


class TranshumanceGraph:
    """
    Weighted Directed Graph for Transhumance Route Optimization.
    
    Complexity: O(E log V) using Dijkstra's algorithm with Min-Heap.
    
    This class implements the Data Layer for the 3-Tier Architecture:
        - Receives route requests from Service Layer (LDSNService)
        - Returns path and weight calculations
        - Hides algorithmic complexity from Presentation Layer
    
    Attributes:
        adj_list: Adjacency list mapping nodes to edges
        node_data: Metadata for each node (location info)
        edge_data: Metadata for each edge (track info)
    
    Author: LDSN Development Team
    Version: 3.0.0
    """
    
    def __init__(self) -> None:
        """
        Initialize an empty transhumance graph.
        
        Data Layer Initialization:
            - adj_list: Dict[str, List[Tuple[str, float]]]
            - node_data: Dict[str, Dict]
            - edge_data: Dict[Tuple[str, str], Dict]
        """
        self.adj_list: Dict[str, List[Tuple[str, float]]] = {}
        self.node_data: Dict[str, Dict] = {}
        self.edge_data: Dict[Tuple[str, str], Dict] = {}
    
    def add_location(
        self,
        name: str,
        region: str = "Unknown",
        is_zvscc: bool = False,
        risk_score: float = 0.0
    ) -> None:
        """
        Add a vertex (location) to the graph.
        
        Args:
            name: Location name (with proper accents)
            region: Administrative region
            is_zvscc: Whether this is a ZVSCC station
            risk_score: Base risk score for the location
        
        Data Layer Operation:
            - Updates adj_list with empty edge list
            - Stores node metadata in node_data
        """
        if name not in self.adj_list:
            self.adj_list[name] = []
            self.node_data[name] = {
                "region": region,
                "is_zvscc": is_zvscc,
                "risk_score": risk_score,
            }
    
    def add_corridor(
        self,
        origin: str,
        destination: str,
        distance_km: float,
        is_paved: bool = False,
        track_type: str = "unpaved"
    ) -> None:
        """
        Add a directed transhumance track or trade corridor.
        
        Args:
            origin: Starting location
            destination: Ending location
            distance_km: Distance in kilometers
            is_paved: Whether the track is paved
            track_type: Type of track (paved, unpaved, highway)
        
        Data Layer Operation:
            - Adds edge to adj_list
            - Stores edge metadata in edge_data
        """
        # Ensure nodes exist
        for name in [origin, destination]:
            if name not in self.adj_list:
                self.add_location(name)
        
        # Add edge
        self.adj_list[origin].append((destination, distance_km))
        
        # Store edge metadata
        edge_key = (origin, destination)
        self.edge_data[edge_key] = {
            "distance_km": distance_km,
            "is_paved": is_paved,
            "track_type": track_type,
            "region": self.node_data[origin].get("region", "Unknown"),
        }
    
    def update_location_risk(self, name: str, new_risk: float) -> None:
        """
        Update risk score for a location.
        
        Used when Union-Find detects an outbreak cluster.
        
        Args:
            name: Location name
            new_risk: New risk score
        
        Service Layer Integration:
            - Called by LDSNService.update_location_risk()
            - Affects subsequent route calculations
        """
        if name in self.node_data:
            self.node_data[name]["risk_score"] = new_risk
    
    def calculate_safe_route(
        self,
        start: str,
        end: str,
        is_rainy_season: bool = False,
        consider_outbreak_risk: bool = True
    ) -> Tuple[List[str], float]:
        """
        Calculate the safest transhumance route using Dijkstra's algorithm.
        
        Effective Weight = Distance × Seasonal Multiplier + Risk Score.
        
        Complexity: O(E log V)
        
        Args:
            start: Starting location
            end: Destination location
            is_rainy_season: Whether it's the rainy season (Duumol)
            consider_outbreak_risk: Whether to include outbreak risk in weights
            
        Returns:
            Tuple of (path as list of locations, total effective weight)
            
        Raises:
            KeyError: If start or end location doesn't exist
        
        Service Layer Integration:
            - Called by LDSNService.calculate_route()
            - Returns path for UI visualization
        """
        if start not in self.adj_list:
            raise KeyError(f"Start location not found: {start}")
        if end not in self.adj_list:
            raise KeyError(f"End location not found: {end}")
        
        # Determine season
        season = SeasonType.RAINY if is_rainy_season else SeasonType.DRY
        
        # Initialize Dijkstra's algorithm
        distances: Dict[str, float] = {node: math.inf for node in self.adj_list}
        distances[start] = 0
        previous: Dict[str, Optional[str]] = {node: None for node in self.adj_list}
        pq: List[Tuple[float, str]] = [(0, start)]
        
        while pq:
            current_dist, current = heapq.heappop(pq)
            
            # Skip if we already found a better path
            if current_dist > distances[current]:
                continue
            
            # Early exit if we reached destination
            if current == end:
                break
            
            # Explore neighbors
            for neighbor, base_distance in self.adj_list[current]:
                # Get edge metadata
                edge_key = (current, neighbor)
                edge_info = self.edge_data.get(edge_key, {})
                is_paved = edge_info.get("is_paved", False)
                region = edge_info.get("region", "Unknown")
                
                # Calculate effective weight with seasonal conditions
                seasonal_multiplier = SEASONAL_MULTIPLIERS[season]
                
                # Additional 2.5× penalty for unpaved Adamawa tracks during rainy season
                # This implements the Duumol mode requirement
                if (
                    is_rainy_season
                    and not is_paved
                    and region == "Adamawa"
                ):
                    seasonal_multiplier *= 2.5
                
                # Add outbreak risk if enabled (Union-Find cluster detection)
                risk_penalty = 0.0
                if consider_outbreak_risk:
                    risk_penalty = self.node_data[neighbor].get("risk_score", 0.0)
                
                weight = (base_distance * seasonal_multiplier) + risk_penalty
                new_dist = current_dist + weight
                
                # Update if we found a shorter path
                if new_dist < distances[neighbor]:
                    distances[neighbor] = new_dist
                    previous[neighbor] = current
                    heapq.heappush(pq, (new_dist, neighbor))
        
        # Reconstruct path
        path = self._reconstruct_path(previous, start, end)
        total_weight = distances[end]
        
        return path, total_weight
    
    def _reconstruct_path(
        self,
        previous: Dict[str, Optional[str]],
        start: str,
        end: str
    ) -> List[str]:
        """
        Reconstruct the path from previous node mappings.
        
        Args:
            previous: Dict mapping each node to its predecessor
            start: Starting location
            end: Destination location
            
        Returns:
            List of locations in path order
        """
        path: List[str] = []
        current = end
        
        while current is not None:
            path.append(current)
            current = previous[current]
        
        path.reverse()
        
        # Verify path starts at expected location
        if path and path[0] == start:
            return path
        return []
    
    def get_all_locations(self) -> List[str]:
        """
        Get list of all locations in the graph.
        
        Returns:
            List of location names
        """
        return list(self.adj_list.keys())
    
    def get_location_info(self, name: str) -> Optional[Dict]:
        """
        Get metadata for a location.
        
        Args:
            name: Location name
            
        Returns:
            Dict with region, is_zvscc, risk_score or None
        """
        return self.node_data.get(name)
    
    def is_zvscc_station(self, name: str) -> bool:
        """
        Check if a location is a ZVSCC station.
        
        Args:
            name: Location name
            
        Returns:
            True if ZVSCC station, False otherwise
        """
        info = self.node_data.get(name, {})
        return info.get("is_zvscc", False)
    
    def get_zvscc_locations(self) -> List[str]:
        """
        Get list of all ZVSCC stations.
        
        Used for prioritizing offline-capable stations.
        
        Returns:
            List of ZVSCC location names
        """
        return [
            name for name, info in self.node_data.items()
            if info.get("is_zvscc", False)
        ]
    
    def __contains__(self, name: str) -> bool:
        """Check if a location exists in the graph."""
        return name in self.adj_list
    
    def __len__(self) -> int:
        """Return number of locations in the graph."""
        return len(self.adj_list)


# ============================================================================
# Cameroon Network Factory
# ============================================================================

def get_cameroon_network() -> TranshumanceGraph:
    """
    Create and populate a TranshumanceGraph with Cameroon key locations.
    
    Location names use proper accents (Ngaoundéré, Yaoundé, Mbé).
    
    Returns:
        Configured TranshumanceGraph instance
    
    Regions covered:
        - Adamawa (Ngaoundéré): Cattle transhumance hub
        - Far North (Maroua, Kousseri): Grazing and border crossings
        - West (Bafoussam, Bamenda, Dschang): Poultry and dairy
        - Centre (Yaoundé): Capital and logistics hub
        - Northwest (Bamenda): Livestock trading
        - North (Garoua): Cattle corridor
        - East (Bertoua): Regional capital
    
    ZVSCC Stations (Offline Capable):
        - Ngaoundéré, Maroua, Kousseri, Yaoundé, Bafoussam, Bamenda, Dschang, Garoua, Bertoua
    
    Author: LDSN Development Team
    Version: 3.0.0
    """
    graph = TranshumanceGraph()
    
    # =========================================================================
    # Adamawa Region - Cattle Transhumance Hub
    # =========================================================================
    # Ngaoundéré: Regional capital, major cattle hub, ZVSCC
    graph.add_location("Ngaoundéré", region="Adamawa", is_zvscc=True, risk_score=0.0)
    # Tibati: Key transhumance corridor to Far North
    graph.add_location("Tibati", region="Adamawa", is_zvscc=False, risk_score=0.0)
    # Mbé: Cattle trading post on transhumance routes
    graph.add_location("Mbé", region="Adamawa", is_zvscc=False, risk_score=0.0)
    
    # =========================================================================
    # Far North Region - Grazing and Border
    # =========================================================================
    # Maroua: Regional capital, proximity to Nigerian border, ZVSCC
    graph.add_location("Maroua", region="Far North", is_zvscc=True, risk_score=0.0)
    # Kousseri: Chad border crossing, livestock export point, ZVSCC
    graph.add_location("Kousseri", region="Far North", is_zvscc=True, risk_score=0.0)
    # Mora: Nigeria border crossing, market town
    graph.add_location("Mora", region="Far North", is_zvscc=False, risk_score=0.0)
    # Logone Floodplain: Seasonal grazing area
    graph.add_location("Logone Floodplain", region="Far North", is_zvscc=False, risk_score=0.0)
    # Mindif: Seasonal grazing area, near Maroua
    graph.add_location("Mindif", region="Far North", is_zvscc=False, risk_score=0.0)
    # Maga: Near Waza Park, floodplain grazing area
    graph.add_location("Maga", region="Far North", is_zvscc=False, risk_score=0.0)
    
    # =========================================================================
    # West Region - Poultry and Dairy
    # =========================================================================
    # Bafoussam: Dairy and poultry production center, ZVSCC
    graph.add_location("Bafoussam", region="West", is_zvscc=True, risk_score=0.0)
    # Bamenda: Northwest Region livestock trading center, ZVSCC
    graph.add_location("Bamenda", region="Northwest", is_zvscc=True, risk_score=0.0)
    # Dschang: Western Highlands livestock center, ZVSCC
    graph.add_location("Dschang", region="West", is_zvscc=True, risk_score=0.0)
    # Bamendjou: Dairy farming area near Bafoussam
    graph.add_location("Bamendjou", region="West", is_zvscc=False, risk_score=0.0)
    
    # =========================================================================
    # Centre Region - Capital and Logistics
    # =========================================================================
    # Yaoundé: National capital, main logistics hub, ZVSCC
    graph.add_location("Yaoundé", region="Centre", is_zvscc=True, risk_score=0.0)
    # Edea: Agricultural zone
    graph.add_location("Edea", region="Centre", is_zvscc=False, risk_score=0.0)
    
    # =========================================================================
    # North Region - Cattle Corridor
    # =========================================================================
    # Garoua: Northern Region capital, cattle corridor, ZVSCC
    graph.add_location("Garoua", region="North", is_zvscc=True, risk_score=0.0)
    
    # =========================================================================
    # East Region
    # =========================================================================
    # Bertoua: Eastern Region capital, cattle corridor, ZVSCC
    graph.add_location("Bertoua", region="East", is_zvscc=True, risk_score=0.0)
    
    # =========================================================================
    # Adamawa Corridors (Unpaved, High Seasonal Impact)
    # =========================================================================
    # These tracks are unpaved and receive 2.5× penalty during Duumol (rainy season)
    graph.add_corridor("Ngaoundéré", "Tibati", 80, is_paved=False, track_type="unpaved")
    graph.add_corridor("Tibati", "Mbé", 60, is_paved=False, track_type="unpaved")
    graph.add_corridor("Mbé", "Ngaoundéré", 70, is_paved=False, track_type="unpaved")
    
    # =========================================================================
    # Adamawa to Far North (Critical Transhumance Route)
    # =========================================================================
    # Ngaoundéré to Maroua: Main seasonal migration corridor
    graph.add_corridor("Ngaoundéré", "Maroua", 150, is_paved=False, track_type="unpaved")
    graph.add_corridor("Maroua", "Logone Floodplain", 45, is_paved=False, track_type="unpaved")
    graph.add_corridor("Ngaoundéré", "Garoua", 200, is_paved=False, track_type="unpaved")
    
    # =========================================================================
    # Far North Corridors
    # =========================================================================
    graph.add_corridor("Maroua", "Kousseri", 120, is_paved=False, track_type="unpaved")
    graph.add_corridor("Maroua", "Mora", 60, is_paved=True, track_type="paved")
    graph.add_corridor("Mora", "Mindif", 30, is_paved=False, track_type="unpaved")
    graph.add_corridor("Mindif", "Logone Floodplain", 40, is_paved=False, track_type="unpaved")
    graph.add_corridor("Maroua", "Maga", 90, is_paved=False, track_type="unpaved")
    graph.add_corridor("Kousseri", "Maga", 70, is_paved=False, track_type="unpaved")
    
    # =========================================================================
    # West Region Corridors
    # =========================================================================
    # Paved roads between major towns
    graph.add_corridor("Bafoussam", "Bamenda", 80, is_paved=True, track_type="paved")
    graph.add_corridor("Bafoussam", "Dschang", 50, is_paved=True, track_type="paved")
    graph.add_corridor("Bamenda", "Dschang", 45, is_paved=False, track_type="unpaved")
    graph.add_corridor("Bafoussam", "Bamendjou", 35, is_paved=False, track_type="unpaved")
    graph.add_corridor("Bamendjou", "Dschang", 40, is_paved=False, track_type="unpaved")
    
    # =========================================================================
    # Cross-Regional Corridors
    # =========================================================================
    # Major highways connecting regions
    graph.add_corridor("Bafoussam", "Yaoundé", 300, is_paved=True, track_type="highway")
    graph.add_corridor("Yaoundé", "Ngaoundéré", 450, is_paved=True, track_type="highway")
    graph.add_corridor("Yaoundé", "Maroua", 520, is_paved=False, track_type="mixed")
    graph.add_corridor("Yaoundé", "Bertoua", 350, is_paved=True, track_type="highway")
    graph.add_corridor("Garoua", "Maroua", 180, is_paved=False, track_type="unpaved")
    graph.add_corridor("Bertoua", "Ngaoundéré", 280, is_paved=False, track_type="unpaved")
    
    # Douala connections (major port city)
    graph.add_corridor("Yaoundé", "Edea", 120, is_paved=True, track_type="highway")
    graph.add_corridor("Bafoussam", "Edea", 180, is_paved=True, track_type="highway")
    
    return graph


# ============================================================================
# Route Analysis Functions
# ============================================================================

def analyze_seasonal_impact(
    graph: TranshumanceGraph,
    start: str,
    end: str
) -> Dict:
    """
    Analyze the impact of seasonal conditions on a route.
    
    Compares dry season and rainy season (Duumol) route weights.
    
    Args:
        graph: TranshumanceGraph instance
        start: Starting location
        end: Destination location
        
    Returns:
        Dictionary with dry and rainy season route analysis
    
    Usage:
        >>> graph = get_cameroon_network()
        >>> analysis = analyze_seasonal_impact(graph, "Ngaoundéré", "Maroua")
        >>> print(f"Rainy season adds {analysis['impact']['percent_increase']}%")
    """
    dry_path, dry_weight = graph.calculate_safe_route(
        start, end, is_rainy_season=False
    )
    rainy_path, rainy_weight = graph.calculate_safe_route(
        start, end, is_rainy_season=True
    )
    
    increase = rainy_weight - dry_weight
    percent_increase = (increase / dry_weight * 100) if dry_weight > 0 else 0
    
    return {
        "dry_season": {
            "path": dry_path,
            "weight": dry_weight,
            "season": "Dry Season (November-May)",
        },
        "rainy_season": {
            "path": rainy_path,
            "weight": rainy_weight,
            "season": "Duumol Rainy Season (July-September)",
        },
        "impact": {
            "absolute_increase": increase,
            "percent_increase": round(percent_increase, 2),
            "duumol_multiplier": 2.5,
        },
    }


def get_fastest_route(
    graph: TranshumanceGraph,
    start: str,
    end: str
) -> Tuple[List[str], float]:
    """
    Calculate the fastest route ignoring risk and season.
    
    Args:
        graph: TranshumanceGraph instance
        start: Starting location
        end: Destination location
        
    Returns:
        Tuple of (path, base_distance)
    """
    return graph.calculate_safe_route(
        start, end,
        is_rainy_season=False,
        consider_outbreak_risk=False
    )


def get_safe_route(
    graph: TranshumanceGraph,
    start: str,
    end: str,
    is_rainy_season: bool = False
) -> Tuple[List[str], float]:
    """
    Calculate the safest route considering risk and season.
    
    This is the primary routing function for emergency response.
    
    Args:
        graph: TranshumanceGraph instance
        start: Starting location
        end: Destination location
        is_rainy_season: Whether it's Duumol season
        
    Returns:
        Tuple of (path, effective_weight)
    """
    return graph.calculate_safe_route(
        start, end,
        is_rainy_season=is_rainy_season,
        consider_outbreak_risk=True
    )


# ============================================================================
# Validation Models
# ============================================================================

class LocationEntry:
    """Validation model for location data."""
    def __init__(self, name: str, region: str, is_zvscc: bool = False, risk_score: float = 0.0):
        if not name or not name.strip():
            raise ValueError("Name cannot be empty")
        if not region or not region.strip():
            raise ValueError("Region cannot be empty")
        if risk_score < 0:
            raise ValueError("Risk score cannot be negative")
        
        self.name = name.strip()
        self.region = region.strip()
        self.is_zvscc = is_zvscc
        self.risk_score = risk_score


class CorridorEntry:
    """Validation model for corridor data."""
    def __init__(self, origin: str, destination: str, distance_km: float, is_paved: bool = False, track_type: str = "unpaved"):
        if not origin or not origin.strip():
            raise ValueError("Origin cannot be empty")
        if not destination or not destination.strip():
            raise ValueError("Destination cannot be empty")
        if distance_km <= 0:
            raise ValueError("Distance must be positive")
        
        self.origin = origin.strip()
        self.destination = destination.strip()
        self.distance_km = distance_km
        self.is_paved = is_paved
        self.track_type = track_type


def validate_location_entry(entry: Dict) -> LocationEntry:
    """Validate a location entry dictionary."""
    return LocationEntry(**entry)


def validate_corridor_entry(entry: Dict) -> CorridorEntry:
    """Validate a corridor entry dictionary."""
    return CorridorEntry(**entry)


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("LDSN Cameroon - Transhumance Graph Demo")
    print("=" * 60)
    
    # Create the Cameroon network
    graph = get_cameroon_network()
    
    print(f"\n✓ Network initialized with {len(graph)} locations")
    print(f"✓ ZVSCC Stations: {len(graph.get_zvscc_locations())}")
    
    # Example: Route during dry season
    print("\n--- Dry Season Route ---")
    path, weight = graph.calculate_safe_route(
        "Ngaoundéré", "Maroua", is_rainy_season=False
    )
    print(f"Route: {' → '.join(path)}")
    print(f"Weight: {weight:.2f}")
    
    # Example: Route during Duumol (rainy season)
    print("\n--- Duumol Rainy Season Route ---")
    path, weight = graph.calculate_safe_route(
        "Ngaoundéré", "Maroua", is_rainy_season=True
    )
    print(f"Route: {' → '.join(path)}")
    print(f"Weight: {weight:.2f}")
    print("⚠ Note: 2.5× penalty applied for unpaved Adamawa tracks")
    
    # Example: Seasonal impact analysis
    print("\n--- Seasonal Impact Analysis ---")
    analysis = analyze_seasonal_impact(graph, "Ngaoundéré", "Maroua")
    print(f"Dry Season Weight: {analysis['dry_season']['weight']:.2f}")
    print(f"Rainy Season Weight: {analysis['rainy_season']['weight']:.2f}")
    print(f"Impact: +{analysis['impact']['percent_increase']:.1f}%")

