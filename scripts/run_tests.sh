#!/bin/bash
# Run tests with coverage

set -e

echo "🧪 Running tests..."

# Activate virtual environment if exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run pytest with coverage
pytest tests/ -v --cov=src --cov-report=html --cov-report=term

echo ""
echo "✅ Tests complete!"
echo "📊 Coverage report: htmlcov/index.html"
