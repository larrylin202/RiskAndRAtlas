# Setup
Assumes you're starting a terminal/command prompt in the folder.
Do these in separate terminals.

## Backend
1.	cd backend
2.  python -m venv venv
3.	source venv/bin/activate (or .\venv\Scripts\activate on Windows)
4.	pip install -r requirements.txt && python run.py

## Frontend
1.  cd frontend
2.  npm install
3.  npm run dev

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
│   │   ├── __init__.py               # Minimal Flask app factory & CORS setup
│   │   ├── config.py                 # Environment variable configurations
│   │   │
│   │   ├── api/                      # REST API routes (add files here as you build)
│   │   │   ├── __init__.py           # Empty package marker
│   │   │   └── hazards.py            # Earthquakes, wildfires, flood endpoints
│   │   │
│   │   ├── services/                 # External API fetchers & normalization
│   │   │   ├── __init__.py           # Empty package marker
│   │   │   ├── usgs_service.py       # USGS GeoJSON ingestion
│   │   │   ├── noaa_service.py       # NOAA weather / fire feeds
│   │   │   └── airnow_service.py     # EPA AirNow AQI ingestion
│   │   │
│   │   ├── scoring/                  # Risk & resilience calculation logic
│   │   │   ├── __init__.py           # Empty package marker
│   │   │   └── calculator.py         # 0–100 normalization formulas
│   │   │
│   │   └── utils/                    # Shared helper functions
│   │       ├── __init__.py           # Empty package marker
│   │       └── geo.py                # Coordinate math, distance, bounding boxes
│   │
│   ├── .env.example                  # Backend environment template
│   ├── requirements.txt              # Flask, flask-cors, requests, python-dotenv
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
├── .gitignore                        # node_modules, venv, .env, __pycache__
└── README.md
```