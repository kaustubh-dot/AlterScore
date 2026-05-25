# AlterScore Platform Orchestrator & Health Check Script
# This script validates environment dependencies, activates virtualenvs, and spins up the backend and frontend.

Clear-Host
Write-Output "========================================================="
Write-Output "       ALTERSCORE GOVERNED RISK PLATFORM ORCHESTRATOR    "
Write-Output "========================================================="

# Step 1: Verify Python environment
Write-Output "▶ Phase 1: Environment Verification..."
if (Test-Path "venv\Scripts\python.exe") {
    $pythonVer = & venv\Scripts\python.exe --version
    Write-Output "  ✓ Active Virtual Environment found: $pythonVer"
} else {
    Write-Output "  ❌ ERROR: Virtual environment 'venv' not found."
    Write-Output "     Please run: py -3.12 -m venv venv"
    Write-Output "     Then install dependencies: venv\Scripts\python.exe -m pip install -r backend\requirements.txt"
    Exit 1
}

# Step 2: Verify Node JS installation
$node = Get-Command node -ErrorAction SilentlyContinue
if ($node) {
    $nodeVer = & node --version
    Write-Output "  ✓ Active Node.js installation found: $nodeVer"
} else {
    Write-Output "  ❌ ERROR: Node.js is required to boot the frontend client."
    Exit 1
}

# Step 3: Check Production serve files
if (!(Test-Path "models/registry/production_manifest.json")) {
    Write-Output "  ❌ ERROR: Production model manifest registry is missing."
    Exit 1
}
Write-Output "  ✓ Production manifest verified."

# Step 4: Boot backend process in a new window
Write-Output "`n▶ Phase 2: Launching FastAPI Backend (Port 8000)..."
Start-Process -FilePath "venv\Scripts\python.exe" -ArgumentList "-m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000" -WindowStyle Normal
Start-Sleep -Seconds 3

# Step 5: Boot frontend process in a new window
Write-Output "▶ Phase 3: Launching React/Vite Frontend (Port 5173)..."
Start-Process -FilePath "cmd.exe" -ArgumentList "/c cd frontend && npm run dev -- --host 127.0.0.1 --port 5173" -WindowStyle Normal
Start-Sleep -Seconds 3

# Step 6: Health verification loops
Write-Output "`n▶ Phase 4: Querying API Health Telemetry..."
try {
    $healthCheck = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/health" -Method Get -TimeoutSec 5
    if ($healthCheck.status -eq "ok" -and $healthCheck.model_loaded -eq $true) {
        Write-Output "  ✓ Connection Secure: AlterScore Risk Engine active!"
        Write-Output "  ✓ Loaded Manifest: $($healthCheck.manifest_version)"
        Write-Output "  ✓ Locked Model version: $($healthCheck.model_version)"
    } else {
        Write-Output "  ⚠️ WARNING: Health check responded, but engine status is degraded."
    }
} catch {
    Write-Output "  ⚠️ Health check query timed out. Backend is still starting up."
}

Write-Output "`n========================================================="
Write-Output "🎉 AlterScore Boot Sequence Complete!"
Write-Output "  👉 Backend API Serving: http://127.0.0.1:8000/api"
Write-Output "  👉 Borrower Frontend:   http://127.0.0.1:5173"
Write-Output "========================================================="
