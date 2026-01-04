"""
Weighted Directed Graph for Transhumance Route Optimization.
Complexity: O(E log V) using a Priority Queue (Min-Heap).
"""
import heapq
import math

class TranshumanceGraph:
    def __init__(self):
        # Adjacency List: { 'StartNode': [(end, weight), ...] }
        self.adj_list = {}
        # Stores specific risk factors (e.g., active outbreaks) per location
        self.node_risk_scores = {}

    def add_location(self, name: str, risk_score: float = 0.0):
        """Adds a vertex (e.g., Ngaoundere, Maroua, Maga) to the graph."""
        if name not in self.adj_list:
            self.adj_list[name] = []
            self.node_risk_scores[name] = risk_score

    def add_corridor(self, u: str, v: str, distance_km: float):
        """Adds a directed transhumance track or trade corridor."""
        self.add_location(u)
        self.add_location(v)
        self.adj_list[u].append((v, distance_km))

    def update_risk(self, location: str, new_risk: float):
        """Increases weight of all paths entering this location if disease is detected."""
        if location in self.node_risk_scores:
            self.node_risk_scores[location] = new_risk

    def calculate_safe_route(self, start: str, end: str, is_rainy_season: bool = False):
        """
        Uses Dijkstra's to find the path with the lowest 'Effective Weight'.
        Effective Weight = Distance + Node Risk + Seasonal Penalty.
        """
        distances = {node: math.inf for node in self.adj_list}
        distances[start] = 0
        pq = [(0, start)]
        previous_nodes = {node: None for node in self.adj_list}

        while pq:
            current_dist, u = heapq.heappop(pq)

            if current_dist > distances[u]:
                continue

            if u == end: break

            for v, dist in self.adj_list.get(u, []):
                # --- Cameroon Adaptation Logic ---
                # 1. Seasonal Penalty: Rainy season (duumol) makes tracks impassable [8]
                seasonal_multiplier = 2.5 if is_rainy_season else 1.0

                # 2. Risk Score: Added cost from Union-Find cluster detections
                target_risk = self.node_risk_scores.get(v, 0.0)

                weight = (dist * seasonal_multiplier) + target_risk

                if distances[u] + weight < distances[v]:
                    distances[v] = distances[u] + weight
                    previous_node
                    s[v] = u
                    heapq.heappush(pq, (distances[v], v))

        return self._reconstruct_path(previous_nodes, end), distances[end]

    def _reconstruct_path(self, previous_nodes, end):
        path = []
        curr = end
        while curr:
            path.append(curr)
            curr = previous_nodes[curr]
        return path[::-1] if path and path[0] == end else []

# --- Example Setup for Northern & West Cameroon Hubs ---
def get_cameroon_network():
    graph = TranshumanceGraph()
    # Key nodes: Adamawa (cattle), West (poultry), Far North (grazing)
    graph.add_corridor("Ngaoundere", "Maroua", 150)
    graph.add_corridor("Maroua", "Logone Floodplain", 45) # Critical ceedu grazing [9]
    graph.add_corridor("Bafoussam", "Yaounde", 300)      # Poultry trade route [10]
    graph.add_corridor("Bamenda", "Bafoussam", 80)       # Dairy/Small ruminant corridor
    return graph
