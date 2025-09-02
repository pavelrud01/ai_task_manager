#!/bin/bash
# scripts/test_smoke.sh
# Unix wrapper for running smoke tests

set -e  # Exit on any error

echo "🧪 Starting AI Marketing Agent Smoke Test"

# Check if Python is available
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
    echo "✅ Python3 found: $(python3 --version)"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
    echo "✅ Python found: $(python --version)"
else
    echo "❌ Python not found. Please install Python 3.12+"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    $PYTHON_CMD -m venv .venv
    if [ $? -ne 0 ]; then
        echo "❌ Failed to create virtual environment"
        exit 1
    fi
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source .venv/bin/activate

# Install dependencies
echo "📚 Installing dependencies..."
$PYTHON_CMD -m pip install --upgrade pip
$PYTHON_CMD -m pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    exit 1
fi

# Check if test fixtures exist
INPUT_FILE="tests/fixtures/input_min.json"
GUIDE_FILE="tests/fixtures/guide_min.md"

if [ ! -f "$INPUT_FILE" ]; then
    echo "❌ Test input file not found: $INPUT_FILE"
    exit 1
fi

if [ ! -f "$GUIDE_FILE" ]; then
    echo "❌ Test guide file not found: $GUIDE_FILE"
    exit 1
fi

echo "✅ Test fixtures found"

# Run smoke test
echo "🎯 Running smoke test..."
$PYTHON_CMD scripts/test_smoke.py

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ Smoke test completed successfully!"
else
    echo "❌ Smoke test failed with exit code: $EXIT_CODE"
fi

echo "📋 Check the artifacts directory for smoke test results"
exit $EXIT_CODE

