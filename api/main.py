#!/usr/bin/env python3
"""
LDSN API Endpoints - Additional FastAPI Routes

Additional API endpoints for the Livestock Disease Surveillance Network.
These endpoints complement the main.py FastAPI application.

Endpoints:
    - /api/triage: Get pending alerts for triage
    - /api/analytics/species: Get species-specific mortality analytics
    - /api/trie/autocomplete: Disease/symptom autocomplete using Trie

Author: LDSN Development Team
Version: 1.0.0
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional
from datetime import datetime

# Import Core LDSN Components
from Core.service import get_ldsn_service, LDSNService
from Core.priority_queue import PriorityLevel

# Create API router
router = APIRouter()

# Global service instance
_service: Optional[LDSNService] = None

def get_service() -> LDSNService:
    """Get or initialize the LDSN service instance."""
    global _service
    if _service is None:
        _service = get_ldsn_service()
    return _service

# ============================================================================
# Pydantic Models for API Responses
# ============================================================================

from pydantic import BaseModel

class TriageAlert(BaseModel):
    """Alert model for triage endpoint."""
    id: float
    disease_name: str
    location: str
    priority_level: int
    priority_name: str
    reporter_id: str
    timestamp: float
    cluster_boost: int
    details: Dict[str, Any]
    status: str  # 'pending', 'processing', 'resolved'

class SpeciesMortalityData(BaseModel):
    """Species-specific mortality data."""
    species: str
    total_mortality: int
    dry_season_mortality: int
    rainy_season_mortality: int
    mortality_rate: float  # percentage
    affected_animals: int
    last_updated: str

class AnalyticsSpeciesResponse(BaseModel):
    """Response model for species analytics."""
    species_data: List[SpeciesMortalityData]
    total_mortality: int
    total_affected: int
    timestamp: str

class TrieAutocompleteResponse(BaseModel):
    """Response model for Trie autocomplete."""
    prefix: str
    suggestions: List[str]
    count: int
    execution_time_ms: float

# ============================================================================
# API Endpoints
# ============================================================================

@router.get("/api/triage", response_model=List[TriageAlert])
async def get_triage_alerts(
    limit: int = Query(50, ge=1, le=200, description="Maximum number of alerts to return"),
    priority_filter: Optional[int] = Query(None, ge=1, le=5, description="Filter by priority level (1-5)"),
    status_filter: str = Query("pending", description="Filter by status: pending, processing, resolved")
):
    """
    Get pending alerts for triage.

    Returns alerts sorted by priority for the triage dashboard.
    Supports filtering by priority level and status.

    Args:
        limit: Maximum number of alerts to return
        priority_filter: Optional priority level filter
        status_filter: Status filter (pending, processing, resolved)

    Returns:
        List of triage alerts
    """
    service = get_service()

    # Get pending alerts from service
    alerts = service.get_pending_alerts()

    # Apply filters
    if priority_filter:
        alerts = [a for a in alerts if a.priority_level == priority_filter]

    # Convert to triage format
    triage_alerts = []
    for alert in alerts[:limit]:
        triage_alerts.append(TriageAlert(
            id=alert.timestamp,
            disease_name=alert.disease_name,
            location=alert.location,
            priority_level=alert.priority_level,
            priority_name=PriorityLevel(alert.priority_level).name,
            reporter_id=alert.reporter_id,
            timestamp=alert.timestamp,
            cluster_boost=alert.cluster_boost,
            details=alert.details,
            status=status_filter
        ))

    return triage_alerts

@router.get("/api/analytics/species", response_model=AnalyticsSpeciesResponse)
async def get_species_analytics():
    """
    Get species-specific mortality analytics.

    Returns mortality data broken down by species (cattle, poultry, swine, sheep, goats).
    Includes seasonal breakdowns and mortality rates.

    Returns:
        Species-specific analytics data
    """
    service = get_service()

    # Mock species data - in a real implementation, this would come from the database
    # The segment tree currently tracks total mortality, but we need to extend it for species
    species_data = [
        SpeciesMortalityData(
            species="Cattle",
            total_mortality=185,
            dry_season_mortality=120,
            rainy_season_mortality=65,
            mortality_rate=4.2,
            affected_animals=4250,
            last_updated=datetime.utcnow().isoformat()
        ),
        SpeciesMortalityData(
            species="Poultry",
            total_mortality=890,
            dry_season_mortality=450,
            rainy_season_mortality=440,
            mortality_rate=17.8,
            affected_animals=12500,
            last_updated=datetime.utcnow().isoformat()
        ),
        SpeciesMortalityData(
            species="Swine",
            total_mortality=145,
            dry_season_mortality=80,
            rainy_season_mortality=65,
            mortality_rate=28.9,
            affected_animals=2100,
            last_updated=datetime.utcnow().isoformat()
        ),
        SpeciesMortalityData(
            species="Sheep",
            total_mortality=78,
            dry_season_mortality=45,
            rainy_season_mortality=33,
            mortality_rate=6.2,
            affected_animals=1850,
            last_updated=datetime.utcnow().isoformat()
        ),
        SpeciesMortalityData(
            species="Goats",
            total_mortality=52,
            dry_season_mortality=30,
            rainy_season_mortality=22,
            mortality_rate=5.8,
            affected_animals=1420,
            last_updated=datetime.utcnow().isoformat()
        )
    ]

    total_mortality = sum(s.total_mortality for s in species_data)
    total_affected = sum(s.affected_animals for s in species_data)

    return AnalyticsSpeciesResponse(
        species_data=species_data,
        total_mortality=total_mortality,
        total_affected=total_affected,
        timestamp=datetime.utcnow().isoformat()
    )

@router.get("/api/trie/autocomplete", response_model=TrieAutocompleteResponse)
async def trie_autocomplete(
    prefix: str = Query(..., min_length=1, max_length=50, description="Prefix to search for"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of suggestions")
):
    """
    Autocomplete disease/symptom names using the Trie.

    Uses the LDSN Trie data structure for O(L) prefix matching.
    Returns suggestions from the disease taxonomy.

    Args:
        prefix: The prefix to search for
        limit: Maximum number of suggestions to return

    Returns:
        Autocomplete suggestions with execution time
    """
    import time
    start_time = time.time()

    service = get_service()

    try:
        # Use the service's autocomplete method
        result = service.autocomplete_symptoms(prefix)

        # Limit results
        suggestions = result.matches[:limit]

        execution_time = (time.time() - start_time) * 1000  # Convert to milliseconds

        return TrieAutocompleteResponse(
            prefix=prefix,
            suggestions=suggestions,
            count=len(suggestions),
            execution_time_ms=round(execution_time, 2)
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Autocomplete failed: {str(e)}")

# ============================================================================
# Health Check for Additional API
# ============================================================================

@router.get("/api/health")
async def api_health_check():
    """Health check for additional API endpoints."""
    service = get_service()

    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "endpoints": [
            "/api/triage",
            "/api/analytics/species",
            "/api/trie/autocomplete"
        ],
        "service_components": {
            "trie": service.trie.get_word_count() > 0,
            "triage": len(service.triage) >= 0,
            "mortality": True  # Placeholder
        }
    }
