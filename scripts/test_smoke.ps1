# scripts/test_smoke.ps1
# PowerShell wrapper for running smoke tests

Write-Host "🧪 Starting AI Marketing Agent Smoke Test" -ForegroundColor Green

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python not found. Please install Python 3.12+" -ForegroundColor Red
    exit 1
}

# Check if virtual environment exists
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

# Check if test fixtures exist
$inputFile = "tests/fixtures/input_min.json"
$guideFile = "tests/fixtures/guide_min.md"

if (-not (Test-Path $inputFile)) {
    Write-Host "❌ Test input file not found: $inputFile" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $guideFile)) {
    Write-Host "❌ Test guide file not found: $guideFile" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Test fixtures found" -ForegroundColor Green

# Run smoke test
Write-Host "🎯 Running smoke test..." -ForegroundColor Green
python scripts/test_smoke.py

$exitCode = $LASTEXITCODE

if ($exitCode -eq 0) {
    Write-Host "✅ Smoke test completed successfully!" -ForegroundColor Green
} else {
    Write-Host "❌ Smoke test failed with exit code: $exitCode" -ForegroundColor Red
}

Write-Host "📋 Check the artifacts directory for smoke test results" -ForegroundColor Cyan
exit $exitCode


