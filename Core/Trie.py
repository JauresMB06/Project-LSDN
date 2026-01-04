"""
Trie Data Structure for Livestock Symptom Taxonomy.
Complexity:
- Insert: O(L) where L is string length.
- Search/Prefix: O(L) where L is prefix length.
"""

class TrieNode:
    def __init__(self):
        self.children = {}
        self.is_end_of_word = False
        # Metadata to store standardized disease descriptions if needed
        self.standard_term = None

class SymptomTrie:
    def __init__(self):
        self.root = TrieNode()

    def insert(self, word: str):
        """Inserts a standardized clinical sign or disease name into the Trie."""
        node = self.root
        for char in word.lower():
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        node.is_end_of_word = True
        node.standard_term = word

    def autocomplete(self, prefix: str):
        """
        Returns all standardized symptoms matching the prefix.
        Used by the CLI to reduce data entry errors in remote ZVSCC centers.
        """
        node = self.root
        for char in prefix.lower():
            if char not in node.children:
                return []
            node = node.children[char]

        results = []
        self._dfs_collect(node, results)
        return results

    def _dfs_collect(self, node, results):
        """Helper method to traverse the Trie and collect terms."""
        if node.is_end_of_word:
            results.append(node.standard_term)
        for child in node.children.values():
            self._dfs_collect(child, results)

# --- Initializing with Cameroon Priority Zoonotic Diseases (PZDs) ---
# See snippet [7]
disease_dictionary = [
    "peste des petits ruminants",
    "highly pathogenic avian influenza",
    "foot and mouth disease",
    "rabies",
    "brucellosis"
]

def get_trained_trie():
    trie = SymptomTrie()
    for disease in disease_dictionary:
        trie.insert(disease)
    return trie
