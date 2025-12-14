#!/bin/sh
set -e

# Change directory to project root
cd /app/auto_stock

# Run migrations
echo "[entrypoint] Running migrations..."
python manage.py migrate --noinput

# Run server
echo "[entrypoint] Starting Django dev server..."
exec python manage.py runserver 0.0.0.0:8000
