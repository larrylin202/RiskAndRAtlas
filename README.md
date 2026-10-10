# Setup
Assumes you're starting a terminal/command prompt in the folder.
Do these in separate terminals.

## Backend
1.	cd backend
2.  python -m venv venv
3.	source venv/bin/activate (or .\venv\Scripts\activate on Windows)
4.	pip install -r requirements.txt
5.  Copy `.env.example` to `.env` and set `DATABASE_URI` (see Database Setup below)
6.  python run.py

## Frontend
1.  cd frontend
2.  npm install
3.  npm run dev

# Database Setup
Hazard data lives in **PostgreSQL + PostGIS**. The API serves the map and risk score from
the database and never calls USGS / NIFC per request. A background thread re-fetches each
feed when its data is older than 10 minutes. Pick one of the two options below.

## Option A: shared Supabase database (just running/testing the app)
1. Ask a teammate for the Supabase `DATABASE_URI` (sent privately, never committed).
2. Put it in `backend/.env`:
   ```
   DATABASE_URI=postgresql://postgres.<project-ref>:<password>@aws-0-<region>.pooler.supabase.com:5432/postgres?sslmode=require
   ```
3. `python run.py`. The tables and data already exist, so there's nothing else to run.

## Option B: local Docker database (schema changes, experiments)
Requires Docker Desktop. From the repo root:
```
docker compose up -d
```
Then in `backend/` (with the venv active), with `DATABASE_URI=postgresql+psycopg://rr:rr@localhost:5432/rr_atlas` in `.env`:
```
flask db upgrade     # creates PostGIS + all tables
flask ingest         # fills them from USGS, NIFC and RTFI (~1 min)
python run.py
```
`docker compose down` stops it (data is kept); `docker compose down -v` wipes it.

## Checking it works
Open http://localhost:5000/api/health. It returns `"database": "ok"` and when each feed
last refreshed, or **503** if the database is unreachable (check `DATABASE_URI`).

## Tables
| Table | What's in it |
|---|---|
| `hazard_features` | One row per hazard from every feed. `hazard_type` is `earthquake`, `wildfire` or `flood`; `geom` is the PostGIS geometry (points or polygons, SRID 4326); `properties` (JSONB) holds the feed's original fields, e.g. `properties["mag"]`; `observed_at` is when it happened. Unique on (`source`, `source_id`). |
| `ingest_runs` | One row per feed (`usgs`, `nifc`, `rtfi`): last attempt/success, feature count, last error. |

Models are in `backend/app/models.py`.


# What's Done
*   Initial scaffolding of full-stack architecture
    *   Route frontend requests starting with `/api` to the Flask backend on port 5000.
*   Environment setup
*   API routing setup
*   Interactive Geospatial Map (frontend/src/components/map/HazardMap.tsx)
*   Requesting user's location (frontend/src/components/map/LocationController.tsx)

# Known Bugs
*   

# Scaffold
```
root/
├── backend/
│   ├── app/
│   │   ├── __init__.py               # App factory, CORS, /api/health, flask ingest command
│   │   ├── config.py                 # Environment variable configurations
│   │   ├── extensions.py             # SQLAlchemy (db) and Flask-Migrate instances
│   │   ├── models.py                 # HazardFeature and IngestRun tables
│   │   │
│   │   ├── api/                      # REST API routes (add files here as you build)
│   │   │   ├── hazards.py            # Earthquakes, wildfires, floods (from DB), air quality
│   │   │   └── scoring.py            # /api/risk/score (PostGIS proximity query)
│   │   │
│   │   ├── services/                 # External feed fetchers & DB ingestion
│   │   │   ├── ingest.py             # upsert_features: shared upsert into hazard_features
│   │   │   ├── refresh.py            # Background refresh of stale feeds
│   │   │   ├── usgs.py               # USGS earthquakes
│   │   │   ├── nifc.py               # NIFC wildfire perimeters
│   │   │   └── rtfi.py               # USGS Real-Time Flood Impact
│   │   │
│   │   ├── scoring/                  # Risk & resilience calculation logic
│   │   │   ├── __init__.py           # Empty package marker
│   │   │   └── calculator.py         # 0–100 normalization formulas
│   │   │
│   │   └── utils/                    # Shared helper functions
│   │       ├── __init__.py           # Empty package marker
│   │       └── geo.py                # Coordinate math, distance, bounding boxes
│   │
│   ├── migrations/                   # Alembic migrations (flask db ...)
│   ├── .env.example                  # Backend environment template
│   ├── requirements.txt              # Flask, SQLAlchemy, GeoAlchemy2, psycopg, requests
│   └── run.py                        # Entry point: starts Flask on port 5000
│
├── frontend/
│   ├── public/
│   │   └── favicon.ico
│   │
│   ├── src/
│   │   ├── types/                    # Shared TypeScript interfaces & types
│   │   │   └── hazards.ts            # GeoJSON, feature properties, coordinate types
│   │   │
│   │   ├── components/
│   │   │   ├── map/
│   │   │   │   ├── HazardMap.tsx          # Main Leaflet map view
│   │   │   │   └── LocationController.tsx # Geolocation API handler
│   │   │   │
│   │   │   ├── search/               # Search bar & hazard chips (future)
│   │   │   └── panels/               # Risk snapshots & comparison cards (future)
│   │   │
│   │   ├── services/
│   │   │   └── api.ts                # Fetch wrapper for /api calls
│   │   │
│   │   ├── styles/
│   │   │   └── index.css             # Global CSS
│   │   │
│   │   ├── App.tsx                   # Top-level React component
│   │   ├── main.tsx                  # React DOM entry point
│   │   └── vite-env.d.ts             # CSS, image, and Vite ambient type declarations
│   │
│   ├── index.html                    # HTML root with Leaflet CDN stylesheet
│   ├── package.json                  # React, react-leaflet, leaflet, TypeScript
│   ├── tsconfig.json                 # TypeScript compiler configuration
│   ├── tsconfig.node.json            # Vite node environment config
│   └── vite.config.ts                # Vite config with /api reverse proxy to Flask
│
├── docker-compose.yml                # Local PostgreSQL + PostGIS (Database Setup, option B)
├── .gitignore                        # node_modules, venv, .env, __pycache__
└── README.md
```