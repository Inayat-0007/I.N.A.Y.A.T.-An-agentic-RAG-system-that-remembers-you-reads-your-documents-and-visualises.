# activate.ps1 — I.N.A.Y.A.T. Super Engineer Activator
$ErrorActionPreference = "Stop"

Write-Host "[1/6] Checking Python..." -ForegroundColor Cyan
python --version

Write-Host "[2/6] Verifying virtual environment..." -ForegroundColor Cyan
if (-not (Test-Path ".venv/Scripts/python.exe")) {
    Write-Host "Creating venv with Python..." -ForegroundColor Yellow
    python -m venv .venv
}

Write-Host "[3/6] Installing locked dependencies..." -ForegroundColor Cyan
& .venv\Scripts\pip install -r requirements.txt -c constraints.txt --upgrade

Write-Host "[4/6] Checking data/documents..." -ForegroundColor Cyan
if (-not (Test-Path "data/documents")) {
    New-Item -ItemType Directory -Path "data/documents" -Force | Out-Null
}
$pdfFiles = Get-ChildItem -Path data/documents -Filter *.pdf -ErrorAction SilentlyContinue
$txtFiles = Get-ChildItem -Path data/documents -Filter *.txt -ErrorAction SilentlyContinue
if (-not $pdfFiles -and -not $txtFiles) {
    Write-Host "WARNING: No document files found. Creating a dummy document for testing..." -ForegroundColor Yellow
    # Create a minimal text file that LlamaIndex can index (as plain text)
    @"
I.N.A.Y.A.T. is a next-generation agentic RAG system built for MCA 2026.
It combines Google Gemini, Mem0 memory, and Neo4j knowledge graphs.
The architecture uses a self-healing circuit breaker.
"@ | Out-File -FilePath data/documents/sample.txt -Encoding utf8
}

Write-Host "[5/6] Running service warmup..." -ForegroundColor Cyan
& .venv\Scripts\python warmup.py

Write-Host "[6/6] Launching Streamlit..." -ForegroundColor Cyan
& .venv\Scripts\streamlit run app.py
