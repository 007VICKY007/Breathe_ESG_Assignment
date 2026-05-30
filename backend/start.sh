#!/usr/bin/env bash
set -euo pipefail
PORT="${PORT:-8080}"
echo "==> Collecting static files..."
python manage.py collectstatic --noinput
echo "==> Running migrations..."
python manage.py migrate --noinput
echo "==> Ensuring demo user exists..."
python manage.py bootstrap_demo || true
echo "==> Starting gunicorn on 0.0.0.0:8080"
exec gunicorn breathe_esg.wsgi:application \
  --bind "0.0.0.0:8080" \
  --workers 2 \
  --timeout 120 \
  --access-logfile - \
  --error-logfile -
