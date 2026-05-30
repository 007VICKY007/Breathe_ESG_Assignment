"""
Production settings for Railway deployment.
"""
from .base import *  # noqa: F403

DEBUG = False

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["*"])

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=True)
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

CELERY_TASK_ALWAYS_EAGER = env.bool("CELERY_TASK_ALWAYS_EAGER", default=False)

# Railway ephemeral disk — acceptable for prototype file uploads
MEDIA_ROOT = BASE_DIR / "media"
