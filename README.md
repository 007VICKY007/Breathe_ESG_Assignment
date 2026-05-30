# Breathe ESG — Emissions Ingestion Prototype

Enterprise ESG data ingestion for **Breathe ESG** tech intern assignment.

Ingests emissions data from three real-world source types (SAP, utility portals, corporate travel), normalizes to a canonical kgCO₂e model, and provides an analyst review dashboard before audit lock.

## Live deployment

| Service | URL | Notes |
|---------|-----|-------|
| **Frontend** | `https://<your-vercel-app>.vercel.app` | React analyst dashboard |
| **Backend API** | `https://<your-railway-app>.up.railway.app/api/v1/` | Django REST |
| **Health check** | `/api/v1/health/` | DB connectivity probe |

### Demo credentials

```
Username: demo
Password: demo12345
```

Created automatically on Railway deploy via `bootstrap_demo` management command.

## Architecture

```
┌─────────────┐     JWT      ┌──────────────────┐     Celery     ┌─────────────┐
│  React UI   │ ──────────► │  Django REST API │ ─────────────► │ Redis worker │
│  (Vercel)   │             │  (Railway web)   │                │  (Railway)   │
└─────────────┘             └────────┬─────────┘                └─────────────┘
                                     │
                              ┌──────▼──────┐
                              │ PostgreSQL  │
                              └─────────────┘
```

**Ingestion flow:** Upload → `IngestionJob(PENDING)` → Celery parse/normalize/dedup/flag → `EmissionRecord` rows → Analyst review → Lock for audit.

## Quick start (local)

### Backend

```bash
cd backend
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
copy .env.example .env
.\.venv\Scripts\python manage.py migrate
.\.venv\Scripts\python manage.py bootstrap_demo
.\.venv\Scripts\python manage.py runserver
```

With `CELERY_TASK_ALWAYS_EAGER=True` (default in dev), ingestion runs synchronously without Redis.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 — login with `demo` / `demo12345`.

### Sample data

Realistic exports in `sample_data/` (also downloadable from the UI):

- `sap_me2m_export.csv` — 50 rows, semicolon-delimited ME2M format
- `utility_meter_export.csv` — 36 rows, 3 meters × 12 billing periods
- `travel_concur_export.csv` — 31 rows, Concur TRX expense extract

Regenerate: `python scripts/generate_sample_data.py`

## Deployment

> **DNS not found on Railway?** See [docs/DEPLOYMENT_TROUBLESHOOTING.md](docs/DEPLOYMENT_TROUBLESHOOTING.md) — this is almost always missing **Public Networking → Generate Domain** on the **web** service, not a code issue.

### Railway (backend + worker + PostgreSQL + Redis)

1. Create Railway project with **PostgreSQL** and **Redis** plugins.
2. Create **two services** from the same repo:
   - **Web service:** Root Directory = `backend`, uses `railway.toml`
   - **Worker service:** Root Directory = `backend`, uses `railway.worker.toml` — **no public URL**
3. On the **WEB service only:** Settings → Networking → **Public Networking** → **Generate Domain**  
   Copy the `https://xxxx.up.railway.app` URL (not `.railway.internal`).
4. Set environment variables on **web + worker**:

```
DJANGO_SETTINGS_MODULE=breathe_esg.settings.production
SECRET_KEY=<random-64-char-string>
DATABASE_URL=${{Postgres.DATABASE_URL}}
REDIS_URL=${{Redis.REDIS_URL}}
RAILWAY_PUBLIC_DOMAIN=xxxx.up.railway.app
ALLOWED_HOSTS=xxxx.up.railway.app,.up.railway.app
CORS_ALLOWED_ORIGINS=https://your-frontend.vercel.app
CELERY_TASK_ALWAYS_EAGER=False
SECURE_SSL_REDIRECT=False
```

5. Verify: `https://xxxx.up.railway.app/api/v1/health/` returns `{"status":"healthy",...}`

### Vercel (frontend)

1. Import repo, set root directory to `frontend/`.
2. Environment variable:

```
VITE_API_BASE_URL=https://your-app.up.railway.app/api/v1
```

3. Deploy — `vercel.json` handles SPA routing.

## Documentation (graded)

| File | Contents |
|------|----------|
| [docs/MODEL.md](docs/MODEL.md) | Schema, multi-tenancy, dedup, audit trail |
| [docs/DECISIONS.md](docs/DECISIONS.md) | Source choices, async pipeline, emission factors |
| [docs/TRADEOFFS.md](docs/TRADEOFFS.md) | Three deliberate omissions |
| [docs/SOURCES.md](docs/SOURCES.md) | Real-world format research per source |

## Tech stack

**Backend:** Django 5.x, DRF, PostgreSQL, Celery + Redis, django-simple-history, Pint, pandas, simplejwt

**Frontend:** React 18, Vite, Tailwind CSS, shadcn-style components, TanStack Query, React Hook Form, Recharts

## Project structure

```
backend/          Django API + Celery workers
frontend/         React analyst dashboard
sample_data/      Realistic CSV exports for testing
scripts/          Sample data generator
docs/             MODEL, DECISIONS, TRADEOFFS, SOURCES
```

## API overview

All endpoints under `/api/v1/`, JWT auth required except health/register/login.

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/ingest/sap/` | Upload SAP ME2M flat file |
| POST | `/ingest/utility/` | Upload utility CSV |
| POST | `/ingest/travel/` | Upload Concur TRX CSV |
| GET | `/jobs/` | List ingestion jobs |
| GET | `/jobs/{id}/records/` | Paginated emission rows |
| POST | `/jobs/{id}/bulk-approve/` | Approve non-flagged rows |
| PATCH | `/records/{id}/` | Analyst edit |
| POST | `/records/{id}/approve\|reject\|lock/` | Review workflow |
| GET | `/records/{id}/history/` | django-simple-history trail |
| GET | `/anomalies/` | Grouped anomaly summary |
| GET | `/audit-log/` | Review action log |

## License

Prototype for Breathe ESG internship evaluation.
