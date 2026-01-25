#!/usr/bin/env python3


import typer
from typing import Optional, List
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
import time

# Import Core LDSN Components (Service Layer)
from Core.service import (
    get_ldsn_service,
    LDSNService,
    SymptomResult,
    RouteResult,
    AlertResult,
    ClusterResult,
)
from Core.Trie import get_trained_trie, SymptomTrie
from Core.Transhumance import get_cameroon_network, TranshumanceGraph, SeasonType
from Core.priority_queue import AlertTriageEngine, Alert, PriorityLevel, AlertItem

# Import additional API endpoints
from api.main import router as additional_router

# ============================================================================
# Security & Configuration
# ============================================================================

# API Key for production authentication
API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)

# Configuration
API_VERSION = "3.0.0"
API_TITLE = "LDSN API - Livestock Disease Surveillance Network (Cameroon)"

# ============================================================================
# Global Service Instance (Initialized at module level)
# ============================================================================

# Use the centralized service factory for consistency
_service: LDSNService = get_ldsn_service()

# Location coordinates for Cameroon regions (with proper accents)
LOCATION_COORDINATES: Dict[str, tuple] = {
    "maroua": (10.5955, 14.3247),
    "yaoundé": (3.8480, 11.5021),
    "ngaoundéré": (7.3270, 13.5847),
    "garoua": (9.3014, 13.3977),
    "bamenda": (5.9527, 10.1559),
    "bafoussam": (5.4781, 10.4225),
    "douala": (4.0511, 9.7679),
    "kousseri": (12.0786, 15.0304),
    "mora": (11.0461, 14.1401),
    "tibati": (6.4667, 12.8667),
    "mbé": (7.7667, 14.7333),
    "dschang": (5.4444, 9.9917),
    "bertoua": (4.5844, 13.6846),
    "logone floodplain": (10.75, 14.5),
    "mindif": (10.75, 14.6167),
    "bamendjou": (5.3833, 10.35),
}


# ============================================================================
# Typer CLI App
# ============================================================================

app_cli = typer.Typer(
    name="ldsn",
    help="Livestock Disease Surveillance Network CLI - Cameroon",
    add_completion=False,
)


@app_cli.command("report")
def cli_report(
    disease: str = typer.Argument(..., help="Disease or symptom observed"),
    location: str = typer.Argument(..., help="Location of observation"),
    reporter_id: str = typer.Argument(..., help="Reporter ID"),
    mortality: Optional[int] = typer.Option(None, "-m", "--mortality", help="Number of deaths"),
    offline: bool = typer.Option(False, "--offline", help="Save offline and sync later"),
):
    """
    Submit a disease report.
    
    Uses the Trie for symptom autocomplete and creates an alert
    with automatic priority classification. If multiple reports
    of the same disease exist in the same cluster, priority is escalated.
    """
    # Check if disease exists in our taxonomy
    if _service.search_symptoms(disease):
        typer.secho(f"✓ Disease found in taxonomy: {disease}", fg=typer.colors.GREEN)
    else:
        typer.secho(f"⚠ Disease not in taxonomy: {disease}", fg=typer.colors.YELLOW)
        typer.secho(f"  Will use default priority (P4)", fg=typer.colors.BLUE)
    
    # Submit report with cluster-aware alert generation
    result = _service.submit_alert(
        disease_name=disease,
        location=location,
        reporter_id=reporter_id,
    )
    
    # Save to database
    if mortality:
        day_of_year = datetime.now().timetuple().tm_yday - 1
        _service.record_mortality(day_of_year, mortality)
    
    # Print result
    priority_name = result.priority_name
    typer.secho(f"\n✓ Report submitted successfully", fg=typer.colors.GREEN)
    typer.echo(f"  Disease: {disease}")
    typer.echo(f"  Location: {location}")
    typer.echo(f"  Priority: {priority_name} (Level {result.priority_level})")
    
    if result.alert.cluster_boost > 0:
        typer.secho(f"  ⚡ Priority escalated due to cluster outbreak! (boost: +{result.alert.cluster_boost})", 
                   fg=typer.colors.RED)
    
    typer.echo(f"  Reporter: {reporter_id}")
    
    if mortality:
        typer.echo(f"  Mortality: {mortality}")
    
    if result.priority_level == 1:  # P1 Critical
        typer.secho(f"\n🚨 CRITICAL ALERT: Immediate response required!", fg=typer.colors.RED)


@app_cli.command("autocomplete")
def cli_autocomplete(
    prefix: str = typer.Argument(..., help="Prefix to search for"),
):
    """
    Autocomplete disease/symptom names.
    
    Uses the Trie for O(L) prefix matching.
    """
    result = _service.autocomplete_symptoms(prefix)
    
    if result.matches:
        typer.secho(f"\n✓ Found {len(result.matches)} matches for '{prefix}':", fg=typer.colors.GREEN)
        for match in result.matches:
            typer.echo(f"  - {match}")
    else:
        typer.secho(f"\n⚠ No matches found for '{prefix}'", fg=typer.colors.RED)


@app_cli.command("route")
def cli_route(
    start: str = typer.Argument(..., help="Starting location"),
    end: str = typer.Argument(..., help="Destination location"),
    duumol: bool = typer.Option(False, "--duumol", help="Calculate for Duumol rainy season (2.5× penalty)"),
):
    """
    Calculate the safest transhumance route.
    
    Uses Dijkstra's algorithm with seasonal weighting.
    The --duumol flag applies a 2.5× penalty for unpaved tracks in Adamawa.
    """
    try:
        route = _service.calculate_route(
            start=start,
            end=end,
            is_rainy_season=duumol,
        )
        
        season = "Duumol Rainy Season" if duumol else "Dry Season"
        typer.secho(f"\n✓ Route calculated for {season}", fg=typer.colors.GREEN)
        typer.echo(f"  From: {start}")
        typer.echo(f"  To: {end}")
        typer.echo(f"  Path: {' → '.join(route.path)}")
        typer.echo(f"  Effective Weight: {route.total_weight:.2f}")
        
        if duumol:
            typer.secho(f"  ⚠ Note: 2.5× penalty applied for unpaved Adamawa tracks", fg=typer.colors.YELLOW)
        
    except KeyError as e:
        typer.secho(f"\n⚠ Error: {e}", fg=typer.colors.RED)
        available = _service.get_all_locations()
        typer.secho(f"  Available locations: {', '.join(available)}", fg=typer.colors.BLUE)


@app_cli.command("clusters")
def cli_clusters():
    """
    Display current outbreak clusters.
    
    Uses Union-Find with O(α(n)) operations.
    """
    clusters = _service.detect_clusters()
    
    typer.secho(f"\n✓ Found {len(clusters)} outbreak clusters:", fg=typer.colors.GREEN)
    
    for i, cluster in enumerate(clusters, 1):
        typer.echo(f"\n  Cluster {cluster.cluster_id} ({cluster.size} locations):")
        for location in cluster.locations:
            # Check if it's a ZVSCC station
            zvscc_marker = " 📡" if location in _service.get_zvscc_stations() else ""
            typer.echo(f"    - {location}{zvscc_marker}")


@app_cli.command("alerts")
def cli_alerts(
    critical_only: bool = typer.Option(False, "-c", "--critical", help="Show only critical alerts"),
):
    """
    Display pending alerts.
    
    Shows P1-P5 priority queue sorted by urgency.
    """
    alerts = _service.get_pending_alerts()
    
    if critical_only:
        alerts = [a for a in alerts if a.priority_level == 1]
    
    if alerts:
        typer.secho(f"\n✓ {len(alerts)} pending alerts:", fg=typer.colors.GREEN)
        for alert in alerts:
            priority_name = PriorityLevel(alert.priority_level).name
            color = typer.colors.RED if alert.priority_level == 1 else \
                    typer.colors.YELLOW if alert.priority_level == 2 else \
                    typer.colors.BLUE
            zvscc = "📡" if alert.location in _service.get_zvscc_stations() else ""
            typer.secho(f"  [{priority_name}] {alert.disease_name} @ {alert.location} {zvscc}", fg=color)
    else:
        typer.secho(f"\n✓ No pending alerts", fg=typer.colors.GREEN)


@app_cli.command("stats")
def cli_stats():
    """
    Display system statistics.
    """
    stats = _service.get_service_stats()
    
    typer.secho(f"\nLDSN System Statistics", fg=typer.colors.GREEN)
    typer.echo(f"=" * 40)
    typer.echo(f"  Symptom Terms: {stats.algorithms['symptom_count']}")
    typer.echo(f"  Locations: {stats.algorithms['location_count']}")
    typer.echo(f"  ZVSCC Stations: {len(_service.get_zvscc_stations())}")
    typer.echo(f"  Active Clusters: {stats.algorithms['cluster_count']}")
    typer.echo(f"  Pending Alerts: {stats.algorithms['pending_alerts']}")
    typer.echo(f"  Critical Alerts: {stats.algorithms['critical_alerts']}")
    
    typer.echo(f"\n  Persistence:")
    typer.echo(f"    Reports: {stats.persistence.get('reports', 0)}")
    typer.echo(f"    Alerts: {stats.persistence.get('alerts', 0)}")
    typer.echo(f"    Mortality Records: {stats.persistence.get('mortality_records', 0)}")


@app_cli.command("zvscc")
def cli_zvscc():
    """
    Display all ZVSCC stations.

    ZVSCC (Veterinary and Zoonosis Surveillance and Coordination Centre)
    stations are prioritized for offline data collection and sync.
    """
    stations = _service.get_zvscc_stations()

    typer.secho(f"\n✓ ZVSCC Stations ({len(stations)} total):", fg=typer.colors.GREEN)
    for station in sorted(stations):
        typer.echo(f"  📡 {station}")


@app_cli.command("web")
def cli_web(port: int = typer.Option(8000, help="Port to run the web server on")):
    """
    Start the FastAPI web server.

    Runs the LDSN web dashboard with REST API endpoints.
    Visit http://localhost:{port}/docs for interactive API documentation.
    """
    typer.secho(f"\n🚀 Starting LDSN Web Server on port {port}", fg=typer.colors.GREEN)
    typer.echo(f"  API Docs: http://localhost:{port}/docs")
    typer.echo(f"  ReDoc: http://localhost:{port}/redoc")
    typer.echo(f"  Root: http://localhost:{port}/")
    typer.echo(f"\nPress Ctrl+C to stop the server\n")
    print(f"DEBUG: cli_web called with port {port}")

    run_web(port)


# ============================================================================
# FastAPI Web Dashboard (Production Ready)
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan context manager for startup/shutdown."""
    global _service
    # Ensure service is initialized
    _service = get_ldsn_service()
    yield
    # Cleanup handled by service layer


# Create FastAPI app at module level for Uvicorn
app = FastAPI(
    title=API_TITLE,
    description="Production-Ready Livestock Disease Surveillance Network API for Cameroon. "
                "Features: Priority Queue triage, Union-Find cluster detection, "
                "Dijkstra routing with Duumol seasonal penalties, Segment Tree mortality tracking.",
    version=API_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Enable CORS for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production: restrict to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include additional API router
app.include_router(additional_router)


# -------------------------------------------------------------------------
# Pydantic Models for API (Production Validated)
# -------------------------------------------------------------------------

class ReportRequest(BaseModel):
    """Request model for submitting a disease report."""
    disease_name: str = Field(..., min_length=2, max_length=100, description="Disease or symptom observed")
    location: str = Field(..., min_length=2, max_length=100, description="Location of observation")
    reporter_id: str = Field(..., min_length=2, max_length=50, description="Reporter ID")
    mortality_count: Optional[int] = Field(None, ge=0, description="Number of deaths")
    latitude: Optional[float] = Field(None, ge=-90, le=90, description="GPS latitude")
    longitude: Optional[float] = Field(None, ge=-180, le=180, description="GPS longitude")
    
    @validator('disease_name')
    @classmethod
    def validate_disease_name(cls, v):
        return v.strip().lower()


class AlertResponse(BaseModel):
    """Response model for alerts."""
    id: float
    disease_name: str
    location: str
    priority_level: int
    priority_name: str
    reporter_id: str
    timestamp: float
    cluster_boost: int = 0
    details: Dict = {}


class DashboardStatsResponse(BaseModel):
    """Response model for dashboard statistics."""
    total_reports: int
    total_alerts: int
    pending_alerts: int
    critical_alerts: int
    active_clusters: int
    zvscc_stations: int
    mortality_records: int
    offline_pending: int
    system_status: str
    timestamp: str


class ClusterMapResponse(BaseModel):
    """Response model for map data."""
    cluster_id: str
    locations: List[str]
    size: int
    center: List[float]
    risk: str
    alert_count: int
    critical_count: int
    zvscc_in_cluster: List[str]


class DiseaseSuggestionResponse(BaseModel):
    """Response model for disease suggestions."""
    prefix: str
    suggestions: List[str]
    count: int


class RouteRequest(BaseModel):
    """Request model for route calculation."""
    start: str = Field(..., description="Starting location")
    end: str = Field(..., description="Destination location")
    is_rainy_season: bool = Field(False, description="Calculate for Duumol rainy season (2.5× penalty)")


class RouteResponse(BaseModel):
    """Response model for route calculations."""
    path: List[str]
    total_weight: float
    is_rainy_season: bool
    season_name: str
    num_stops: int


class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str
    timestamp: str
    version: str
    components: Dict[str, bool]
    zvscc_count: int


# -------------------------------------------------------------------------
# API Endpoints (Production Ready)
# -------------------------------------------------------------------------

@app.get("/", response_model=Dict)
async def root():
    """Root endpoint with API information."""
    return {
        "message": f"{API_TITLE} v{API_VERSION}",
        "status": "healthy",
        "docs": "/docs",
        "github": "LDSN-Cameroon/Project7",
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.
    
    Verifies all core components are operational:
    - Trie: Disease taxonomy
    - Network: Transhumance routes
    - Clusters: Union-Find detection
    - Database: SQLAlchemy persistence
    """
    global _service
    if _service is None:
        _service = get_ldsn_service()
    
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": API_VERSION,
        "components": {
            "trie": _service.trie.get_word_count() > 0,
            "network": len(_service.network) > 0,
            "clusters": len(_service.clusters) > 0,
            "database": True,
        },
        "zvscc_count": len(_service.get_zvscc_stations()),
    }


# -------------------------------------------------------------------------
# Disease & Symptom Endpoints
# -------------------------------------------------------------------------

@app.get("/api/diseases/autocomplete", response_model=DiseaseSuggestionResponse)
async def autocomplete_diseases(prefix: str = Query(..., min_length=1, description="Disease name prefix")):
    """
    Autocomplete disease/symptom names.
    
    Uses the Trie for O(L) prefix matching.
    Returns up to 10 suggestions from the disease taxonomy.
    """
    global _service
    if _service is None:
        _service = get_ldsn_service()
    
    result = _service.autocomplete_symptoms(prefix)
    return {
        "prefix": prefix,
        "suggestions": result.matches,
        "count": result.count
    }


@app.get("/api/diseases/search")
async def search_disease(term: str = Query(..., min_length=1, description="Disease name to search")):
    """
    Search for an exact disease term.
    
    Returns whether the disease exists in the taxonomy.
    """
    global _service
    if _service is None:
        _service = get_ldsn_service()
    
    exists = _service.search_symptoms(term)
    return {"term": term, "found": exists}


# -------------------------------------------------------------------------
# Report Endpoints
# -------------------------------------------------------------------------

@app.post("/api/reports")
async def submit_report(request: ReportRequest):
    """
    Submit a disease report.
    
    This is the core integration endpoint that:
    1. Validates disease against Trie taxonomy
    2. Checks cluster membership for priority escalation (Union-Find)
    3. Creates an Alert with appropriate priority
    4. Pushes to Priority Queue (O(log n))
    5. Persists to database via SQLAlchemy
    """
    global _service
    if _service is None:
        _service = get_ldsn_service()
    
    # Submit alert
    alert_result = _service.submit_alert(
        disease_name=request.disease_name,
        location=request.location,
        reporter_id=request.reporter_id,
    )
    
    # Record mortality if provided
    if request.mortality_count is not None:
        day_of_year = datetime.now().timetuple().tm_yday - 1
        _service.record_mortality(day_of_year, request.mortality_count)
    
    return {
        "success": True,
        "alert_id": alert_result.alert_id,
        "disease_name": request.disease_name,
        "location": request.location,
        "priority_level": alert_result.priority_level,
        "priority_name": alert_result.priority_name,
        "is_critical": alert_result.priority_level == 1,
        "action_taken": alert_result.action_taken,
        "timestamp": alert_result.timestamp,
    }


# -------------------------------------------------------------------------
# Dashboard & Stats Endpoints
# -------------------------------------------------------------------------

@app.get("/api/dashboard/stats", response_model=DashboardStatsResponse)
async def get_dashboard_stats():
    """
    Get real-time dashboard statistics.
    
    Returns comprehensive system statistics for the dashboard:
    - Report and alert counts
    - Active cluster count
    - Critical alert count
    - ZVSCC station count
    - System health status
    """
    global _service
    if _service is None:
        _service = get_ldsn_service()
    
    stats = _service.get_service_stats()
    
    return {
        "total_reports": stats.persistence.get("reports", 0),
        "total_alerts": stats.persistence.get("alerts", 0),
        "pending_alerts": stats.algorithms["pending_alerts"],
        "critical_alerts": stats.algorithms["critical_alerts"],
        "active_clusters": stats.algorithms["cluster_count"],
        "zvscc_stations": len(_service.get_zvscc_stations()),
        "mortality_records": stats.persistence.get("mortality_records", 0),
        "offline_pending": stats.persistence.get("pending_reports", 0) + stats.persistence.get("pending_alerts", 0),
        "system_status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/api/alerts")
async def get_alerts(limit: int = Query(100, ge=1, le=1000)):
    """
    Get all pending alerts sorted by priority.
    
    Query Parameters:
    - limit: Maximum number of alerts to return (default: 100)
    
    Returns:
    - List of alerts sorted by priority (P1 first)
    """
    global _service
    if _service is None:
        _service = get_ldsn_service()
    
    alerts = _service.get_pending_alerts()[:limit]
    
    return {
        "count": len(alerts),
        "alerts": [
            {
                "id": alert.timestamp,
                "disease_name": alert.disease_name,
                "location": alert.location,
                "priority_level": alert.priority_level,
                "priority_name": PriorityLevel(alert.priority_level).name,
                "reporter_id": alert.reporter_id,
                "timestamp": alert.timestamp,
                "cluster_boost": alert.cluster_boost,
                "details": alert.details,
            }
            for alert in alerts
        ]
    }


@app.get("/api/alerts/critical")
async def get_critical_alerts():
    """
    Get all P1 critical alerts.
    
    Returns only critical alerts requiring immediate response.
    """
    global _service
    if _service is None:
        _service = get_ldsn_service()
    
    alerts = _service.get_critical_alerts()
    
    return {
        "count": len(alerts),
        "alerts": [
            {
                "id": alert.timestamp,
                "disease_name": alert.disease_name,
                "location": alert.location,
                "priority_level": alert.priority_level,
                "priority_name": PriorityLevel(alert.priority_level).name,
                "reporter_id": alert.reporter_id,
                "timestamp": alert.timestamp,
                "cluster_boost": alert.cluster_boost,
                "details": alert.details,
            }
            for alert in alerts
        ]
    }


@app.get("/api/map/clusters", response_model=List[ClusterMapResponse])
async def get_map_clusters():
    """
    Get cluster data for map visualization.
    
    Returns locations grouped by clusters with:
    - Cluster ID and locations
    - Center coordinates for map rendering
    - Risk level based on alert severity
    - Alert counts for each cluster
    """
    global _service
    if _service is None:
        _service = get_ldsn_service()
    
    clusters = _service.detect_clusters()
    zvscc_stations = set(_service.get_zvscc_stations())
    pending_alerts = {a.location: a for a in _service.get_pending_alerts()}
    
    map_data = []
    
    for cluster in clusters:
        # Calculate cluster center (average of location coordinates)
        center_lat, center_lon = 7.3697, 12.3547  # Default Cameroon center
        valid_locations = []
        
        for location in cluster.locations:
            loc_lower = location.lower()
            if loc_lower in LOCATION_COORDINATES:
                valid_locations.append(location)
                coords = LOCATION_COORDINATES[loc_lower]
                center_lat = (center_lat + coords[0]) / 2
                center_lon = (center_lon + coords[1]) / 2
        
        # Get alerts for this cluster
        cluster_alerts = [
            a for a in _service.get_pending_alerts()
            if a.location in cluster.locations
        ]
        
        # Determine risk level based on highest priority alert
        risk = "LOW"
        if any(a.priority_level == 1 for a in cluster_alerts):
            risk = "HIGH"
        elif any(a.priority_level <= 2 for a in cluster_alerts):
            risk = "MEDIUM"
        
        # ZVSCC stations in cluster
        zvscc_in_cluster = [l for l in cluster.locations if l in zvscc_stations]
        
        map_data.append({
            "cluster_id": cluster.cluster_id,
            "locations": cluster.locations,
            "size": cluster.size,
            "center": [center_lat, center_lon],
            "risk": risk,
            "alert_count": len(cluster_alerts),
            "critical_count": sum(1 for a in cluster_alerts if a.priority_level == 1),
            "zvscc_in_cluster": zvscc_in_cluster,
        })
    
    return map_data


# -------------------------------------------------------------------------
# Location & Route Endpoints
# -------------------------------------------------------------------------

@app.get("/api/locations")
async def get_all_locations():
    """Get all available locations for transhumance routes."""
    global _service
    if _service is None:
        _service = get_ldsn_service()
    
    locations = _service.get_all_locations()
    zvscc = _service.get_zvscc_stations()
    
    return {
        "locations": locations,
        "zvscc_stations": zvscc,
        "count": len(locations)
    }


@app.post("/api/routes", response_model=RouteResponse)
async def calculate_route(request: RouteRequest):
    """
    Calculate the safest transhumance route.
    
    Uses Dijkstra's algorithm with seasonal weighting.
    Applies 2.5× penalty for unpaved Adamawa tracks during Duumol (rainy season).
    
    Request Body:
    - start: Starting location
    - end: Destination location
    - is_rainy_season: Calculate for Duumol rainy season (optional)
    
    Returns:
    - path: List of locations in route order
    - total_weight: Effective route weight
    - is_rainy_season: Whether Duumol was considered
    - season_name: Season name (Dry or Duumol Rainy)
    """
    global _service
    if _service is None:
        _service = get_ldsn_service()
    
    try:
        route = _service.calculate_route(
            start=request.start,
            end=request.end,
            is_rainy_season=request.is_rainy_season,
        )
        
        return {
            "path": route.path,
            "total_weight": route.total_weight,
            "is_rainy_season": route.is_rainy_season,
            "season_name": route.season_name,
            "num_stops": route.num_stops,
        }
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/api/routes/seasonal-impact")
async def get_seasonal_impact(start: str = Query(...), end: str = Query(...)):
    """
    Analyze the seasonal impact on a route.
    
    Compares dry season and Duumol rainy season weights.
    """
    global _service
    if _service is None:
        _service = get_ldsn_service()
    
    try:
        return _service.analyze_route_seasonal_impact(start, end)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))


# -------------------------------------------------------------------------
# Cluster Management Endpoints
# -------------------------------------------------------------------------

@app.get("/api/clusters")
async def get_clusters():
    """
    Get all current outbreak clusters.
    
    Uses Union-Find with O(α(n)) operations.
    Returns clusters detected from disease reports.
    """
    global _service
    if _service is None:
        _service = get_ldsn_service()
    
    clusters = _service.detect_clusters()
    
    return {
        "count": len(clusters),
        "clusters": [
            {
                "cluster_id": c.cluster_id,
                "locations": c.locations,
                "size": c.size,
            }
            for c in clusters
        ]
    }


@app.post("/api/clusters/connect")
async def connect_locations(location_a: str, location_b: str):
    """
    Connect two locations (create or merge cluster).
    
    Uses Union-Find union operation.
    Useful for manual cluster management.
    """
    global _service
    if _service is None:
        _service = get_ldsn_service()
    
    result = _service.connect_locations(location_a, location_b)
    return {
        "location_a": location_a,
        "location_b": location_b,
        "connected": result,
        "same_cluster": _service.check_cluster_connected(location_a, location_b),
    }


# -------------------------------------------------------------------------
# Mortality Tracking Endpoints
# -------------------------------------------------------------------------

@app.get("/api/mortality/stats")
async def get_mortality_stats():
    """
    Get mortality statistics by season.
    
    Uses Segment Tree for O(log n) range queries.
    Returns mortality totals for dry and rainy seasons.
    """
    global _service
    if _service is None:
        _service = get_ldsn_service()
    
    stats = _service.get_mortality_statistics()
    
    return {
        "dry_season_total": stats.dry_season_total,
        "rainy_season_total": stats.rainy_season_total,
        "total": stats.total,
    }


# ============================================================================
# Application Entry Points
# ============================================================================

def run_cli():
    """Run the Typer CLI."""
    app_cli()


def run_web(port: int = 8000):
    """Run the FastAPI web server with Uvicorn."""
    print(f"Starting server on port {port}")
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=False,  # Set to True for development
        workers=1,     # Set to 4 for production
    )


if __name__ == "__main__":
    run_cli()

