#!/bin/bash
# scripts/run_caseC.sh
# Unix script for running Case C (full run scenario)

set -e  # Exit on any error

PROJECT_DIR="${1:-projects/CaseC}"
INPUT_FILE="${2:-$PROJECT_DIR/input.json}"

echo "🚀 Starting Case C: Full Run Scenario"
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

# Check for seed data
DATA_DIR="$PROJECT_DIR/data"
if [ -d "$DATA_DIR" ]; then
    echo "🌱 Found seed data directory: $DATA_DIR"
    DATA_FILES=$(find "$DATA_DIR" -type f | wc -l)
    echo "Seed data files found: $DATA_FILES"
    find "$DATA_DIR" -type f -exec basename {} \; | while read -r file; do
        echo "  - $file"
    done
else
    echo "⚠️  No seed data directory found: $DATA_DIR"
    echo "Case C works best with seed data for initial hypotheses"
fi

# Check for context files
CONTEXT_DIR="$PROJECT_DIR/context"
if [ -d "$CONTEXT_DIR" ]; then
    echo "📋 Found context directory: $CONTEXT_DIR"
    CONTEXT_FILES=$(find "$CONTEXT_DIR" -type f | wc -l)
    echo "Context files found: $CONTEXT_FILES"
    find "$CONTEXT_DIR" -type f -exec basename {} \; | while read -r file; do
        echo "  - $file"
    done
else
    echo "ℹ️  No context directory found: $CONTEXT_DIR"
    echo "Using global context files"
fi

# Run the main script
echo "🎯 Running AI Marketing Agent..."
echo "Command: $PYTHON_CMD main.py --input $INPUT_FILE --project-dir $PROJECT_DIR"

$PYTHON_CMD main.py --input "$INPUT_FILE" --project-dir "$PROJECT_DIR"

if [ $? -eq 0 ]; then
    echo "✅ Case C completed successfully!"
else
    echo "❌ Case C failed with exit code: $?"
    exit $?
fi

echo "📋 Check the artifacts directory for results"
echo "📊 Check the exports directory for detailed reports"

