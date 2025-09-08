# Rerun latest workflow run on branch feat/ci-flutter, wait, download logs, and print pre-check + install step logs
# Usage: open PowerShell in repo root, ensure $env:GITHUB_TOKEN is set, then:
#   .\scripts\rerun_fetch_logs.ps1

if (-not $env:GITHUB_TOKEN) {
    Write-Host 'ERROR: $env:GITHUB_TOKEN is not set in this PowerShell session.'
    Write-Host "Set it with: `$env:GITHUB_TOKEN = '<your_pat>' (do not paste tokens in chat)"
    exit 2
}

$owner = 'WebQx'
$repo  = 'MMT'
$branch = 'feat/ci-flutter'
$headers = @{ Authorization = "Bearer $env:GITHUB_TOKEN"; Accept = 'application/vnd.github+json' }

Write-Host "Querying recent runs for $owner/$repo branch $branch..."
$runs = Invoke-RestMethod -Headers $headers -Uri "https://api.github.com/repos/$owner/$repo/actions/runs?branch=$branch&per_page=5"
if (-not $runs.workflow_runs) { Write-Host 'No workflow runs found for that branch'; exit 3 }
$latest = $runs.workflow_runs | Sort-Object created_at -Descending | Select-Object -First 1
Write-Host "Latest run id: $($latest.id)  created_at: $($latest.created_at)  status: $($latest.status)  conclusion: $($latest.conclusion)  head_sha: $($latest.head_sha)"

Write-Host "Requesting rerun for run id $($latest.id) ..."
try {
    Invoke-RestMethod -Method Post -Headers $headers -Uri "https://api.github.com/repos/$owner/$repo/actions/runs/$($latest.id)/rerun" -ErrorAction Stop
    Write-Host 'Rerun requested.'
} catch {
    Write-Host "Rerun request failed: $($_.Exception.Message)"
}

# Wait up to 3 minutes for a new run entry (the rerun may create a new run)
$runToWatch = $latest.id
for ($i=0; $i -lt 36; $i++) {
    Start-Sleep -Seconds 5
    $runs2 = Invoke-RestMethod -Headers $headers -Uri "https://api.github.com/repos/$owner/$repo/actions/runs?branch=$branch&per_page=10"
    $candidate = $runs2.workflow_runs | Sort-Object created_at -Descending | Select-Object -First 1
    if ($candidate.created_at -ne $latest.created_at) { $runToWatch = $candidate.id; Write-Host "Detected new run id: $runToWatch created_at: $($candidate.created_at)"; break }
    Write-Host "[poll $i] no new run yet (latest id $($candidate.id) created_at $($candidate.created_at))"
}

Write-Host "Watching run id $runToWatch until it completes (timeout ~10 minutes)"
for ($i=0; $i -lt 120; $i++) {
    Start-Sleep -Seconds 5
    $runInfo = Invoke-RestMethod -Headers $headers -Uri "https://api.github.com/repos/$owner/$repo/actions/runs/$runToWatch"
    Write-Host "[poll $i] status=$($runInfo.status)  conclusion=$($runInfo.conclusion)"
    if ($runInfo.status -eq 'completed') { Write-Host 'Run completed'; break }
}

if ($runInfo.status -ne 'completed') { Write-Host "Run did not complete in time (last status: $($runInfo.status))"; exit 4 }

# Download and extract logs
$zipFile = Join-Path (Get-Location) ("logs_rerun_$runToWatch.zip")
Write-Host "Downloading logs to $zipFile ..."
Invoke-WebRequest -Headers $headers -Uri $runInfo.logs_url -OutFile $zipFile
$dest = Join-Path (Get-Location) ("logs_rerun_$runToWatch")
if (Test-Path $dest) { Remove-Item -Recurse -Force $dest }
Expand-Archive -Force -Path $zipFile -DestinationPath $dest
Write-Host "Extracted logs to $dest"

# Search for files containing the step names and print them
$patterns = 'Inspect pubspec','Install dependencies'
$txtFiles = Get-ChildItem -Path $dest -Recurse -Filter '*.txt' -ErrorAction SilentlyContinue
$found = @()
foreach ($f in $txtFiles) {
    foreach ($p in $patterns) {
        if (Select-String -Path $f.FullName -Pattern $p -SimpleMatch -Quiet) { $found += $f.FullName; break }
    }
}

if (-not $found) {
    Write-Host 'No matching step log files found. Listing extracted files (first 200):'
    Get-ChildItem -Path $dest -Recurse | Select-Object -First 200 | ForEach-Object { Write-Host $_.FullName }
    Write-Host "Logs zip: $zipFile; extracted to: $dest"
    exit 0
}

foreach ($path in $found | Sort-Object) {
    Write-Host "---- File: $path ----"
    Get-Content $path -TotalCount 400 | ForEach-Object { Write-Host $_ }
    Write-Host "---- end ----`n"
}

Write-Host "Saved zip: $zipFile; extracted to: $dest"

# End of script
