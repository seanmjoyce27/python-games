#!/bin/bash

# Startup script for Replit and local deployment
echo "🎮 Starting Python Game Builder..."

# Ensure we're in the project root
cd "$(dirname "$0")/.."

# Create instance directory if it doesn't exist
mkdir -p instance

# Check if database exists
if [ ! -f instance/python_games.db ]; then
    echo "📦 First run - database will be created..."
else
    echo "✓ Database found"
fi

# Start the application
if [ "$1" = "--production" ] || [ "$FLASK_ENV" = "production" ]; then
    echo "🚀 Starting Gunicorn production server..."
    gunicorn app:app -c gunicorn.conf.py
else
    echo "🚀 Starting Flask development server..."
    ./venv/bin/python -u app.py
fi
