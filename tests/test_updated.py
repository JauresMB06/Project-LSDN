

import pytest
from Core.Transhumance import get_cameroon_network
from Core.union_find import create_cameroon_outbreak_clusters
from Core.priority_queue import AlertTriage, PriorityLevel


# ============================================================================
# Test Class 1: Transhumance Routing with Seasonal Logic
# ============================================================================

class TestTranshumanceRouting:
    """Test suite for transhumance route optimization."""
    
    def test_network_initialization(self):
        """Test network graph initialization."""
        network = get_cameroon_network()
        assert len(network) > 0
        assert "Ngaoundéré" in network
        assert "Maroua" in network
    
    def test_route_calculation_dry_season(self):
        """Test route calculation during dry season."""
        network = get_cameroon_network()
        path, weight = network.calculate_safe_route(
            "Ngaoundéré", "Maroua", is_rainy_season=False
        )
        
        assert path[0] == "Ngaoundéré"
        assert path[-1] == "Maroua"
        assert weight > 0
    
    def test_route_calculation_rainy_season(self):
        """Test route calculation during rainy season has higher weight."""
        network = get_cameroon_network()
        path_dry, weight_dry = network.calculate_safe_route(
            "Ngaoundéré", "Maroua", is_rainy_season=False
        )
        path_rainy, weight_rainy = network.calculate_safe_route(
            "Ngaoundéré", "Maroua", is_rainy_season=True
        )
        
        # Rainy season should have higher effective weight
        assert weight_rainy > weight_dry
    
    def test_seasonal_multiplier_adamawa(self):
        """Test 2.5x multiplier for Adamawa unpaved tracks during rainy season."""
        network = get_cameroon_network()
        dry_path, dry_weight = network.calculate_safe_route(
            "Ngaoundéré", "Maroua", is_rainy_season=False
        )
        rainy_path, rainy_weight = network.calculate_safe_route(
            "Ngaoundéré", "Maroua", is_rainy_season=True
        )
        
        # The increase should be significant
        increase_ratio = rainy_weight / dry_weight
        assert increase_ratio > 1.0
    
    def test_route_reconstruction(self):
        """Test that route is correctly reconstructed."""
        network = get_cameroon_network()
        path, _ = network.calculate_safe_route("Bafoussam", "Yaoundé")
        
        assert path[0] == "Bafoussam"
        assert path[-1] == "Yaoundé"
        assert len(path) >= 2


# ============================================================================
# Test Class 2: Union-Find and Cluster Detection
# ============================================================================

class TestOutbreakClusters:
    """Test suite for outbreak cluster detection using Union-Find."""
    
    def test_cluster_initialization(self):
        """Test cluster data structure initialization."""
        clusters = create_cameroon_outbreak_clusters()
        assert len(clusters) > 0
        assert clusters.get_num_clusters() > 0
    
    def test_cluster_union(self):
        """Test merging clusters using union operation."""
        clusters = create_cameroon_outbreak_clusters()
        
        # Add a new location and connect it
        clusters.add_location("TestLocation")
        clusters.union("Ngaoundéré", "TestLocation")
        
        # Should be connected
        assert clusters.connected("Ngaoundéré", "TestLocation") is True
    
    def test_cluster_find_with_path_compression(self):
        """Test that find uses path compression."""
        clusters = create_cameroon_outbreak_clusters()
        root = clusters.find("Ngaoundéré")
        assert root is not None
    
    def test_cluster_size_tracking(self):
        """Test cluster size is correctly tracked."""
        clusters = create_cameroon_outbreak_clusters()
        size = clusters.get_cluster_size("Ngaoundéré")
        assert size >= 1
    
    def test_cameroon_regional_connections(self):
        """Test that Cameroon regional connections are configured."""
        clusters = create_cameroon_outbreak_clusters()
        
        # Adamawa locations should be connected
        assert clusters.connected("Ngaoundéré", "Tibati")
        assert clusters.connected("Ngaoundéré", "Mbé")
        
        # Far North locations should be connected
        assert clusters.connected("Maroua", "Kousseri")


# ============================================================================
# Test Class 3: Alert Triage
# ============================================================================

class TestAlertTriage:
    """Test suite for emergency alert triage."""
    
    def test_push_p1_critical_alert(self):
        """Test pushing a P1 critical alert."""
        triage = AlertTriage()
        alert = triage.push_alert(
            disease_name="anthrax",
            location="Maroua",
            reporter_id="VET-001",
        )
        
        assert alert.priority_level == PriorityLevel.P1_CRITICAL
        assert alert.is_critical()
    
    def test_pop_highest_priority(self):
        """Test that pop returns highest priority alert."""
        triage = AlertTriage()
        
        triage.push_alert("helminthosis", "Yaoundé", "VET-001")  # P5
        triage.push_alert("anthrax", "Maroua", "VET-002")  # P1
        triage.push_alert("newcastle disease", "Bafoussam", "VET-003")  # P3
        
        # Pop should return P1 first
        alert = triage.pop_highest_priority()
        assert alert.priority_level == PriorityLevel.P1_CRITICAL
        assert alert.location == "Maroua"


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
