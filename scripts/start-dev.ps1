# One-step dev starter for MMT (PowerShell)
# - Starts backend (uvicorn) on port 8000 in a background job
# - Runs Flutter web-server on port 3000 with BASE_URL=http://localhost:8000
# Usage: From repo root run: .\scripts\start-dev.ps1

param(
  [int]$BackendPort = 8000,
  [int]$WebPort = 3000,
  [switch]$NoInstall
)

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Write-Host "MMT dev starter - repo: $repoRoot"

# Start backend
Push-Location "$repoRoot\backend"
if (-not $NoInstall) {
    Write-Host "Installing backend requirements (pip)..."
    if (Test-Path ".venv") {
        Write-Host "Detected .venv, skipping venv creation. Activate if needed."
    } else {
        Write-Host "Creating virtual environment .venv..."
        python -m venv .venv
    }
}

# Start uvicorn in background process (ensure correct working dir and venv python if present)
$backendDir = Join-Path $repoRoot 'backend'
$venvPython = Join-Path $backendDir ".venv\Scripts\python.exe"
if (Test-Path $venvPython) {
    $pythonExe = $venvPython
    Write-Host "Using virtualenv python: $pythonExe"
} else {
    $pythonExe = "python"
    Write-Host "Using system python: $pythonExe"
}

$uvicornArgs = "-m uvicorn main:app --reload --port $BackendPort"
Write-Host "Starting backend: $pythonExe $uvicornArgs (working dir: $backendDir)"

$startInfo = @{
    FilePath = $pythonExe
    ArgumentList = $uvicornArgs
    WorkingDirectory = $backendDir
    WindowStyle = 'Hidden'
}

# Start the backend as a background process and return the PID
$proc = Start-Process @startInfo -PassThru
if ($proc -and $proc.Id) {
    Write-Host "Backend started (PID $($proc.Id))."
} else {
    Write-Warning "Failed to start backend process. Check output above for errors."
}

Pop-Location

# Start Flutter web server
Push-Location "$repoRoot\app"
if (-not $NoInstall) {
    Write-Host "Running flutter pub get..."
    flutter pub get
}

$dartDefine = "--dart-define=BASE_URL=http://localhost:$BackendPort"
$webCmd = "flutter run -d web-server --web-hostname 0.0.0.0 --web-port $WebPort $dartDefine"
Write-Host "Launching Flutter web-server: $webCmd"

# Start Flutter web-server as a background process so we can poll the port
$appDir = Join-Path $repoRoot 'app'
$flutterArgs = "run -d web-server --web-hostname 0.0.0.0 --web-port $WebPort $dartDefine"
Write-Host "Starting Flutter (background): flutter $flutterArgs (working dir: $appDir)"
try {
    $flutterProc = Start-Process -FilePath "flutter" -ArgumentList $flutterArgs -WorkingDirectory $appDir -PassThru
    if ($flutterProc -and $flutterProc.Id) {
        Write-Host "Flutter started (PID $($flutterProc.Id)). Logs will be in the new process stdout/stderr."
    } else {
        Write-Warning "Failed to start Flutter process."
    }
} catch {
    Write-Warning "Exception starting Flutter: $_"
}

Pop-Location

# Basic check: wait up to 15s for WebPort to be listening on 0.0.0.0 or localhost
Write-Host "Checking whether port $WebPort is listening..."
$wait = 0
$listening = $false
while ($wait -lt 15) {
    Start-Sleep -Seconds 1
    $tcp = Get-NetTCPConnection -LocalPort $WebPort -ErrorAction SilentlyContinue
    if ($tcp) { $listening = $true; break }
    $wait++
}

if ($listening) {
    Write-Host "Port $WebPort appears to be listening. Open http://localhost:$WebPort/ in your browser."
} else {
    Write-Warning "Port $WebPort is not listening after startup. Common causes: Flutter failed to start, firewall blocking, or binding only to IPv6 (::1)."
    Write-Host "Run these checks in PowerShell to debug:"
    Write-Host "  Test-NetConnection -ComputerName localhost -Port $WebPort"
    Write-Host "  netstat -ano | Select-String ":$WebPort""
    Write-Host "If Flutter printed an error about 'address already in use' or similar, try a different port or stop the conflicting process."
}

Write-Host "If you need to stop the backend uvicorn process run: Stop-Process -Id <PID>"
