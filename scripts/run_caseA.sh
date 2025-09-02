#!/bin/bash
# scripts/run_caseA.sh
# Unix script for running Case A (simulate scenario)

set -e  # Exit on any error

PROJECT_DIR="${1:-projects/CaseA}"
INPUT_FILE="${2:-$PROJECT_DIR/input.json}"

echo "🚀 Starting Case A: Simulate Scenario"
echo "Project Directory: $PROJECT_DIR"
echo "Input File: $INPUT_FILE"

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

# Create virtual environment if it doesn't exist
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

# Check if input file exists
if [ ! -f "$INPUT_FILE" ]; then
    echo "❌ Input file not found: $INPUT_FILE"
    echo "Please create the input file or specify a different path"
    exit 1
fi

# Check if project directory exists
if [ ! -d "$PROJECT_DIR" ]; then
    echo "❌ Project directory not found: $PROJECT_DIR"
    exit 1
fi

# Run the main script
echo "🎯 Running AI Marketing Agent..."
echo "Command: $PYTHON_CMD main.py --input $INPUT_FILE --project-dir $PROJECT_DIR"

$PYTHON_CMD main.py --input "$INPUT_FILE" --project-dir "$PROJECT_DIR"

if [ $? -eq 0 ]; then
    echo "✅ Case A completed successfully!"
else
    echo "❌ Case A failed with exit code: $?"
    exit $?
fi

echo "📋 Check the artifacts directory for results"

