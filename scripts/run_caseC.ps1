# scripts/run_caseC.ps1
# PowerShell script for running Case C (full run scenario)

param(
    [string]$ProjectDir = "projects/CaseC",
    [string]$Input = "$ProjectDir/input.json"
)

Write-Host "🚀 Starting Case C: Full Run Scenario" -ForegroundColor Green
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

# Check for seed data
$dataDir = "$ProjectDir/data"
if (Test-Path $dataDir) {
    Write-Host "🌱 Found seed data directory: $dataDir" -ForegroundColor Green
    $dataFiles = Get-ChildItem $dataDir -File
    Write-Host "Seed data files found: $($dataFiles.Count)" -ForegroundColor Cyan
    foreach ($file in $dataFiles) {
        Write-Host "  - $($file.Name)" -ForegroundColor Gray
    }
} else {
    Write-Host "⚠️  No seed data directory found: $dataDir" -ForegroundColor Yellow
    Write-Host "Case C works best with seed data for initial hypotheses" -ForegroundColor Yellow
}

# Check for context files
$contextDir = "$ProjectDir/context"
if (Test-Path $contextDir) {
    Write-Host "📋 Found context directory: $contextDir" -ForegroundColor Green
    $contextFiles = Get-ChildItem $contextDir -File
    Write-Host "Context files found: $($contextFiles.Count)" -ForegroundColor Cyan
    foreach ($file in $contextFiles) {
        Write-Host "  - $($file.Name)" -ForegroundColor Gray
    }
} else {
    Write-Host "ℹ️  No context directory found: $contextDir" -ForegroundColor Blue
    Write-Host "Using global context files" -ForegroundColor Blue
}

# Run the main script
Write-Host "🎯 Running AI Marketing Agent..." -ForegroundColor Green
Write-Host "Command: python main.py --input $Input --project-dir $ProjectDir" -ForegroundColor Cyan

python main.py --input $Input --project-dir $ProjectDir

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Case C completed successfully!" -ForegroundColor Green
} else {
    Write-Host "❌ Case C failed with exit code: $LASTEXITCODE" -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host "📋 Check the artifacts directory for results" -ForegroundColor Cyan
Write-Host "📊 Check the exports directory for detailed reports" -ForegroundColor Cyan

