#!/usr/bin/env bash
set -euo pipefail

# Railway injects PORT; default 8000 for local Docker tests
PORT="${PORT:-8000}"

echo "==> Running migrations..."
python manage.py migrate --noinput

echo "==> Ensuring demo user exists..."
python manage.py bootstrap_demo || true

echo "==> Starting gunicorn on 0.0.0.0:${PORT}"
exec gunicorn breathe_esg.wsgi:application \
  --bind "0.0.0.0:${PORT}" \
  --workers 2 \
  --timeout 120 \
  --access-logfile - \
  --error-logfile -
