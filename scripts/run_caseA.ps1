# scripts/run_caseA.ps1
# PowerShell script for running Case A (simulate scenario)

param(
    [string]$ProjectDir = "projects/CaseA",
    [string]$Input = "$ProjectDir/input.json"
)

Write-Host "🚀 Starting Case A: Simulate Scenario" -ForegroundColor Green
Write-Host "Project Directory: $ProjectDir" -ForegroundColor Cyan
Write-Host "Input File: $Input" -ForegroundColor Cyan

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python not found. Please install Python 3.12+" -ForegroundColor Red
    exit 1
}

# Create virtual environment if it doesn't exist
if (-not (Test-Path ".venv")) {
    Write-Host "📦 Creating virtual environment..." -ForegroundColor Yellow
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to create virtual environment" -ForegroundColor Red
        exit 1
    }
}

# Activate virtual environment
Write-Host "🔧 Activating virtual environment..." -ForegroundColor Yellow
& .\.venv\Scripts\Activate.ps1

# Install dependencies
Write-Host "📚 Installing dependencies..." -ForegroundColor Yellow
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to install dependencies" -ForegroundColor Red
    exit 1
}

# Check if input file exists
if (-not (Test-Path $Input)) {
    Write-Host "❌ Input file not found: $Input" -ForegroundColor Red
    Write-Host "Please create the input file or specify a different path" -ForegroundColor Yellow
    exit 1
}

# Check if project directory exists
if (-not (Test-Path $ProjectDir)) {
    Write-Host "❌ Project directory not found: $ProjectDir" -ForegroundColor Red
    exit 1
}

# Run the main script
Write-Host "🎯 Running AI Marketing Agent..." -ForegroundColor Green
Write-Host "Command: python main.py --input $Input --project-dir $ProjectDir" -ForegroundColor Cyan

python main.py --input $Input --project-dir $ProjectDir

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Case A completed successfully!" -ForegroundColor Green
} else {
    Write-Host "❌ Case A failed with exit code: $LASTEXITCODE" -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host "📋 Check the artifacts directory for results" -ForegroundColor Cyan


