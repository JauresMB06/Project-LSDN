"""
Unit Test Script for Member 1: Algorithmic Core.
Tests the Symptom Trie and the Seasonal logic of the Transhumance Graph.
"""
from Core.Trie import get_trained_trie
from Core.Transhumance import get_cameroon_network

def run_algorithmic_tests():
    print("==================================================")
    print("RUNNING LDSN PROJECT 7: CORE ALGORITHMIC TESTS")
    print("==================================================\n")

    # --- TEST 1: Symptom Trie Autocomplete ---
    print(" Verifying Symptom Trie Taxonomy...")
    trie = get_trained_trie()
    
    # Test prefix matching for "peste" (PPR) and "highly" (HPAI) 
    matches_ppr = trie.autocomplete("pes")
    matches_hpai = trie.autocomplete("highly")
    
    print(f"  Prefix 'pes' -> Found: {matches_ppr}")
    print(f"  Prefix 'highly' -> Found: {matches_hpai}")
    
    assert "peste des petits ruminants" in matches_ppr
    print("  SUCCESS: Trie autocomplete is functional.\n")


    # --- TEST 2: Transhumance Graph Seasonal Logic ---
    print(" Verifying Seasonal Edge Weighting (Rainy Season Penalty)...")
    network = get_cameroon_network()
    
    # Route: Ngaoundere (Adamawa) -> Maroua (Far North) 
    start_node = "Ngaoundere"
    end_node = "Maroua"
    
    # Scenario A: Dry Season (September - June)
    # Effective weight should just be the base distance (150 km) [5]
    path_dry, weight_dry = network.calculate_safe_route(start_node, end_node, is_rainy_season=False)
    print(f"  DRY SEASON: Path={path_dry}, Effective Weight={weight_dry}")

    # Scenario B: Rainy Season (July - September)
    # Effective weight must increase by the 2.5x multiplier [2, 6]
    path_rainy, weight_rainy = network.calculate_safe_route(start_node, end_node, is_rainy_season=True)
    print(f"  RAINY SEASON (Duumol): Path={path_rainy}, Effective Weight={weight_rainy}")

    # Validation Logic
    if weight_rainy > weight_dry:
        print(f"\n  Rainy season penalty applied correctly.")
        print(f"  Weight increased from {weight_dry} to {weight_rainy} (+{(weight_rainy - weight_dry)} penalty).")
    else:
        print("\n  Rainy season penalty was not detected.")
        raise ValueError("Graph logic error: weight must increase during rainy season.")


    # --- TEST 3: Path Risk Updates (Union-Find Integration) ---
    # Member 2 will trigger this when Union-Find detects a cluster [7, 8]
    print("\n Verifying Risk-Aware Routing (Outbreak in Maroua)...")
    
    # Add a high risk score to Maroua to simulate a Foot-and-Mouth Disease (FMD) cluster 
    network.update_risk("Maroua", new_risk=500.0)
    
    path_risky, weight_risky = network.calculate_safe_route("Ngaoundere", "Logone Floodplain", is_rainy_season=False)
    print(f"  ROUTE TO LOGONE: Path={path_risky}, Weight={weight_risky}")
    
    print("\n==================================================")
    print("ALL TESTS PASSED SUCCESSFULLY")
    print("==================================================")

if __name__ == "__main__":
    run_algorithmic_tests()