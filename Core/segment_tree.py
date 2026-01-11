"""
Livestock Disease Surveillance Network (LDSN) - Segment Tree

Segment tree for efficient range queries on livestock mortality data.
Implements Point Updates and Range Sum Queries in O(log n) complexity.

Designed for temporal mortality tracking across Cameroon's regions.

Author: LDSN Development Team
Version: 2.0.0
"""

from typing import List, Optional


class SegmentTreeConfig:
    """Configuration model for segment tree initialization."""
    def __init__(self, size: int, validate_size: bool = True):
        if validate_size and size < 1:
            raise ValueError("Size must be at least 1")
        self.size = size
        self.validate_size = validate_size


class MortalitySegmentTree:
    """
    Segment Tree for efficient range sum queries on mortality data.
    
    Complexity:
        - Build: O(n)
        - Point Update: O(log n)
        - Range Query: O(log n)
    
    This implementation uses a 1-indexed binary tree representation
    stored in a flat array for cache efficiency.
    
    Attributes:
        size: Number of data points (e.g., 365 days)
        tree: Flat array storing segment tree nodes
    """
    
    # Class-level constants for validation
    MIN_SIZE = 1
    MAX_SIZE = 10_000_000  # 10 million data points
    
    def __init__(self, size: int) -> None:
        """
        Initialize the segment tree with a specified size.
        
        Args:
            size: Number of data points (e.g., 365 for daily mortality tracking)
            
        Raises:
            ValueError: If size is not a positive integer
        """
        if not isinstance(size, int):
            raise ValueError(f"Size must be an integer, got {type(size).__name__}")
        if size < self.MIN_SIZE:
            raise ValueError(f"Size must be at least {self.MIN_SIZE}, got {size}")
        if size > self.MAX_SIZE:
            raise ValueError(f"Size exceeds maximum allowed ({self.MAX_SIZE})")
        
        self.size = size
        # Use 4 * size as safe upper bound for segment tree array
        self.tree: List[int] = [0] * (4 * size)
    
    def build(self, data: List[int]) -> None:
        """
        Build the segment tree from an initial data array.
        
        Args:
            data: Initial mortality counts for each data point
            
        Raises:
            ValueError: If data length doesn't match tree size
        """
        if len(data) != self.size:
            raise ValueError(
                f"Data length ({len(data)}) must match tree size ({self.size})"
            )
        self._build_recursive(1, 0, self.size - 1, data)
    
    def _build_recursive(
        self, node: int, start: int, end: int, data: List[int]
    ) -> None:
        """
        Recursively build the segment tree.
        
        Args:
            node: Current tree node index
            start: Start index of the segment
            end: End index of the segment
            data: Source data array
        """
        if start == end:
            self.tree[node] = data[start]
            return
        
        mid = (start + end) // 2
        left_child = 2 * node
        right_child = 2 * node + 1
        
        self._build_recursive(left_child, start, mid, data)
        self._build_recursive(right_child, mid + 1, end, data)
        self.tree[node] = self.tree[left_child] + self.tree[right_child]
    
    def update(self, index: int, value: int) -> None:
        """
        Update the value at a specific index.
        
        Args:
            index: Index to update (0-based)
            value: New value to set
            
        Raises:
            ValueError: If index is out of bounds
        """
        if index < 0 or index >= self.size:
            raise ValueError(
                f"Index {index} out of bounds [0, {self.size - 1}]"
            )
        self._update_recursive(1, 0, self.size - 1, index, value)
    
    def _update_recursive(
        self, node: int, start: int, end: int, index: int, value: int
    ) -> None:
        """
        Recursively update a value in the segment tree.
        
        Args:
            node: Current tree node index
            start: Start index of the segment
            end: End index of the segment
            index: Index to update
            value: New value to set
        """
        if start == end:
            self.tree[node] = value
            return
        
        mid = (start + end) // 2
        if index <= mid:
            self._update_recursive(2 * node, start, mid, index, value)
        else:
            self._update_recursive(2 * node + 1, mid + 1, end, index, value)
        
        self.tree[node] = self.tree[2 * node] + self.tree[2 * node + 1]
    
    def query_range(self, left: int, right: int) -> int:
        """
        Query the sum of values in the range [left, right].
        
        Args:
            left: Left bound of the range (inclusive)
            right: Right bound of the range (inclusive)
            
        Returns:
            Sum of values in the specified range
            
        Raises:
            ValueError: If range is invalid
        """
        if left < 0 or right >= self.size or left > right:
            raise ValueError(
                f"Invalid range [{left}, {right}]. Must be within [0, {self.size - 1}]"
            )
        return self._query_recursive(1, 0, self.size - 1, left, right)
    
    def _query_recursive(
        self, node: int, start: int, end: int, left: int, right: int
    ) -> int:
        """
        Recursively query a range sum.
        
        Args:
            node: Current tree node index
            start: Start index of the segment
            end: End index of the segment
            left: Query left bound
            right: Query right bound
            
        Returns:
            Sum of values in the query range
        """
        # No overlap
        if right < start or end < left:
            return 0
        
        # Total overlap
        if left <= start and end <= right:
            return self.tree[node]
        
        # Partial overlap
        mid = (start + end) // 2
        left_sum = self._query_recursive(2 * node, start, mid, left, right)
        right_sum = self._query_recursive(2 * node + 1, mid + 1, end, left, right)
        return left_sum + right_sum
    
    def query_single(self, index: int) -> int:
        """
        Query the value at a single index.
        
        Args:
            index: Index to query (0-based)
            
        Returns:
            Value at the specified index
            
        Raises:
            ValueError: If index is out of bounds
        """
        if index < 0 or index >= self.size:
            raise ValueError(
                f"Index {index} out of bounds [0, {self.size - 1}]"
            )
        return self._query_recursive(1, 0, self.size - 1, index, index)
    
    def get_total(self) -> int:
        """
        Get the total sum of all values in the tree.
        
        Returns:
            Total sum of all values
        """
        return self.tree[1]
    
    def __len__(self) -> int:
        """Return the size of the data array."""
        return self.size


# ============================================================================
# Cameroon Mortality Data Utilities
# ============================================================================

# Cameroon regional mortality tracking periods
# Adamawa (Adamawa Region): June-September (Transhumance season)
# Far North (Extrême-Nord): July-October (Rainy season)
# West (Ouest): Year-round (Poultry production)

class CameroonMortalityTracker:
    """
    Convenience wrapper for Cameroon-specific mortality tracking.
    
    Provides methods for querying regional mortality statistics
    aligned with Cameroon's climatic and seasonal patterns.
    """
    
    # Standard day ranges for Cameroon seasons
    DRY_SEASON_DAYS = (31, 151)  # February-May
    RAINY_SEASON_DAYS = (181, 273)  # July-September (Duumol)
    
    def __init__(self, days: int = 365) -> None:
        """
        Initialize mortality tracker with specified number of days.
        
        Args:
            days: Number of days to track (default: 365)
        """
        self.tree = MortalitySegmentTree(days)
    
    def record_mortality(self, day: int, count: int) -> None:
        """
        Record mortality for a specific day.
        
        Args:
            day: Day number (0-based)
            count: Number of deaths
        """
        self.tree.update(day, count)
    
    def get_dry_season_mortality(self) -> int:
        """
        Get total mortality during dry season.
        
        Returns:
            Total mortality count for dry season period
        """
        return self.tree.query_range(*self.DRY_SEASON_DAYS)
    
    def get_rainy_season_mortality(self) -> int:
        """
        Get total mortality during rainy season (Duumol).
        
        Returns:
            Total mortality count for rainy season period
        """
        return self.tree.query_range(*self.RAINY_SEASON_DAYS)
    
    def get_total_mortality(self) -> int:
        """
        Get total mortality across all tracked days.
        
        Returns:
            Total mortality count
        """
        return self.tree.get_total()
    
    def bulk_load(self, mortality_data: List[int]) -> None:
        """
        Load mortality data from a list.
        
        Args:
            mortality_data: List of daily mortality counts
        """
        self.tree.build(mortality_data)


# ============================================================================
# Validation Models
# ============================================================================

class MortalityEntry(BaseModel):
    """Pydantic model for validating mortality data entries."""
    location: str
    day: int
    mortality_count: int
    disease_suspected: Optional[str] = None
    
    class Config:
        min_number_day = 0
        min_number_mortality_count = 0


def validate_mortality_entry(entry: dict) -> MortalityEntry:
    """
    Validate a mortality entry dictionary using Pydantic.
    
    Args:
        entry: Dictionary containing mortality data
        
    Returns:
        Validated MortalityEntry object
        
    Raises:
        ValidationError: If entry fails validation
    """
    return MortalityEntry(**entry)

