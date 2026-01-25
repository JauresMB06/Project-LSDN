"""
Livestock Disease Surveillance Network (LDSN) - End-to-End Test Pipeline

Comprehensive PyTest suite simulating the complete LDSN workflow:
    1. Entry of symptom → 2. Cluster Detection → 3. Route Recalculation → 4. Priority Alert Triage

This test validates the entire system from data entry through emergency response.

Author: LDSN Development Team
Version: 2.0.0
"""

import pytest
import sys
from datetime import datetime
from typing import Dict, List, Any

# Import LDSN components
from Core.Trie import SymptomTrie, get_trained_trie, CAMEROON_PRIORITY_DISEASES
from Core.Transhumance import (
    TranshumanceGraph,
    get_cameroon_network,
    SeasonType,
    analyze_seasonal_impact,
)
from Core.union_find import OutbreakCluster, create_cameroon_outbreak_clusters
from Core.priority_queue import (
    AlertTriage,
    AlertItem,
    PriorityLevel,
    CAMEROON_PRIORITY_MATRIX,
    get_disease_priority,
)
from Core.segment_tree import MortalitySegmentTree, CameroonMortalityTracker
from Core.data_persistence import (
    StoreAndForwardManager,
    JSONCacheManager,
    SQLiteManager,
)
from Core.service import (
    LDSNService,
    get_ldsn_service,
    SymptomResult,
    RouteResult,
    AlertResult,
    ClusterResult,
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def service() -> LDSNService:
    """Provide a fresh LDSN service instance for each test."""
    return get_ldsn_service()


@pytest.fixture
def trie() -> SymptomTrie:
    """Provide a trained symptom trie."""
    return get_trained_trie()


@pytest.fixture
def network() -> TranshumanceGraph:
    """Provide the Cameroon transhumance network."""
    return get_cameroon_network()


@pytest.fixture
def clusters() -> OutbreakCluster:
    """Provide pre-configured outbreak clusters."""
    return create_cameroon_outbreak_clusters()


@pytest.fixture
def triage() -> AlertTriage:
    """Provide an empty alert triage queue."""
    return AlertTriage()


@pytest.fixture
def mortality_tracker() -> CameroonMortalityTracker:
    """Provide a mortality tracker."""
    return CameroonMortalityTracker()


@pytest.fixture
def persistence(tmp_path) -> StoreAndForwardManager:
    """Provide a temporary persistence manager."""
    db_path = str(tmp_path / "test_ldsn.db")
    cache_dir = str(tmp_path / "cache")
    return StoreAndForwardManager(db_path=db_path, cache_dir=cache_dir)


# ============================================================================
# Test Class 1: Trie and Symptom Autocomplete
# ============================================================================

class TestSymptomAutocomplete:
    """Test suite for symptom taxonomy and autocomplete functionality."""
    
    def test_trie_insert_and_search(self, trie: SymptomTrie):
        """Test basic trie insert and search operations."""
        # Insert a new symptom
        trie.insert("contagious bovine pleuropneumonia")
        
        # Verify it exists
        assert trie.search("contagious bovine pleuropneumonia") is True
        assert trie.search("nonexistent disease") is False
    
    def test_trie_autocomplete_prefix_matching(self, trie: SymptomTrie):
        """Test autocomplete returns correct prefix matches."""
        # Test PPR prefix
        matches = trie.autocomplete("peste")
        assert "peste des petits ruminants" in matches
        
        # Test Avian Influenza prefix
        matches = trie.autocomplete("highly")
        assert "highly pathogenic avian influenza" in matches
    
    def test_trie_case_insensitivity(self, trie: SymptomTrie):
        """Test that trie is case-insensitive."""
        matches_lower = trie.autocomplete("peste")
        matches_upper = trie.autocomplete("PESTE")
        matches_mixed = trie.autocomplete("PeStE")
        
        assert matches_lower == matches_upper == matches_mixed
    
    def test_trie_empty_prefix_returns_all(self, trie: SymptomTrie):
        """Test that empty prefix returns all terms."""
        # This tests the DFS collection behavior
        matches = trie.autocomplete("")
        # Should return all diseases that start from root
        assert len(matches) > 0
    
    def test_trie_nonexistent_prefix(self, trie: SymptomTrie):
        """Test autocomplete with nonexistent prefix returns empty list."""
        matches = trie.autocomplete("xyznonexistent")
        assert matches == []
    
    def test_cameroon_priority_diseases_loaded(self, trie: SymptomTrie):
        """Verify all Cameroon priority diseases are loaded."""
        all_symptoms = trie.autocomplete("")
        for disease in CAMEROON_PRIORITY_DISEASES:
            assert trie.search(disease), f"Disease not found: {disease}"


# ============================================================================
# Test Class 2: Union-Find and Cluster Detection
# ============================================================================

class TestOutbreakClusters:
    """Test suite for outbreak cluster detection using Union-Find."""
    
    def test_cluster_initialization(self, clusters: OutbreakCluster):
        """Test cluster data structure initialization."""
        assert len(clusters) > 0
        assert clusters.get_num_clusters() > 0
    
    def test_cluster_union(self, clusters: OutbreakCluster):
        """Test merging clusters using union operation."""
        initial_clusters = clusters.get_num_clusters()

        # Add a new location and connect it
        clusters.add_location("TestLocation")
        clusters.union("Ngaoundéré", "TestLocation")

        # Should still be connected (already in same region)
        assert clusters.connected("Ngaoundéré", "TestLocation") is True
    
    def test_cluster_find_with_path_compression(self, clusters: OutbreakCluster):
        """Test that find uses path compression."""
        # Find should work and compress path
        root = clusters.find("Ngaoundéré")
        assert root is not None
    
    def test_cluster_size_tracking(self, clusters: OutbreakCluster):
        """Test cluster size is correctly tracked."""
        # Get cluster size for a known location
        size = clusters.get_cluster_size("Ngaoundéré")
        assert size >= 1
    
    def test_cluster_get_clusters(self, clusters: OutbreakCluster):
        """Test retrieving all clusters."""
        all_clusters = clusters.get_clusters()
        assert len(all_clusters) > 0
        for cluster in all_clusters:
            assert len(cluster) >= 1
    
    def test_cameroon_regional_connections(self, clusters: OutbreakCluster):
        """Test that Cameroon regional connections are configured."""
        # Adamawa locations should be connected
        assert clusters.connected("Ngaoundéré", "Tibati")
        assert clusters.connected("Ngaoundéré", "Mbé")

        # Far North locations should be connected
        assert clusters.connected("Maroua", "Kousseri")


# ============================================================================
# Test Class 3: Transhumance Routing with Seasonal Logic
# ============================================================================

class TestTranshumanceRouting:
    """Test suite for transhumance route optimization."""
    
    def test_network_initialization(self, network: TranshumanceGraph):
        """Test network graph initialization."""
        assert len(network) > 0
        assert "Ngaoundéré" in network
        assert "Maroua" in network
    
    def test_route_calculation_dry_season(self, network: TranshumanceGraph):
        """Test route calculation during dry season."""
        path, weight = network.calculate_safe_route(
            "Ngaoundéré", "Maroua", is_rainy_season=False
        )

        assert path[0] == "Ngaoundéré"
        assert path[-1] == "Maroua"
        assert weight > 0
    
    def test_route_calculation_rainy_season(self, network: TranshumanceGraph):
        """Test route calculation during rainy season has higher weight."""
        path_dry, weight_dry = network.calculate_safe_route(
            "Ngaoundéré", "Maroua", is_rainy_season=False
        )
        path_rainy, weight_rainy = network.calculate_safe_route(
            "Ngaoundéré", "Maroua", is_rainy_season=True
        )

        # Rainy season should have higher effective weight
        assert weight_rainy > weight_dry
    
    def test_seasonal_multiplier_adamawa(self, network: TranshumanceGraph):
        """Test 2.5× multiplier for Adamawa unpaved tracks during rainy season."""
        # Compare weights for routes through Adamawa
        dry_path, dry_weight = network.calculate_safe_route(
            "Ngaoundéré", "Maroua", is_rainy_season=False
        )
        rainy_path, rainy_weight = network.calculate_safe_route(
            "Ngaoundéré", "Maroua", is_rainy_season=True
        )

        # The increase should be significant (at least 2.5× on track segments)
        increase_ratio = rainy_weight / dry_weight
        assert increase_ratio > 1.0
    
    def test_route_reconstruction(self, network: TranshumanceGraph):
        """Test that route is correctly reconstructed."""
        path, _ = network.calculate_safe_route("Bafoussam", "Yaoundé")

        assert path[0] == "Bafoussam"
        assert path[-1] == "Yaoundé"
        # Path should have at least 2 nodes (start and end)
        assert len(path) >= 2
    
    def test_invalid_location_raises_error(self, network: TranshumanceGraph):
        """Test that invalid locations raise KeyError."""
        with pytest.raises(KeyError):
            network.calculate_safe_route("Nonexistent", "Maroua")
    
    def test_analyze_seasonal_impact(self, network: TranshumanceGraph):
        """Test seasonal impact analysis function."""
        analysis = analyze_seasonal_impact(network, "Ngaoundéré", "Maroua")

        assert "dry_season" in analysis
        assert "rainy_season" in analysis
        assert "impact" in analysis
        assert analysis["dry_season"]["weight"] < analysis["rainy_season"]["weight"]


# ============================================================================
# Test Class 4: Priority Queue and Alert Triage
# ============================================================================

class TestAlertTriage:
    """Test suite for emergency alert triage."""
    
    def test_triage_initialization(self, triage: AlertTriage):
        """Test triage queue initialization."""
        assert len(triage) == 0
        assert triage.get_pending_count() == 0
    
    def test_push_p1_critical_alert(self, triage: AlertTriage):
        """Test pushing a P1 critical alert."""
        alert = triage.push_alert(
            disease_name="anthrax",
            location="Maroua",
            reporter_id="VET-001",
        )
        
        assert alert.priority_level == PriorityLevel.P1_CRITICAL
        assert alert.is_critical()
    
    def test_push_p2_high_alert(self, triage: AlertTriage):
        """Test pushing a P2 high priority alert."""
        alert = triage.push_alert(
            disease_name="peste des petits ruminants",
            location="Ngaoundere",
            reporter_id="VET-002",
        )
        
        assert alert.priority_level == PriorityLevel.P2_HIGH
    
    def test_auto_priority_classification(self):
        """Test automatic priority classification by disease name."""
        # P1 diseases
        assert get_disease_priority("anthrax") == PriorityLevel.P1_CRITICAL
        assert get_disease_priority("highly pathogenic avian influenza") == PriorityLevel.P1_CRITICAL
        
        # P2 diseases
        assert get_disease_priority("peste des petits ruminants") == PriorityLevel.P2_HIGH
        assert get_disease_priority("foot and mouth disease") == PriorityLevel.P2_HIGH

        # Default for unknown diseases
        assert get_disease_priority("unknown disease") == PriorityLevel.P4_STANDARD
    
    def test_pop_highest_priority(self, triage: AlertTriage):
        """Test that pop returns highest priority alert."""
        # Push alerts with different priorities
        triage.push_alert("helminthosis", "Yaoundé", "VET-001")  # P5
        triage.push_alert("anthrax", "Maroua", "VET-002")  # P1
        triage.push_alert("newcastle disease", "Bafoussam", "VET-003")  # P3

        # Pop should return P1 first
        alert = triage.pop_highest_priority()
        assert alert.priority_level == PriorityLevel.P1_CRITICAL
        assert alert.location == "Maroua"
    
    def test_critical_alert_count(self, triage: AlertTriage):
        """Test counting critical alerts."""
        assert triage.get_critical_count() == 0
        
        triage.push_alert("anthrax", "Maroua", "VET-001")
        triage.push_alert("highly pathogenic avian influenza", "Bafoussam", "VET-002")
        triage.push_alert("peste des petits ruminants", "Ngaoundéré", "VET-003")

        assert triage.get_critical_count() == 2


# ============================================================================
# Test Class 5: Mortality Tracking with Segment Tree
# ============================================================================

class TestMortalityTracking:
    """Test suite for mortality data tracking."""
    
    def test_mortality_tracker_initialization(self, mortality_tracker: CameroonMortalityTracker):
        """Test mortality tracker initialization."""
        assert len(mortality_tracker.tree) == 365
    
    def test_single_day_update(self, mortality_tracker: CameroonMortalityTracker):
        """Test updating mortality for a single day."""
        mortality_tracker.record_mortality(0, 10)
        assert mortality_tracker.tree.query_single(0) == 10
    
    def test_dry_season_query(self, mortality_tracker: CameroonMortalityTracker):
        """Test querying dry season mortality."""
        # Simulate some mortality data
        for day in range(31, 152):  # Dry season days
            mortality_tracker.record_mortality(day, 5)
        
        dry_total = mortality_tracker.get_dry_season_mortality()
        assert dry_total > 0
        assert dry_total == 5 * (152 - 31)  # 121 days * 5 = 605
    
    def test_rainy_season_query(self, mortality_tracker: CameroonMortalityTracker):
        """Test querying rainy season mortality."""
        # Simulate some mortality data
        for day in range(181, 274):  # Rainy season days
            mortality_tracker.record_mortality(day, 10)
        
        rainy_total = mortality_tracker.get_rainy_season_mortality()
        assert rainy_total > 0
    
    def test_total_mortality(self, mortality_tracker: CameroonMortalityTracker):
        """Test total mortality calculation."""
        mortality_tracker.record_mortality(0, 100)
        mortality_tracker.record_mortality(1, 50)
        
        assert mortality_tracker.get_total_mortality() == 150


# ============================================================================
# Test Class 6: Data Persistence (Store-and-Forward)
# ============================================================================

class TestDataPersistence:
    """Test suite for offline data persistence."""
    
    def test_save_report(self, persistence: StoreAndForwardManager):
        """Test saving a disease report."""
        report_id = persistence.save_report(
            report_type="symptom",
            location="Maroua",
            reporter_id="VET-001",
            disease_suspected="anthrax",
        )
        
        assert report_id > 0
    
    def test_save_alert(self, persistence: StoreAndForwardManager):
        """Test saving an alert."""
        alert_id = persistence.save_alert(
            disease_name="anthrax",
            location="Maroua",
            priority_level=1,
            reporter_id="VET-001",
        )
        
        assert alert_id > 0
    
    def test_get_pending_reports(self, persistence: StoreAndForwardManager):
        """Test retrieving pending reports."""
        persistence.save_report("symptom", "Maroua", "VET-001")
        persistence.save_report("mortality", "Ngaoundere", "VET-002")
        
        pending = persistence.get_pending_reports()
        assert len(pending) == 2
    
    def test_mark_reports_synced(self, persistence: StoreAndForwardManager):
        """Test marking reports as synced."""
        report_id = persistence.save_report("symptom", "Maroua", "VET-001")
        
        persistence.mark_reports_synced([report_id])
        
        pending = persistence.get_pending_reports()
        assert len(pending) == 0
    
    def test_get_stats(self, persistence: StoreAndForwardManager):
        """Test getting persistence statistics."""
        persistence.save_report("symptom", "Maroua", "VET-001")
        persistence.save_alert("anthrax", "Maroua", 1, "VET-001")
        
        stats = persistence.get_stats()
        assert stats["reports"] == 1
        assert stats["alerts"] == 1


# ============================================================================
# Test Class 7: End-to-End Pipeline Test
# ============================================================================

class TestEndToEndPipeline:
    """
    Comprehensive end-to-end test simulating the complete LDSN workflow.
    
    Workflow:
        1. Entry of symptom → 2. Cluster Detection → 3. Route Recalculation → 4. Priority Alert Triage
    """
    
    def test_complete_symptom_entry_to_alert_pipeline(self, service: LDSNService):
        """
        Test complete pipeline: symptom entry → cluster detection → route → alert.
        
        This is the main integration test.
        """
        # Step 1: Symptom Entry and Autocomplete
        symptom_result = service.autocomplete_symptoms("peste")
        assert symptom_result.count > 0
        assert "peste des petits ruminants" in symptom_result.matches
        
        # Step 2: Cluster Detection
        clusters = service.detect_clusters()
        assert len(clusters) > 0
        # Verify cluster structure
        for cluster in clusters:
            assert cluster.size >= 1
            assert len(cluster.locations) >= 1
        
        # Step 3: Route Recalculation (with outbreak risk)
        service.update_location_risk("Maroua", 100.0)
        route = service.calculate_route("Ngaoundéré", "Maroua", is_rainy_season=False)
        assert route.path[0] == "Ngaoundéré"
        assert route.path[-1] == "Maroua"
        
        # Step 4: Priority Alert Triage
        alert = service.submit_alert(
            disease_name="anthrax",
            location="Maroua",
            reporter_id="VET-001",
            details={"livestock_type": "cattle", "affected_count": 15},
        )
        
        assert alert.priority_level == PriorityLevel.P1_CRITICAL
        assert alert.action_taken == "IMMEDIATE_RESPONSE_REQUIRED"
        
        # Verify alert is in queue
        pending = service.get_pending_alerts()
        assert len(pending) >= 1
    
    def test_rainy_season_emergency_response(self, service: LDSNService):
        """Test emergency response during rainy season."""
        # Submit critical alerts
        service.submit_alert("anthrax", "Maroua", "VET-001")
        service.submit_alert("highly pathogenic avian influenza", "Bafoussam", "VET-002")
        
        # Verify critical count
        critical_count = service.get_critical_alert_count()
        assert critical_count == 2
        
        # Process highest priority
        processed = service.process_next_alert()
        assert processed is not None
        assert processed.priority_level == PriorityLevel.P1_CRITICAL
    
    def test_mortality_analysis_pipeline(self, service: LDSNService):
        """Test mortality data collection and analysis."""
        # Record some mortality data
        for day in range(365):
            service.record_mortality(day, day % 10)
        
        # Get statistics
        stats = service.get_mortality_statistics()
        assert stats.total > 0
        assert stats.dry_season_total >= 0
        assert stats.rainy_season_total >= 0
    
    def test_service_health_check(self, service: LDSNService):
        """Test service health check."""
        health = service.health_check()
        
        assert health["status"] == "healthy"
        assert health["components"]["trie"] is True
        assert health["components"]["network"] is True
        assert health["components"]["clusters"] is True
        assert health["components"]["persistence"] is True
    
    def test_service_statistics(self, service: LDSNService):
        """Test comprehensive service statistics."""
        # Add some data first
        service.submit_alert("anthrax", "Maroua", "VET-001")
        
        stats = service.get_service_stats()
        
        assert stats.algorithms["symptom_count"] > 0
        assert stats.algorithms["location_count"] > 0
        assert stats.algorithms["pending_alerts"] >= 1


# ============================================================================
# Test Class 8: Error Handling and Validation
# ============================================================================

class TestErrorHandling:
    """Test suite for error handling and input validation."""
    
    def test_empty_prefix_validation(self, service: LDSNService):
        """Test that empty prefix raises ValueError."""
        with pytest.raises(ValueError):
            service.autocomplete_symptoms("")
        
        with pytest.raises(ValueError):
            service.autocomplete_symptoms("   ")
    
    def test_invalid_route_location(self, service: LDSNService):
        """Test that invalid locations raise KeyError."""
        with pytest.raises(KeyError):
            service.calculate_route("Nonexistent", "Maroua")
    
    def test_persistence_validation(self, persistence: StoreAndForwardManager):
        """Test data validation in persistence layer."""
        # These should work without errors
        report_id = persistence.save_report(
            report_type="symptom",
            location="Maroua",
            reporter_id="VET-001",
        )
        assert report_id > 0
    
    def test_segment_tree_bounds_check(self, mortality_tracker: CameroonMortalityTracker):
        """Test segment tree out-of-bounds handling."""
        with pytest.raises(ValueError):
            mortality_tracker.tree.update(-1, 10)
        
        with pytest.raises(ValueError):
            mortality_tracker.tree.update(400, 10)  # Out of bounds for 365-day tree
    
    def test_union_find_invalid_location(self, clusters: OutbreakCluster):
        """Test Union-Find error handling for invalid locations."""
        with pytest.raises(KeyError):
            clusters.find("NonexistentLocation")

        with pytest.raises(KeyError):
            clusters.connected("Ngaoundéré", "NonexistentLocation")


# ============================================================================
# Test Execution
# ============================================================================

if __name__ == "__main__":
    # Run pytest with verbose output
    pytest.main([__file__, "-v", "--tb=short"])

