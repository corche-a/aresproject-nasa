# ARES: Planetary Analog Temporal Discovery Engine

This repository contains the source code for the **ARES** Next.js web application and offline NASA data pipeline. ARES evaluates **56 Earth endorheic basins** across **672 monthly climatology windows** to identify seasonal field-campaign analogues for key **Mars** and **Moon** exploration targets.

Developed during the **NASA Space Apps Challenge 2026** (CUGDL, Guadalajara, Jalisco, Mexico). ARES is an exploratory screening tool—not a substitute for field validation—and discloses missing measurements rather than fabricating values.

---

## Features

- **Interactive Explorer (`/explorer`)**
  - **NASA GIBS Satellite Imagery:** Switch between Blue Marble reference, Terra MODIS, Aqua MODIS, and Suomi NPP VIIRS true-color basemaps (`lib/gibs.ts`).
  - **5 Planetary Target Signatures:** Compare Earth basins against Jezero Crater, Gale Crater / Aeolis Palus, Meridiani Planum, Eberswalde Paleolake (Mars), and Shackleton Rim / Lunar Regolith (Moon).
  - **Custom 9-Metric Weighting:** Recompute weighted Euclidean similarity scores across analog fidelity and operational screening dimensions (`lib/similarity.ts`) and inspect locations scoring ≥ 60%.
  - **Ask ARES (`/api/ask`):** Server-side Gemini assistant grounded in the selected Explorer context (`month`, `target`, `weights`), with automatic local fallback responses when no key is configured or the upstream API is unavailable.
- **Basin Detail Views (`/basin/[id]`)**
  - Pre-rendered pages for all 56 basins showing best climatology window, plain-language match/gap explanations, measured vs. derived parameters, visual Earth-vs-target comparison bars, and physical analogy limits (*gravity, surface pressure, radiation, temperature*).
  - Live reverse-geocoded country/address context via OpenStreetMap Nominatim (`/api/location`) and a live 2020 NASA POWER all-sky vs. clear-sky solar cloud-attenuation proxy (`/api/nasa-coverage`).
- **Transparency Pages (`/about`, `/method`)**
  - Documents data sources, proxy definitions, physical limits, and AI usage boundaries.

---

## Tech Stack

- **Framework:** Next.js 15 (App Router, `output: "standalone"`), React 19
- **Mapping:** Leaflet & React-Leaflet with NASA GIBS WMTS tiles
- **Testing:** Vitest (`lib/similarity.test.ts`)
- **Offline Data Pipeline:** Python (`pandas`, `numpy`, `requests`, and `pyarrow` for Parquet I/O)
- **Hosting:** AWS Amplify Hosting (`WEB_COMPUTE` SSR via `amplify.yml`)

---

## Similarity Model

Each basin-month record is scored using weighted Euclidean distance across 9 normalized indicators (`0`–`1`), grouped in the Explorer UI into:

1. **Analog fidelity (70% default weight):** `slope`, `mineral` (literature prior match), `thermal` (diurnal temperature range), `aridity` (derived from precipitation), and `dust` (derived from wind, aridity, and relative humidity).
2. **Base and launch operations (30% default weight):** `latitude` (8%), `elevation` (4%), `platform` (slope flatness, 10%), and `weather` (wind/humidity/precipitation screening proxy, 8%).

For missing products and scientific limitations in the checked-in dataset (`emit_integrated: false`), see [`MISSING_FIELDS.md`](MISSING_FIELDS.md).

---

## API Routes

| Route | Method | Description |
| --- | --- | --- |
| `/api/ask` | `POST` | Server-side Gemini query (`lib/ai.ts`) with local fallback handling (`public/data/briefs.json`). |
| `/api/basins` | `GET` | Returns all 672 basin-month records from `public/data/analogs_data.json`. |
| `/api/basins/[id]` | `GET` | Returns the 12 monthly records for a specific `basin_id`. |
| `/api/climate` | `GET` | Live 2015–2024 monthly NASA POWER proxy (`?lat=&lon=`). |
| `/api/nasa-coverage` | `GET` | Live 2020 monthly NASA POWER all-sky vs. clear-sky solar cloud-attenuation proxy (`?lat=&lon=&month=`). |
| `/api/location` | `GET` | OpenStreetMap Nominatim reverse geocoding (`?lat=&lon=&name=`). |

---

## Offline Data Pipeline

The checked-in dataset in `public/data/analogs_data.json` is generated offline from:

- **Input coordinates:** `data/raw/cuencas.csv` (56 basins)
- **Topography:** Copernicus DEM elevation and derived slope (`scripts/build_basins_base.py` via Open-Meteo Elevation API)
- **Climatology:** NASA POWER monthly climatology (`T2M_MAX`, `T2M_MIN`, `PRECTOTCORR`, `WS10M`, `RH2M`, `ALLSKY_SFC_SW_DWN`)
- **Mineralogy:** Currently literature priors (`emit_integrated: false`); AppEEARS `EMIT_L2B_MIN.001` ingestion steps are documented in [`scripts/README_PIPELINE.md`](scripts/README_PIPELINE.md).

---

## Project Structure

```text
aresproject-nasa/
├── app/
│   ├── api/                 # Next.js App Router API endpoints (ask, basins, climate, location, nasa-coverage)
│   ├── basin/[id]/          # Static/SSG basin detail pages (56 basins)
│   ├── explorer/            # Interactive map, weights, ranking, and Ask ARES page
│   ├── about/ & method/     # Data sources, limits, and transparency pages
│   └── page.tsx             # Landing page
├── components/              # Client UI and Leaflet/NASA GIBS map components
├── data/
│   ├── raw/cuencas.csv      # 56 basin coordinates
│   └── processed/           # Intermediate parquet and CSV tables
├── lib/                     # Similarity scoring, AI client, data loader, GIBS layers, POWER client
├── public/data/             # Generated analogs_data.json and fallback briefs.json
├── scripts/                 # Python pipeline scripts and AppEEARS EMIT request template
├── amplify.yml              # AWS Amplify Hosting build spec
├── DEPLOY.md                # AWS Amplify deployment notes
└── MISSING_FIELDS.md        # Explicit disclosure of unmeasured/unscored variables
```

---

## Deployment (AWS Amplify)

See [`DEPLOY.md`](DEPLOY.md) and [`amplify.yml`](amplify.yml) for Amplify Hosting (`WEB_COMPUTE` / Next.js SSR) setup. Set `GOOGLE_AI_API_KEY` (and optionally `GOOGLE_AI_MODEL`) as server environment variables in the Amplify Console before deploying—`amplify.yml` copies those two variables into `.env.production` at build time.

---

## Languages Used

| Language / Format | Function in the Project |
| --- | --- |
| **TypeScript (`.ts`)** | Implements backend Next.js API route handlers (`app/api/`), the 9-metric weighted similarity engine (`lib/similarity.ts`), the Google AI Studio Gemini client (`lib/ai.ts`), NASA GIBS/POWER data helpers (`lib/gibs.ts`, `lib/power.ts`, `lib/data.ts`), shared TypeScript types (`lib/types.ts`), and Vitest unit tests (`lib/similarity.test.ts`). |
| **TSX / React (`.tsx`)** | Powers the Next.js App Router pages (`app/`) and interactive client components (`components/`), including the Explorer controls, weight sliders, Ask ARES panel, basin comparison charts, and Leaflet/NASA GIBS map views. |
| **CSS (`.css`)** | Defines the visual layout, cards, typography, comparison bars, status badges, and map container styling (`app/globals.css`). |
| **Python (`.py`)** | Drives the offline scientific data pipeline (`scripts/build_basins_base.py`, `scripts/build_engine.py`) to fetch Copernicus DEM elevation/slope and NASA POWER monthly climatology, compute derived aridity/thermal/dust/slope indices, and output `public/data/analogs_data.json`. |
| **JSON & CSV / Parquet** | Stores the 56 basin coordinates (`data/raw/cuencas.csv`), processed tabular datasets (`data/processed/`), the compiled analog engine dataset (`public/data/analogs_data.json`), fallback Ask ARES responses (`public/data/briefs.json`), AppEEARS request templates, and project configuration (`package.json`, `tsconfig.json`). |
| **YAML (`.yml`)** | Configures the AWS Amplify Hosting build phases and `.next` SSR artifact output (`amplify.yml`). |
