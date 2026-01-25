# Livestock Disease Surveillance Network (LDSN)

A comprehensive 3-tier architecture system for real-time epidemiological monitoring in Cameroon, featuring advanced algorithmic data structures optimized for veterinary surveillance challenges.

## Table of Contents

- [Features](#features)
- [System Architecture](#system-architecture)
- [Installation](#installation)
- [Setup Instructions](#setup-instructions)
- [Usage](#usage)
- [Test Cases](#test-cases)
- [Sample Data](#sample-data)
- [API Documentation](#api-documentation)
- [Contributing](#contributing)
- [License](#license)

## Features

- **Symptom Autocomplete**: Trie-based disease name suggestions
- **Mortality Tracking**: Segment tree for efficient range queries
- **Cluster Detection**: Union-Find for outbreak pattern recognition
- **Alert Triage**: Priority queue with automatic P1-P5 classification
- **Route Optimization**: Dijkstra's algorithm with seasonal weighting
- **Offline Capability**: Store-and-forward persistence
- **Dual Interface**: CLI and web dashboard
- **Real-time Monitoring**: WebSocket-based live updates

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                       │
│  ┌─────────────────┐    ┌──────────────────────────────┐  │
│  │   CLI (Typer)   │    │   Web Dashboard (FastAPI)   │  │
│  │                 │    │                              │  │
│  │ • report        │    │ • REST API endpoints         │  │
│  │ • route         │    │ • Stats visualization        │  │
│  │ • sync          │    │ • Mortality range queries    │  │
│  │ • clusters      │    │ • Cluster visualization      │  │
│  └─────────────────┘    └──────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     SERVICE LAYER                           │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                   LDSNService                        │  │
│  │                                                      │  │
│  │  • Symptom Autocomplete   • Route Calculation       │  │
│  │  • Cluster Detection      • Alert Triage            │  │
│  │  • Mortality Tracking     • Persistence Management  │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      DATA LAYER                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐ │
│  │   Core       │  │  Database    │  │  Persistence     │ │
│  │ Algorithms   │  │  (SQLAlchemy)│  │  (SQLite/JSON)   │ │
│  │              │  │              │  │                  │  │
│  │ • Trie       │  │ • Reports    │  │ • Store-and-     │  │
│  │ • Seg. Tree  │  │ • Alerts     │  │   Forward        │  │
│  │ • Union-Find │  │ • Mortality  │  │ • Offline Cache  │  │
│  │ • P-Queue    │  │ • Clusters   │  │ • Sync Manager   │  │
│  │ • Graph      │  │              │  │                  │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Installation

### Prerequisites

- Python 3.8+
- Node.js 16+ (for frontend)
- SQLite3

### Backend Setup

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd project7
   ```

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run database migrations:**
   ```bash
   python -c "from Core.database_manager import DatabaseManager; db = DatabaseManager(); db.create_tables()"
   ```

### Frontend Setup

1. **Navigate to frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install Node.js dependencies:**
   ```bash
   npm install
   # or
   yarn install
   # or
   pnpm install
   ```

3. **Build the frontend:**
   ```bash
   npm run build
   ```

## Setup Instructions

### Quick Start

1. **Run the complete system:**
   ```bash
   # Start both backend and frontend
   ./start_frontend.bat
   ```

2. **Or run components separately:**

   **Backend only:**
   ```bash
   python main.py
   ```

   **Frontend only:**
   ```bash
   ./start_frontend_only.bat
   ```

### Environment Configuration

Create a `.env` file in the root directory:

```env
# Database
DATABASE_URL=sqlite:///ldsn_data.db

# API
API_HOST=0.0.0.0
API_PORT=8000

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000

# Logging
LOG_LEVEL=INFO
```

### Offline Mode Setup

The system automatically detects connectivity and switches to offline mode:

```python
from Core.service import get_ldsn_service
service = get_ldsn_service()

# Reports are automatically cached when offline
service.submit_report("anthrax", "Maroua", "VET-001", mortality=5)

# Sync when connectivity returns
service.sync_offline_data()
```

## Usage

### CLI Commands

```bash
# Submit disease report with auto-triage
ldsn report anthrax Maroua VET-001 --mortality 5

# Autocomplete disease symptoms
ldsn autocomplete peste

# Calculate safe transhumance route
ldsn route Ngaoundere Maroua --rainy

# View pending alerts
ldsn alerts --critical

# Sync offline data
ldsn sync

# Display system statistics
ldsn stats
```

### Web Interface

Access the dashboard at `http://localhost:3000`:

- **Report Page**: Submit disease reports with autocomplete
- **Analytics Page**: View mortality trends and statistics
- **Triage Page**: Monitor and manage alerts
- **Health Page**: System health and performance metrics

### API Endpoints

```bash
# Submit report
POST /api/reports
{
  "disease": "anthrax",
  "location": "Maroua",
  "reporter_id": "VET-001",
  "mortality_count": 5
}

# Get autocomplete suggestions
GET /api/symptoms/autocomplete?prefix=peste

# Calculate route
POST /api/routes
{
  "start": "Ngaoundere",
  "end": "Maroua",
  "is_rainy_season": true
}

# Get mortality range
POST /api/mortality/range
{
  "start_day": 31,
  "end_day": 151
}
```

## Test Cases

### Running Tests

```bash
# Run all tests
python run_tests.py

# Run specific test suite
python -m pytest tests/test_pipeline.py -v

# Run stress tests
python tests/stress_test.py
```

### Core Algorithm Tests

```python
# 1. Trie Autocomplete Test
from Core.Trie import get_trained_trie
trie = get_trained_trie()
result = trie.autocomplete("peste")
assert "peste des petits ruminants" in result
print("✓ Trie test passed")

# 2. Transhumance Route Test
from Core.Transhumance import get_cameroon_network
network = get_cameroon_network()
_, dry_weight = network.calculate_safe_route("Ngaoundéré", "Maroua", False)
_, rainy_weight = network.calculate_safe_route("Ngaoundéré", "Maroua", True)
assert rainy_weight > dry_weight
print("✓ Transhumance test passed")

# 3. Union-Find Cluster Test
from Core.union_find import create_cameroon_outbreak_clusters
clusters = create_cameroon_outbreak_clusters()
assert clusters.connected("Ngaoundéré", "Tibati")
print("✓ Union-Find test passed")

# 4. Priority Queue Test
from Core.priority_queue import AlertTriage
triage = AlertTriage()
triage.push_alert("anthrax", "Maroua", "VET-001")
assert triage.get_critical_count() == 1
print("✓ Priority Queue test passed")

# 5. Segment Tree Test
from Core.segment_tree import CameroonMortalityTracker
tracker = CameroonMortalityTracker()
tracker.record_mortality(0, 100)
tracker.record_mortality(100, 50)
assert tracker.get_total_mortality() == 150
print("✓ Segment Tree test passed")

# 6. Service Integration Test
from Core.service import get_ldsn_service
service = get_ldsn_service()
alert = service.submit_alert("anthrax", "Maroua", "VET-001")
assert alert.priority_level == 1
print("✓ Service test passed")
```

### Performance Test Results

```
--- 365-DAY SEGMENT TREE STRESS TEST ---
Update efficiency: 365 updates in 0.000123s
Range query (dry season): 0.000045s
Range query (rainy season): 0.000044s
SUCCESS: O(log n) performance verified

--- UNION-FIND CLUSTER STRESS TEST ---
1000 locations, 500 unions: 0.001234s
Find operations: Effectively O(1)
SUCCESS: O(α(n)) performance verified
```

## Sample Data

### Disease Reports

```json
[
  {
    "disease": "anthrax",
    "location": "Maroua",
    "reporter_id": "VET-001",
    "mortality_count": 5,
    "timestamp": "2024-01-15T10:30:00Z"
  },
  {
    "disease": "peste des petits ruminants",
    "location": "Ngaoundéré",
    "reporter_id": "VET-002",
    "mortality_count": 12,
    "timestamp": "2024-01-15T11:00:00Z"
  }
]
```

### Mortality Data

```json
{
  "location": "Adamawa",
  "daily_mortality": [5, 3, 8, 2, 6, 9, 1, 4, 7, 2],
  "species_breakdown": {
    "cattle": 25,
    "poultry": 15,
    "swine": 8,
    "sheep": 12,
    "goats": 10
  },
  "seasonal_totals": {
    "dry_season": 45,
    "rainy_season": 36
  }
}
```

### Route Data

```json
{
  "start": "Ngaoundéré",
  "end": "Maroua",
  "season": "rainy",
  "path": ["Ngaoundéré", "Maroua"],
  "distance_km": 150,
  "effective_weight": 562.5,
  "risk_score": 0.0,
  "estimated_time_hours": 8.5
}
```

### Cluster Data

```json
{
  "clusters": [
    {
      "locations": ["Ngaoundéré", "Tibati", "Mbé"],
      "size": 3,
      "risk_level": "high",
      "connection_type": "transhumance_corridor"
    },
    {
      "locations": ["Maroua", "Kousseri"],
      "size": 2,
      "risk_level": "medium",
      "connection_type": "border_crossing"
    }
  ],
  "total_clusters": 8,
  "epidemiological_links": 12
}
```

## API Documentation

### REST API Endpoints

| Endpoint | Method | Description | Request Body |
|----------|--------|-------------|--------------|
| `/api/reports` | POST | Submit disease report | Report JSON |
| `/api/symptoms/autocomplete` | GET | Get autocomplete suggestions | Query param: `prefix` |
| `/api/routes` | POST | Calculate safe route | Route request JSON |
| `/api/mortality/range` | POST | Query mortality range | Range query JSON |
| `/api/clusters` | GET | Get outbreak clusters | - |
| `/api/alerts` | GET | Get pending alerts | Query params: `priority`, `limit` |
| `/api/stats` | GET | Get system statistics | - |

### WebSocket Events

```javascript
// Real-time alert updates
socket.on('alert:new', (alert) => {
  console.log('New alert:', alert);
});

// Mortality updates
socket.on('mortality:update', (data) => {
  console.log('Mortality update:', data);
});

// Cluster changes
socket.on('cluster:update', (clusters) => {
  console.log('Cluster update:', clusters);
});
```

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and add tests
4. Run the test suite: `python run_tests.py`
5. Commit your changes: `git commit -am 'Add feature'`
6. Push to the branch: `git push origin feature-name`
7. Submit a pull request

### Development Guidelines

- Follow PEP 8 for Python code
- Use TypeScript for frontend components
- Add comprehensive tests for new features
- Update documentation for API changes
- Ensure offline functionality works

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Livestock Disease Surveillance Network (LDSN)**  
*Real-time epidemiological monitoring for Cameroon*  
*Version 2.0.0*
