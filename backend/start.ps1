#!/usr/bin/env pwsh
# Astra AI Backend — Windows Startup Script
# Run from the backend/ directory.

Write-Host "🌍 Astra AI Backend Startup" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan

# ── 1. Check GPU ──────────────────────────────────────────────────────────────
Write-Host "`n[1/5] Checking GPU..." -ForegroundColor Yellow
try {
    $gpuInfo = & nvidia-smi --query-gpu=name,memory.total --format=csv,noheader 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✅ GPU found: $gpuInfo" -ForegroundColor Green
    } else {
        Write-Host "  ⚠  No NVIDIA GPU detected. Models will run on CPU (very slow)." -ForegroundColor Yellow
    }
} catch {
    Write-Host "  ⚠  nvidia-smi not found. GPU status unknown." -ForegroundColor Yellow
}

# ── 2. Check Python venv ──────────────────────────────────────────────────────
Write-Host "`n[2/5] Checking Python virtual environment..." -ForegroundColor Yellow
$venvPath = ".venv\Scripts\Activate.ps1"
if (Test-Path $venvPath) {
    & $venvPath
    Write-Host "  ✅ Virtual environment activated." -ForegroundColor Green
} else {
    Write-Host "  ⚠  No virtual environment found. Creating one..." -ForegroundColor Yellow
    python -m venv .venv
    & $venvPath
    Write-Host "  Installing dependencies..." -ForegroundColor Yellow
    pip install -r requirements.txt
    Write-Host "  ✅ Dependencies installed." -ForegroundColor Green
}

# ── 3. Check .env ─────────────────────────────────────────────────────────────
Write-Host "`n[3/5] Checking configuration..." -ForegroundColor Yellow
if (Test-Path ".env") {
    Write-Host "  ✅ .env file found." -ForegroundColor Green
} else {
    Write-Host "  ⚠  .env not found. Copying from .env.example..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host "  ❌ IMPORTANT: Edit .env and add your GEMINI_API_KEY before starting." -ForegroundColor Red
    Write-Host "     Run: notepad .env" -ForegroundColor Yellow
    exit 1
}

# ── 4. Start FastAPI backend ──────────────────────────────────────────────────
Write-Host "`n[4/5] Starting FastAPI backend (port 8000)..." -ForegroundColor Yellow
$backendJob = Start-Job -ScriptBlock {
    Set-Location $using:PWD
    & ".venv\Scripts\python.exe" -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
}
Start-Sleep -Seconds 3

# Health check
try {
    $health = Invoke-RestMethod -Uri "http://localhost:8000/health" -TimeoutSec 5
    Write-Host "  ✅ Backend online. GPU: $($health.gpu.available)" -ForegroundColor Green
} catch {
    Write-Host "  ❌ Backend failed to start. Check logs." -ForegroundColor Red
    Receive-Job $backendJob
    exit 1
}

# ── 5. Start Cloudflare Tunnel ────────────────────────────────────────────────
Write-Host "`n[5/5] Starting Cloudflare Tunnel..." -ForegroundColor Yellow
Write-Host "  (If cloudflared is not installed: winget install Cloudflare.cloudflared)" -ForegroundColor Gray

try {
    $tunnelJob = Start-Job -ScriptBlock {
        cloudflared tunnel --url http://localhost:8000
    }
    Start-Sleep -Seconds 5

    $tunnelLog = Receive-Job $tunnelJob 2>&1
    $tunnelUrl = ($tunnelLog | Select-String "https://.*trycloudflare.com").Matches[0].Value

    if ($tunnelUrl) {
        Write-Host "`n  ✅ Tunnel active: $tunnelUrl" -ForegroundColor Green
        Write-Host "`n  📋 Add this URL to:" -ForegroundColor Cyan
        Write-Host "     1. ALLOWED_ORIGINS in backend/.env" -ForegroundColor White
        Write-Host "     2. NEXT_PUBLIC_API_URL in frontend/.env.local" -ForegroundColor White
    } else {
        Write-Host "  ⚠  Could not extract tunnel URL. Check cloudflared output." -ForegroundColor Yellow
    }
} catch {
    Write-Host "  ⚠  cloudflared not found. Run locally without tunnel." -ForegroundColor Yellow
    Write-Host "     Backend available at: http://localhost:8000" -ForegroundColor Gray
}

Write-Host "`n🚀 Astra AI Backend is running!" -ForegroundColor Green
Write-Host "   Health check: http://localhost:8000/health" -ForegroundColor Gray
Write-Host "   API docs:     http://localhost:8000/docs" -ForegroundColor Gray
Write-Host "`nPress Ctrl+C to stop." -ForegroundColor Gray

# Keep running and show backend logs
Receive-Job $backendJob -Wait
