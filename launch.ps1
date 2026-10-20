#!/usr/bin/env pwsh
# Astra AI -- Full Stack Launcher
# SIH26167 | ISRO/SAC | SatQuery AI
#
# Usage (from repo root):
#   .\launch.ps1
# ============================================================

param(
    [switch]$NoCF,
    [int]$Port = 8000
)

$ErrorActionPreference = "Continue"

$REPO_ROOT   = $PSScriptRoot
$BACKEND_DIR = Join-Path $REPO_ROOT "backend"
$venvPython  = Join-Path $BACKEND_DIR ".venv\Scripts\python.exe"
$venvActivate = Join-Path $BACKEND_DIR ".venv\Scripts\Activate.ps1"
$envFile     = Join-Path $BACKEND_DIR ".env"

Write-Host ""
Write-Host "  Astra AI -- SIH26167 / ISRO.SAC / SatQuery" -ForegroundColor Cyan
Write-Host "  RTX 5060 GPU Backend + Cloudflare Tunnel" -ForegroundColor Cyan
Write-Host ""

# ── 1. GPU ────────────────────────────────────────────────────────────────────
Write-Host "[1/5] Checking GPU..." -ForegroundColor Yellow
try {
    $gpuInfo = & nvidia-smi --query-gpu=name,memory.total --format=csv,noheader 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  OK  GPU: $gpuInfo" -ForegroundColor Green
    } else {
        Write-Host "  WARN  No NVIDIA GPU -- models will run on CPU." -ForegroundColor Yellow
    }
} catch {
    Write-Host "  WARN  nvidia-smi not found." -ForegroundColor Yellow
}

# ── 2. venv ───────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "[2/5] Activating Python venv..." -ForegroundColor Yellow
if (-not (Test-Path $venvActivate)) {
    Write-Host "  WARN  venv not found. Creating..." -ForegroundColor Yellow
    & python -m venv (Join-Path $BACKEND_DIR ".venv")
    & $venvActivate
    & pip install -r (Join-Path $BACKEND_DIR "requirements.txt")
} else {
    & $venvActivate
    Write-Host "  OK  venv activated." -ForegroundColor Green
}

# ── 3. .env ───────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "[3/5] Checking .env..." -ForegroundColor Yellow
if (-not (Test-Path $envFile)) {
    Copy-Item (Join-Path $BACKEND_DIR ".env.example") $envFile
    Write-Host "  ERROR  No .env found -- copied .env.example. Add your GEMINI_API_KEY then re-run." -ForegroundColor Red
    exit 1
} else {
    Write-Host "  OK  .env present." -ForegroundColor Green
}

# ── 4. FastAPI ────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "[4/5] Starting FastAPI on port $Port..." -ForegroundColor Yellow

# Kill anything already on the port
$existing = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
if ($existing) {
    $existingPid = ($existing | Select-Object -First 1).OwningProcess
    Write-Host "  WARN  Port $Port in use by PID $existingPid -- killing..." -ForegroundColor Yellow
    Stop-Process -Id $existingPid -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 1
}

$backendProc = Start-Process `
    -FilePath $venvPython `
    -ArgumentList "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "$Port", "--reload" `
    -WorkingDirectory $BACKEND_DIR `
    -PassThru `
    -WindowStyle Normal

Write-Host "  Backend PID: $($backendProc.Id)" -ForegroundColor Gray

# Wait for health
$ready = $false
$attempts = 0
Write-Host "  Waiting for backend..." -ForegroundColor Gray
while (-not $ready -and $attempts -lt 20) {
    Start-Sleep -Milliseconds 800
    $attempts++
    try {
        $h = Invoke-RestMethod -Uri "http://localhost:$Port/health" -TimeoutSec 3
        if ($h.status -eq "online") {
            $ready = $true
            Write-Host "  OK  Backend online! GPU: $($h.gpu.name)" -ForegroundColor Green
            Write-Host "      VRAM: $($h.gpu.vram_free_gb) GB free / $($h.gpu.vram_total_gb) GB total" -ForegroundColor Cyan
        }
    } catch {
        Write-Host "  ... attempt $attempts/20" -ForegroundColor DarkGray
    }
}

if (-not $ready) {
    Write-Host "  ERROR  Backend did not start. Check the uvicorn window for errors." -ForegroundColor Red
    exit 1
}

# ── 5. Cloudflare Tunnel ──────────────────────────────────────────────────────
$tunnelUrl = $null

if (-not $NoCF) {
    Write-Host ""
    Write-Host "[5/5] Starting Cloudflare tunnel..." -ForegroundColor Yellow

    # Find cloudflared on PATH or common install locations
    $cfPath = $null
    $env:PATH = [System.Environment]::GetEnvironmentVariable("PATH","Machine") + ";" +
                [System.Environment]::GetEnvironmentVariable("PATH","User")

    foreach ($candidate in @("cloudflared", "$env:ProgramFiles\cloudflared\cloudflared.exe")) {
        try {
            $null = & $candidate --version 2>&1
            if ($LASTEXITCODE -eq 0) { $cfPath = $candidate; break }
        } catch {}
    }

    if (-not $cfPath) {
        $found = Get-ChildItem "$env:ProgramFiles","$env:LOCALAPPDATA" -Recurse -Filter "cloudflared.exe" -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($found) { $cfPath = $found.FullName }
    }

    if ($cfPath) {
        Write-Host "  Found: $cfPath" -ForegroundColor Gray

        $tunnelLog = [System.IO.Path]::GetTempFileName() + ".log"

        $tunnelProc = Start-Process `
            -FilePath $cfPath `
            -ArgumentList "tunnel", "--url", "http://localhost:$Port" `
            -PassThru `
            -RedirectStandardError $tunnelLog `
            -WindowStyle Hidden

        Write-Host "  Tunnel PID: $($tunnelProc.Id)" -ForegroundColor Gray
        Write-Host "  Waiting for tunnel URL..." -ForegroundColor Gray

        $waited = 0
        while (-not $tunnelUrl -and $waited -lt 30) {
            Start-Sleep -Seconds 1
            $waited++
            if (Test-Path $tunnelLog) {
                $logContent = Get-Content $tunnelLog -Raw -ErrorAction SilentlyContinue
                if ($logContent -match "https://[a-z0-9\-]+\.trycloudflare\.com") {
                    $tunnelUrl = $Matches[0]
                }
            }
        }

        if ($tunnelUrl) {
            Write-Host "  OK  Tunnel active: $tunnelUrl" -ForegroundColor Green
        } else {
            Write-Host "  WARN  Could not detect tunnel URL. Log: $tunnelLog" -ForegroundColor Yellow
        }
    } else {
        Write-Host "  WARN  cloudflared not found. Install: winget install Cloudflare.cloudflared" -ForegroundColor Yellow
    }
}

# ── Summary ───────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "==========================================================" -ForegroundColor Green
Write-Host "  Astra AI -- LIVE" -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green
Write-Host "  Local Backend : http://localhost:$Port" -ForegroundColor White
Write-Host "  API Docs      : http://localhost:$Port/docs" -ForegroundColor White

if ($tunnelUrl) {
    $pairUrl = "https://sih-orbilens-2026-tm.web.app/backend-config.html?url=$tunnelUrl"
    Write-Host "  Public Tunnel : $tunnelUrl" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  1-CLICK FIREBASE PAIRING:" -ForegroundColor Green
    Write-Host "  $pairUrl" -ForegroundColor White
    Write-Host ""
    Write-Host "  Opening pairing page in your browser..." -ForegroundColor Yellow
    Start-Process $pairUrl

    $tunnelUrl | Set-Clipboard
    Write-Host ""
    Write-Host "  Tunnel URL copied to clipboard!" -ForegroundColor Cyan
}

Write-Host "==========================================================" -ForegroundColor Green
Write-Host ""
Write-Host "  Press Ctrl+C to stop." -ForegroundColor Gray
Write-Host ""

$backendProc | Wait-Process
