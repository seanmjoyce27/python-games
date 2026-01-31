#!/bin/bash
# Port cleanup utility for Python Game Builder
# Usage: ./cleanup_port.sh [port_number]
# Default port: 8080 (standard for many Replit/container setups) or from $PORT

PORT=${1:-${PORT:-8080}}

# Ensure we're in the project root
cd "$(dirname "$0")/.."

echo "🔍 Checking for processes on port $PORT..."

# Find processes using the port
if command -v lsof &> /dev/null; then
    PIDS=$(lsof -ti :$PORT 2>/dev/null)

    if [ -z "$PIDS" ]; then
        echo "✅ Port $PORT is already free"
        exit 0
    fi

    echo "Found processes using port $PORT:"
    lsof -i :$PORT

    echo ""
    echo "🛑 Killing processes..."
    for pid in $PIDS; do
        echo "  Killing PID $pid"
        kill -TERM $pid 2>/dev/null || kill -KILL $pid 2>/dev/null
    done

    # Wait a moment for processes to die
    sleep 1

    # Check if port is now free
    REMAINING=$(lsof -ti :$PORT 2>/dev/null)
    if [ -z "$REMAINING" ]; then
        echo "✅ Port $PORT is now free"
        exit 0
    else
        echo "⚠️  Some processes still running. Trying force kill..."
        for pid in $REMAINING; do
            kill -KILL $pid 2>/dev/null
        done
        sleep 1
        echo "✅ Port cleanup complete"
    fi
else
    echo "⚠️  'lsof' command not found. Cannot check port usage."
    echo "   Install lsof or manually check: netstat -an | grep $PORT"
    exit 1
fi
