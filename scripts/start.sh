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

# Reconcile Alembic state with the actual database before upgrading.
# Three cases this handles:
#   1. Fresh DB (no tables)               → let `flask db upgrade` create everything
#   2. Pre-Alembic DB (tables, no version) → stamp head so upgrade is a no-op
#   3. Schema drift (migration would fail) → skip upgrade; init_db() self-heals
$PY - <<'PY' || true
from app import app, db
from sqlalchemy import inspect, text
with app.app_context():
    insp = inspect(db.engine)
    tables = set(insp.get_table_names())
    if 'game' not in tables:
        # Fresh install — nothing to stamp. flask db upgrade will create tables.
        raise SystemExit(0)

    stamped = False
    if 'alembic_version' in tables:
        row = db.session.execute(text("SELECT version_num FROM alembic_version LIMIT 1")).fetchone()
        stamped = row is not None

    if not stamped:
        print("📌 Existing database without migration tracking — stamping current head...")
        from flask_migrate import stamp
        stamp(revision='head')
PY

# Run pending migrations. If this fails (e.g. schema drift on a legacy DB),
# don't abort startup — init_db()'s self-healing ALTER TABLEs will patch things up.
if ! $PY -m flask db upgrade 2>/tmp/migrate.err; then
    echo "⚠️  Migration step reported an error; relying on init_db() self-healing."
    echo "    (Details in /tmp/migrate.err — usually safe to ignore on legacy databases.)"
fi

# Start the application
if [ "$1" = "--production" ] || [ "$FLASK_ENV" = "production" ]; then
    echo "🚀 Starting Gunicorn production server..."
    gunicorn app:app -c gunicorn.conf.py
else
    echo "🚀 Starting Flask development server..."
    ./venv/bin/python3 -u app.py
fi
