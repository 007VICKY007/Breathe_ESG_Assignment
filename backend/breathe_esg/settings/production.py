"""
Production settings for Railway deployment.
"""
from .base import *  # noqa: F403

DEBUG = False

# Django rejects Host headers when DEBUG=False — "*" is NOT valid here.
# .up.railway.app matches any Railway-generated subdomain.
_default_hosts = [
    ".up.railway.app",
    "localhost",
    "127.0.0.1",
]
# Set exact hostname too, e.g. breathe-esg-production.up.railway.app
if env("RAILWAY_PUBLIC_DOMAIN", default=""):
    _default_hosts.append(env("RAILWAY_PUBLIC_DOMAIN"))
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=_default_hosts)

# Railway terminates TLS at the edge; redirect loops break health checks if misconfigured
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=False)
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Vercel frontend + Railway API
_csrf_origins = env.list("CSRF_TRUSTED_ORIGINS", default=[])
CSRF_TRUSTED_ORIGINS = _csrf_origins

CELERY_TASK_ALWAYS_EAGER = env.bool("CELERY_TASK_ALWAYS_EAGER", default=False)

# Run ingestion in the web process when no Celery worker is deployed (Railway default).
# Set False only when a dedicated worker service is running.
INGESTION_RUN_SYNC = env.bool("INGESTION_RUN_SYNC", default=True)

MEDIA_ROOT = BASE_DIR / "media"

# CORS: set CORS_ALLOWED_ORIGINS=https://your-app.vercel.app in Railway
# Also allow all *.vercel.app preview deployments unless disabled
CORS_ALLOW_ALL_ORIGINS = env.bool("CORS_ALLOW_ALL_ORIGINS", default=False)
if not CORS_ALLOW_ALL_ORIGINS:
    CORS_ALLOWED_ORIGIN_REGEXES = [
        r"^https://.*\.vercel\.app$",
    ]
