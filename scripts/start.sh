#!/bin/bash

# Startup script for Replit and local deployment
echo "🎮 Starting Python Game Builder..."

# Ensure we're in the project root
cd "$(dirname "$0")/.."

# Create instance directory if it doesn't exist
mkdir -p instance

# Check database status
if [ -z "$DATABASE_URL" ]; then
    echo "⚠️  DATABASE_URL not set. Defaulting to local: sqlite:///python_games.db"
    echo "📦 For PostgreSQL, set DATABASE_URL=postgresql://user:pass@localhost/dbname"
else
    echo "🐘 Using configured database: $DATABASE_URL"
fi

# Run database migrations (schema updates)
echo "🔄 Checking for database migrations..."
if [ -d "venv" ]; then
    PY=./venv/bin/python3
else
    PY=python3
fi

# If the DB already has tables from a pre-Alembic install but no alembic_version
# row, stamp it to head so the initial migration doesn't try to recreate tables.
$PY - <<'PY'
from app import app, db
from sqlalchemy import inspect
with app.app_context():
    insp = inspect(db.engine)
    tables = set(insp.get_table_names())
    if 'game' in tables and 'alembic_version' not in tables:
        print("📌 Existing pre-Alembic database detected — stamping current head...")
        from flask_migrate import stamp
        stamp(revision='head')
PY

$PY -m flask db upgrade

# Start the application
if [ "$1" = "--production" ] || [ "$FLASK_ENV" = "production" ]; then
    echo "🚀 Starting Gunicorn production server..."
    gunicorn app:app -c gunicorn.conf.py
else
    echo "🚀 Starting Flask development server..."
    ./venv/bin/python3 -u app.py
fi
