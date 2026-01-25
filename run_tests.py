#!/usr/bin/env python3
import sys
sys.path.insert(0, ".")
from Core.Trie import get_trained_trie
trie = get_trained_trie()
assert "peste des petits ruminants" in trie.autocomplete("peste")
print("1. Trie: OK")

from Core.Transhumance import get_cameroon_network
n = get_cameroon_network()
_, w1 = n.calculate_safe_route("Ngaoundéré", "Maroua", False)
_, w2 = n.calculate_safe_route("Ngaoundéré", "Maroua", True)
assert w2 > w1
print("2. Transhumance: OK")

from Core.union_find import create_cameroon_outbreak_clusters
c = create_cameroon_outbreak_clusters()
assert c.connected("Ngaoundéré", "Tibati")
print("3. Union-Find: OK")

from Core.priority_queue import AlertTriage
t = AlertTriage()
t.push_alert("anthrax", "Maroua", "VET-001")
assert t.get_critical_count() == 1
print("4. Priority Queue: OK")

from Core.segment_tree import CameroonMortalityTracker
tr = CameroonMortalityTracker()
tr.record_mortality(0, 100)
tr.record_mortality(100, 50)
assert tr.get_total_mortality() == 150
print("5. Segment Tree: OK")

from Core.service import get_ldsn_service
s = get_ldsn_service()
a = s.submit_alert("anthrax", "Maroua", "VET-001")
assert a.priority_level == 1
print("6. Service: OK")

print("")
print("ALL 7 TESTS PASSED!")

