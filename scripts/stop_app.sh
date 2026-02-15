#!/bin/bash
# Stop the Python Game Builder app

# Default port
PORT=${PORT:-8080}

# Ensure we're in the project root
cd "$(dirname "$0")/.."

# Read port from .env if it exists
if [ -f .env ]; then
    # Grep for PORT line, extract value
    ENV_PORT=$(grep "^PORT=" .env | cut -d '=' -f2)
    if [ ! -z "$ENV_PORT" ]; then
        PORT=$ENV_PORT
    fi
fi

echo "🛑 Stopping Python Game Builder..."

# Method 1: Kill by port (cleanest)
if [ -f ./scripts/cleanup_port.sh ]; then
    chmod +x ./scripts/cleanup_port.sh
    ./scripts/cleanup_port.sh $PORT
else
    # Fallback if cleanup script missing
    if command -v lsof &> /dev/null; then
        PIDS=$(lsof -ti :$PORT 2>/dev/null)
        if [ ! -z "$PIDS" ]; then
            echo "Killing process on port $PORT..."
            kill -9 $PIDS 2>/dev/null
        fi
    fi
fi

# Method 2: Kill by process name (surefire backup)
# This catches cases where the app might be stuck or not listening yet
pkill -f "python3 app.py" 2>/dev/null
pkill -f "gunicorn" 2>/dev/null

echo "✅ App stopped."
