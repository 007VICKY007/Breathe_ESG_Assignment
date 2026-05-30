# Breathe ESG — Frontend

React 18 + Vite + Tailwind v4 + TanStack Query analyst dashboard.

## Run locally

```bash
# Terminal 1 — Django API
cd ../backend
.\.venv\Scripts\python manage.py runserver

# Terminal 2 — Frontend (proxies /api → :8000)
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 — register an org or sign in as `demo` / `demo12345` if seeded.

## Environment

Copy `.env.example` to `.env` for production API URL:

```
VITE_API_BASE_URL=https://your-railway-app.up.railway.app/api/v1
```

Local dev uses Vite proxy (`/api/v1`) when `VITE_API_BASE_URL` is unset.

## Pages

| Route | Page |
|-------|------|
| `/` | Ingestion history + uploads |
| `/jobs/:id` | Job detail, bulk approve, per-row review |
| `/anomalies` | Anomaly summary + Recharts |
| `/audit` | Review action audit log |

## Deploy (Vercel)

Set `VITE_API_BASE_URL` to your Railway backend `/api/v1` and enable CORS on Django.
