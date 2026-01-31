#!/bin/bash

# Startup script for Replit and local deployment
echo "🎮 Starting Python Game Builder..."

# Create instance directory if it doesn't exist
mkdir -p instance

# Check if database exists
if [ ! -f instance/python_games.db ]; then
    echo "📦 First run - database will be created..."
else
    echo "✓ Database found"
fi

# Start the application
echo "🚀 Starting Flask server..."
python app.py
