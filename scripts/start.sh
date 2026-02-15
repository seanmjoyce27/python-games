#!/bin/bash

# Startup script for Replit and local deployment
echo "🎮 Starting Python Game Builder..."

# Ensure we're in the project root
cd "$(dirname "$0")/.."

# Create instance directory if it doesn't exist
mkdir -p instance

# Check database status
if [ -z "$DATABASE_URL" ]; then
    echo "⚠️  DATABASE_URL not set. App will try to connect to: postgresql://localhost/python_games"
    echo "🐘 Ensure you have a local PostgreSQL server running."
else
    echo "🐘 Using configured PostgreSQL database"
fi

# Run database migrations (schema updates)
echo "🔄 Checking for database migrations..."
if [ -d "venv" ]; then
    ./venv/bin/python3 -m flask db upgrade
else
    python3 -m flask db upgrade
fi

# Start the application
if [ "$1" = "--production" ] || [ "$FLASK_ENV" = "production" ]; then
    echo "🚀 Starting Gunicorn production server..."
    gunicorn app:app -c gunicorn.conf.py
else
    echo "🚀 Starting Flask development server..."
    ./venv/bin/python3 -u app.py
fi
