#!/bin/sh

echo "=== Environment ==="
echo "DATABASE_URL set: $([ -n "$DATABASE_URL" ] && echo yes || echo NO - MISSING)"
echo "SECRET_KEY set:   $([ -n "$SECRET_KEY" ] && echo yes || echo NO - MISSING)"
echo "PORT: ${PORT:-8000}"
echo "RAILWAY_ENVIRONMENT: ${RAILWAY_ENVIRONMENT:-not set}"
echo "==================="

echo "Running migrations..."
alembic upgrade head || { echo "Migration failed - check DATABASE_URL and PostgreSQL connectivity"; exit 1; }

echo "Starting server..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
