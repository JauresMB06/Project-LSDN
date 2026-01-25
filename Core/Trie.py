
from typing import Dict, List, Optional


class TrieNode:
    """Validated trie node with type-safe children dictionary."""
    def __init__(self) -> None:
        self.children: Dict[str, 'TrieNode'] = {}
        self.is_end_of_word: bool = False
        self.standard_term: Optional[str] = None


class SymptomTrie:
    """
    Prefix tree for livestock disease symptom taxonomy.
    
    Complexity:
        - Insert: O(L) where L is the length of the symptom string
        - Search/Prefix: O(L) where L is the prefix length
        - Autocomplete: O(L + K) where K is the number of results
    
    Attributes:
        root: Root node of the trie
    """
    
    def __init__(self) -> None:
        """Initialize an empty trie with a root node."""
        self.root = TrieNode()
    
    def insert(self, word: str) -> None:
        """
        Insert a standardized clinical sign or disease name into the Trie.
        
        Args:
            word: The symptom or disease term to insert
            
        Raises:
            ValueError: If word is empty or None
        """
        if not word or not word.strip():
            raise ValueError("Cannot insert empty or whitespace-only term")
        
        normalized_word = word.lower().strip()
        node = self.root
        
        for char in normalized_word:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        
        node.is_end_of_word = True
        node.standard_term = normalized_word
    
    def search(self, word: str) -> bool:
        """
        Check if a word exists in the trie.
        
        Args:
            word: The term to search for
            
        Returns:
            True if the word exists, False otherwise
        """
        if not word:
            return False
        
        node = self._get_node(word.lower().strip())
        return node is not None and node.is_end_of_word
    
    def _get_node(self, prefix: str) -> Optional[TrieNode]:
        """
        Get the node corresponding to a prefix.
        
        Args:
            prefix: The prefix to search for
            
        Returns:
            The node at the prefix, or None if not found
        """
        node = self.root
        for char in prefix:
            if char not in node.children:
                return None
            node = node.children[char]
        return node
    
    def autocomplete(self, prefix: str) -> List[str]:
        """
        Returns all standardized symptoms matching the prefix.
        Used by the CLI to reduce data entry errors in remote ZVSCC centers.
        
        Args:
            prefix: The prefix to search for
            
        Returns:
            List of matching symptom terms
            
        Raises:
            ValueError: If prefix is None
        """
        if prefix is None:
            raise ValueError("Prefix cannot be None")
        
        normalized_prefix = prefix.lower().strip()
        node = self._get_node(normalized_prefix)
        
        if node is None:
            return []
        
        results: List[str] = []
        self._dfs_collect(node, results)
        return results
    
    def _dfs_collect(self, node: TrieNode, results: List[str]) -> None:
        """
        Depth-first search helper to collect all terms from a node.
        
        Args:
            node: The current node to explore
            results: List to collect matching terms
        """
        if node.is_end_of_word and node.standard_term:
            results.append(node.standard_term)
        for child in node.children.values():
            self._dfs_collect(child, results)
    
    def starts_with(self, prefix: str) -> bool:
        """
        Check if any word in the trie starts with the given prefix.
        
        Args:
            prefix: The prefix to check
            
        Returns:
            True if any word starts with the prefix, False otherwise
        """
        if not prefix:
            return False
        return self._get_node(prefix.lower().strip()) is not None
    
    def get_word_count(self) -> int:
        """
        Get the total number of words in the trie.
        
        Returns:
            Number of words stored
        """
        count = 0
        for node in self._all_nodes(self.root):
            if node.is_end_of_word:
                count += 1
        return count
    
    def _all_nodes(self, node: TrieNode):
        """Generator to iterate through all nodes in the trie."""
        yield node
        for child in node.children.values():
            yield from self._all_nodes(child)


# ============================================================================
# Cameroon Priority Zoonotic Diseases (PZD) Configuration
# ============================================================================

# Cameroon Ministry of Livestock, Fisheries and Animal Industries (MINEPIA)
# Priority diseases with automatic P1 (Critical) classification
# Anthrax and Highly Pathogenic Avian Influenza are P1 (Critical)

CAMEROON_PRIORITY_DISEASES: List[str] = [
    # P1 - Critical (Zoonotic/Emergency)
    "anthrax",
    "highly pathogenic avian influenza",
    # P2 - High Priority
    "peste des petits ruminants",
    "foot and mouth disease",
    "rabies",
    "brucellosis",
    # P3 - Moderate Priority
    "contagious bovine pleuropneumonia",
    "newcastle disease",
    "african swine fever",
    "lumpy skin disease",
    # P4 - Surveillance
    "sheep pox",
    "goat pox",
    # P5 - Informational
    "helminthosis",
    "tick-borne diseases"
]


def get_trained_trie() -> SymptomTrie:
    """
    Create and populate a trie with Cameroon Priority Zoonotic Diseases.
    
    Returns:
        A SymptomTrie instance pre-loaded with Cameroon's priority diseases
    """
    trie = SymptomTrie()
    for disease in CAMEROON_PRIORITY_DISEASES:
        trie.insert(disease)
    return trie


# ============================================================================
# Validation Models for Data Entry
# ============================================================================

class SymptomEntry:
    """Validation model for symptom data entries."""
    def __init__(self, symptom_term: str, location: str, reporter_id: str):
        if not symptom_term or not symptom_term.strip():
            raise ValueError("Symptom term cannot be empty")
        if not location or not location.strip():
            raise ValueError("Location cannot be empty")
        if not reporter_id or not reporter_id.strip():
            raise ValueError("Reporter ID cannot be empty")

        self.symptom_term = symptom_term.strip()
        self.location = location.strip()
        self.reporter_id = reporter_id.strip()


def validate_symptom_entry(entry: Dict) -> SymptomEntry:
    """
    Validate a symptom entry dictionary using native validation.

    Args:
        entry: Dictionary containing symptom data

    Returns:
        Validated SymptomEntry object

    Raises:
        ValueError: If entry fails validation
    """
    return SymptomEntry(**entry)

