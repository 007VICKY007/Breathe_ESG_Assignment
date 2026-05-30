# Deployment troubleshooting — Railway + Vercel

## "DNS_PROBE_FINISHED_NXDOMAIN" / "DNS not found"

**This is not a Django or React bug.** The browser cannot resolve the hostname to an IP address. The request never reaches your app.

### Most common causes

| Cause | What you did wrong | Fix |
|-------|-------------------|-----|
| **No public domain generated** | Service is "Online" but Networking has no `*.up.railway.app` URL | Open the **WEB** service → **Settings** → **Networking** → **Public Networking** → **Generate Domain** |
| **Wrong service** | Generated URL on Worker, Postgres, or Redis | Only the **Django/gunicorn WEB** service needs a public domain. Worker and DB stay private. |
| **Private networking only** | Used `something.railway.internal` in the browser | Internal hostnames are **not** reachable from your laptop or Vercel. Use the **public** `*.up.railway.app` URL. |
| **Custom domain without DNS** | Added `api.yourcompany.com` but no CNAME at registrar | Either finish DNS (CNAME → Railway target) or use the default `*.up.railway.app` URL first. |
| **Typo / stale URL** | Copied URL from deleted deployment | Copy the domain again from Railway dashboard after redeploy. |
| **Wrong root directory** | Deployed repo root instead of `backend/` | Service **Settings** → **Root Directory** = `backend` → Redeploy. |

### Correct Railway setup (checklist)

1. **One project** with plugins: PostgreSQL, Redis.
2. **Web service** (from GitHub repo):
   - Root Directory: `backend`
   - Uses `railway.toml` in that folder
   - Variables: see below
   - **Public domain** generated → note URL e.g. `breathe-esg-api-production.up.railway.app`
3. **Worker service** (same repo):
   - Root Directory: `backend`
   - Config file: `railway.worker.toml` (or custom start: `celery -A breathe_esg worker -l info`)
   - **No public domain** on worker
   - Same `DATABASE_URL`, `REDIS_URL`, `SECRET_KEY`, `DJANGO_SETTINGS_MODULE`
4. Link Postgres/Redis variables to both web + worker (`${{Postgres.DATABASE_URL}}` syntax in Railway).

### Verify backend is alive

When DNS works, open in browser:

```
https://YOUR-SERVICE.up.railway.app/api/v1/health/
```

Expected JSON:

```json
{"status": "healthy", "database": "up", "service": "breathe-esg-api"}
```

If DNS works but you get 502/503 → check **Deploy Logs** (migrate crash, missing `DATABASE_URL`, gunicorn not binding `PORT`).

---

## Connect Vercel → Railway

Only after the health URL works in a browser.

### Vercel (frontend)

| Setting | Value |
|---------|--------|
| Root Directory | `frontend` |
| `VITE_API_BASE_URL` | `https://YOUR-SERVICE.up.railway.app/api/v1` |

Redeploy Vercel after changing env vars (build-time variable).

### Railway (backend)

| Variable | Example |
|----------|---------|
| `DJANGO_SETTINGS_MODULE` | `breathe_esg.settings.production` |
| `SECRET_KEY` | long random string |
| `DATABASE_URL` | from Postgres plugin |
| `REDIS_URL` | from Redis plugin |
| `RAILWAY_PUBLIC_DOMAIN` | `your-service.up.railway.app` (optional, helps ALLOWED_HOSTS) |
| `ALLOWED_HOSTS` | `your-service.up.railway.app,.up.railway.app` |
| `CORS_ALLOWED_ORIGINS` | `https://your-app.vercel.app` |
| `CELERY_TASK_ALWAYS_EAGER` | `False` |
| `SECURE_SSL_REDIRECT` | `False` |

`CORS_ALLOWED_ORIGIN_REGEXES` already allows `https://*.vercel.app` in production settings.

---

## Railway shows "Online" but URL doesn't work

1. **Deployments** tab → latest deploy **Succeeded** (not crashed during migrate).
2. **HTTP Logs** → requests arriving when you hit the URL.
3. If deploy failed on migrate: fix `DATABASE_URL` reference to Postgres service.
4. If health check fails: open `/api/v1/health/` path matches `railway.toml` `healthcheckPath`.

---

## Quick test without Vercel

```bash
curl https://YOUR-SERVICE.up.railway.app/api/v1/health/
curl -X POST https://YOUR-SERVICE.up.railway.app/api/v1/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"demo","password":"demo12345"}'
```

Login on Vercel UI only after both work.
