#!/bin/bash

# Test runner script for Python Game Builder

echo "🧪 Running Python Game Builder Tests"
echo "======================================"

# Ensure we're in the project root
cd "$(dirname "$0")/.."

# Activate virtual environment if not already active
if [ -z "$VIRTUAL_ENV" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Install dev dependencies if not installed
if ! python -c "import pytest" 2>/dev/null; then
    echo "Installing development dependencies..."
    pip install -r requirements-dev.txt
fi

# Run tests
echo ""
echo "Running tests..."
pytest tests/ -v --cov=app --cov-report=term-missing

# Check exit code
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ All tests passed!"
else
    echo ""
    echo "❌ Some tests failed"
    exit 1
fi
